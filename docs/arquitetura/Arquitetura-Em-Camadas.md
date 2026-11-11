# Arquitetura em camadas – Sistema de pedidos multicanal
## Visão geral
O projeto é dividido em quatro camadas: Domain, Application, Infrastructure e API. É uma Clean Architecture simplificada, sem depender de framework específico. O que importa é a separação de responsabilidades e a regra de dependência abaixo.

**Regra de dependência:** a seta sempre aponta para dentro.

1. A API conhece a Application e o Domain. Nenhum arquivo da API, incluindo o dependencies.py, importa a Infrastructure.

2. A Application conhece só o Domain.

3. O Domain não conhece ninguém.

4. A Infrastructure conhece a Application e o Domain, porque implementa as interfaces (portas) que a Application define e converte entre os modelos de tabela do banco e as entidades do Domain. A Application nunca importa a Infrastructure, e o Domain nunca depende dela.

`API  ->  Application  ->  Domain`

`              ^`

`              |  (implementa as interfaces)`

`        Infrastructure`

A montagem de tudo (qual repositório entra em qual caso de uso) fica em um único lugar: o container.py, na raiz de app/, chamado pelo main.py. Esses dois arquivos são os únicos que conhecem as quatro camadas. O resto da API recebe os casos de uso já prontos e não importa a Infrastructure.

**Tecnologias:** Python com FastAPI (API), SQLAlchemy e Alembic (persistência e migrations) e banco MySQL, que eu modelo e consulto pelo MySQL Workbench. Os testes usam pytest. A injeção de dependências usa o Depends do FastAPI, mas só para entregar à rota o caso de uso já montado pelo container.py.

O SQLAlchemy é usado no modo síncrono (rotas def), por ser mais simples e suficiente para o trabalho. O banco é o MySQL 8.0.
## Domain (domínio)
**Responsabilidade:** as entidades, as regras de negócio e as validações. É o que continuaria igual se trocássemos o banco ou o framework.

**O que tem:** 

1. Entidades: Pedido, ItemPedido, Produto, ItemCardapio (preço e ativo de um produto em uma unidade), Estoque, Unidade, Usuário (Cliente), Pagamento e Consentimento.

2. Tipos fixos: CanalPedido, StatusPedido, ResultadoPagamento e perfil do usuário.

3. Regras que ficam nas entidades: as transições válidas de status do pedido, a validação dos itens (quantidade inteira maior ou igual a 1, sem produto repetido), o cálculo do total a partir do preço do ItemCardapio, o estoque disponível (quantidade menos reservada), a regra de reservar, liberar e baixar, o consentimento ativo e o cálculo dos pontos (1 por R$ 1,00, arredondado para baixo).

4. Erros de domínio: DadosInvalidos, EstoqueInsuficiente e TransicaoInvalida. A reserva vencida não é um erro do Domain: o Pedido só informa se a reserva venceu (por exemplo, reserva_venceu(agora)), e a Application decide o que fazer e devolve o resultado ReservaExpirada.

**O que não pode ter:** HTTP, SQL, JWT, ORM ou qualquer biblioteca de framework.
## Application (aplicação)
**Responsabilidade:** os casos de uso. Cada um orquestra um fluxo: abre a transação, chama os repositórios, chama o gateway, aplica as regras do domínio e grava a auditoria. Não tem regra de negócio própria nem detalhe técnico.

**Casos de uso:** 

1. CriarPedido (UC4, passos 1 a 4)

2. PagarPedido (UC4, passos 5 a 11, inclui aplicar fidelidade)

3. ConsultarCardapio (UC3, RF04)

4. CancelarPedido

5. AtualizarStatusPedido

6. ListarPedidos

7. CadastrarUsuario e Login

8. ConsultarAuditoria

**Portas (interfaces) que ela define:** 

1. PedidoRepository, EstoqueRepository, PagamentoRepository, UsuarioRepository, ConsentimentoRepository e AuditoriaRepository.

2. CardapioRepository e UnidadeRepository: buscar a unidade e o ItemCardapio (preço e ativo) de um produto naquela unidade. São elas que permitem o 404 do UC4 e o preço do servidor.

3. PagamentoGateway (o pagamento externo).

4. TokenService (gerar e validar o token), para a API autenticar sem importar a Infrastructure.

5. Transação (para o pedido, a reserva e o estoque ficarem na mesma operação).

6. Relógio (devolve a hora atual, para o teste poder simular os 10 minutos).

7. Configuração do prazo da reserva.

Também ficam aqui os objetos de entrada e saída de cada caso de uso (DTOs).

**Erros da Application:** NaoEncontrado (unidade, produto ou pedido inexistente, ou pedido de outro cliente; vira 404) e Conflito (pedido já pago ou cancelado, ou troca de status que não afetou nenhuma linha; vira 409). A reserva vencida, a recusa e o erro do gateway não são erros: são resultados devolvidos pelo caso de uso.

**O que não pode ter:** HTTP, SQL, nem classes concretas da Infrastructure.
## Infrastructure (infraestrutura)
**Responsabilidade:** os detalhes técnicos. Implementa as portas da Application.

**O que tem:** 

1. Persistência: SQLAlchemy 2 com o driver PyMySQL. Os modelos de tabela (ORM) ficam só aqui e são separados das entidades do Domain; o repositório converte um no outro. As migrations são do Alembic e criam as tabelas do DER.

2. Operações atômicas no banco: o UPDATE condicional da reserva do estoque e o UPDATE ... WHERE status = 'AGUARDANDO_PAGAMENTO' que garante o invariante (RN 4, RN 5 e RN 7). A regra é do domínio, mas a garantia de que ela vale mesmo com duas requisições ao mesmo tempo vem do banco. Por isso a porta devolve se o UPDATE afetou 1 linha (o rowcount do SQLAlchemy), e a Application só segue se afetou.

3. GatewayPagamentoMock: o gateway simulado, que lê o simularResultado (RN 10).

4. Segurança: hash de senha (bcrypt) e a implementação do TokenService com JWT.

5. Configuração: o prazo da reserva (600 segundos no padrão, 2 segundos no ambiente de teste), lida de variável de ambiente com pydantic-settings.

6. Log e relógio real.

7. Transação: uma sessão do SQLAlchemy por requisição. O caso de uso faz commit quando termina, inclusive nos resultados que precisam ficar gravados mesmo sendo uma falha (reserva vencida e erro do gateway). O rollback fica para erros antes de gravar algo (validação, 404, estoque insuficiente) e para erros inesperados.
## API (interface)
**Responsabilidade:** receber a requisição HTTP e devolver a resposta. É só tradução: converte o request em chamada de caso de uso e converte o resultado (ou o erro) em resposta.

**O que tem:** 

1. Rotas e controllers (os routers do FastAPI).

2. Autenticação (401 sem token ou token inválido) e autorização por perfil (403), feitas como dependências do FastAPI que usam a porta TokenService.

3. Validação do formato do corpo (campo ausente, tipo errado) com os schemas do Pydantic. As regras de negócio dos dados (quantidade menor que 1, produto repetido) ficam no Domain; nos dois casos a resposta é 422, o mesmo código que o FastAPI já usa por padrão nos erros do Pydantic.

4. Contratos de request e response (schemas do Pydantic, separados das entidades do Domain).

5. Tratamento central de erros (exception handlers), no padrão do projeto: error, message, details, timestamp, path. Inclui trocar o formato de erro padrão do FastAPI por esse.

6. Paginação do RF10 (page e limit).

7. Swagger/OpenAPI, gerado automaticamente pelo FastAPI em /docs.

**O que não pode ter:** regra de negócio nem acesso direto ao banco. Um controller não calcula total, não confere estoque e não muda status.
## Estrutura de pastas
Estrutura de pastas em Python:

`app/`

`  domain/`

`    entities/        pedido.py, item_pedido.py, produto.py, item_cardapio.py,`

`                     estoque.py, unidade.py, usuario.py, pagamento.py,`

`                     consentimento.py`

`    enums.py         CanalPedido, StatusPedido, ResultadoPagamento`

`    errors.py        erros de domínio`

`  application/`

`    use_cases/       criar_pedido.py, pagar_pedido.py, consultar_cardapio.py,`

`                     cancelar_pedido.py...`

`    ports/           interfaces dos repositórios (incluindo cardapio e unidade),`

`                     do gateway, do token e do relógio`

`    dto.py           entrada e saída dos casos de uso`

`  infrastructure/`

`    database.py      conexão e sessão do SQLAlchemy`

`    persistence/     models.py (tabelas) e repositórios`

`    migrations/      Alembic`

`    payment/         gateway_mock.py`

`    security/        hash de senha e JWT (implementa o TokenService)`

`    config.py        prazo da reserva e demais configurações`

`  api/`

`    routers/         auth.py, cardapio.py, pedidos.py, estoque.py, auditoria.py...`

`    schemas/         contratos de request e response (Pydantic)`

`    dependencies.py  autenticação, perfil e entrega dos casos de uso prontos`

`                     (não importa a Infrastructure)`

`    error_handlers.py`

`  container.py       monta repositórios e casos de uso (único que liga as camadas)`

`  main.py            cria o app FastAPI e chama o container`

`tests/`

`  domain/            testes unitários das regras`

`  application/       casos de uso com repositórios falsos`

`  api/               testes de integração`

`postman/             coleção Postman`

`docker-compose.yml   MySQL 8.0 para rodar o projeto`

`.env.example         variáveis de ambiente de exemplo`

O Domain usa classes Python simples (dataclass), sem Pydantic e sem SQLAlchemy. As portas da Application são interfaces (Protocol ou classes abstratas).
## O UC4 atravessando as camadas
**POST /pedidos (passos 1 a 4)** 

1. API: confere o token (401) e o perfil CLIENTE (403), valida o formato do corpo e chama CriarPedido.

2. Application: abre a transação e libera as reservas vencidas. Busca a unidade e o ItemCardapio de cada produto pelo CardapioRepository (404 se a unidade ou o produto não existir ou não estiver ativo).

3. Domain: Pedido valida os itens, calcula o total com os preços do ItemCardapio e nasce AGUARDANDO_PAGAMENTO.

4. Application: reserva todos os itens pela porta do estoque (409 se algum não cabe, e a transação desfaz o resto), salva o pedido, grava a auditoria e confirma a transação.

5. API: responde 201 com o pedido.

**POST /pedidos/{id}/pagamento (passos 5 a 11)** 

1. API: confere token e perfil e chama PagarPedido com o id e o simularResultado opcional.

2. Application: busca o pedido do cliente (404 se não existir ou for de outro cliente) e pergunta ao Domain se ainda dá para pagar. Se já foi pago ou cancelado, devolve o resultado de conflito (409). Se a reserva venceu (o Domain só informa que venceu), a Application cancela o pedido, libera a reserva, confirma no banco (commit) e só então devolve o resultado ReservaExpirada (409).

3. Application: chama o PagamentoGateway. A Infrastructure responde com o resultado do mock.

4. Application: grava o PAGAMENTO com o resultado. Se aprovado, tenta mudar o pedido para PAGO pelo UPDATE condicional, baixa o estoque (pelas operações atômicas) e o Domain calcula os pontos, que só são creditados com consentimento ativo. Se o UPDATE não afetar 1 linha (por exemplo, o pedido foi cancelado ao mesmo tempo), devolve conflito (409) e não baixa estoque nem credita pontos. Se recusado, cancela o pedido e libera a reserva. Se der erro no gateway, o pedido continua aguardando.

5. Application: grava a auditoria e confirma a transação. No erro do gateway, o registro do PAGAMENTO (ERRO_GATEWAY) e a auditoria também são confirmados, mesmo com a resposta de erro.

6. API: aprovado responde 200 com o pedido PAGO e os pontos creditados. Recusado responde 200 com o pedido CANCELADO e o motivo. Erro do gateway responde 502. Reserva vencida responde 409.
## Transação e resultados que precisam ficar gravados
O PagarPedido não lança exceção nos casos em que o banco precisa guardar o que aconteceu: reserva vencida (o cancelamento e a liberação), pagamento recusado e erro do gateway (o registro do PAGAMENTO). Nesses casos o caso de uso faz o commit e devolve um resultado (por exemplo PAGO, RECUSADO, ERRO_GATEWAY, RESERVA_EXPIRADA), e a API traduz o resultado em 200, 502 ou 409. Exceção com rollback fica para quando nada deve ser gravado: dados inválidos, 404, estoque insuficiente e erros inesperados.
## Onde fica cada regra de negócio do UC4
1. RN 1 (dados válidos): Domain, com a checagem de formato na API.

2. RN 2 (cardápio da unidade): Application, consultando o CardapioRepository e o UnidadeRepository.

3. RN 3 (preço e total do servidor): Domain, a partir do ItemCardapio.

4. RN 4 (reserva de 10 minutos): Domain, com a garantia atômica na Infrastructure.

5. RN 5 (tudo ou nada): Application, pela transação.

6. RN 6 (reservas vencidas): Application chama, Infrastructure executa.

7. RN 7 (status do pedido): Domain, com o UPDATE condicional na Infrastructure.

8. RN 8 (chamada ao gateway): Application.

9. RN 9 (pedido do próprio cliente): Application.

10. RN 10 (controle do mock): campo na API e comportamento na Infrastructure.

11. RN 11 (registro das tentativas): Application.

12. RN 12 (pontos): Domain calcula, Application aplica.

13. RN 13 (auditoria): Application.
## Erros e códigos HTTP
Os erros nascem no Domain e na Application, sem saber de HTTP. Só a API traduz:

1. DadosInvalidos: 422.

2. Não autenticado: 401. Sem permissão: 403.

3. NaoEncontrado (unidade, produto, pedido): 404.

4. Conflito (EstoqueInsuficiente, pedido já pago ou cancelado, troca de status que não afetou nenhuma linha): 409.

5. Erro do gateway: 502.

6. Pagamento recusado não é erro: responde 200 com o pedido CANCELADO e o motivo.

7. Reserva expirada (409), recusa (200) e erro do gateway (502) são resultados devolvidos depois do commit, e não exceções que desfazem a transação.
## Como cada camada é testada
1. Prioridade: a coleção Postman, que é obrigatória, cobrindo os fluxos do UC4 com o prazo curto da reserva (2 segundos).

2. Domain: testes unitários com pytest, sem banco e sem servidor.

3. UC4 (CriarPedido e PagarPedido): testes com repositórios falsos em memória e um relógio falso, o que permite testar a expiração sem esperar 10 minutos.

4. Os demais casos de uso e os testes com TestClient contra um banco MySQL de teste ficam por último, se houver tempo.
## Execução e README
O README precisa permitir rodar o projeto do zero:

1. docker-compose.yml com o MySQL 8.0, para quem não tem o MySQL instalado.

2. .env.example com a DATABASE_URL, o prazo da reserva e a chave do JWT.

3. Passos: copiar o .env.example para .env, subir o banco (docker compose up -d), rodar as migrations (alembic upgrade head), rodar o seed (usuários de cada perfil, unidades, produtos, cardápio e estoque) e iniciar o servidor (uvicorn app.main:app).

4. Onde estão o Swagger (/docs) e a coleção Postman, e como rodar com o prazo curto.

5. Alternativa se faltar tempo ou o avaliador não tiver Docker nem MySQL: apontar a DATABASE_URL para SQLite, já que o SQLAlchemy permite trocar só a URL. Só documentar isso depois de testar o projeto com SQLite.
## Ordem de implementação
Implementar por fatia vertical, atravessando as quatro camadas em cada passo, e não camada por camada. A coleção Postman cresce a cada fatia.

1. Base: configuração, conexão com o banco, migrations e seed.

2. Login: cadastro, login, token e perfil.

3. Cardápio: consultar o cardápio da unidade (RF04).

4. Criar pedido: validações, preço do servidor, reserva do estoque.

5. Pagar pedido: mock, recusa, falha do gateway e vencimento da reserva.

6. Fidelidade e auditoria.

7. Atualizar o status do pedido (RF08) e listar pedidos com paginação (RF10). Fazem parte do fluxo mínimo pedido, pagamento e status.

8. Cancelamento do pedido pelo cliente (RF11a), só se houver tempo. O cancelamento feito pelo sistema (recusa e vencimento) já está no item 5.
## Em aberto
1. Os nomes dos endpoints serão ajustados quando o Swagger existir.

2. Decidir se o SQLite entra como alternativa documentada no README (depende do tempo).
