from fastapi import APIRouter, Depends
from httpx import get

from app.api.dependencies import exigir_perfil, get_criar_pedido, get_pagar_pedido
from app.api.schemas.pedido import CriarPedidoRequest, ItemPedidoResponse, PedidoResponse
from app.application.ports.token_service import DadosToken
from app.application.use_cases.criar_pedido import CriarPedido
from app.domain.entities.pedido import ItemSolicitado, Pedido
from app.application.errors import Conflito, ErroGateway
from app.api.schemas.pedido import PagamentoRequest, PedidoPagoResponse
from app.application.use_cases.pagar_pedido import PagarPedido, Desfecho


router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

#funções para criar pedidos, incluindo a conversão de entidades de domínio em respostas de API e a execução do caso de uso de criação de pedidos com validação de perfil do usuário.
def _para_resposta(pedido: Pedido) -> PedidoResponse:
    return PedidoResponse(
        id=pedido.id, unidadeId=pedido.unidade_id, canalPedido=pedido.canal.value,
        status=pedido.status.value, total=float(pedido.total),
        reservaExpiraEm=pedido.reserva_expira_em,
        itens=[ItemPedidoResponse(produtoId=i.produto_id, quantidade=i.quantidade,
                                  precoUnitario=float(i.preco_unitario))
               for i in pedido.itens],
    )


@router.post("", response_model=PedidoResponse, status_code=201)
def criar_pedido(
    corpo: CriarPedidoRequest,
    dados: DadosToken = Depends(exigir_perfil("CLIENTE")),
    caso_de_uso: CriarPedido = Depends(get_criar_pedido),
):
    itens = [ItemSolicitado(i.produtoId, i.quantidade) for i in corpo.itens]
    pedido = caso_de_uso.executar(dados.usuario_id, corpo.unidadeId, corpo.canalPedido, itens)
    return _para_resposta(pedido)

@router.post("/{pedido_id}/pagamento", response_model=PedidoPagoResponse)
def pagar_pedido(
    pedido_id: int,
    corpo: PagamentoRequest = PagamentoRequest(),
    dados: DadosToken = Depends(exigir_perfil("CLIENTE")),
    caso_de_uso: PagarPedido = Depends(get_pagar_pedido),
):
    r = caso_de_uso.executar(dados.usuario_id, pedido_id, corpo.simularResultado)
    # O commit já aconteceu no caso de uso: aqui só traduzimos o resultado.
    if r.desfecho == Desfecho.ERRO_GATEWAY:
        raise ErroGateway(r.motivo or "Falha no gateway de pagamento.")
    if r.desfecho == Desfecho.RESERVA_EXPIRADA:
        raise Conflito("Reserva expirada: o pedido foi cancelado.")
    base = _para_resposta(r.pedido).model_dump()
    return PedidoPagoResponse(**base, pontosCreditados=r.pontos_creditados, motivo=r.motivo)