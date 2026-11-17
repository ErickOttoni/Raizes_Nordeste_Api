from fastapi import APIRouter, Depends

from app.api.dependencies import get_login, usuario_atual
from app.api.schemas.auth import LoginRequest, LoginResponse
from app.application.ports.token_service import DadosToken
from app.application.use_cases.login import Login
#router de autenticação, com endpoints para login e para obter informações do usuário atual
router = APIRouter(prefix="/auth", tags=["Autenticação"])

#rota para login, que recebe um email e senha, executa o caso de uso de login e retorna um token de acesso
@router.post("/login", response_model=LoginResponse)
def login(corpo: LoginRequest, caso_de_uso: Login = Depends(get_login)):
    resultado = caso_de_uso.executar(corpo.email, corpo.senha)
    return LoginResponse(access_token=resultado.access_token,
                         token_type=resultado.token_type, perfil=resultado.perfil)

#rota para obter informações do usuário atual, que depende da autenticação e retorna o id e perfil do usuário
@router.get("/me")
def me(dados: DadosToken = Depends(usuario_atual)):
    return {"usuarioId": dados.usuario_id, "perfil": dados.perfil}