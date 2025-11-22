from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import Response
from app.core.auth import get_current_active_user
from app.models.user import User
from app.generators.mpr_generator import GeradorMPR
import tempfile

router = APIRouter(prefix="/editor", tags=["editor"])


class FuroData(BaseModel):
    tipo: str  # 'vertical' ou 'horizontal'
    x: float
    y: float
    diametro: float
    profundidade: float
    lado: Optional[str] = None  # Para furos horizontais: XP, XM, YP, YM


class PecaData(BaseModel):
    nome: str
    largura: float
    comprimento: float
    espessura: float
    furos: List[FuroData]
    peca_id: Optional[int] = None


@router.post("/export-mpr")
async def export_mpr(
    peca: PecaData,
    current_user: User = Depends(get_current_active_user)
):
    """
    Exporta peça criada no editor como arquivo MPR
    
    Args:
        peca: Dados da peça com dimensões e furos
        
    Returns:
        Arquivo MPR para download
    """
    try:
        print(f"\n📤 ===== EXPORTANDO MPR =====")
        print(f"👤 Usuário: {current_user.username}")
        print(f"📦 Peça: {peca.nome}")
        print(f"📐 Dimensões: {peca.largura}x{peca.comprimento}x{peca.espessura}mm")
        print(f"🔵 Total de furos: {len(peca.furos)}")
        
        # Converter Pydantic para dict
        peca_dict = {
            'nome': peca.nome,
            'largura': peca.largura,
            'comprimento': peca.comprimento,
            'espessura': peca.espessura,
            'furos': [
                {
                    'tipo': f.tipo,
                    'x': f.x,
                    'y': f.y,
                    'diametro': f.diametro,
                    'profundidade': f.profundidade,
                    'lado': f.lado
                }
                for f in peca.furos
            ]
        }
        
        # Gerar MPR
        gerador = GeradorMPR()
        mpr_content = gerador.gerar_mpr(peca_dict)
        
        print(f"✅ MPR gerado: {len(mpr_content)} caracteres")
        
        # Retornar como arquivo para download
        filename = f"{peca.nome}.mpr"
        
        return Response(
            content=mpr_content.encode('utf-8'),
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        print(f"❌ Erro ao exportar MPR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar MPR: {str(e)}")


@router.post("/generate-pdf")
async def generate_pdf_from_editor(
    largura: float = Form(...),
    comprimento: float = Form(...),
    espessura: float = Form(...),
    nome_peca: str = Form(...),
    furos_verticais: str = Form("[]"),
    furos_horizontais: str = Form("[]"),
    peca_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Gera PDF diretamente dos dados do editor (sem passar por MPR)
    """
    try:
        import json
        from app.parsers.mpr_parser import Peca, Dimensoes, FuroVertical, FuroHorizontal
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
        
        # Converter dados do editor para formato Peca
        dimensoes = Dimensoes(
            largura=largura,
            comprimento=comprimento,
            espessura=espessura
        )
        
        furos_verticais_obj = []
        furos_horizontais_obj = []
        
        for furo in furos_vert:
            if furo.get('tipo') == 'vertical':
                furos_verticais_obj.append(
                    FuroVertical(
                        x=furo['x'],
                        y=furo['y'],
                        diametro=furo['diametro'],
                        profundidade=furo.get('profundidade', 0)
                    )
                )
        
        for furo in furos_horiz:
            if furo.get('tipo') == 'horizontal':
                furos_horizontais_obj.append(
                    FuroHorizontal(
                        lado=furo.get('lado', 'XP'),
                        y=furo['y'],
                        z=furo['x'],
                        diametro=furo['diametro'],
                        profundidade=furo.get('profundidade', 0)
                    )
                )
        
        peca_obj = Peca(
            nome_peca=nome_peca,
            dimensoes=dimensoes,
            furos_verticais=furos_verticais_obj,
            furos_horizontais=furos_horizontais_obj
        )
        
        # Gerar PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name
        
        gerador = GeradorDesenhoTecnico()
        dados_adicionais = {
            'angulo_rotacao': 0,
            'espelhar_peca': False,
            'bordas': {'top': None, 'bottom': None, 'left': None, 'right': None},
            'alerta': None,
            'revisao': '00',
            'codigo_peca': codigo_peca,
            'nome_peca': nome_peca_db,
            'codigo_produto': codigo_produto,
            'nome_produto': nome_produto
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