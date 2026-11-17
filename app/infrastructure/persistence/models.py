#Modelos de tabela (ORM) do banco.

#Ficam só na Infrastructure e são separados das entidades do Domain: Orepositório converte um no outro. Os nomes das colunas seguem exatamente o DER para bater com o JSON da API.

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


def agora() -> datetime:
#Hora atual em UTC, sem fuso, para a coluna DATETIME do MySQL.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UnidadeModel(Base):
    __tablename__ = "unidade"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100))
    regiao: Mapped[str | None] = mapped_column(String(60))  # atributo proposto
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)


class ProdutoModel(Base):
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100))
    descricao: Mapped[str | None] = mapped_column(String(255))


class CardapioModel(Base):
    __tablename__ = "cardapio"

    unidadeId: Mapped[int] = mapped_column(BigInteger, ForeignKey("unidade.id"), primary_key=True)
    produtoId: Mapped[int] = mapped_column(BigInteger, ForeignKey("produto.id"), primary_key=True)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class UsuarioModel(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint(
            "perfil IN ('CLIENTE', 'ATENDENTE', 'COZINHA', 'GERENTE')",
            name="ck_usuario_perfil",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True)
    senhaHash: Mapped[str] = mapped_column(String(100))
    perfil: Mapped[str] = mapped_column(String(20))
    saldoPontos: Mapped[int] = mapped_column(Integer, default=0)
    unidadeId: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("unidade.id"))
    criadoEm: Mapped[datetime] = mapped_column(DateTime, default=agora)


class EstoqueModel(Base):
    __tablename__ = "estoque"
    __table_args__ = (
        CheckConstraint(
            "0 <= quantidadeReservada AND quantidadeReservada <= quantidade",
            name="ck_estoque_reserva",
        ),
    )

    unidadeId: Mapped[int] = mapped_column(BigInteger, ForeignKey("unidade.id"), primary_key=True)
    produtoId: Mapped[int] = mapped_column(BigInteger, ForeignKey("produto.id"), primary_key=True)
    quantidade: Mapped[int] = mapped_column(Integer)
    quantidadeReservada: Mapped[int] = mapped_column(Integer, default=0)


class PedidoModel(Base):
    __tablename__ = "pedido"
    __table_args__ = (
        CheckConstraint(
            "canalPedido IN ('APP', 'TOTEM', 'BALCAO', 'PICKUP', 'WEB')",
            name="ck_pedido_canal",
        ),
        CheckConstraint(
            "status IN ('AGUARDANDO_PAGAMENTO', 'PAGO', 'EM_PREPARO', "
            "'PRONTO', 'ENTREGUE', 'CANCELADO')",
            name="ck_pedido_status",
        ),
        Index("ix_pedido_status_reserva", "status", "reservaExpiraEm"),
        Index("ix_pedido_unidade_canal", "unidadeId", "canalPedido"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    clienteId: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id"))
    unidadeId: Mapped[int] = mapped_column(BigInteger, ForeignKey("unidade.id"))
    canalPedido: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(25), default="AGUARDANDO_PAGAMENTO")
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    reservaExpiraEm: Mapped[datetime] = mapped_column(DateTime)
    pontosCreditados: Mapped[int] = mapped_column(Integer, default=0)
    motivoCancelamento: Mapped[str | None] = mapped_column(String(120))
    criadoEm: Mapped[datetime] = mapped_column(DateTime, default=agora)
    atualizadoEm: Mapped[datetime] = mapped_column(DateTime, default=agora, onupdate=agora)


class ItemPedidoModel(Base):
    __tablename__ = "item_pedido"
    __table_args__ = (
        UniqueConstraint("pedidoId", "produtoId", name="uq_item_pedido_pedido_produto"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pedidoId: Mapped[int] = mapped_column(BigInteger, ForeignKey("pedido.id"))
    produtoId: Mapped[int] = mapped_column(BigInteger, ForeignKey("produto.id"))
    quantidade: Mapped[int] = mapped_column(Integer)
    precoUnitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class PagamentoModel(Base):
    __tablename__ = "pagamento"
    __table_args__ = (
        CheckConstraint("forma IN ('GATEWAY', 'DINHEIRO')", name="ck_pagamento_forma"),
        CheckConstraint(
            "resultado IN ('APROVADO', 'RECUSADO', 'ERRO_GATEWAY')",
            name="ck_pagamento_resultado",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pedidoId: Mapped[int] = mapped_column(BigInteger, ForeignKey("pedido.id"))
    forma: Mapped[str] = mapped_column(String(10))
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    resultado: Mapped[str] = mapped_column(String(15))
    motivo: Mapped[str | None] = mapped_column(String(120))
    processadoEm: Mapped[datetime] = mapped_column(DateTime, default=agora)


class ConsentimentoModel(Base):
    __tablename__ = "consentimento"
    __table_args__ = (
        UniqueConstraint("usuarioId", "finalidade", name="uq_consentimento_usuario_finalidade"),
        CheckConstraint("finalidade IN ('FIDELIDADE')", name="ck_consentimento_finalidade"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuarioId: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id"))
    finalidade: Mapped[str] = mapped_column(String(20))
    aceito: Mapped[bool] = mapped_column(Boolean, default=False)
    registradoEm: Mapped[datetime] = mapped_column(DateTime, default=agora)
    revogadoEm: Mapped[datetime | None] = mapped_column(DateTime)  # atributo proposto


class AuditoriaModel(Base):
#Somente inserção: não há UPDATE nem DELETE nesta tabela.

    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuarioId: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("usuario.id"))
    acao: Mapped[str] = mapped_column(String(60))
    entidade: Mapped[str] = mapped_column(String(40))
    entidadeId: Mapped[int] = mapped_column(BigInteger)
    estadoAnterior: Mapped[str | None] = mapped_column(Text)
    estadoNovo: Mapped[str | None] = mapped_column(Text)
    dataHora: Mapped[datetime] = mapped_column(DateTime, default=agora)