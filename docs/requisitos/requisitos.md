# Requisitos do sistema de pedidos multicanal

Versão em Markdown da planilha `requisitos_pedidos.xlsx`, que é a fonte. Em caso de diferença, vale a planilha.

## Requisitos funcionais (RF)

Canais válidos de canalPedido: APP, TOTEM, BALCAO, PICKUP, WEB. Escopo 'Implementado' = fluxo fechado pedido → pagamento → status, mais LGPD e pontos; o restante é 'Proposto' (prazo de entrega: 23/11).

| ID | Módulo | Descrição | UC | Prioridade | Escopo | Se apertar o prazo |
|---|---|---|---|---|---|---|
| RF01 | Acesso | Cadastrar clientes. O cadastro aceita o campo opcional consentimentoFidelidade (true ou false) e sempre cria a linha de consentimento (aceito = false quando o campo não vem), com data/hora e finalidade; recusar não impede o cadastro nem o uso do sistema. Os usuários de teste de login nascem por esta API. | UC1 | Essencial | Implementado |  |
| RF02 | Acesso | Autenticar usuários com token JWT. | UC2 | Essencial | Implementado |  |
| RF03 | Acesso | Autorizar cada endpoint por perfil (cliente, atendente, cozinha, gerente). | UC2 | Essencial | Implementado |  |
| RF04 | Cardápio | Exibir o cardápio da unidade escolhida. | UC3 | Essencial | Implementado |  |
| RF05 | Cardápio | Gerenciar produtos e cardápio por unidade. | UC22 | Importante | Proposto |  |
| RF06 | Pedidos | Criar pedido com unidadeId, itens e canalPedido (APP, TOTEM, WEB ou PICKUP; obrigatório, validado e filtrável). O cliente vem do token JWT. Retorna 400/422 se canalPedido estiver ausente ou inválido e 404 se a unidade ou o produto não existir ou se o produto não estiver ativo no cardápio da unidade. O pedido nasce em AGUARDANDO_PAGAMENTO. | UC4 | Essencial | Implementado |  |
| RF07 | Pedidos | Registrar pedido no balcão com canal BALCAO gravado automaticamente. | UC13 | Importante | Proposto |  |
| RF08 | Pedidos | Controlar o status do pedido e permitir só as transições válidas (ver aba 'Status e cancelamento'). | UC16 | Essencial | Implementado |  |
| RF09 | Pedidos | Acompanhar o status do próprio pedido. | UC5 | Importante | Proposto | Cortado para compensar a volta do RF32. A resposta da criação do pedido já devolve o status. |
| RF10 | Pedidos | Listar pedidos para atendente e cozinha, com paginação (page e limit, por exemplo ?page=1&limit=10) e filtro por status e por canal. Atendente e cozinha veem só os pedidos da própria unidade (USUARIO.unidadeId). | UC17 | Importante | Implementado |  |
| RF11a | Pedidos | Cancelar pedido em AGUARDANDO_PAGAMENTO: o cliente cancela o próprio pedido, e o sistema cancela quando o pagamento é recusado ou a reserva vence. A reserva é liberada. | UC6 | Essencial | Implementado | Corte 1, se ainda apertar (manter o cancelamento pelo sistema). |
| RF11b | Pedidos | Cancelar pedido já pago ou em preparo (cliente até PAGO, atendente em pedido de balcão até PAGO, gerente até PRONTO), com estorno registrado (mock), devolução do estoque e reversão de pontos. | UC6 | Importante | Proposto |  |
| RF12 | Pedidos | Ajustar ou reabrir pedido (gerente). | UC18 | Desejável | Proposto |  |
| RF13 | Estoque | Validar o estoque da unidade ao criar o pedido, reservar os itens por 10 minutos e recusar a venda de item indisponível (409). A reserva fica na coluna quantidadeReservada do estoque por unidade/produto, e o pedido guarda reservaExpiraEm. Antes de calcular o disponível, o sistema libera todas as reservas vencidas, e não só as do pedido consultado. | UC27 | Essencial | Implementado |  |
| RF14 | Estoque | Baixar o estoque após o pagamento aprovado; liberar a reserva se o pagamento for recusado, o pedido cancelado ou a reserva vencer. Reservas vencidas são liberadas por checagem na hora (ao criar, consultar ou pagar pedido), sem job em segundo plano. Pagar um pedido depois dos 10 minutos cancela o pedido e retorna erro (409, motivo 'reserva expirada'), sem aprovar o pagamento. | UC27 | Essencial | Implementado |  |
| RF15 | Estoque | Gerenciar o estoque por unidade. | UC19 | Importante | Proposto |  |
| RF16 | Pagamento | Solicitar o pagamento ao gateway (mock). | UC11 | Essencial | Implementado |  |
| RF17 | Pagamento | Receber o resultado do gateway (aprovado ou recusado) e atualizar o status do pedido: PAGO se aprovado; CANCELADO com motivo registrado se recusado. | UC11 | Essencial | Implementado |  |
| RF18 | Pagamento | Registrar o pagamento de cada pedido (forma, valor, resultado, data/hora). | UC14 | Essencial | Implementado |  |
| RF19 | Pagamento | Receber pagamento em dinheiro no balcão. | UC15 | Importante | Proposto |  |
| RF20 | Fidelidade e LGPD | Registrar a escolha de consentimento de fidelidade (aceite ou recusa, com data/hora e finalidade), capturada opcionalmente no cadastro. O consentimento é independente do cadastro: o serviço não depende dele, e o UC8 continua como caso de uso próprio. | UC8 | Essencial | Implementado |  |
| RF21 | Fidelidade e LGPD | Revogar o consentimento a qualquer momento. | UC26 | Importante | Proposto |  |
| RF22 | Fidelidade e LGPD | Acumular pontos após o pagamento aprovado, só se consentimentoFidelidade for true (com false o pagamento segue normal e não há crédito, usado como teste negativo): 1 ponto por R$ 1,00 pago, arredondado para baixo. Pedido recusado ou cancelado não gera pontos. O saldo fica na coluna saldoPontos do cliente e o valor creditado aparece na resposta do pagamento aprovado. | UC7 | Importante | Implementado |  |
| RF23 | Fidelidade e LGPD | Consultar saldo de pontos. Exige consentimento ativo. | UC10 | Importante | Proposto | Já cortado do escopo implementado. |
| RF24 | Fidelidade e LGPD | Resgatar pontos. Exige consentimento ativo. | UC9 | Importante | Proposto |  |
| RF25 | Promoções | Aplicar promoção ou campanha ao pedido. | UC28 | Desejável | Proposto |  |
| RF26 | Promoções | Gerenciar promoções e campanhas. | UC29 | Desejável | Proposto |  |
| RF27 | Gestão | Gerenciar usuários e perfis. | UC20 | Importante | Proposto |  |
| RF28 | Gestão | Gerenciar unidades. | UC21 | Importante | Proposto |  |
| RF29 | Gestão | Emitir relatórios: vendas por unidade e região, produtos mais consumidos e financeiros. | UC23 | Importante | Proposto |  |
| RF30 | Gestão | Consultar pedidos agrupados por canal (com filtro por canalPedido). | UC24 | Importante | Proposto |  |
| RF31 | Auditoria | Gravar registro (usuário, ação, data/hora, estado anterior e novo) nas operações críticas implementadas: pagamento (aprovado e recusado), cancelamento, reserva/baixa/liberação de estoque, mudança de status, consentimento e crédito de pontos. Estorno e reversão de pontos passam a ser auditados quando o RF11b for implementado. | UC25 | Essencial | Implementado |  |
| RF32 | Auditoria | Consultar os logs de auditoria (GET /auditoria), somente gerente; cliente recebe 403. Serve de evidência de auditoria na coleção Postman e de caso para o teste de 403. | UC25 | Essencial | Implementado |  |

## Requisitos não funcionais (RNF)

| ID | Categoria | Descrição | Como verificar | Escopo | Se apertar o prazo |
|---|---|---|---|---|---|
| RNF01 | Segurança | JWT com expiração, senha em hash, autorização por perfil e nenhum dado de cartão armazenado. HTTPS é proposta: o ambiente local roda em HTTP, e isso será declarado no documento. | Testes de endpoints com perfis diferentes (401/403); inspeção do banco. | Implementado (HTTPS: Proposto) |  |
| RNF02 | LGPD | Consentimento de fidelidade opcional, registrado no cadastro (aceite ou recusa, data/hora e finalidade) e exigido só para pontos; o serviço não depende dele. O registro de acesso a dados sensíveis (UC20) fica como proposta, junto com a gestão de usuários. Anonimização após revogação ou inatividade (sugestão: 12 meses), mantendo pedidos e logs sem identificação, e a política de retenção ficam como proposta: exigem rotina agendada e definição de prazos legais, fora do prazo de 23/11. Prazos a ajustar ao caso. | Cadastro com consentimentoFidelidade true gera crédito de pontos; com false, não gera (teste negativo). Anonimização, retenção e log de acesso a dados sensíveis não têm teste (proposta). | Consentimento: Implementado. Anonimização, retenção e log de acesso a dados sensíveis: Proposto |  |
| RNF03 | Desempenho e disponibilidade | Meta, não garantia: no pico (hipótese: 50 pedidos/min por unidade), p95 <= 2 s na criação do pedido. Disponibilidade-alvo de 99,5% (cerca de 3,6 h de queda/mês), justificada pelo uso em horário comercial. | Teste de carga simples para o p95; a disponibilidade não é verificável localmente. | Proposto |  |
| RNF04 | Tolerância a falha do gateway | Falha do gateway (erro do mock) não perde o pedido: ele fica AGUARDANDO_PAGAMENTO com a reserva ativa e aceita nova tentativa dentro dos 10 min. Passado o prazo, é cancelado e a reserva liberada (checagem na hora, ver RF14). O timeout real de 5 s e o pagamento em dinheiro como alternativa no balcão (UC15) ficam como proposta. | Mock configurado para falhar; conferir status, reserva e nova tentativa. | Implementado (timeout de 5 s: Proposto) | Timeout de 5 s já cortado. |
| RNF05 | Auditoria | Registros imutáveis: a API não expõe alteração nem exclusão de logs, e o código só insere. Bloqueio por trigger no banco fica como proposta. Cobre as operações do RF31. | Conferir que não existe endpoint de alteração ou exclusão de logs e que as operações do RF31 geram registro. | Implementado (trigger no banco: Proposto) |  |
| RNF06 | Documentação e erros | Swagger/OpenAPI reflete os endpoints reais. O README permite subir o sistema do zero. A API usa um único padrão de erro com os campos error, message, details, timestamp e path. | Comparar Swagger com as rotas; subir o projeto seguindo só o README; conferir os campos do erro em 400, 404 e 409. | Implementado |  |
| RNF07 | Consistência do estoque | Estoque por unidade consistente sob concorrência: a reserva é um UPDATE condicional atômico (só reserva se quantidade - quantidadeReservada >= pedido). Se dois pedidos disputam a última unidade, só um reserva e o outro recebe 409. | Teste sequencial: pedir mais do que o disponível e conferir o 409. O teste concorrente fica como proposta. | Implementado (teste concorrente: Proposto) | Teste concorrente já cortado. |
| RNF08 | Idempotência | Reenvio da mesma requisição de pedido ou pagamento (chave de idempotência) não gera pedido nem cobrança duplicados. Proposta: não faz parte do fluxo mínimo e o gateway é um mock, sem cobrança real. | Reenviar a mesma requisição e conferir que há um único pedido/pagamento. | Proposto | Já cortado do escopo implementado. |

## Status e cancelamento

| De | Para | Quem executa | Escopo |
|---|---|---|---|
| AGUARDANDO_PAGAMENTO | PAGO | Sistema (pagamento aprovado) | Implementado |
| PAGO | EM_PREPARO | Cozinha | Implementado |
| EM_PREPARO | PRONTO | Cozinha | Implementado |
| PRONTO | ENTREGUE | Atendente | Implementado |
| AGUARDANDO_PAGAMENTO | CANCELADO | Cliente (próprio pedido) ou sistema (pagamento recusado, reserva de 10 min vencida ou tentativa de pagar após o vencimento) | Implementado |
| PAGO | CANCELADO | Cliente, atendente (balcão) ou gerente, com estorno | Proposto |
| EM_PREPARO / PRONTO | CANCELADO | Somente gerente, até PRONTO, com estorno | Proposto |

Qualquer outra transição retorna erro.

### Cancelamento (RF11a e RF11b)

| Quem | Até qual status | Observação | Escopo |
|---|---|---|---|
| Cliente | AGUARDANDO_PAGAMENTO | Apenas o próprio pedido. Libera a reserva. | Implementado |
| Sistema | AGUARDANDO_PAGAMENTO | Pagamento recusado, reserva de 10 min vencida ou tentativa de pagar após o vencimento (retorna erro). Libera a reserva. | Implementado |
| Cliente | PAGO (antes do preparo) | Apenas o próprio pedido. Gera estorno. | Proposto |
| Gerente | PRONTO | Qualquer pedido. | Proposto |
| Atendente | PAGO | Somente pedidos de balcão. A associação Atendente-UC6 já consta no diagrama; a restrição 'só balcão' fica na especificação do UC6. | Proposto |
| Pedido pago e cancelado | - | Estorno registrado (mock), estoque devolvido e pontos revertidos. | Proposto |

## Decisões UC4

| Tema | Decisão | Justificativa | Situação |
|---|---|---|---|
| Estoque | Reservar na criação do pedido, por até 10 minutos; baixa definitiva só após o pagamento aprovado. | Evita vender a mesma unidade duas vezes no pico e não deixa o estoque preso por pedidos abandonados. | Decidido |
| Pagamento recusado | Implementar: a reserva é liberada na hora, o pedido vai para CANCELADO com o motivo registrado e auditado, e nenhum ponto é creditado. O cliente cria um novo pedido. | Libera o item imediatamente e mantém o histórico da recusa. | Decidido (implementar) |
| Falha do gateway (timeout) | A reserva continua até os 10 min, permitindo nova tentativa (RNF04). | Timeout não é recusa: o cliente pode ter pagamento ainda válido. | Decidido (implementar) |
| Pontos de fidelidade | Implementar o crédito (RF22): só após a aprovação do pagamento e só se consentimentoFidelidade for true. O consentimento é opcional e independente do cadastro: com false o cadastro e o pagamento funcionam e não há crédito (teste negativo). O saldo fica na coluna saldoPontos do cliente e o valor creditado aparece na resposta do pagamento aprovado. Consulta de saldo (RF23) e resgate (RF24) ficam como proposta. | Creditar na criação obrigaria a estornar pontos de pedidos recusados/cancelados e abriria brecha para criar pedidos só para pontuar. | Decidido (implementar) |
| Regra de conversão de pontos | 1 ponto por R$ 1,00 pago, arredondado para baixo (R$ 19,90 gera 19 pontos). Pedido recusado ou cancelado não gera pontos. | Dá um valor esperado simples para o crédito e para o teste do saldo. | Decidido (implementar) |
| Expiração da reserva (10 min) | Checagem na hora, sem job em segundo plano. Regras: (1) ao criar um pedido, liberar todas as reservas vencidas antes de calcular o disponível, senão o 409 sai com estoque que já venceu; (2) pagar depois dos 10 minutos cancela o pedido e responde com erro (409, motivo 'reserva expirada'), sem aprovar. Escrever estas regras na descrição do UC4 e no PDF. | Bem mais simples que um agendador e suficiente para o prazo. | Decidido (implementar) |
| Armazenamento da reserva | Coluna quantidadeReservada no estoque por unidade/produto e reservaExpiraEm no pedido. Disponível = quantidade - quantidadeReservada. | Evita uma tabela extra de reservas e entra no DER. | Decidido (implementar) |
| Concorrência no estoque | A reserva é um UPDATE condicional atômico, sem lock explícito: só reserva se o disponível cobrir o pedido; senão, 409. | Resolve a disputa pela última unidade com uma única instrução e pouco código. | Decidido (implementar) |
| Consentimento independente do cadastro | O UC8 continua como caso de uso próprio e opcional. No diagrama, ligar o UC8 ao UC1 por «extend» e manter a associação com o Cliente. O cadastro aceita consentimentoFidelidade true ou false. | O serviço não pode depender do consentimento. Assim a regra 'pontos só com consentimento' é exercida e testada (caso negativo). | Decidido (implementar) |
| Invariante da reserva | Reserva ativa = pedido em AGUARDANDO_PAGAMENTO com reservaExpiraEm futuro. Expirar, recusar, cancelar e aprovar mudam o status com UPDATE ... WHERE status = 'AGUARDANDO_PAGAMENTO' (na aprovação, também com a reserva válida), na mesma transação que ajusta o estoque. O estoque só é devolvido ou baixado se o UPDATE afetou 1 linha. | Evita devolver o estoque duas vezes quando expiração, recusa e cancelamento chegam ao mesmo tempo. | Decidido (implementar) |
| Consentimento no modelo | Uma linha por usuarioId e finalidade (UNIQUE). Consentimento ativo = aceito true e revogadoEm nulo. O cadastro sempre cria a linha, com aceito = false quando o campo não vem. O histórico de aceite, recusa e revogação fica em AUDITORIA (estadoAnterior e estadoNovo). | Consulta simples no crédito de pontos e testes diretos, sem perder o histórico. | Decidido (implementar) |
| Auditoria de estoque | Reserva, baixa e liberação são auditadas com entidade PEDIDO e entidadeId = pedidoId; unidadeId e produtoId ficam em estadoNovo. | A reserva sempre nasce de um pedido, e ESTOQUE tem chave composta. | Decidido (implementar) |
| Cortes de escopo | Movidos para proposta: idempotência (RNF08), timeout real de 5 s do gateway, trigger de imutabilidade no banco, consulta de saldo (RF23), acompanhar pedido (RF09), teste concorrente do estoque e log de acesso a dados sensíveis (UC20). Revertidos por serem baratos e exigidos pelo roteiro: consulta de logs (RF32, evidência de auditoria na coleção Postman e teste de 403) e paginação do RF10 (regra mínima 5.4). Mantidos: pedido → pagamento → status, consentimento opcional no cadastro, crédito de pontos e registro de auditoria. | Prazo de 23/11. O roteiro valoriza um fluxo fechado mais do que muitos endpoints. | Decidido |

## Resumo

| Prioridade | Implementado | Proposto | Total |
|---|---|---|---|
| Essencial | 15 | 0 | 15 |
| Importante | 2 | 13 | 15 |
| Desejável | 0 | 3 | 3 |
| Total | 17 | 16 | 33 |

Contagens calculadas por fórmula a partir da aba RF (RF11a e RF11b contam como dois requisitos).

Já cortado: idempotência (RNF08), timeout real do gateway, trigger de imutabilidade, RF23, RF09, teste concorrente do estoque e log de acesso a dados sensíveis. Próximo corte, se ainda apertar: RF11a manual do cliente (manter o cancelamento pelo sistema). Preservar pedido → pagamento → status.
