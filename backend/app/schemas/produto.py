from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ProdutoBase(BaseModel):
    codigo: str
    nome: Optional[str] = None
    descricao: Optional[str] = None

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoResponse(ProdutoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True