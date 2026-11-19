from pydantic import BaseModel


class ItemCardapioResponse(BaseModel):
    produtoId: int
    nome: str
    descricao: str | None
    preco: float  # o domínio usa Decimal; na resposta, número simples