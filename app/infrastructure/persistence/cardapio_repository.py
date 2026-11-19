from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.item_cardapio import ItemCardapio
from app.domain.entities.unidade import Unidade
from app.infrastructure.persistence.models import CardapioModel, ProdutoModel, UnidadeModel

#classe de repositório para manipulação de cardápio e unidades no banco de dados

class SqlUnidadeRepository:
    def __init__(self, db: Session):
        self._db = db

    def buscar_por_id(self, unidade_id: int) -> Unidade | None:
        m = self._db.get(UnidadeModel, unidade_id)
        return Unidade(m.id, m.nome, m.regiao, m.ativa) if m else None


class SqlCardapioRepository:
    def __init__(self, db: Session):
        self._db = db

    def listar_ativos(self, unidade_id: int) -> list[ItemCardapio]:
        consulta = (
            select(CardapioModel, ProdutoModel)
            .join(ProdutoModel, ProdutoModel.id == CardapioModel.produtoId)
            .where(CardapioModel.unidadeId == unidade_id, CardapioModel.ativo.is_(True))
            .order_by(ProdutoModel.nome)
        )
        return [self._para_entidade(c, p) for c, p in self._db.execute(consulta).all()]

    def buscar_item(self, unidade_id: int, produto_id: int) -> ItemCardapio | None:
        consulta = (
            select(CardapioModel, ProdutoModel)
            .join(ProdutoModel, ProdutoModel.id == CardapioModel.produtoId)
            .where(CardapioModel.unidadeId == unidade_id, CardapioModel.produtoId == produto_id)
        )
        linha = self._db.execute(consulta).first()
        return self._para_entidade(*linha) if linha else None

    @staticmethod
    def _para_entidade(c: CardapioModel, p: ProdutoModel) -> ItemCardapio:
        return ItemCardapio(c.unidadeId, c.produtoId, p.nome, p.descricao, c.preco, c.ativo)