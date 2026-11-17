from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.errors import NaoAutenticado, SemPermissao
from app.application.ports.token_service import DadosToken, TokenService
from app.application.use_cases.login import Login

bearer = HTTPBearer(auto_error=False)  # sem erro automático: o 401 sai no nosso padrão


# Pontos de entrada que o container.py preenche (a API não importa a Infrastructure).
def get_login() -> Login:
    raise NotImplementedError


def get_token_service() -> TokenService:
    raise NotImplementedError

# Dependências para autenticação e autorização
def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer),
    tokens: TokenService = Depends(get_token_service),
) -> DadosToken:
    if credenciais is None:
        raise NaoAutenticado("Token ausente.")
    return tokens.validar(credenciais.credentials)


def exigir_perfil(*perfis: str):
    def checar(dados: DadosToken = Depends(usuario_atual)) -> DadosToken:
        if dados.perfil not in perfis:
            raise SemPermissao("Perfil sem permissão para este recurso.")
        return dados
    return checar