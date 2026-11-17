from dataclasses import dataclass

from app.domain.enums import PerfilUsuario

# Entidade de domínio que representa um usuário do sistema.
@dataclass
class Usuario:
    id: int | None
    nome: str
    email: str
    senha_hash: str
    perfil: PerfilUsuario
    saldo_pontos: int = 0
    unidade_id: int | None = None