from fastapi import APIRouter, Depends

from app.api.dependencies import exigir_perfil, get_criar_pedido
from app.api.schemas.pedido import CriarPedidoRequest, ItemPedidoResponse, PedidoResponse
from app.application.ports.token_service import DadosToken
from app.application.use_cases.criar_pedido import CriarPedido
from app.domain.entities.pedido import ItemSolicitado, Pedido

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