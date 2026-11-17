class NaoAutenticado(Exception):
    """Sem token, token inválido ou expirado (vira 401)."""

class SemPermissao(Exception):
    """Token válido, mas o perfil não pode (vira 403)."""

class NaoEncontrado(Exception):
    """Recurso inexistente (vira 404)."""

class Conflito(Exception):
    """Estado que não permite a operação (vira 409)."""