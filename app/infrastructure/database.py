from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.infrastructure.config import settings

#pool_pre_ping é usado para verificar se a conexão com o banco de dados ainda está ativa antes de usá-la, evitando erros de conexão. 
engine = create_engine(settings.database_url, pool_pre_ping=True)
#uma sessão por requisição
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

#classe de qual todas as tabelas herdam
class Base(DeclarativeBase):
    pass