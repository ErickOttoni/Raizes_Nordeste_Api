from collections.abc import Iterator

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.api import dependencies as dep
from app.application.use_cases.atualizar_status_pedido import AtualizarStatusPedido
from app.application.use_cases.consultar_auditoria import ConsultarAuditoria
from app.application.use_cases.consultar_cardapio import ConsultarCardapio
from app.application.use_cases.criar_pedido import CriarPedido
from app.application.use_cases.login import Login
from app.application.use_cases.pagar_pedido import PagarPedido
from app.infrastructure.clock import RelogioSistema
from app.infrastructure.config import settings
from app.infrastructure.database import SessionLocal
from app.infrastructure.persistence.cardapio_repository import (
    SqlCardapioRepository,
    SqlUnidadeRepository,
)
from app.infrastructure.persistence.pedido_repository import (
    SqlAuditoriaRepository,
    SqlConsentimentoRepository,
    SqlEstoqueRepository,
    SqlPagamentoRepository,
    SqlPedidoRepository,
    SqlTransacao,
)
from app.infrastructure.persistence.usuario_repository import SqlUsuarioRepository
from app.infrastructure.security.jwt_service import JwtTokenService
from app.infrastructure.security.passwords import BcryptHash
from app.infrastructure.payment.gateway_mock import GatewayPagamentoMock


# Uma sessão do banco por requisição.
def get_session() -> Iterator[Session]:
    with SessionLocal() as db:  # uma sessão por requisição
        yield db

#definir a função de configuração do aplicativo FastAPI, registrando os casos de uso e serviços necessários para autenticação e autorização.
def configurar(app: FastAPI) -> None:
    tokens = JwtTokenService()
    hasher = BcryptHash()

    def login_pronto(db: Session = Depends(get_session)) -> Login:
        return Login(SqlUsuarioRepository(db), hasher, tokens)

    app.dependency_overrides[dep.get_login] = login_pronto
    app.dependency_overrides[dep.get_token_service] = lambda: tokens

    def cardapio_pronto(db: Session = Depends(get_session)) -> ConsultarCardapio:
        return ConsultarCardapio(SqlUnidadeRepository(db), SqlCardapioRepository(db))

    app.dependency_overrides[dep.get_consultar_cardapio] = cardapio_pronto

    relogio = RelogioSistema()

    def criar_pedido_pronto(db: Session = Depends(get_session)) -> CriarPedido:
        return CriarPedido(
            SqlUnidadeRepository(db), SqlCardapioRepository(db), SqlPedidoRepository(db),
            SqlEstoqueRepository(db), SqlAuditoriaRepository(db), relogio,
            SqlTransacao(db), settings.reserva_ttl_segundos,
            )

    app.dependency_overrides[dep.get_criar_pedido] = criar_pedido_pronto

    gateway = GatewayPagamentoMock()

    def pagar_pedido_pronto(db: Session = Depends(get_session)) -> PagarPedido:
        return PagarPedido(
            SqlPedidoRepository(db), SqlEstoqueRepository(db), SqlPagamentoRepository(db),
            SqlConsentimentoRepository(db), SqlUsuarioRepository(db),
            SqlAuditoriaRepository(db), gateway, relogio, SqlTransacao(db),
        )

    app.dependency_overrides[dep.get_pagar_pedido] = pagar_pedido_pronto

    def auditoria_pronta(db: Session = Depends(get_session)) -> ConsultarAuditoria:
        return ConsultarAuditoria(SqlAuditoriaRepository(db))

    app.dependency_overrides[dep.get_consultar_auditoria] = auditoria_pronta

    def atualizar_status_pronto(db: Session = Depends(get_session)) -> AtualizarStatusPedido:
        return AtualizarStatusPedido(
            usuarios=SqlUsuarioRepository(db),
            pedidos=SqlPedidoRepository(db),
            auditoria=SqlAuditoriaRepository(db),
            transacao=SqlTransacao(db),
        )

    app.dependency_overrides[dep.get_atualizar_status] = atualizar_status_pronto