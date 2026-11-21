from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RegistroAuditoria:
    id: int
    usuario_id: int | None
    acao: str
    entidade: str
    entidade_id: int
    estado_anterior: dict | None
    estado_novo: dict | None
    data_hora: datetime