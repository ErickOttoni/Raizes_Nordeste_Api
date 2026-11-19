from typing import Protocol

from app.domain.entities.item_cardapio import ItemCardapio
from app.domain.entities.unidade import Unidade


class UnidadeRepository(Protocol):
    def buscar_por_id(self, unidade_id: int) -> Unidade | None: ...


class CardapioRepository(Protocol):
    def listar_ativos(self, unidade_id: int) -> list[ItemCardapio]: ...
    def buscar_item(self, unidade_id: int, produto_id: int) -> ItemCardapio | None: ...