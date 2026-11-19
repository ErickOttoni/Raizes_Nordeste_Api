from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import CanalPedido

#classes para representar os dados de requisição e resposta relacionados a pedidos, incluindo itens de pedido, criação de pedidos e detalhes do pedido.
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