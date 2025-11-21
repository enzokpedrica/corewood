from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class PecaDB(Base):
    __tablename__ = "pecas"
    
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True)
    codigo = Column(String(20), nullable=False, index=True)
    nome = Column(String(200))
    material = Column(String(100))
    espessura = Column(Numeric(10, 2))
    comprimento = Column(Numeric(10, 2))
    largura = Column(Numeric(10, 2))
    quantidade = Column(Integer, default=1)
    mpr_path = Column(String(500))
    pdf_path = Column(String(500))
    furos = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamento
    produto = relationship("Produto", back_populates="pecas")