import bcrypt

#Funções pra gerar hash de senha e verificar senha
def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

#Função pra verificar se a senha corresponde ao hash
def verificar(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())