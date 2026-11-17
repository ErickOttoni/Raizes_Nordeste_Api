#Popula o banco com dados de teste: unidades, produtos, cardápio, estoque e usuários.

from app.infrastructure.security.passwords import BcryptHash, gerar_hash
from decimal import Decimal

import bcrypt
from sqlalchemy import select

from app.infrastructure.database import SessionLocal
from app.infrastructure.persistence.models import (
    CardapioModel, ConsentimentoModel, EstoqueModel,
    ProdutoModel, UnidadeModel, UsuarioModel,
)

SENHA_PADRAO = "senha123"

def main() -> None:
    with SessionLocal() as db:
        if db.scalar(select(UsuarioModel.id).limit(1)) is not None:
            print("Seed já aplicado.")
            return

        unidades = [
            UnidadeModel(nome="Raízes Recife", regiao="Nordeste"),
            UnidadeModel(nome="Raízes Fortaleza", regiao="Nordeste"),
        ]
        produtos = [
            (ProdutoModel(nome="Tapioca", descricao="Tapioca com queijo coalho"), Decimal("12.00")),
            (ProdutoModel(nome="Cuscuz", descricao="Cuscuz com ovo"), Decimal("10.00")),
            (ProdutoModel(nome="Baião de dois", descricao="Prato do dia"), Decimal("25.00")),
            (ProdutoModel(nome="Suco de caju", descricao="300 ml"), Decimal("8.00")),
        ]
        db.add_all(unidades + [p for p, _ in produtos])
        db.flush()  # grava e já preenche os ids

        recife = unidades[0]
        baiao = produtos[2][0]
        for unidade in unidades:
            for produto, preco in produtos:
                # Baião de dois em Recife tem só 2 unidades: serve para o teste do 409.
                quantidade = 2 if (unidade is recife and produto is baiao) else 10
                db.add(CardapioModel(unidadeId=unidade.id, produtoId=produto.id, preco=preco))
                db.add(EstoqueModel(unidadeId=unidade.id, produtoId=produto.id, quantidade=quantidade))
        
        senha = BcryptHash().gerar(SENHA_PADRAO) #gera o hash da senha padrão para todos os usuários de teste.
        cliente = UsuarioModel(nome="Cliente Teste", email="cliente@teste.com",
                               senhaHash=senha, perfil="CLIENTE")
        cliente2 = UsuarioModel(nome="Cliente Sem Fidelidade", email="cliente2@teste.com",
                                senhaHash=senha, perfil="CLIENTE")
        atendente = UsuarioModel(nome="Atendente Teste", email="atendente@teste.com",
                                 senhaHash=senha, perfil="ATENDENTE", unidadeId=recife.id)
        cozinha = UsuarioModel(nome="Cozinha Teste", email="cozinha@teste.com",
                               senhaHash=senha, perfil="COZINHA", unidadeId=recife.id)
        gerente = UsuarioModel(nome="Gerente Teste", email="gerente@teste.com",
                               senhaHash=senha, perfil="GERENTE")
        db.add_all([cliente, cliente2, atendente, cozinha, gerente])
        db.flush()  # para ter os ids dos usuários

        # Todo cliente tem a linha de consentimento (aceito=False quando não aceitou).
        db.add(ConsentimentoModel(usuarioId=cliente.id, finalidade="FIDELIDADE", aceito=True))
        db.add(ConsentimentoModel(usuarioId=cliente2.id, finalidade="FIDELIDADE", aceito=False))

        db.commit()
        print("Seed aplicado.")
        print(f"Usuários de teste (senha: {SENHA_PADRAO}): cliente@teste.com, cliente2@teste.com, "
              "atendente@teste.com, cozinha@teste.com, gerente@teste.com")

if __name__ == "__main__":
    main()