from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import CanalPedido, ResultadoPagamento, StatusPedido

#classes de request e response para pedidos, incluindo itens do pedido e detalhes de pagamento.
class ItemPedidoRequest(BaseModel):
    produtoId: int
    quantidade: int


class CriarPedidoRequest(BaseModel):
    unidadeId: int
    canalPedido: CanalPedido
    itens: list[ItemPedidoRequest]


class ItemPedidoResponse(BaseModel):
    produtoId: int
    quantidade: int
    precoUnitario: float


class PedidoResponse(BaseModel):
    id: int
    unidadeId: int
    canalPedido: str
    status: str
    total: float
    reservaExpiraEm: datetime
    itens: list[ItemPedidoResponse]


class PagamentoRequest(BaseModel):
    simularResultado: ResultadoPagamento = ResultadoPagamento.APROVADO  # só existe por ser mock


class PedidoPagoResponse(PedidoResponse):
    pontosCreditados: int = 0
    motivo: str | None = None

class AtualizarStatusRequest(BaseModel):
    status: StatusPedido