from datetime import datetime, timedelta, timezone

import jwt

from app.application.errors import NaoAutenticado
from app.application.ports.token_service import DadosToken
from app.infrastructure.config import settings

ALGORITMO = "HS256"


class JwtTokenService:
    def gerar(self, usuario_id: int, perfil: str) -> str:
        agora = datetime.now(timezone.utc)
        payload = {
            "sub": str(usuario_id),  # o PyJWT exige texto em "sub"
            "perfil": perfil,
            "iat": agora,
            "exp": agora + timedelta(minutes=settings.jwt_expire_minutes),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITMO)

    def validar(self, token: str) -> DadosToken:
        try:
            dados = jwt.decode(
                token, settings.jwt_secret, algorithms=[ALGORITMO],
                options={"require": ["exp", "sub", "perfil"]},
            )
            return DadosToken(usuario_id=int(dados["sub"]), perfil=dados["perfil"])
        except (jwt.PyJWTError, KeyError, ValueError, TypeError):
            raise NaoAutenticado("Token inválido ou expirado.") from None