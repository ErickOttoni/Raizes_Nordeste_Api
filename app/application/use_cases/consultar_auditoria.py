from app.application.ports.pedido_ports import AuditoriaRepository
from app.domain.entities.auditoria import RegistroAuditoria


class ConsultarAuditoria:
    def __init__(self, auditoria: AuditoriaRepository):
        self._auditoria = auditoria

    def executar(self, pagina: int, limite: int) -> list[RegistroAuditoria]:
        return self._auditoria.listar(pagina, limite)