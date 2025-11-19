from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.produto import Produto
from app.models.peca_db import PecaDB
from app.schemas.peca import PecaResponse
from typing import List
import pandas as pd
import io
import re

router = APIRouter(prefix="/pecas", tags=["Peças"])

def extrair_espessura(material: str) -> float:
    """Extrai espessura do código do material (ex: MDF15 -> 15)"""
    match = re.search(r'(\d+)', material)
    return float(match.group(1)) if match else 15.0

@router.post("/importar", response_model=dict)
async def importar_pecas(
    codigo_produto: str = Form(...),
    nome_produto: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Importa peças do Excel do CargaMaquina
    """
    
    # Validar arquivo
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")
    
    try:
        # Ler Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Validar colunas necessárias
        colunas_necessarias = ['Peça', 'Material', 'C', 'L', 'Cod. Peça', 'Família']
        colunas_faltando = [col for col in colunas_necessarias if col not in df.columns]
        
        if colunas_faltando:
            raise HTTPException(
                status_code=400, 
                detail=f"Colunas faltando no Excel: {', '.join(colunas_faltando)}"
            )
        
        # Criar ou buscar produto
        produto = db.query(Produto).filter(Produto.codigo == codigo_produto).first()
        
        if not produto:
            produto = Produto(
                codigo=codigo_produto,
                nome=nome_produto or f"Produto {codigo_produto}"
            )
            db.add(produto)
            db.commit()
            db.refresh(produto)
        
        # Processar peças
        pecas_criadas = 0
        
        for _, row in df.iterrows():
            # Extrair dados
            codigo_peca = str(int(float(row['Cod. Peça']))).strip()
            nome_peca = str(row['Peça']).strip()
            material = str(row['Material']).strip()
            comprimento = float(row['C']) if pd.notna(row['C']) else 0
            largura = float(row['L']) if pd.notna(row['L']) else 0
            familia = str(row['Família']).strip() if pd.notna(row['Família']) else None
            espessura = extrair_espessura(material)
            
            # Verificar se peça já existe
            peca_existente = db.query(PecaDB).filter(
                PecaDB.produto_id == produto.id,
                PecaDB.codigo == codigo_peca
            ).first()
            
            if peca_existente:
                # Atualizar
                peca_existente.nome = nome_peca
                peca_existente.material = material
                peca_existente.comprimento = comprimento
                peca_existente.largura = largura
                peca_existente.espessura = espessura
                peca_existente.familia = familia
            else:
                # Criar nova
                nova_peca = PecaDB(
                    produto_id=produto.id,
                    codigo=codigo_peca,
                    nome=nome_peca,
                    material=material,
                    comprimento=comprimento,
                    largura=largura,
                    espessura=espessura,
                    familia=familia
                )
                db.add(nova_peca)
                pecas_criadas += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{pecas_criadas} peças importadas com sucesso!",
            "produto_id": produto.id,
            "codigo_produto": produto.codigo
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao importar: {str(e)}")

@router.get("/produto/{codigo_produto}", response_model=List[PecaResponse])
def listar_pecas_produto(codigo_produto: str, db: Session = Depends(get_db)):
    """Lista todas as peças de um produto"""
    
    produto = db.query(Produto).filter(Produto.codigo == codigo_produto).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    pecas = db.query(PecaDB).filter(PecaDB.produto_id == produto.id).all()
    
    return pecas