# UC4 – Realizar o pedido

**Descrição:** Permite que o cliente faça um pedido em uma unidade, informando o canal e os itens. O sistema reserva o estoque, solicita o pagamento ao gateway e, se o pagamento for aprovado, confirma o pedido e credita os pontos de fidelidade quando o cliente tiver consentimento. O fluxo é feito em duas chamadas da API: POST /pedidos (passos 1 a 4, cria o pedido e reserva o estoque) e POST /pedidos/{id}/pagamento (passos 5 a 11, paga o pedido). Os nomes dos endpoints serão ajustados quando o Swagger existir.

**Ator principal:** Cliente (App, Totem ou Web).

**Demais atores:** Sistemas externos de pagamento (gateway).

**Pré-condições:**

1. O cliente está autenticado (UC2) com um token válido e o perfil dele é CLIENTE.

**Pós-condições:**

1. O pedido é criado com o canal, a unidade, os itens e o total.
2. Se o pagamento for aprovado, o pagamento fica registrado como APROVADO, o pedido fica PAGO, o estoque é baixado e os pontos são creditados (se houver consentimento).
3. Se o pagamento for recusado ou vier depois dos 10 minutos, o pedido fica CANCELADO e a reserva é liberada, sem pontos.
4. Se o gateway falhar, o pedido continua AGUARDANDO_PAGAMENTO e a reserva vale até vencer.
5. Toda tentativa de pagamento fica gravada em PAGAMENTO, e as operações ficam registradas na auditoria.

**Origem das informações:** O cliente vem do token de login. A unidade, o canal e os itens (produto e quantidade) são informados pelo cliente. O preço e o total não vêm do cliente: os preços vêm do cardápio da unidade e o total é calculado pelo servidor. O estoque disponível vem da tabela de estoque, o consentimento vem da tabela de consentimento e o resultado do pagamento vem do gateway (no mock, do campo simularResultado).

**Usuários responsáveis:** Cliente, que faz o pedido. Gerente / Administrador, responsável pelo cardápio, pelo estoque e pelas regras da unidade.

**Pendências:**

1. Idempotência (RNF08, proposta): se a mesma requisição de pedido ou de pagamento for enviada duas vezes, ainda pode haver duplicidade.
2. Pagamento aprovado quando o pedido foi cancelado ao mesmo tempo: o estorno é proposto (RF11b) e ainda não está implementado.

**Fluxo base:**

1. Cliente: escolhe a unidade (unidadeId\*), os itens do cardápio com a quantidade de cada um (itens\*) e informa o canal do pedido (canalPedido\*): APP, TOTEM, WEB ou PICKUP. Não envia preço. [RN 1] [RN 3]
2. Sistema: confere os campos, a unidade e se os produtos constam no cardápio da unidade. [RN 1] [RN 2]
3. Sistema: libera as reservas vencidas e confere se o estoque da unidade cobre os itens. [RN 6] [RN 4]
4. Sistema: na mesma transação, reserva todos os itens por 10 minutos, calcula o total com os preços do cardápio e cria o pedido com status AGUARDANDO_PAGAMENTO. [RN 3] [RN 4] [RN 5] [RN 7]
5. Cliente: pede para pagar o pedido, dentro dos 10 minutos. No mock, pode enviar simularResultado (opcional). [RN 10]
6. Sistema: confere se o pedido existe e é do cliente, se ainda está AGUARDANDO_PAGAMENTO e se a reserva está dentro do prazo. [RN 9] [RN 8]
7. Sistema: solicita o pagamento ao gateway. [RN 8] [RN 10]
8. Sistema externo de pagamento: processa a transação e responde que foi aprovada.
9. Sistema: grava o pagamento como APROVADO, muda o pedido para PAGO e dá baixa no estoque. [RN 7] [RN 11]
10. Sistema: se o cliente tiver consentimento ativo, credita os pontos. [RN 12]
11. Sistema: grava a auditoria e devolve o pedido PAGO ao cliente, com os pontos creditados. [RN 13]

**Fluxo alternativo:**

**A1 – Dados inválidos**

No passo 2, algum campo está ausente ou inválido: canalPedido ausente ou diferente de APP, TOTEM, WEB ou PICKUP; unidadeId ausente; itens ausente ou vazio; quantidade menor que 1 ou não inteira (por exemplo 0, -2 ou 1,5); ou o mesmo produto repetido nos itens. O sistema responde com erro 400 ou 422 indicando o campo e não cria o pedido. [RN 1]

**A2 – Sem token, token inválido ou perfil sem permissão**

No passo 1 ou no passo 5, ao enviar a requisição, não há token ou o token é inválido ou expirou: o sistema responde com erro 401. Se o token é válido mas o perfil não é CLIENTE (atendente, cozinha ou gerente), o sistema responde com erro 403. Nos dois casos não cria o pedido nem chama o gateway. Essa verificação vem antes da validação dos dados.

**A3 – Unidade ou produto inexistente**

No passo 2, a unidade ou algum produto não existe, ou o produto não está ativo no cardápio da unidade. O sistema responde com erro 404 e não cria o pedido. [RN 2]

**A4 – Estoque insuficiente**

No passo 3 ou 4, algum item tem quantidade maior que a disponível. O sistema responde com erro 409, desfaz qualquer reserva já feita para os outros itens e não cria o pedido. [RN 4] [RN 5]

**A5 – Pedido inexistente ou de outro cliente**

No passo 6, o pedido não existe ou pertence a outro cliente. O sistema responde com erro 404 nos dois casos, para não revelar que o pedido existe, e não chama o gateway. [RN 9]

**A6 – Pedido já pago ou cancelado**

No passo 6, o pedido já está PAGO ou CANCELADO (por exemplo, o cliente clicou duas vezes em pagar). O sistema responde com erro 409, não chama o gateway e não muda nada no pedido nem no estoque. [RN 8]

**A7 – Pagamento recusado**

No passo 8, o gateway recusa o pagamento. O sistema grava o PAGAMENTO com resultado RECUSADO e o motivo, muda o pedido para CANCELADO, libera a reserva e não credita pontos. O cliente precisa fazer um novo pedido. [RN 7]

**A8 – Falha do gateway**

Nos passos 7 ou 8, o gateway dá erro. O sistema grava o PAGAMENTO com resultado ERRO_GATEWAY. O pedido continua AGUARDANDO_PAGAMENTO e a reserva continua valendo. O cliente pode tentar pagar de novo até os 10 minutos, e cada tentativa gera uma nova linha em PAGAMENTO.

**A9 – Pagamento depois dos 10 minutos**

No passo 6, a reserva já venceu. O sistema cancela o pedido, libera a reserva e responde com erro 409 com o motivo 'reserva expirada', sem chamar o gateway. [RN 8]

**Regras de negócio:**

**RN 1 – Campos obrigatórios e dados válidos:** canalPedido\*, unidadeId\* e itens\* são obrigatórios. O canal precisa ser APP, TOTEM, WEB ou PICKUP (o BALCAO é gravado só nos pedidos de balcão, UC13). Os itens não podem ser vazios, cada quantidade é um número inteiro maior ou igual a 1 e o mesmo produto não pode aparecer duas vezes no pedido.

**RN 2 – Cardápio da unidade:** os itens precisam constar e estar ativos no cardápio da unidade escolhida.

**RN 3 – Preço e total vêm do servidor:** o cliente nunca envia preço. O servidor usa o preço do cardápio da unidade, grava em precoUnitario de cada item e calcula o total do pedido.

**RN 4 – Reserva de 10 minutos:** ao criar o pedido, o sistema reserva os itens por 10 minutos. O disponível é a quantidade menos a quantidade reservada. A reserva só acontece se o disponível cobrir o pedido; do contrário, o pedido não é criado (409). Se dois pedidos disputam a última unidade, só um reserva.

**RN 5 – Reserva tudo ou nada:** a reserva de todos os itens e a criação do pedido ficam na mesma transação. Se um item não cabe, a reserva dos itens anteriores é desfeita e nada é gravado.

**RN 6 – Reservas vencidas:** antes de calcular o disponível, o sistema libera todas as reservas vencidas, e não só a do pedido consultado. A checagem é feita na hora (ao criar, consultar ou pagar), sem rotina em segundo plano.

**RN 7 – Status do pedido:** o pedido nasce AGUARDANDO_PAGAMENTO e só vai para PAGO ou CANCELADO se ainda estiver nesse status. Essa troca é feita junto com o ajuste do estoque, e o estoque só é baixado ou devolvido se a troca de fato aconteceu. Assim, expirar, recusar e cancelar ao mesmo tempo nunca devolvem o estoque duas vezes. A baixa definitiva do estoque só acontece depois do pagamento aprovado.

**RN 8 – Chamada ao gateway:** o gateway só é chamado se o pedido ainda estiver AGUARDANDO_PAGAMENTO e a reserva estiver dentro dos 10 minutos. Pedido já pago ou cancelado retorna 409. Pagar depois dos 10 minutos cancela o pedido, libera a reserva e retorna 409.

**RN 9 – Pedido do próprio cliente:** o cliente só paga e consulta os próprios pedidos. Pedido inexistente ou de outro cliente retorna 404, sem chamar o gateway.

**RN 10 – Controle do mock:** o gateway é um mock. O corpo do pagamento aceita o campo opcional simularResultado (APROVADO, RECUSADO ou ERRO_GATEWAY), e o padrão é APROVADO. Assim o teste escolhe o resultado em cada requisição, sem reiniciar o servidor. Outro valor nesse campo retorna 400 ou 422. O campo existe só porque o gateway é simulado e não iria para produção.

**RN 11 – Registro das tentativas:** toda tentativa de pagamento é gravada em PAGAMENTO com o resultado (APROVADO, RECUSADO ou ERRO_GATEWAY), inclusive as que não aprovam.

**RN 12 – Pontos:** só são creditados depois do pagamento aprovado e só se o cliente tiver consentimento ativo (aceito e não revogado). São 1 ponto por R\$ 1,00 pago, arredondado para baixo. Pedido recusado ou cancelado não gera pontos.

**RN 13 – Auditoria:** cada operação (criação, reserva, pagamento, cancelamento, baixa, liberação e crédito de pontos) registra usuário, ação, data/hora e estado anterior e novo. Os eventos de estoque são registrados no pedido.
