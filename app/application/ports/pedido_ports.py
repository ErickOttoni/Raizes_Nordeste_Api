from datetime import datetime
from typing import Protocol

from app.domain.entities.pedido import Pedido


class PedidoRepository(Protocol):
    def criar(self, pedido: Pedido) -> Pedido: ...


class EstoqueRepository(Protocol):
    def reservar(self, unidade_id: int, produto_id: int, quantidade: int) -> bool: ...
    def liberar_vencidas(self, agora: datetime) -> list[int]:
        """Cancela os pedidos com reserva vencida, devolve o estoque e retorna os ids."""
        ...
class AuditoriaRepository(Protocol):
    def registrar(self, usuario_id: int | None, acao: str, entidade: str,
                  entidade_id: int, estado_anterior: dict | None,
                  estado_novo: dict | None) -> None: ...


class Relogio(Protocol):
    def agora(self) -> datetime: ...


class Transacao(Protocol):
    def commit(self) -> None: ...