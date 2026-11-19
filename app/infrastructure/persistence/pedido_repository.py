import json
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.entities.pedido import Pedido
from app.infrastructure.persistence.models import (
    AuditoriaModel, EstoqueModel, ItemPedidoModel, PedidoModel,
)

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


class SqlTransacao:
    def __init__(self, db: Session):
        self._db = db

    def commit(self) -> None:
        self._db.commit()