from dataclasses import dataclass
from enum import Enum

from app.application.errors import Conflito, NaoEncontrado
from app.application.ports.pagamento_ports import (
    ConsentimentoRepository, PagamentoGateway, PagamentoRepository,
)
from app.application.ports.pedido_ports import (
    AuditoriaRepository, EstoqueRepository, PedidoRepository, Relogio, Transacao,
)
from app.application.ports.usuario_repository import UsuarioRepository
from app.domain.entities.pedido import Pedido
from app.domain.enums import ResultadoPagamento, StatusPedido

#classes que representam o resultado do pagamento, incluindo o desfecho, o pedido, os pontos creditados e o motivo (quando aplicável).
class Desfecho(str, Enum):
    PAGO = "PAGO"
    RECUSADO = "RECUSADO"
    ERRO_GATEWAY = "ERRO_GATEWAY"
    RESERVA_EXPIRADA = "RESERVA_EXPIRADA"


@dataclass
class PagamentoResultado:
    desfecho: Desfecho
    pedido: Pedido
    pontos_creditados: int = 0
    motivo: str | None = None


class PagarPedido:
    def __init__(self, pedidos: PedidoRepository, estoque: EstoqueRepository,
                 pagamentos: PagamentoRepository, consentimentos: ConsentimentoRepository,
                 usuarios: UsuarioRepository, auditoria: AuditoriaRepository,
                 gateway: PagamentoGateway, relogio: Relogio, transacao: Transacao):
        self._pedidos = pedidos
        self._estoque = estoque
        self._pagamentos = pagamentos
        self._consentimentos = consentimentos
        self._usuarios = usuarios
        self._auditoria = auditoria
        self._gateway = gateway
        self._relogio = relogio
        self._transacao = transacao

    def _auditar_estoque(self, acao: str, pedido: Pedido, usuario_id: int) -> None:
        for item in pedido.itens:
            self._auditoria.registrar(
                acao=acao, entidade="PEDIDO", entidade_id=pedido.id, usuario_id=usuario_id,
                estado_anterior=None,
                estado_novo={"unidadeId": pedido.unidade_id, "produtoId": item.produto_id,
                             "quantidade": item.quantidade},
            )

    def executar(self, cliente_id: int, pedido_id: int,
                 simular_resultado: ResultadoPagamento = ResultadoPagamento.APROVADO
                 ) -> PagamentoResultado:
        # 1. Pedido inexistente e pedido de outro cliente dão o mesmo 404
        pedido = self._pedidos.buscar_do_cliente(pedido_id, cliente_id)
        if pedido is None:
            raise NaoEncontrado("Pedido não encontrado.")

        # 2. Já pago ou cancelado: 409, sem gravar nada
        if not pedido.aguardando_pagamento():
            raise Conflito("Pedido não está aguardando pagamento.")
        agora = self._relogio.agora()

        # 3. Reserva vencida: o cancelamento precisa ficar gravado, então commit e resultado
        if pedido.reserva_vencida(agora):
            motivo = "Reserva expirada"
            if self._pedidos.cancelar_se_aguardando(pedido.id, motivo):
                self._estoque.liberar_reserva(pedido.unidade_id, pedido.itens)
                self._auditar_estoque("ESTOQUE_LIBERADO", pedido, cliente_id)
                self._auditoria.registrar(
                    acao="RESERVA_EXPIRADA", entidade="PEDIDO", entidade_id=pedido.id,
                    usuario_id=cliente_id,
                    estado_anterior={"status": "AGUARDANDO_PAGAMENTO"},
                    estado_novo={"status": "CANCELADO"},
                )
            pedido.status = StatusPedido.CANCELADO
            pedido.motivo_cancelamento = motivo
            self._transacao.commit()
            return PagamentoResultado(Desfecho.RESERVA_EXPIRADA, pedido, motivo=motivo)

        # 4. Gateway: qualquer exceção (timeout, falha) é erro do gateway, não recusa
        try:
            resultado, motivo = self._gateway.cobrar(pedido.id, pedido.total, simular_resultado)
        except Exception:
            resultado, motivo = ResultadoPagamento.ERRO_GATEWAY, "Falha ao contatar o gateway."

        # 5. Toda tentativa fica registrada (RN 11)
        self._pagamentos.registrar(
            pedido_id=pedido.id, forma="GATEWAY", valor=pedido.total,
            resultado=resultado, motivo=motivo,
        )

        # 6. Erro do gateway: o pedido continua aguardando; grava a tentativa e responde 502
        if resultado == ResultadoPagamento.ERRO_GATEWAY:
            self._auditoria.registrar(
                acao="PAGAMENTO_ERRO_GATEWAY", entidade="PEDIDO", entidade_id=pedido.id,
                usuario_id=cliente_id, estado_anterior=None, estado_novo={"motivo": motivo},
            )
            self._transacao.commit()
            return PagamentoResultado(Desfecho.ERRO_GATEWAY, pedido, motivo=motivo)

        # 7. Recusado: cancela, libera a reserva, nenhum ponto
        if resultado == ResultadoPagamento.RECUSADO:
            motivo = motivo or "Pagamento recusado."
            if self._pedidos.cancelar_se_aguardando(pedido.id, motivo):
                self._estoque.liberar_reserva(pedido.unidade_id, pedido.itens)
                self._auditar_estoque("ESTOQUE_LIBERADO", pedido, cliente_id)
            pedido.status = StatusPedido.CANCELADO
            pedido.motivo_cancelamento = motivo
            self._auditoria.registrar(
                acao="PAGAMENTO_RECUSADO", entidade="PEDIDO", entidade_id=pedido.id,
                usuario_id=cliente_id,
                estado_anterior={"status": "AGUARDANDO_PAGAMENTO"},
                estado_novo={"status": "CANCELADO", "motivo": motivo},
            )
            self._transacao.commit()
            return PagamentoResultado(Desfecho.RECUSADO, pedido, motivo=motivo)

        # 8. Aprovado: pontos só com consentimento ativo; marcar_pago grava pontos e status juntos
        pontos = 0
        if self._consentimentos.ativo(cliente_id, "FIDELIDADE"):
            pontos = pedido.pontos_a_creditar()

        if not self._pedidos.marcar_pago(pedido.id, agora, pontos):
            # Alguém cancelou ao mesmo tempo: o rollback desfaz o registro do pagamento
            raise Conflito("Pedido não está mais aguardando pagamento.")

        self._estoque.baixar(pedido.unidade_id, pedido.itens)
        self._auditar_estoque("ESTOQUE_BAIXADO", pedido, cliente_id)
        if pontos > 0:
            self._usuarios.creditar_pontos(cliente_id, pontos)
        pedido.status = StatusPedido.PAGO
        pedido.pontos_creditados = pontos

        self._auditoria.registrar(
            acao="PAGAMENTO_APROVADO", entidade="PEDIDO", entidade_id=pedido.id,
            usuario_id=cliente_id,
            estado_anterior={"status": "AGUARDANDO_PAGAMENTO"},
            estado_novo={"status": "PAGO", "total": str(pedido.total)},
        )
        if pontos > 0:
            self._auditoria.registrar(
                acao="PONTOS_CREDITADOS", entidade="USUARIO", entidade_id=cliente_id,
                usuario_id=cliente_id, estado_anterior=None, estado_novo={"pontos": pontos},
            )
        self._transacao.commit()
        return PagamentoResultado(Desfecho.PAGO, pedido, pontos_creditados=pontos)