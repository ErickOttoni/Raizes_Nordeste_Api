
from pydantic import BaseModel

#define as classes de request e response para o login
class LoginRequest(BaseModel):
    email: str
    senha: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    perfil: str