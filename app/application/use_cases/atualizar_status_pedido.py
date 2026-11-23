from app.application.errors import Conflito, NaoAutenticado, NaoEncontrado, SemPermissao
from app.domain.entities.pedido import Pedido, perfil_da_transicao
from app.domain.enums import StatusPedido


class AtualizarStatusPedido:
    def __init__(self, usuarios, pedidos, auditoria, transacao):
        self._usuarios = usuarios
        self._pedidos = pedidos
        self._auditoria = auditoria
        self._transacao = transacao

    def executar(self, usuario_id: int, perfil: str, pedido_id: int,
                 novo_status: StatusPedido) -> Pedido:
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NaoAutenticado("Usuário não encontrado.")
        if usuario.unidade_id is None:
            raise NaoEncontrado("Pedido não encontrado.")

        # Só enxerga pedidos da própria unidade (outra unidade = 404).
        pedido = self._pedidos.buscar_na_unidade(pedido_id, usuario.unidade_id)
        if pedido is None:
            raise NaoEncontrado("Pedido não encontrado.")

        executor = perfil_da_transicao(pedido.status, novo_status)
        if executor is None:
            raise Conflito(
                f"Transição inválida: {pedido.status.value} para {novo_status.value}."
            )
        if executor.value != perfil:
            raise SemPermissao("Este perfil não pode executar esta transição.")

        anterior = pedido.status
        if not self._pedidos.atualizar_status(pedido.id, anterior, novo_status):
            raise Conflito("O status do pedido mudou. Consulte e tente de novo.")

        self._auditoria.registrar(
            usuario_id, "STATUS_ALTERADO", "PEDIDO", pedido.id,
            {"status": anterior.value}, {"status": novo_status.value},
        )
        self._transacao.commit()
        pedido.status = novo_status
        return pedido