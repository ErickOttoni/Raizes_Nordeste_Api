from decimal import Decimal

from app.domain.enums import ResultadoPagamento


class GatewayPagamentoMock:
    """Gateway simulado: o resultado vem do campo simularResultado (RN 10)."""

    def cobrar(self, pedido_id: int, valor: Decimal,
               simular_resultado: ResultadoPagamento) -> tuple[ResultadoPagamento, str | None]:
        if simular_resultado == ResultadoPagamento.RECUSADO:
            return ResultadoPagamento.RECUSADO, "Pagamento recusado pelo gateway (simulado)."
        if simular_resultado == ResultadoPagamento.ERRO_GATEWAY:
            return ResultadoPagamento.ERRO_GATEWAY, "Gateway indisponível (simulado)."
        return ResultadoPagamento.APROVADO, None