from collections.abc import Iterator

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.api import dependencies as dep
from app.application.use_cases.login import Login
from app.infrastructure.database import SessionLocal
from app.infrastructure.persistence.usuario_repository import SqlUsuarioRepository
from app.infrastructure.security.jwt_service import JwtTokenService
from app.infrastructure.security.passwords import BcryptHash

# Configura o container de dependências da aplicação FastAPI, registrando os casos de uso e serviços necessários para autenticação e autorização.
def get_session() -> Iterator[Session]:
    with SessionLocal() as db:  # uma sessão por requisição
        yield db

#definir a função de configuração do container, que cria instâncias dos serviços de token e hash, e define as dependências para o caso de uso de login
def configurar(app: FastAPI) -> None:
    tokens = JwtTokenService()
    hasher = BcryptHash()

    def login_pronto(db: Session = Depends(get_session)) -> Login:
        return Login(SqlUsuarioRepository(db), hasher, tokens)

    app.dependency_overrides[dep.get_login] = login_pronto
    app.dependency_overrides[dep.get_token_service] = lambda: tokens