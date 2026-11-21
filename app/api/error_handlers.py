from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.domain.errors import DadosInvalidos, EstoqueInsuficiente, TransicaoInvalida

from app.application.errors import Conflito, ErroGateway, NaoAutenticado, NaoEncontrado, SemPermissao

# Funções para padronizar o tratamento de erros na API
def _resposta(request: Request, status: int, erro: str, mensagem: str, detalhes=None):
    return JSONResponse(status_code=status, content={
        "error": erro,
        "message": mensagem,
        "details": detalhes or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
    })


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(NaoAutenticado)
    async def _401(request: Request, exc: NaoAutenticado):
        return _resposta(request, 401, "UNAUTHORIZED", str(exc))
    @app.exception_handler(ErroGateway)
    async def _502(request: Request, exc: ErroGateway):
        return _resposta(request, 502, "BAD_GATEWAY", str(exc))
    
    @app.exception_handler(SemPermissao)
    async def _403(request: Request, exc: SemPermissao):
        return _resposta(request, 403, "FORBIDDEN", str(exc))

    @app.exception_handler(NaoEncontrado)
    async def _404(request: Request, exc: NaoEncontrado):
        return _resposta(request, 404, "NOT_FOUND", str(exc))

    @app.exception_handler(Conflito)
    async def _409(request: Request, exc: Conflito):
        return _resposta(request, 409, "CONFLICT", str(exc))

    @app.exception_handler(RequestValidationError)
    async def _422(request: Request, exc: RequestValidationError):
        detalhes = [{"campo": ".".join(str(p) for p in e["loc"][1:]), "mensagem": e["msg"]}
                    for e in exc.errors()]
        return _resposta(request, 422, "VALIDATION_ERROR", "Dados inválidos.", detalhes)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        return _resposta(request, exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(DadosInvalidos)
    async def _dados_invalidos(request: Request, exc: DadosInvalidos):
        detalhes = [{"campo": exc.campo, "mensagem": str(exc)}]
        return _resposta(request, 422, "VALIDATION_ERROR", "Dados inválidos.", detalhes)

    @app.exception_handler(EstoqueInsuficiente)
    async def _estoque(request: Request, exc: EstoqueInsuficiente):
        return _resposta(request, 409, "CONFLICT", str(exc))

    @app.exception_handler(TransicaoInvalida)
    async def _transicao(request: Request, exc: TransicaoInvalida):
        return _resposta(request, 409, "CONFLICT", str(exc))