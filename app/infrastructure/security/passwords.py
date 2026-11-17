import bcrypt

#verifica se a senha é valida e retorna o hash da senha
class BcryptHash:
    def gerar(self, senha: str) -> str:
        return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    def verificar(self, senha: str, senha_hash: str) -> bool:
        return bcrypt.checkpw(senha.encode(), senha_hash.encode())