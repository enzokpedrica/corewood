"""
CoreWood API - FastAPI Application
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import tempfile
import os
from pathlib import Path
from .parser.mpr_parser import parse_furacao
from .generators.pdf_generator import GeradorDesenhoTecnico
from .database import engine, Base
from .routes import auth
from .core.auth import get_current_active_user
from .models.user import User
import json

# Criar tabelas no banco
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CoreWood API",
    description="API para geração de documentação técnica de peças",
    version="1.0.0"
)

# CORS - Permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínio do Netlify
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas de autenticação
app.include_router(auth.router)

@app.get("/")
def root():
    """Endpoint raiz - Health check"""
    return {
        "message": "CoreWood API Online! 🚀",
        "version": "1.0.0",
        "endpoints": {
            "parse": "/parse-mpr",
            "generate": "/generate-pdf",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/parse-mpr")
async def parse_mpr(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)  # ← ADICIONAR
):
    """
    Parse arquivo MPR e retorna dados estruturados
    
    Args:
        file: Arquivo MPR (upload)
        
    Returns:
        JSON com dados da peça (dimensões, furos, etc)
    """
    try:
        # Ler conteúdo do arquivo
        content = await file.read()
        content_str = content.decode('utf-8', errors='ignore')
        
        # Parse
        nome_peca = file.filename.replace('.mpr', '').replace('.MPR', '')
        peca = parse_furacao(content_str, nome_peca)
        
        # Converter para dict
        return {
            "status": "success",
            "data": {
                "nome": peca.nome,
                "dimensoes": {
                    "largura": peca.dimensoes.largura,
                    "comprimento": peca.dimensoes.comprimento,
                    "espessura": peca.dimensoes.espessura
                },
                "furos_verticais": [
                    {
                        "x": f.x,
                        "y": f.y,
                        "diametro": f.diametro,
                        "profundidade": f.profundidade
                    }
                    for f in peca.furos_verticais
                ],
                "furos_horizontais": [
                    {
                        "x": f.x,
                        "y": f.y,
                        "z": f.z,
                        "diametro": f.diametro,
                        "profundidade": f.profundidade,
                        "lado": f.lado
                    }
                    for f in peca.furos_horizontais
                ],
                "comentarios": peca.comentarios
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/generate-pdf")
async def generate_pdf(
    file: UploadFile = File(...),
    angulo_rotacao: int = 0,
    espelhar_peca: bool = False,
    bordas: str = "{}",  # JSON string com bordas
    alerta: str = None,
    revisao: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Gera PDF técnico a partir de arquivo MPR
    
    Args:
        file: Arquivo MPR
        angulo_rotacao: 0, 90, 180, 270
        espelhar_peca: True/False
        posicao_borda_comprimento: 'top', 'bottom', None
        posicao_borda_largura: 'left', 'right', None
        alerta: Texto de alerta (opcional)
        
    Returns:
        Arquivo PDF para download
    """
    try:
        # Parse do arquivo
        content = await file.read()
        content_str = content.decode('utf-8', errors='ignore')
        nome_peca = file.filename.replace('.mpr', '').replace('.MPR', '')
        peca = parse_furacao(content_str, nome_peca)
        
        # Parse das bordas JSON
        try:
            bordas_dict = json.loads(bordas) if bordas else {}
        except:
            bordas_dict = {}
        
        # Dados adicionais
        dados_adicionais = {
            'angulo_rotacao': angulo_rotacao,
            'espelhar_peca': espelhar_peca,
            'bordas': bordas_dict,  # ← Novo formato!
            'alerta': alerta,
            'revisao': revisao
        }
        
        # Gerar PDF em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name
        
        gerador = GeradorDesenhoTecnico()
        gerador.gerar_pdf(peca, pdf_path, dados_adicionais)
        
        # Retornar arquivo
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f"{nome_peca}_furacao.pdf",
            background=None  # Não deletar automaticamente
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)