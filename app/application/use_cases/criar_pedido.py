from app.application.errors import NaoEncontrado
from app.application.ports.cardapio_repository import CardapioRepository, UnidadeRepository
from app.application.ports.pedido_ports import (
    AuditoriaRepository, EstoqueRepository, PedidoRepository, Relogio, Transacao,
)
from app.domain.entities.pedido import ItemPedido, ItemSolicitado, Pedido, validar_itens
from app.domain.enums import CanalPedido
from app.domain.errors import DadosInvalidos, EstoqueInsuficiente


class CriarPedido:
    def __init__(self, unidades: UnidadeRepository, cardapio: CardapioRepository,
                 pedidos: PedidoRepository, estoque: EstoqueRepository,
                 auditoria: AuditoriaRepository, relogio: Relogio,
                 transacao: Transacao, reserva_ttl_segundos: int):
        self._unidades = unidades
        self._cardapio = cardapio
        self._pedidos = pedidos
        self._estoque = estoque
        self._auditoria = auditoria
        self._relogio = relogio
        self._transacao = transacao
        self._ttl = reserva_ttl_segundos

    def executar(self, cliente_id: int, unidade_id: int, canal: CanalPedido,
                 itens: list[ItemSolicitado]) -> Pedido:
        # 1. Pedido de balcão não é feito pelo cliente nesta API (422)
        if canal == CanalPedido.BALCAO:
            raise DadosInvalidos("Canal BALCAO não é permitido neste endpoint.", "canalPedido")
        validar_itens(itens)

        # 2. Unidade precisa existir e estar ativa
        unidade = self._unidades.buscar_por_id(unidade_id)
        if unidade is None or not unidade.ativa:
            raise NaoEncontrado("Unidade não encontrada.")

        # 3. Preço sempre do cardápio, nunca do cliente
        itens_pedido: list[ItemPedido] = []
        for item in itens:
            item_cardapio = self._cardapio.buscar_item(unidade_id, item.produto_id)
            if item_cardapio is None or not item_cardapio.ativo:
                raise NaoEncontrado(f"Produto {item.produto_id} não disponível nesta unidade.")
            itens_pedido.append(
                ItemPedido(produto_id=item.produto_id, quantidade=item.quantidade,
                           preco_unitario=item_cardapio.preco)
            )

        agora = self._relogio.agora()
        pedido = Pedido.criar(cliente_id, unidade_id, canal, itens_pedido, agora, self._ttl)

        # 4. RN 6: libera todas as reservas vencidas e audita cada pedido cancelado
        for pedido_id in self._estoque.liberar_vencidas(agora):
            self._auditoria.registrar(
                acao="RESERVA_EXPIRADA", entidade="PEDIDO", entidade_id=pedido_id,
                usuario_id=None,
                estado_anterior={"status": "AGUARDANDO_PAGAMENTO"},
                estado_novo={"status": "CANCELADO"},
            )

        # 5. Reserva tudo ou nada; ordem por produto evita deadlock entre pedidos concorrentes
        for item in sorted(itens_pedido, key=lambda i: i.produto_id):
            if not self._estoque.reservar(unidade_id, item.produto_id, item.quantidade):
                raise EstoqueInsuficiente(item.produto_id)

        pedido = self._pedidos.criar(pedido)

        # 6. Auditoria do pedido e de cada reserva
        self._auditoria.registrar(
            acao="PEDIDO_CRIADO", entidade="PEDIDO", entidade_id=pedido.id,
            usuario_id=cliente_id, estado_anterior=None,
            estado_novo={"status": pedido.status.value, "total": str(pedido.total)},
        )
        for item in itens_pedido:
            self._auditoria.registrar(
                acao="ESTOQUE_RESERVADO", entidade="PEDIDO", entidade_id=pedido.id,
                usuario_id=cliente_id, estado_anterior=None,
                estado_novo={"unidadeId": unidade_id, "produtoId": item.produto_id,
                             "quantidade": item.quantidade},
            )

        self._transacao.commit()
        return pedido