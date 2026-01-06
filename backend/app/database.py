"""
Configuração do banco de dados
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# URL do banco (variável de ambiente ou local)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_o2KqUb4ykPZh@ep-silent-dream-ah42tefe-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
    #"postgresql://kp_user:kp_pass@localhost/corewood_db"
)

# Criar engine com configurações de reconexão
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Testa conexão antes de usar
    pool_recycle=300,    # Recicla conexões a cada 5 minutos
    pool_size=5,         # Tamanho do pool
    max_overflow=10      # Conexões extras permitidas
)

# Session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para models
Base = declarative_base()

# Dependency para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()