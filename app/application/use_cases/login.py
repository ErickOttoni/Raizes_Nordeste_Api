# Caso de uso: login do usuário
from dataclasses import dataclass

from app.application.errors import NaoAutenticado
from app.application.ports.token_service import TokenService
from app.application.ports.usuario_repository import HashDeSenha, UsuarioRepository

#classe que representa o resultado do login, contendo o token de acesso, tipo de token e perfil do usuário.
@dataclass(frozen=True)
class LoginResultado:
    access_token: str
    token_type: str
    perfil: str

#classe que implementa o caso de uso de login, verificando as credenciais do usuário e gerando um token de acesso.
class Login:
    def __init__(self, usuarios: UsuarioRepository, hasher: HashDeSenha, tokens: TokenService):
        self._usuarios = usuarios
        self._hasher = hasher
        self._tokens = tokens

    def executar(self, email: str, senha: str) -> LoginResultado:
        usuario = self._usuarios.buscar_por_email(email)
        if usuario is None or not self._hasher.verificar(senha, usuario.senha_hash):
            raise NaoAutenticado("Credenciais inválidas.")
        token = self._tokens.gerar(usuario.id, usuario.perfil.value)
        return LoginResultado(token, "bearer", usuario.perfil.value)