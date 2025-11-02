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
    for linha in linhas:
        if '_BSX=' in linha:
            x = float(linha.split('=')[1])
        elif '_BSY=' in linha:
            y = float(linha.split('=')[1])
        elif '_BSZ=' in linha:
            z = float(linha.split('=')[1])
            dimensoes = Dimensoes(largura=x, comprimento=y, espessura=z)
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
                x_base_val = furo_data.get('XA', '0')
                x_base = x_base_val if x_base_val == 'x' else float(x_base_val)
                
                y_base_arquivo = float(furo_data.get('YA', 0))
                altura_peca = dimensoes.comprimento if dimensoes else 304
                y_base = altura_peca - y_base_arquivo
                
                z_base = float(furo_data.get('ZA', 0))
                diametro = float(furo_data.get('DU', 0))
                profundidade = float(furo_data.get('TI', 0))
                lado = furo_data.get('BM', 'XP')
                
                quantidade = int(furo_data.get('AN', 1))
                distancia = float(furo_data.get('AB', 0))
                angulo = float(furo_data.get('WI', 90))
                
                for n in range(quantidade):
                    if isinstance(x_base, str) and x_base == 'x':
                        x_atual = 'x'
                        y_atual = y_base - (n * distancia) if angulo == 90 else y_base
                    elif angulo == 90:
                        x_atual = x_base if isinstance(x_base, float) else float(x_base)
                        y_atual = y_base - (n * distancia)
                    else:
                        x_atual = x_base + (n * distancia) if isinstance(x_base, float) else x_base
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
        
        # Comentários
        elif '<101 \\Kommentar\\' in linha:
            j = i + 1
            while j < len(linhas) and 'KM=' in linhas[j]:
                km = extrair_valor(linhas[j], 'KM')
                if km and km.strip():
                    comentarios.append(km.strip())
                j += 1
            i = j - 1
        
        i += 1
    
    return Peca(
        nome=nome_peca,
        dimensoes=dimensoes,
        furos_verticais=furos_verticais,
        furos_horizontais=furos_horizontais,
        comentarios=comentarios
    )