from decimal import Decimal
from typing import Protocol

from app.domain.entities.pedido import ItemPedido, Pedido
from app.domain.enums import ResultadoPagamento


class PagamentoGateway(Protocol):
    def cobrar(self, pedido_id: int, valor: Decimal,
               simular_resultado: ResultadoPagamento) -> tuple[ResultadoPagamento, str | None]:
        """Devolve o resultado e o motivo (quando recusado)."""
        ...


class PagamentoRepository(Protocol):
    def registrar(self, pedido_id: int, forma: str, valor: Decimal,
                  resultado: ResultadoPagamento, motivo: str | None) -> None: ...


class ConsentimentoRepository(Protocol):
    def ativo(self, usuario_id: int, finalidade: str) -> bool: ...