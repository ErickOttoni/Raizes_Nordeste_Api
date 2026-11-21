import json
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.entities.auditoria import RegistroAuditoria
from app.domain.entities.pedido import Pedido
from app.infrastructure.persistence.models import (
    AuditoriaModel, EstoqueModel, ItemPedidoModel, PedidoModel, ConsentimentoModel, PagamentoModel
)
from app.domain.entities.pedido import ItemPedido, Pedido
from app.domain.enums import CanalPedido, StatusPedido


#classe de repositório para manipulação de pedidos, estoque e auditoria no banco de dados
class SqlPedidoRepository:
    def __init__(self, db: Session):
        self._db = db

    def criar(self, pedido: Pedido) -> Pedido:
        modelo = PedidoModel(
            clienteId=pedido.cliente_id, unidadeId=pedido.unidade_id,
            canalPedido=pedido.canal.value, status=pedido.status.value,
            total=pedido.total, reservaExpiraEm=pedido.reserva_expira_em,
        )
        self._db.add(modelo)
        self._db.flush()  # gera o id do pedido
        for item in pedido.itens:
            self._db.add(ItemPedidoModel(
                pedidoId=modelo.id, produtoId=item.produto_id,
                quantidade=item.quantidade, precoUnitario=item.preco_unitario,
            ))
        self._db.flush()
        pedido.id = modelo.id
        return pedido
    def buscar_do_cliente(self, pedido_id: int, cliente_id: int) -> Pedido | None:
        m = self._db.scalar(select(PedidoModel).where(
            PedidoModel.id == pedido_id, PedidoModel.clienteId == cliente_id))
        if m is None:
            return None
        itens = self._db.scalars(
            select(ItemPedidoModel).where(ItemPedidoModel.pedidoId == m.id)).all()
        return Pedido(
            id=m.id, cliente_id=m.clienteId, unidade_id=m.unidadeId,
            canal=CanalPedido(m.canalPedido), status=StatusPedido(m.status),
            total=m.total, reserva_expira_em=m.reservaExpiraEm,
            itens=[ItemPedido(i.produtoId, i.quantidade, i.precoUnitario) for i in itens],
            pontos_creditados=m.pontosCreditados, motivo_cancelamento=m.motivoCancelamento,
        )

    def cancelar_se_aguardando(self, pedido_id: int, motivo: str) -> bool:
        r = self._db.execute(
            update(PedidoModel)
            .where(PedidoModel.id == pedido_id, PedidoModel.status == "AGUARDANDO_PAGAMENTO")
            .values(status="CANCELADO", motivoCancelamento=motivo[:120])
        )
        return r.rowcount == 1

    def marcar_pago(self, pedido_id: int, agora: datetime, pontos: int) -> bool:
        r = self._db.execute(
            update(PedidoModel)
            .where(PedidoModel.id == pedido_id,
                   PedidoModel.status == "AGUARDANDO_PAGAMENTO",
                   PedidoModel.reservaExpiraEm >= agora)
            .values(status="PAGO", pontosCreditados=pontos)
        )
        return r.rowcount == 1


class SqlEstoqueRepository:
    def __init__(self, db: Session):
        self._db = db

    def reservar(self, unidade_id: int, produto_id: int, quantidade: int) -> bool:
        """RN 4: UPDATE condicional atômico. Só reserva se o disponível cobre."""
        resultado = self._db.execute(
            update(EstoqueModel)
            .where(
                EstoqueModel.unidadeId == unidade_id,
                EstoqueModel.produtoId == produto_id,
                EstoqueModel.quantidade - EstoqueModel.quantidadeReservada >= quantidade,
            )
            .values(quantidadeReservada=EstoqueModel.quantidadeReservada + quantidade)
        )
        return resultado.rowcount == 1

    def liberar_vencidas(self, agora: datetime) -> list[int]:
        """RN 6 e RN 7: cancela os vencidos e devolve o estoque só se o UPDATE afetou 1 linha."""
        vencidos = self._db.scalars(
            select(PedidoModel.id).where(
                PedidoModel.status == "AGUARDANDO_PAGAMENTO",
                PedidoModel.reservaExpiraEm < agora,
            )
        ).all()
        cancelados: list[int] = []
        for pedido_id in vencidos:
            resultado = self._db.execute(
                update(PedidoModel)
                .where(
                    PedidoModel.id == pedido_id,
                    PedidoModel.status == "AGUARDANDO_PAGAMENTO",
                    PedidoModel.reservaExpiraEm < agora,
                )
                .values(status="CANCELADO", motivoCancelamento="Reserva expirada")
            )
            if resultado.rowcount != 1:
                continue  # outra requisição já cancelou: não devolve o estoque de novo
            unidade_id = self._db.scalar(
                select(PedidoModel.unidadeId).where(PedidoModel.id == pedido_id)
            )
            itens = self._db.scalars(
                select(ItemPedidoModel).where(ItemPedidoModel.pedidoId == pedido_id)
            ).all()
            for item in itens:
                self._db.execute(
                    update(EstoqueModel)
                    .where(EstoqueModel.unidadeId == unidade_id,
                           EstoqueModel.produtoId == item.produtoId)
                    .values(quantidadeReservada=EstoqueModel.quantidadeReservada - item.quantidade)
                )
            cancelados.append(pedido_id)
        return cancelados
    
    def liberar_reserva(self, unidade_id: int, itens: list[ItemPedido]) -> None:
        for item in itens:
            self._db.execute(
                update(EstoqueModel)
                .where(EstoqueModel.unidadeId == unidade_id, EstoqueModel.produtoId == item.produto_id)
                .values(quantidadeReservada=EstoqueModel.quantidadeReservada - item.quantidade)
            )

    def baixar(self, unidade_id: int, itens: list[ItemPedido]) -> None:
        for item in itens:
            self._db.execute(
                update(EstoqueModel)
                .where(EstoqueModel.unidadeId == unidade_id, EstoqueModel.produtoId == item.produto_id)
                .values(quantidade=EstoqueModel.quantidade - item.quantidade,
                        quantidadeReservada=EstoqueModel.quantidadeReservada - item.quantidade)
            )

class SqlAuditoriaRepository:
    def __init__(self, db: Session):
        self._db = db

    def registrar(self, usuario_id, acao, entidade, entidade_id, estado_anterior, estado_novo) -> None:
        def _texto(valor):
            return None if valor is None else json.dumps(valor, ensure_ascii=False)

        self._db.add(AuditoriaModel(
            usuarioId=usuario_id, acao=acao, entidade=entidade, entidadeId=entidade_id,
            estadoAnterior=_texto(estado_anterior), estadoNovo=_texto(estado_novo),
        ))
    def listar(self, pagina: int, limite: int) -> list[RegistroAuditoria]:
        def _json(texto):
            return None if texto is None else json.loads(texto)

        consulta = (select(AuditoriaModel).order_by(AuditoriaModel.id.desc())
                    .offset((pagina - 1) * limite).limit(limite))
        return [
            RegistroAuditoria(m.id, m.usuarioId, m.acao, m.entidade, m.entidadeId,
                              _json(m.estadoAnterior), _json(m.estadoNovo), m.dataHora)
            for m in self._db.scalars(consulta)
        ]

class SqlTransacao:
    def __init__(self, db: Session):
        self._db = db

    def commit(self) -> None:
        self._db.commit()

class SqlPagamentoRepository:
    def __init__(self, db: Session):
        self._db = db

    def registrar(self, pedido_id, forma, valor, resultado, motivo) -> None:
        self._db.add(PagamentoModel(
            pedidoId=pedido_id, forma=forma, valor=valor,
            resultado=resultado.value, motivo=motivo[:120] if motivo else None,
        ))


class SqlConsentimentoRepository:
    def __init__(self, db: Session):
        self._db = db

    def ativo(self, usuario_id: int, finalidade: str) -> bool:
        c = self._db.scalar(select(ConsentimentoModel).where(
            ConsentimentoModel.usuarioId == usuario_id,
            ConsentimentoModel.finalidade == finalidade))
        return c is not None and c.aceito and c.revogadoEm is None