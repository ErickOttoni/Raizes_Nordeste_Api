from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.domain.enums import CanalPedido, StatusPedido, PerfilUsuario
from app.domain.errors import DadosInvalidos


@dataclass(frozen=True)
class ItemSolicitado:
    produto_id: int
    quantidade: int


def validar_itens(itens: list[ItemSolicitado]) -> None:
    """RN 1: itens não vazios, quantidade inteira >= 1, sem produto repetido."""
    if not itens:
        raise DadosInvalidos("O pedido precisa ter ao menos um item.", "itens")
    vistos: set[int] = set()
    for item in itens:
        if isinstance(item.quantidade, bool) or not isinstance(item.quantidade, int) or item.quantidade < 1:
            raise DadosInvalidos("A quantidade deve ser um número inteiro maior ou igual a 1.", "itens.quantidade")
        if item.produto_id in vistos:
            raise DadosInvalidos("Produto repetido nos itens.", "itens.produtoId")
        vistos.add(item.produto_id)

#classes de entidade para representar itens de pedido e pedidos, incluindo validação de itens e criação de pedidos com cálculo de total e reserva de tempo.
@dataclass
class ItemPedido:
    produto_id: int
    quantidade: int
    preco_unitario: Decimal


@dataclass
class Pedido:
    id: int | None
    cliente_id: int
    unidade_id: int
    canal: CanalPedido
    status: StatusPedido
    total: Decimal
    reserva_expira_em: datetime
    itens: list[ItemPedido]
    pontos_creditados: int = 0
    motivo_cancelamento: str | None = None

    @classmethod
    def criar(cls, cliente_id: int, unidade_id: int, canal: CanalPedido,
              itens: list[ItemPedido], agora: datetime, ttl_segundos: int) -> "Pedido":
        """RN 3 e RN 4: total calculado pelo servidor e reserva de 10 minutos (ttl)."""
        total = sum((i.preco_unitario * i.quantidade for i in itens), Decimal("0"))
        return cls(
            id=None, cliente_id=cliente_id, unidade_id=unidade_id, canal=canal,
            status=StatusPedido.AGUARDANDO_PAGAMENTO, total=total,
            reserva_expira_em=agora + timedelta(seconds=ttl_segundos), itens=itens,
        )
    
    def aguardando_pagamento(self) -> bool:
        return self.status == StatusPedido.AGUARDANDO_PAGAMENTO

    def reserva_vencida(self, agora: datetime) -> bool:
        return agora > self.reserva_expira_em

    def pontos_a_creditar(self) -> int:
        """RN 12: 1 ponto por R$ 1,00 pago, arredondado para baixo."""
        return int(self.total)  # int() de Decimal positivo trunca (19,90 -> 19)
    
# RF08: quem pode executar cada transição manual de status.
TRANSICOES_MANUAIS: dict[tuple[StatusPedido, StatusPedido], PerfilUsuario] = {
    (StatusPedido.PAGO, StatusPedido.EM_PREPARO): PerfilUsuario.COZINHA,
    (StatusPedido.EM_PREPARO, StatusPedido.PRONTO): PerfilUsuario.COZINHA,
    (StatusPedido.PRONTO, StatusPedido.ENTREGUE): PerfilUsuario.ATENDENTE,
}


def perfil_da_transicao(de: StatusPedido, para: StatusPedido) -> PerfilUsuario | None:
    """Devolve o perfil que executa a transição, ou None se ela não existe."""
    return TRANSICOES_MANUAIS.get((de, para))