from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class PecaBase(BaseModel):
    codigo: str
    nome: Optional[str] = None
    material: Optional[str] = None
    espessura: Optional[float] = None
    comprimento: Optional[float] = None
    largura: Optional[float] = None
    quantidade: Optional[int] = 1

class PecaCreate(PecaBase):
    produto_id: int

class PecaResponse(PecaBase):
    id: int
    produto_id: int
    mpr_path: Optional[str] = None
    pdf_path: Optional[str] = None
    furos: Optional[Any] = None
    bordas: Optional[Any] = None
    transformacao: Optional[Any] = None
    created_at: datetime
    updated_at: datetime
    alerta: Optional[bool] = False
    observacoes: Optional[str] = None
    
    class Config:
        from_attributes = True

class ImportarPecasRequest(BaseModel):
    codigo_produto: str
    nome_produto: Optional[str] = None