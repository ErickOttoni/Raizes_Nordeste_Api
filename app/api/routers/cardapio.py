from fastapi import APIRouter, Depends

from app.api.dependencies import get_consultar_cardapio, usuario_atual
from app.api.schemas.cardapio import ItemCardapioResponse
from app.application.ports.token_service import DadosToken
from app.application.use_cases.consultar_cardapio import ConsultarCardapio

router = APIRouter(tags=["Cardápio"])


@router.get("/unidades/{unidade_id}/cardapio", response_model=list[ItemCardapioResponse])
def consultar_cardapio(
    unidade_id: int,
    _: DadosToken = Depends(usuario_atual),
    caso_de_uso: ConsultarCardapio = Depends(get_consultar_cardapio),
):
    itens = caso_de_uso.executar(unidade_id)
    return [ItemCardapioResponse(produtoId=i.produto_id, nome=i.nome,
                                 descricao=i.descricao, preco=float(i.preco)) for i in itens]