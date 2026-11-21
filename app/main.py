from fastapi import FastAPI

from app.api.error_handlers import registrar_handlers
from app.api.routers import auth, cardapio, pedidos
from app.container import configurar
from app.api.routers import auditoria, auth, cardapio, pedidos

# Cria a aplicação, registra os tratadores de erro, as rotas e a montagem das dependências.
app = FastAPI(title="Raízes do Nordeste API", version="0.1.0")
registrar_handlers(app)
app.include_router(auth.router)
app.include_router(auditoria.router)
app.include_router(cardapio.router)
app.include_router(pedidos.router)
configurar(app)