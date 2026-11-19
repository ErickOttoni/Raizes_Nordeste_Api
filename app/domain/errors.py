class ErroDeDominio(Exception):
    """Base dos erros de regra de negócio."""


class DadosInvalidos(ErroDeDominio):
    def __init__(self, mensagem: str, campo: str | None = None):
        super().__init__(mensagem)
        self.campo = campo


class EstoqueInsuficiente(ErroDeDominio):
    def __init__(self, produto_id: int):
        super().__init__(f"Estoque insuficiente para o produto {produto_id}.")
        self.produto_id = produto_id


class TransicaoInvalida(ErroDeDominio):
    pass