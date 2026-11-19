from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.domain.enums import CanalPedido, StatusPedido
from app.domain.errors import DadosInvalidos


@dataclass(frozen=True)
class ItemSolicitado:
    produto_id: int
    quantidade: int


def validar_itens(itens: list[ItemSolicitado]) -> None:
    """RN 1: itens não vazios, quantidade inteira >= 1, sem produto repetido."""
    if not itens:
        raise DadosInvalidos("O pedido precisa ter ao menos um item.", "itens")
    vistos: set[int] = set()
    for item in itens:
        if isinstance(item.quantidade, bool) or not isinstance(item.quantidade, int) or item.quantidade < 1:
            raise DadosInvalidos("A quantidade deve ser um número inteiro maior ou igual a 1.", "itens.quantidade")
        if item.produto_id in vistos:
            raise DadosInvalidos("Produto repetido nos itens.", "itens.produtoId")
        vistos.add(item.produto_id)

#classes de entidade para representar itens de pedido e pedidos, incluindo validação de itens e criação de pedidos com cálculo de total e reserva de tempo.
@dataclass
class ItemPedido:
    produto_id: int
    quantidade: int
    preco_unitario: Decimal


@dataclass
class Pedido:
    id: int | None
    cliente_id: int
    unidade_id: int
    canal: CanalPedido
    status: StatusPedido
    total: Decimal
    reserva_expira_em: datetime
    itens: list[ItemPedido]
    pontos_creditados: int = 0
    motivo_cancelamento: str | None = None

    @classmethod
    def criar(cls, cliente_id: int, unidade_id: int, canal: CanalPedido,
              itens: list[ItemPedido], agora: datetime, ttl_segundos: int) -> "Pedido":
        """RN 3 e RN 4: total calculado pelo servidor e reserva de 10 minutos (ttl)."""
        total = sum((i.preco_unitario * i.quantidade for i in itens), Decimal("0"))
        return cls(
            id=None, cliente_id=cliente_id, unidade_id=unidade_id, canal=canal,
            status=StatusPedido.AGUARDANDO_PAGAMENTO, total=total,
            reserva_expira_em=agora + timedelta(seconds=ttl_segundos), itens=itens,
        )