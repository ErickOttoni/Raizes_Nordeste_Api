from fastapi import FastAPI

from app.api.error_handlers import registrar_handlers
from app.api.routers import auth
from app.container import configurar
# Configura a aplicação FastAPI, registrando os manipuladores de erros, os roteadores e as dependências do container.
app = FastAPI(title="Raízes do Nordeste API", version="0.1.0")
registrar_handlers(app)
app.include_router(auth.router)
configurar(app)