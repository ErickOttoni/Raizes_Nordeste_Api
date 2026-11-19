from app.application.errors import NaoEncontrado
from app.application.ports.cardapio_repository import CardapioRepository, UnidadeRepository
from app.domain.entities.item_cardapio import ItemCardapio


class ConsultarCardapio:
    def __init__(self, unidades: UnidadeRepository, cardapio: CardapioRepository):
        self._unidades = unidades
        self._cardapio = cardapio

    def executar(self, unidade_id: int) -> list[ItemCardapio]:
        unidade = self._unidades.buscar_por_id(unidade_id)
        if unidade is None or not unidade.ativa:
            raise NaoEncontrado("Unidade não encontrada.")
        return self._cardapio.listar_ativos(unidade_id)