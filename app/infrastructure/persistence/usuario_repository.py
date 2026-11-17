from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.usuario import Usuario
from app.domain.enums import PerfilUsuario
from app.infrastructure.persistence.models import UsuarioModel

#classe de repositório para manipulação de usuários no banco de dados
class SqlUsuarioRepository:
    def __init__(self, db: Session):
        self._db = db

    def buscar_por_email(self, email: str) -> Usuario | None:
        modelo = self._db.scalar(select(UsuarioModel).where(UsuarioModel.email == email))
        return self._para_entidade(modelo) if modelo else None

    def buscar_por_id(self, usuario_id: int) -> Usuario | None:
        modelo = self._db.get(UsuarioModel, usuario_id)
        return self._para_entidade(modelo) if modelo else None

    def criar(self, usuario: Usuario) -> Usuario:
        modelo = UsuarioModel(
            nome=usuario.nome, email=usuario.email, senhaHash=usuario.senha_hash,
            perfil=usuario.perfil.value, saldoPontos=usuario.saldo_pontos,
            unidadeId=usuario.unidade_id,
        )
        self._db.add(modelo)
        self._db.flush()  # preenche o id; o commit fica com o caso de uso
        return self._para_entidade(modelo)

    #define um método estático para converter o modelo de banco de dados em uma entidade de domínio
    @staticmethod
    def _para_entidade(m: UsuarioModel) -> Usuario:
        return Usuario(id=m.id, nome=m.nome, email=m.email, senha_hash=m.senhaHash,
                       perfil=PerfilUsuario(m.perfil), saldo_pontos=m.saldoPontos,
                       unidade_id=m.unidadeId)