from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.produto import Produto
from app.models.peca_db import PecaDB
from app.schemas.peca import PecaResponse
from typing import List
from app.core.auth import get_current_active_user
from app.models.user import User
import pandas as pd
import io
import re

router = APIRouter(prefix="/pecas", tags=["Peças"])

def extrair_espessura(material: str) -> float:
    """Extrai espessura do código do material (ex: MDF15 -> 15)"""
    match = re.search(r'(\d+)', material)
    return float(match.group(1)) if match else 15.0

def converter_numero(valor):
    if pd.isna(valor):
        return 0
    if isinstance(valor, (int, float)):
        return float(valor)
    # Tratar string com vírgula como decimal
    return float(str(valor).strip().replace(',', '.'))



@router.post("/importar", response_model=dict)
async def importar_pecas(
    codigo_produto: str = Form(...),
    nome_produto: str = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Importa peças do Excel ou CSV do CargaMaquina
    """
    
    # Validar arquivo
    extensoes_validas = ('.xlsx', '.xls', '.csv')
    if not file.filename.lower().endswith(extensoes_validas):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx, .xls) ou CSV (.csv)")
    
    try:
        # Ler arquivo
        contents = await file.read()
        
        # Detectar tipo e ler adequadamente
        if file.filename.lower().endswith('.csv'):
            # Tentar diferentes encodings para CSV
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(io.BytesIO(contents), encoding=encoding, sep=None, engine='python')
                    break
                except:
                    continue
            else:
                raise HTTPException(status_code=400, detail="Não foi possível ler o CSV. Verifique o encoding.")
        else:
            # Excel - tentar diferentes engines
            try:
                df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
            except:
                try:
                    df = pd.read_excel(io.BytesIO(contents), engine='xlrd')
                except:
                    raise HTTPException(
                        status_code=400, 
                        detail="Arquivo Excel corrompido. Abra no Excel, salve como novo arquivo e tente novamente."
                    )

        # Remove última linha (informações desnecessárias)
        df = df[:-1]
        
        # Validar colunas necessárias
        colunas_necessarias = ['Peça', 'Material', 'C', 'L', 'Cod. Peça', 'Família']
        colunas_faltando = [col for col in colunas_necessarias if col not in df.columns]
        
        if colunas_faltando:
            raise HTTPException(
                status_code=400, 
                detail=f"Colunas faltando no arquivo: {', '.join(colunas_faltando)}"
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
            comprimento = converter_numero(row['C'])
            largura = converter_numero(row['L'])
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
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao importar: {str(e)}")
    
@router.put("/{peca_id}/salvar", response_model=PecaResponse)
async def salvar_peca(
    peca_id: int,
    largura: float = Form(...),
    comprimento: float = Form(...),
    espessura: float = Form(...),
    furos: str = Form("{}"),
    bordas: str = Form("{}"),
    transformacao: str = Form("{}"),
    current_user: User = Depends(get_current_active_user),
    alerta: str = Form("false"),
    observacoes: str = Form(""),
    db: Session = Depends(get_db)
):
    print(f"\n\n🔴🔴🔴 ROTA SALVAR CHAMADA! peca_id={peca_id} 🔴🔴🔴\n\n")
    print(f"⚠️ ALERTA recebido: '{alerta}'")
    print(f"📝 OBSERVAÇÕES: '{observacoes}'")
    
    peca = db.query(PecaDB).filter(PecaDB.id == peca_id).first()
    
    if not peca:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    
    import json
    
    # Atualizar dimensões
    peca.largura = largura
    peca.comprimento = comprimento
    peca.espessura = espessura
    
    # Atualizar furos (JSON)
    peca.furos = json.loads(furos)
    
    # Atualizar bordas (JSON)
    peca.bordas = json.loads(bordas)
    
    # Atualizar transformação (JSON)
    peca.transformacao = json.loads(transformacao)

    peca.alerta = alerta.lower() == 'true'
    peca.observacoes = observacoes      
    
    print(f"💾 Salvando peça {peca_id}:")
    print(f"   Dimensões: {largura}x{comprimento}x{espessura}")
    print(f"   Furos: {peca.furos}")
    print(f"   Bordas: {peca.bordas}")
    print(f"   Transformação: {peca.transformacao}")
    
    db.commit()
    db.refresh(peca)
    
    return peca  
    

@router.get("/produto/{codigo_produto}", response_model=List[PecaResponse])
def listar_pecas_produto(
    codigo_produto: str, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)):
    """Lista todas as peças de um produto"""
    
    produto = db.query(Produto).filter(Produto.codigo == codigo_produto).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    pecas = db.query(PecaDB).filter(PecaDB.produto_id == produto.id).order_by(PecaDB.codigo).all()
    
    # DEBUG
    for p in pecas:
        print(f"🔍 Peça {p.id} - {p.codigo}: alerta={p.alerta}, obs={p.observacoes}")
    
    return pecas