"""
Parser para arquivos de furação HOMAG/TopSolid
Extrai informações de dimensões e furações
"""

import re
from typing import Optional
from ..models.peca import Peca, Dimensoes, FuroVertical, FuroHorizontal


def extrair_valor(linha: str, chave: str) -> Optional[str]:
    """Extrai valor de uma linha no formato CHAVE="valor" """
    padrao = f'{chave}="([^"]*)"'
    match = re.search(padrao, linha)
    return match.group(1) if match else None


def parse_furacao(conteudo: str, nome_peca: str = "Peça") -> Peca:
    """
    Parse do arquivo de furação
    
    Args:
        conteudo: Conteúdo do arquivo MPR
        nome_peca: Nome da peça
        
    Returns:
        Objeto Peca com todas as informações
    """
    linhas = conteudo.split('\n')
    
    # Extrair dimensões
    dimensoes = None
    largura = 0
    comprimento = 0
    espessura = 0

    for linha in linhas:
        if '_BSX=' in linha:
            comprimento = float(linha.split('=')[1])  # X = comprimento
        elif '_BSY=' in linha:
            largura = float(linha.split('=')[1])      # Y = largura
        elif '_BSZ=' in linha:
            espessura = float(linha.split('=')[1])    # Z = espessura
            dimensoes = Dimensoes(largura=largura, comprimento=comprimento, espessura=espessura)
            break
    
    # Extrair furos
    furos_verticais = []
    furos_horizontais = []
    comentarios = []
    
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        
        # Furo Vertical
        if '<102 \\BohrVert\\' in linha:
            furo_data = {}
            j = i
            while j < len(linhas) and not (linhas[j].startswith('<') and j != i):
                if '="' in linhas[j]:
                    partes = linhas[j].split('=')
                    if len(partes) >= 2:
                        chave = partes[0].strip()
                        valor = partes[1].strip().strip('"')
                        furo_data[chave] = valor
                j += 1
            
            if 'XA' in furo_data and 'YA' in furo_data:
                x_base = float(furo_data.get('XA', 0))
                y_base = float(furo_data.get('YA', 0))
                diametro = float(furo_data.get('DU', 0))
                profundidade = float(furo_data.get('TI', 0))
                lado = furo_data.get('BM', 'LS')
                
                quantidade = int(furo_data.get('AN', 1))
                distancia = float(furo_data.get('AB', 0))
                angulo = float(furo_data.get('WI', 0))
                
                for n in range(quantidade):
                    if angulo == 90:
                        x_atual = x_base
                        y_atual = y_base + (n * distancia)
                    else:
                        x_atual = x_base + (n * distancia)
                        y_atual = y_base
                    
                    furo = FuroVertical(
                        x=x_atual,
                        y=y_atual,
                        diametro=diametro,
                        profundidade=profundidade,
                        lado=lado
                    )
                    furos_verticais.append(furo)
                    
            i = j - 1
        
        # Furo Horizontal
        elif '<103 \\BohrHoriz\\' in linha:
            furo_data = {}
            j = i
            while j < len(linhas) and not (linhas[j].startswith('<') and j != i):
                if '="' in linhas[j]:
                    partes = linhas[j].split('=')
                    if len(partes) >= 2:
                        chave = partes[0].strip()
                        valor = partes[1].strip().strip('"')
                        furo_data[chave] = valor
                j += 1
            
            if 'XA' in furo_data and 'YA' in furo_data:
                # Tratar X (pode ser 'x' = comprimento)
                x_base_val = furo_data.get('XA', '0')
                if x_base_val == 'x':
                    x_base = 'x'
                else:
                    x_base = float(x_base_val)
                
                y_base = float(furo_data.get('YA', 0))  # ← SEM inversão
                
                z_base = float(furo_data.get('ZA', 0))
                diametro = float(furo_data.get('DU', 0))
                profundidade = float(furo_data.get('TI', 0))
                lado = furo_data.get('BM', 'XP')
                
                quantidade = int(furo_data.get('AN', 1))
                distancia = float(furo_data.get('AB', 0))
                angulo = float(furo_data.get('WI', 0))  # padrão 0, não 90
                
                for n in range(quantidade):
                    if isinstance(x_base, str) and x_base == 'x':
                        x_atual = 'x'
                        y_atual = y_base + (n * distancia) if angulo == 90 else y_base  # ← Somando
                    elif angulo == 90:
                        x_atual = x_base if isinstance(x_base, float) else float(x_base)
                        y_atual = y_base + (n * distancia)  # ← Somando
                    else:
                        x_atual = x_base + (n * distancia) if isinstance(x_base, (int, float)) else x_base
                        y_atual = y_base
                    
                    furo = FuroHorizontal(
                        x=x_atual,
                        y=y_atual,
                        z=z_base,
                        diametro=diametro,
                        profundidade=profundidade,
                        lado=lado
                    )
                    furos_horizontais.append(furo)
                    
            i = j - 1
    
    return Peca(
        nome=nome_peca,
        dimensoes=dimensoes,
        furos_verticais=furos_verticais,
        furos_horizontais=furos_horizontais,
        comentarios=comentarios
    )