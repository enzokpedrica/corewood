from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import Response
from ..auth.dependencies import get_current_active_user
from ..models import User
from ..generators.mpr_generator import GeradorMPR
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
    peca: PecaData,
    current_user: User = Depends(get_current_active_user)
):
    """
    Gera PDF diretamente dos dados do editor (sem passar por MPR)
    
    Args:
        peca: Dados da peça com dimensões e furos
        
    Returns:
        Arquivo PDF para download
    """
    try:
        from ..parsers.mpr_parser import Peca, Dimensoes, FuroVertical, FuroHorizontal
        from ..generators.pdf_generator import GeradorDesenhoTecnico
        from fastapi.responses import FileResponse
        
        print(f"\n📄 ===== GERANDO PDF DO EDITOR =====")
        print(f"👤 Usuário: {current_user.username}")
        print(f"📦 Peça: {peca.nome}")
        
        # Converter dados do editor para formato Peca
        dimensoes = Dimensoes(
            largura=peca.largura,
            comprimento=peca.comprimento,
            espessura=peca.espessura
        )
        
        furos_verticais = []
        furos_horizontais = []
        
        for furo in peca.furos:
            if furo.tipo == 'vertical':
                furos_verticais.append(
                    FuroVertical(
                        x=furo.x,
                        y=furo.y,
                        diametro=furo.diametro,
                        profundidade=furo.profundidade
                    )
                )
            elif furo.tipo == 'horizontal':
                furos_horizontais.append(
                    FuroHorizontal(
                        lado=furo.lado or 'XP',
                        y=furo.y,
                        z=furo.x,  # No horizontal, X vira Z
                        diametro=furo.diametro,
                        profundidade=furo.profundidade
                    )
                )
        
        peca_obj = Peca(
            nome_peca=peca.nome,
            dimensoes=dimensoes,
            furos_verticais=furos_verticais,
            furos_horizontais=furos_horizontais
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
            'revisao': '00'
        }
        
        gerador.gerar_pdf(peca_obj, pdf_path, dados_adicionais)
        
        print(f"✅ PDF gerado: {pdf_path}")
        
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f"{peca.nome}_furacao.pdf",
            background=None
        )
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")