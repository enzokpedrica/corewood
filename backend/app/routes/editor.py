from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import Response
from app.core.auth import get_current_active_user
from app.models.user import User
from app.generators.mpr_generator import GeradorMPR
from app.database import get_db
from sqlalchemy.orm import Session
import tempfile
from typing import Union
import os
from app.models.peca_db import PecaDB
from app.models.produto import Produto

router = APIRouter(prefix="/editor", tags=["editor"])


class FuroData(BaseModel):
    tipo: str = "vertical"  # Padrão = vertical
    x: Union[float, str] = 0
    y: float
    z: Optional[float] = None
    diametro: float
    profundidade: float = 0
    lado: Optional[str] = "LS"
    id: Optional[float] = None


class FuroHorizontalData(BaseModel):
    x: Optional[float] = 0
    y: float
    z: float = 7.5
    diametro: float
    profundidade: float = 22.0
    lado: str = "XP"
    tipo: str = "horizontal"

class PecaData(BaseModel):
    nome: str
    comprimento: float
    largura: float
    espessura: float
    furos: List[FuroData] = []
    furosHorizontais: List[FuroHorizontalData] = []
    peca_id: Optional[int] = None


@router.post("/export-mpr")
async def export_mpr(
    peca: PecaData,
    current_user: User = Depends(get_current_active_user)
):
    """
    Exporta peça criada no editor como arquivo MPR
    """
    try:
        print(f"\n📤 ===== EXPORTANDO MPR =====")
        print(f"👤 Usuário: {current_user.username}")
        print(f"📦 Peça: {peca.nome}")
        print(f"📐 Dimensões: {peca.largura}x{peca.comprimento}x{peca.espessura}mm")
        print(f"🔴 Furos verticais: {len(peca.furos)}")
        print(f"🔵 Furos horizontais: {len(peca.furosHorizontais)}")
        
        # Juntar furos verticais e horizontais
        todos_furos = []
        
        # Furos verticais
        for f in peca.furos:
            todos_furos.append({
                'tipo': getattr(f, 'tipo', 'vertical'),
                'x': f.x,
                'y': f.y,
                'diametro': f.diametro,
                'profundidade': f.profundidade,
                'lado': getattr(f, 'lado', 'LS')
            })
        
        # Furos horizontais
        for f in peca.furosHorizontais:
            todos_furos.append({
                'tipo': 'horizontal',
                'x': f.x,
                'y': f.y,
                'z': f.z,
                'diametro': f.diametro,
                'profundidade': f.profundidade,
                'lado': f.lado
            })
        
        # Converter para dict
        peca_dict = {
            'nome': peca.nome,
            'largura': peca.largura,
            'comprimento': peca.comprimento,
            'espessura': peca.espessura,
            'furos': todos_furos
        }
        
        # Gerar MPR
        gerador = GeradorMPR()
        mpr_content = gerador.gerar_mpr(peca_dict)
        
        print(f"✅ MPR gerado: {len(mpr_content)} caracteres")
        
        # Retornar como arquivo para download
        filename = f"{peca.nome}.mpr"
        
        return Response(
            content=mpr_content.encode('cp1252', errors='replace'),
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        print(f"❌ Erro ao exportar MPR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar MPR: {str(e)}")


@router.post("/generate-pdf")
async def generate_pdf_from_editor(
    comprimento: float = Form(...),
    largura: float = Form(...),
    espessura: float = Form(...),
    nome_peca: str = Form(...),
    furos_verticais: str = Form("[]"),
    furos_horizontais: str = Form("[]"),
    bordas: str = Form("{}"),
    transformacao: str = Form("{}"),
    peca_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_active_user),
    alerta: bool = Form(False),
    observacoes: str = Form(""),
    db: Session = Depends(get_db)
):
    """
    Gera PDF diretamente dos dados do editor (sem passar por MPR)
    """
    try:
        import json
        from app.models.peca import Peca, Dimensoes, FuroVertical, FuroHorizontal
        from app.generators.pdf_generator import GeradorDesenhoTecnico
        from fastapi.responses import FileResponse
        from app.models.peca_db import PecaDB
        from app.models.produto import Produto
        
        print(f"\n📄 ===== GERANDO PDF DO EDITOR =====")
        print(f"👤 Usuário: {current_user.username}")
        print(f"📦 Peça: {nome_peca}")
        print(f"🆔 peca_id recebido: {peca_id}")

        # Buscar dados da peça se vier peca_id
        codigo_peca = None
        nome_peca_db = None
        codigo_produto = None
        nome_produto = None
        
        if peca_id:
            print(f"🔍 Buscando peça ID {peca_id} no banco...")
            peca_db = db.query(PecaDB).filter(PecaDB.id == peca_id).first()
            
            if peca_db:
                produto = db.query(Produto).filter(Produto.id == peca_db.produto_id).first()
                
                codigo_peca = peca_db.codigo
                nome_peca_db = peca_db.nome
                codigo_produto = produto.codigo if produto else None
                nome_produto = produto.nome if produto else None
                
                print(f"📋 Dados do banco encontrados:")
                print(f"   Código Peça: {codigo_peca}")
                print(f"   Nome Peça: {nome_peca_db}")
                print(f"   Código Produto: {codigo_produto}")
                print(f"   Nome Produto: {nome_produto}")
            else:
                print(f"⚠️ Peça ID {peca_id} não encontrada no banco")
        
        # Converter JSON strings para objetos
        furos_vert = json.loads(furos_verticais)
        furos_horiz = json.loads(furos_horizontais)

        # Converter bordas
        bordas_dict = json.loads(bordas)
        print(f"🎨 Bordas recebidas: {bordas_dict}")

        # Mapear nomes do frontend para o PDF
        bordas_pdf = {
            'top': bordas_dict.get('topo'),
            'bottom': bordas_dict.get('baixo'),
            'left': bordas_dict.get('esquerda'),
            'right': bordas_dict.get('direita')
        }

        # Converter 'nenhum' para None
        for key in bordas_pdf:
            if bordas_pdf[key] == 'nenhum':
                bordas_pdf[key] = None

        print(f"🎨 Bordas mapeadas para PDF: {bordas_pdf}")

        # Converter transformação
        transformacao_dict = json.loads(transformacao)
        print(f"🔄 Transformação: {transformacao_dict}")
        
        print(f"🔴 Furos verticais recebidos: {len(furos_vert)}")
        print(f"🔵 Furos horizontais recebidos: {len(furos_horiz)}")
        
        # Converter dados do editor para formato Peca
        dimensoes = Dimensoes(
            largura=comprimento,
            comprimento=largura,
            espessura=espessura
        )
        
        furos_verticais_obj = []
        furos_horizontais_obj = []
        
        # Processar furos verticais (não verificar 'tipo', assumir que são verticais)
        for furo in furos_vert:
            # Pular se tiver campo 'lado' de horizontal (XP, XM, YP, YM)
            lado = furo.get('lado', 'LS')
            if lado in ['XP', 'XM', 'YP', 'YM']:
                continue
                
            furos_verticais_obj.append(
                FuroVertical(
                    x=furo['x'],
                    y=furo['y'],
                    diametro=furo['diametro'],
                    profundidade=furo.get('profundidade', 0),
                    lado=lado
                )
            )
        
        # Processar furos horizontais
        for furo in furos_horiz:
            x_val = furo.get('x', 0)
            if x_val == 'x':
                x_val = 'x'
            else:
                x_val = float(x_val) if x_val else 0
            
            furos_horizontais_obj.append(
                FuroHorizontal(
                    x=x_val,
                    y=furo['y'],
                    z=furo.get('z', 7.5),
                    diametro=furo['diametro'],
                    profundidade=furo.get('profundidade', 0),
                    lado=furo.get('lado', 'XP')
                )
            )
        
        print(f"🔴 Furos verticais processados: {len(furos_verticais_obj)}")
        print(f"🔵 Furos horizontais processados: {len(furos_horizontais_obj)}")
        
        peca_obj = Peca(
            nome=nome_peca,
            dimensoes=dimensoes,
            furos_verticais=furos_verticais_obj,
            furos_horizontais=furos_horizontais_obj,
            comentarios=[]
        )
        
        # Gerar PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name
        
        gerador = GeradorDesenhoTecnico()
        dados_adicionais = {
            'angulo_rotacao': transformacao_dict.get('rotacao', 0),
            'espelhar_peca': transformacao_dict.get('espelhado', False),
            'bordas': bordas_pdf,
            'alerta': alerta,        
            'observacoes': observacoes,
            'revisao': '00',
            'status': 'CÓPIA CONTROLADA',
            'codigo_peca': codigo_peca,
            'nome_peca': nome_peca_db,
            'codigo_produto': codigo_produto,
            'nome_produto': nome_produto,
            'responsavel': current_user.username
        }
        
        gerador.gerar_pdf(peca_obj, pdf_path, dados_adicionais)
        
        print(f"✅ PDF gerado: {pdf_path}")
        
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f"{nome_peca}_furacao.pdf",
            background=None
        )
        
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")
    
@router.post("/generate-pdfs-batch")
async def generate_pdfs_batch(
    request: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Gera PDFs de múltiplas peças e retorna um ZIP
    """
    import zipfile
    import io
    from fastapi.responses import StreamingResponse
    
    peca_ids = request.get('peca_ids', [])
    
    if not peca_ids:
        raise HTTPException(status_code=400, detail="Nenhuma peça selecionada")
    
    print(f"\n📄 ===== GERANDO PDFs EM LOTE =====")
    print(f"👤 Usuário: {current_user.username}")
    print(f"📦 Peças: {peca_ids}")
    
    # Criar ZIP em memória
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for peca_id in peca_ids:
            try:
                # Buscar peça
                peca_db = db.query(PecaDB).filter(PecaDB.id == peca_id).first()
                if not peca_db:
                    print(f"⚠️ Peça {peca_id} não encontrada")
                    continue
                
                # Buscar produto
                produto = db.query(Produto).filter(Produto.id == peca_db.produto_id).first()
                
                print(f"📄 Gerando PDF: {peca_db.codigo} - {peca_db.nome}")
                
                # Montar dados da peça
                from app.models.peca import Peca, Dimensoes, FuroVertical, FuroHorizontal
                from app.generators.pdf_generator import GeradorDesenhoTecnico
                
                dimensoes = Dimensoes(
                    largura=float(peca_db.comprimento or 0),
                    comprimento=float(peca_db.largura or 0),
                    espessura=float(peca_db.espessura or 15)
                )
                
                # Processar furos
                furos_verticais_obj = []
                furos_horizontais_obj = []
                
                furos_data = peca_db.furos or {}
                
                for furo in furos_data.get('verticais', []):
                    lado = furo.get('lado', 'LS')
                    if lado not in ['XP', 'XM', 'YP', 'YM']:
                        furos_verticais_obj.append(
                            FuroVertical(
                                x=furo['x'],
                                y=furo['y'],
                                diametro=furo['diametro'],
                                profundidade=furo.get('profundidade', 0),
                                lado=lado
                            )
                        )
                
                for furo in furos_data.get('horizontais', []):
                    x_val = furo.get('x', 0)
                    if x_val == 'x':
                        x_val = 'x'
                    else:
                        x_val = float(x_val) if x_val else 0
                    
                    furos_horizontais_obj.append(
                        FuroHorizontal(
                            x=x_val,
                            y=furo['y'],
                            z=furo.get('z', 7.5),
                            diametro=furo['diametro'],
                            profundidade=furo.get('profundidade', 0),
                            lado=furo.get('lado', 'XP')
                        )
                    )
                
                peca_obj = Peca(
                    nome=peca_db.nome,
                    dimensoes=dimensoes,
                    furos_verticais=furos_verticais_obj,
                    furos_horizontais=furos_horizontais_obj,
                    comentarios=[]
                )
                
                # Buscar transformação e bordas
                transformacao = peca_db.transformacao or {}
                bordas = peca_db.bordas or {}
                
                # Mapear bordas
                bordas_pdf = {
                    'top': bordas.get('topo') if bordas.get('topo') != 'nenhum' else None,
                    'bottom': bordas.get('baixo') if bordas.get('baixo') != 'nenhum' else None,
                    'left': bordas.get('esquerda') if bordas.get('esquerda') != 'nenhum' else None,
                    'right': bordas.get('direita') if bordas.get('direita') != 'nenhum' else None
                }
                
                # Gerar PDF temporário
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    pdf_path = tmp_file.name
                
                gerador = GeradorDesenhoTecnico()
                dados_adicionais = {
                    'angulo_rotacao': transformacao.get('rotacao', 0),
                    'espelhar_peca': transformacao.get('espelhado', False),
                    'bordas': bordas_pdf,
                    'alerta': None,
                    'revisao': '00',
                    'status': 'CÓPIA CONTROLADA',
                    'codigo_peca': peca_db.codigo,
                    'nome_peca': peca_db.nome,
                    'codigo_produto': produto.codigo if produto else None,
                    'nome_produto': produto.nome if produto else None,
                    'responsavel': current_user.username
                }
                
                gerador.gerar_pdf(peca_obj, pdf_path, dados_adicionais)
                
                # Adicionar ao ZIP
                nome_arquivo = f"{peca_db.codigo}_{peca_db.nome}.pdf".replace(' ', '_')
                with open(pdf_path, 'rb') as pdf_file:
                    zip_file.writestr(nome_arquivo, pdf_file.read())
                
                # Limpar arquivo temporário
                os.remove(pdf_path)
                
                print(f"✅ PDF gerado: {nome_arquivo}")
                
            except Exception as e:
                print(f"❌ Erro ao gerar PDF da peça {peca_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
    
    zip_buffer.seek(0)
    
    print(f"✅ ZIP gerado com sucesso!")
    
    return StreamingResponse(
        zip_buffer,
        media_type='application/zip',
        headers={'Content-Disposition': 'attachment; filename=pecas_pdfs.zip'}
    )    