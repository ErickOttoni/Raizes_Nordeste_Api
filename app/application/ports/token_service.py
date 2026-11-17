from dataclasses import dataclass
from typing import Protocol

#definir a interface do serviço de token
@dataclass(frozen=True)
class DadosToken:
    usuario_id: int
    perfil: str


class TokenService(Protocol):
    def gerar(self, usuario_id: int, perfil: str) -> str: ...
    def validar(self, token: str) -> DadosToken: ...  # levanta NaoAutenticado