from datetime import datetime

from app.infrastructure.persistence.models import agora


class RelogioSistema:
    def agora(self) -> datetime:
        return agora()