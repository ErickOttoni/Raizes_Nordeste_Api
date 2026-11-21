from datetime import datetime

from pydantic import BaseModel


class AuditoriaResponse(BaseModel):
    id: int
    usuarioId: int | None
    acao: str
    entidade: str
    entidadeId: int
    estadoAnterior: dict | None
    estadoNovo: dict | None
    dataHora: datetime