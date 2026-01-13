"""
CoreWood API - Rotas para Parser STEP com pythonOCC
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response, StreamingResponse
from typing import Optional
import tempfile
import os
import re
import io
import zipfile

from ..parser.step_parser_occ import parse_step_occ
from ..generators.mpr_generator import GeradorMPR
from ..core.auth import get_current_active_user
from ..models.user import User

router = APIRouter(
    prefix="/api/step",
    tags=["STEP (pythonOCC)"]
)


@router.post("/parse")
async def parse_step_occ_endpoint(
    file: UploadFile = File(...),
    debug: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    Parse arquivo STEP usando pythonOCC (mais preciso)
    
    - Detecta furos verticais e horizontais
    - Filtra rebaixos (Ø > 15mm)
    - Ignora bordas/fitas automaticamente
    
    Args:
        file: Arquivo STEP (.step ou .stp)
        debug: Se True, retorna informações extras de debug
    
    Returns:
        JSON com peças e furos detectados
    """
    # Validar extensão
    filename = file.filename.lower()
    if not filename.endswith(('.step', '.stp')):
        raise HTTPException(
            status_code=400, 
            detail="Arquivo deve ser .step ou .stp"
        )
    
    try:
        # Salvar arquivo temporário (pythonOCC precisa de arquivo físico)
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.step',
            mode='wb'
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Parse com pythonOCC
            resultado = parse_step_occ(filepath=tmp_path, debug=debug)
            
            # Adicionar nome do arquivo original
            resultado['arquivo'] = file.filename
            
            return {
                "status": "success",
                "parser": "pythonOCC",
                **resultado
            }
            
        finally:
            # Limpar arquivo temporário
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar STEP: {str(e)}"
        )


@router.post("/to-mpr")
async def step_to_mpr_occ(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Converte STEP para MPR usando pythonOCC
    
    - Uma peça: retorna arquivo .mpr
    - Múltiplas peças: retorna .zip com todos os .mpr
    """
    filename = file.filename.lower()
    if not filename.endswith(('.step', '.stp')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .step ou .stp")
    
    try:
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.step', mode='wb') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Parse
            dados = parse_step_occ(filepath=tmp_path, debug=False)
            pecas = dados.get("pecas", [])
            
            if not pecas:
                raise HTTPException(status_code=400, detail="Nenhuma peça encontrada no STEP")
            
            gerador = GeradorMPR()
            
            # Uma peça: retorna MPR direto
            if len(pecas) == 1:
                peca = pecas[0]
                nome = peca.get("nome", "peca")
                nome_limpo = re.sub(r'[^\w\s-]', '', nome).strip().replace(' ', '_')
                
                mpr_content = gerador.gerar_mpr({
                    "largura": peca["largura"],
                    "comprimento": peca["comprimento"],
                    "espessura": peca["espessura"],
                    "furos": peca.get("furos", [])
                })
                
                return Response(
                    content=mpr_content.encode('cp1252', errors='replace'),
                    media_type='application/octet-stream',
                    headers={
                        'Content-Disposition': f'attachment; filename="{nome_limpo}.mpr"'
                    }
                )
            
            # Múltiplas peças: retorna ZIP
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for idx, peca in enumerate(pecas, start=1):
                    nome = peca.get("nome", f"peca_{idx}")
                    nome_limpo = re.sub(r'[^\w\s-]', '', nome).strip().replace(' ', '_')
                    
                    mpr_content = gerador.gerar_mpr({
                        "largura": peca["largura"],
                        "comprimento": peca["comprimento"],
                        "espessura": peca["espessura"],
                        "furos": peca.get("furos", [])
                    })
                    
                    zipf.writestr(f"{nome_limpo}.mpr", mpr_content.encode('cp1252', errors='replace'))
            
            zip_buffer.seek(0)
            
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.rsplit('.', 1)[0]}_mprs.zip"
                }
            )
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao converter STEP para MPR: {str(e)}")


@router.post("/to-json")
async def step_to_json_occ(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Converte STEP para JSON CoreWood usando pythonOCC
    """
    import json
    
    filename = file.filename.lower()
    if not filename.endswith(('.step', '.stp')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .step ou .stp")
    
    try:
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.step', mode='wb') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            dados = parse_step_occ(filepath=tmp_path, debug=False)
            dados['arquivo_origem'] = file.filename
            dados['parser'] = 'pythonOCC'
            
            json_content = json.dumps(dados, indent=2, ensure_ascii=False)
            
            nome_base = file.filename.rsplit('.', 1)[0]
            
            return Response(
                content=json_content.encode('utf-8'),
                media_type='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename="{nome_base}_corewood.json"'
                }
            )
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao converter STEP para JSON: {str(e)}")