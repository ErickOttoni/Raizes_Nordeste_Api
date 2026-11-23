# Raízes do Nordeste API

API back-end da rede de lanchonetes **Raízes do Nordeste**, desenvolvida para o Projeto Multidisciplinar (trilha Back-End, Uninter). A entrega implementa o **Fluxo A**: criar pedido, pagar (gateway simulado) e atualizar o status, com autenticação JWT por perfil, reserva de estoque, programa de fidelidade condicionado a consentimento (LGPD) e trilha de auditoria.

- Repositório: https://github.com/ErickOttoni/Raizes_Nordeste_Api
- Swagger/OpenAPI (com o servidor rodando): http://127.0.0.1:8000/docs
- Coleção Postman: [`postman/Raizes-Nordeste.postman_collection.json`](postman/Raizes-Nordeste.postman_collection.json)

## Tecnologias

| Item | Versão / escolha |
|---|---|
| Linguagem | Python 3.12 |
| Framework | FastAPI + Uvicorn |
| Banco de dados | MySQL 8.0 |
| ORM e migrations | SQLAlchemy 2 (síncrono) + PyMySQL + Alembic |
| Configuração | pydantic-settings (arquivo `.env`) |
| Autenticação | JWT (PyJWT, HS256) e senhas com bcrypt |
| Testes | Coleção Postman (76 verificações em 41 requisições) |

## Arquitetura

Camadas inspiradas em Clean Architecture, com dependências apontando sempre para dentro:

```
app/
  domain/          # entidades, enums e erros de domínio (sem framework)
  application/     # casos de uso e ports (interfaces)
  infrastructure/  # MySQL/SQLAlchemy, JWT, bcrypt, gateway mock, config, seed
  api/             # routers FastAPI, schemas, dependências e tratamento de erros
  container.py     # composição: liga as ports às implementações
  main.py          # criação da aplicação
alembic/           # migrations
postman/           # coleção de testes
docs/              # casos de uso, DER, requisitos e arquitetura
```

A camada `api` nunca importa `infrastructure`: as dependências são ligadas em `container.py` por meio de `dependency_overrides`.

## Requisitos

- Python 3.12
- MySQL 8.0 em execução
- Git

## Instalação

Os comandos abaixo são para Windows (PowerShell). Em Linux/macOS, troque a ativação do ambiente virtual por `source .venv/bin/activate`.

```powershell
git clone https://github.com/ErickOttoni/Raizes_Nordeste_Api.git
cd Raizes_Nordeste_Api

py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente virtual:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Configuração

1. Crie o banco e o usuário no MySQL (ajuste a senha):

```sql
CREATE DATABASE raizes_nordeste CHARACTER SET utf8mb4;
CREATE USER 'raizes'@'localhost' IDENTIFIED BY 'troque-esta-senha';
GRANT ALL PRIVILEGES ON raizes_nordeste.* TO 'raizes'@'localhost';
FLUSH PRIVILEGES;
```

2. Copie o arquivo de exemplo e preencha os valores:

```powershell
copy .env.example .env
```

| Variável | Descrição | Exemplo |
|---|---|---|
| `DATABASE_URL` | String de conexão com o MySQL | `mysql+pymysql://raizes:SENHA@localhost:3306/raizes_nordeste` |
| `JWT_SECRET` | Segredo para assinar tokens (mínimo 32 caracteres) | gere com o comando abaixo |
| `JWT_EXPIRE_MINUTES` | Validade do token em minutos | `60` |
| `RESERVA_TTL_SEGUNDOS` | Tempo da reserva de estoque | `600` (10 minutos) |

Para gerar um segredo JWT:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

O arquivo `.env` não é versionado.

## Migrations e dados iniciais

```powershell
alembic upgrade head
python -m app.infrastructure.seed
```

O seed é idempotente: se já existir usuário no banco, ele não faz nada. Para recomeçar do zero, apague e recrie o banco (ou rode `alembic downgrade base`, `alembic upgrade head` e o seed de novo).

Dados criados pelo seed:

- **Unidades:** Recife (id 1) e Fortaleza (id 2)
- **Produtos:** Tapioca (id 1, R$ 12,00), Cuscuz (id 2, R$ 10,00), Baião de dois (id 3, R$ 25,00), Suco de caju (id 4, R$ 8,00)
- **Estoque:** 10 unidades de cada produto por unidade, exceto Baião de dois em Recife, com 2

Usuários de teste (senha de todos: `senha123`):

| E-mail | Perfil | Observação |
|---|---|---|
| `cliente@teste.com` | CLIENTE | consentimento de fidelidade aceito |
| `cliente2@teste.com` | CLIENTE | sem consentimento (não acumula pontos) |
| `atendente@teste.com` | ATENDENTE | unidade Recife |
| `cozinha@teste.com` | COZINHA | unidade Recife |
| `gerente@teste.com` | GERENTE | acesso à auditoria |

## Executando

```powershell
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- OpenAPI (JSON): http://127.0.0.1:8000/openapi.json

Para autenticar no Swagger: faça `POST /auth/login`, copie o `access_token`, clique em **Authorize** e cole o token.

## Endpoints

| Método | Rota | Perfil | Descrição |
|---|---|---|---|
| POST | `/auth/login` | público | Autentica e devolve o token JWT |
| GET | `/auth/me` | qualquer autenticado | Dados do usuário logado |
| GET | `/unidades/{unidade_id}/cardapio` | qualquer autenticado | Cardápio ativo da unidade |
| POST | `/pedidos` | CLIENTE | Cria o pedido e reserva o estoque (status `AGUARDANDO_PAGAMENTO`) |
| POST | `/pedidos/{pedido_id}/pagamento` | CLIENTE | Paga o pedido no gateway simulado |
| GET | `/auditoria?page=1&limit=10` | GERENTE | Consulta paginada da trilha de auditoria |

Exemplo de criação de pedido:

```json
{
  "unidadeId": 1,
  "canalPedido": "APP",
  "itens": [{ "produtoId": 4, "quantidade": 1 }]
}
```

`canalPedido` aceita `APP`, `TOTEM`, `BALCAO`, `PICKUP` e `WEB`. Esta entrega aceita pedidos de cliente pelos canais digitais; `BALCAO` é rejeitado com 422.

Exemplo de pagamento (o corpo é opcional; sem ele o resultado é `APROVADO`):

```json
{ "simularResultado": "APROVADO" }
```

Valores aceitos: `APROVADO`, `RECUSADO` e `ERRO_GATEWAY`.

## Regras de negócio principais

- O **preço vem sempre do cardápio**, nunca do corpo da requisição.
- O estoque é **reservado por 10 minutos** na criação do pedido (`RESERVA_TTL_SEGUNDOS`). A reserva é feita com um `UPDATE` condicional atômico, que impede vender além do estoque mesmo com pedidos simultâneos.
- Reservas vencidas são liberadas ao consultar disponibilidade. Pagar depois do prazo cancela o pedido e retorna 409.
- A **baixa definitiva do estoque** só ocorre após o pagamento aprovado.
- Pagamento recusado cancela o pedido e libera a reserva. Falha do gateway retorna 502 e mantém a reserva.
- **Fidelidade:** 1 ponto por R$ 1,00 (valor truncado), creditado apenas se o cliente tiver consentimento ativo (aceito e não revogado).
- Um pedido já pago ou cancelado responde 409; pedido inexistente ou de outro cliente responde 404.

## Padrão de erros

Todas as respostas de erro seguem o mesmo formato:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Dados inválidos.",
  "details": [],
  "timestamp": "2026-11-21T19:00:00Z",
  "path": "/auditoria"
}
```

| Código HTTP | `error` |
|---|---|
| 401 | `UNAUTHORIZED` |
| 403 | `FORBIDDEN` |
| 404 | `NOT_FOUND` |
| 409 | `CONFLICT` |
| 422 | `VALIDATION_ERROR` |
| 502 | `BAD_GATEWAY` (falha do gateway de pagamento) |

## Testes (coleção Postman)

Os testes são feitos pela coleção em `postman/Raizes-Nordeste.postman_collection.json`, com **41 requisições** e **76 verificações automáticas**.

1. Suba a API (`uvicorn app.main:app --reload`) com o banco migrado e o seed aplicado.
2. No Postman, use **Import** e selecione o arquivo `.json` da coleção.
3. Clique na coleção > **Run collection**, mantenha as pastas **1 a 5** marcadas, desmarque a pasta 6 e clique em **Run**.

| Pasta | Conteúdo |
|---|---|
| 1. Autenticação | Logins dos perfis, senha errada, corpo inválido, `/auth/me` com e sem token |
| 2. Cardápio | Cardápio da unidade, unidade inexistente, sem token |
| 3. Criar pedido: erros | Perfil sem permissão, canal inválido, produto inexistente, estoque insuficiente e outras validações |
| 4. Pedido e pagamento (Fluxo A) | Pedido, pagamento aprovado, recusado, repetido, de outro cliente, pontos de fidelidade |
| 5. Auditoria (RF32) | Consulta do gerente, paginação, 422, 403 e 401 |
| 6. Opcional | Reserva vencida (exige `RESERVA_TTL_SEGUNDOS=2` no `.env` e reiniciar a API) |

Observações:

- Rode sempre a coleção completa (pastas 1 a 5 em ordem): o login da pasta 1 grava os tokens usados pelas demais.
- Cada execução consome estoque (1 suco e 1 cuscuz). Para repetir os testes, restaure o banco: `alembic downgrade base`, `alembic upgrade head` e `python -m app.infrastructure.seed`.

## LGPD

| Dado tratado | Finalidade | Base legal |
|---|---|---|
| Nome, e-mail e senha (armazenada apenas como hash bcrypt) | Identificar e autenticar o usuário | Execução de contrato |
| Dados do pedido e do pagamento | Processar a compra e o histórico de atendimento | Execução de contrato |
| Consentimento de fidelidade (aceite, data e revogação) | Acumular pontos do programa de fidelidade | Consentimento (art. 7º, I) |
| Logs de auditoria | Rastrear ações relevantes e prevenir fraudes | Legítimo interesse e obrigação de segurança |

- Sem consentimento ativo, o pedido é processado normalmente, mas nenhum ponto é creditado.
- O consentimento fica registrado em tabela própria, com possibilidade de revogação (`revogadoEm`).
- Senhas nunca são armazenadas nem registradas em texto puro.

## Documentação

Os documentos de projeto estão em `docs/`: diagrama de casos de uso, descrição do caso de uso UC4 (Realizar o Pedido), DER, requisitos e arquitetura em camadas.

## Escopo desta entrega

Implementado: autenticação por perfil, cardápio, criação de pedido com reserva de estoque, pagamento com gateway simulado, fidelidade condicionada a consentimento e consulta de auditoria.

Previsto, mas fora desta entrega: cadastro de cliente com registro de consentimento via API, alteração de status do pedido pela cozinha/atendente, listagem de pedidos com paginação e cancelamento pelo cliente.
