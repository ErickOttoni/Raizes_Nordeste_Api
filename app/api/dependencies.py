from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.errors import NaoAutenticado, SemPermissao
from app.application.ports.token_service import DadosToken, TokenService
from app.application.use_cases.criar_pedido import CriarPedido
from app.application.use_cases.login import Login
from app.application.use_cases.consultar_cardapio import ConsultarCardapio
from app.application.use_cases.pagar_pedido import PagarPedido

def get_pagar_pedido() -> PagarPedido:
    raise NotImplementedError

def get_criar_pedido() -> CriarPedido:
    raise NotImplementedError

def get_consultar_cardapio() -> ConsultarCardapio:
    raise NotImplementedError

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