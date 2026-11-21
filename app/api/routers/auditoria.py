from fastapi import APIRouter, Depends, Query

from app.api.dependencies import exigir_perfil, get_consultar_auditoria
from app.api.schemas.auditoria import AuditoriaResponse
from app.application.ports.token_service import DadosToken
from app.application.use_cases.consultar_auditoria import ConsultarAuditoria

router = APIRouter(tags=["Auditoria"])


@router.get("/auditoria", response_model=list[AuditoriaResponse])
def consultar_auditoria(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    _: DadosToken = Depends(exigir_perfil("GERENTE")),
    caso_de_uso: ConsultarAuditoria = Depends(get_consultar_auditoria),
):
    registros = caso_de_uso.executar(page, limit)
    return [AuditoriaResponse(id=r.id, usuarioId=r.usuario_id, acao=r.acao, entidade=r.entidade,
                              entidadeId=r.entidade_id, estadoAnterior=r.estado_anterior,
                              estadoNovo=r.estado_novo, dataHora=r.data_hora)
            for r in registros]