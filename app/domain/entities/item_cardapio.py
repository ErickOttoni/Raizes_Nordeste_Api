
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ItemCardapio:
    unidade_id: int
    produto_id: int
    nome: str
    descricao: str | None
    preco: Decimal
    ativo: bool