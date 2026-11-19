
from dataclasses import dataclass


@dataclass
class Unidade:
    id: int
    nome: str
    regiao: str | None
    ativa: bool