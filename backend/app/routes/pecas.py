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

        # Remove última linha (informações desnecessárias)
        df = df[:-1]
        
        # Validar colunas necessárias
        colunas_necessarias = ['Peça', 'Material', 'C', 'L', 'Cod. Peça', 'Família']
        colunas_faltando = [col for col in colunas_necessarias if col not in df.columns]
        
        if colunas_faltando:
            raise HTTPException(
                status_code=400, 
                detail=f"Colunas faltando no Excel: {', '.join(colunas_faltando)}"
            )
        
        # Pegar família (nome do produto) da primeira linha
        familia_produto = None
        if len(df) > 0 and 'Família' in df.columns:
            familia_produto = str(df.iloc[0]['Família']).strip() if pd.notna(df.iloc[0]['Família']) else None

        # Criar ou buscar produto
        produto = db.query(Produto).filter(Produto.codigo == codigo_produto).first()

        if not produto:
            produto = Produto(
                codigo=codigo_produto,
                nome=familia_produto or nome_produto or f"Produto {codigo_produto}"
            )
            db.add(produto)
            db.commit()
            db.refresh(produto)
        else:
            # Atualizar nome com a família (sempre)
            if familia_produto:
                produto.nome = familia_produto
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
    
@router.put("/{peca_id}/salvar", response_model=PecaResponse)
async def salvar_peca(
    peca_id: int,
    largura: float = Form(...),
    comprimento: float = Form(...),
    espessura: float = Form(...),
    furos: str = Form("{}"),  # JSON string
    db: Session = Depends(get_db)
):
    """Salva alterações da peça (dimensões + furos)"""
    
    peca = db.query(PecaDB).filter(PecaDB.id == peca_id).first()
    
    if not peca:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    
    # Atualizar dimensões
    peca.largura = largura
    peca.comprimento = comprimento
    peca.espessura = espessura
    
    # Atualizar furos (JSON)
    import json
    peca.furos = json.loads(furos)
    
    db.commit()
    db.refresh(peca)
    
    return peca    
    

@router.get("/produto/{codigo_produto}", response_model=List[PecaResponse])
def listar_pecas_produto(codigo_produto: str, db: Session = Depends(get_db)):
    """Lista todas as peças de um produto"""
    
    produto = db.query(Produto).filter(Produto.codigo == codigo_produto).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    pecas = db.query(PecaDB).filter(PecaDB.produto_id == produto.id).all()
    
    return pecas