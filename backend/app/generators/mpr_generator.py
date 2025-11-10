from datetime import datetime
from typing import List, Dict

class GeradorMPR:
    """Gera arquivos MPR no formato HOMAG"""
    
    def __init__(self):
        self.version = "4.0 Alpha"
        self.ww = "6.0.18"
    
    def gerar_mpr(self, peca_data: Dict) -> str:
        """
        Gera conteúdo do arquivo MPR
        
        Args:
            peca_data: {
                'nome': 'LATERAL_01',
                'largura': 780,
                'comprimento': 305,
                'espessura': 15,
                'furos': [
                    {
                        'tipo': 'vertical',
                        'x': 21,
                        'y': 41,
                        'diametro': 5,
                        'profundidade': 0  # 0 = passante
                    },
                    ...
                ]
            }
        
        Returns:
            Conteúdo do arquivo MPR como string
        """
        
        largura = float(peca_data['largura'])
        comprimento = float(peca_data['comprimento'])
        espessura = float(peca_data['espessura'])
        furos = peca_data.get('furos', [])
        
        # Apenas furos verticais por enquanto
        furos_verticais = [f for f in furos if f['tipo'] == 'vertical']
        
        mpr = []
        
        # ===== HEADER =====
        mpr.append('[H')
        mpr.append(f'VERSION="{self.version}"')
        mpr.append(f'WW="{self.ww}"')
        mpr.append('OP="1"')
        mpr.append('WRK2="0"')
        mpr.append('SCHN="0"')
        mpr.append('HSP="0"')
        mpr.append('O2="0"')
        mpr.append('O4="0"')
        mpr.append('O3="0"')
        mpr.append('O5="0"')
        mpr.append('SR="0"')
        mpr.append('FM="1"')
        mpr.append('ML="2000"')
        mpr.append('UF="STANDARD"')
        mpr.append('DN="STANDARD"')
        mpr.append('GP="0"')
        mpr.append('GY="0"')
        mpr.append('GXY="0"')
        mpr.append('NP="1"')
        mpr.append('NE="0"')
        mpr.append('NA="0"')
        mpr.append('BFS="1"')
        mpr.append('US="0"')
        mpr.append('CB="0"')
        mpr.append('UP="0"')
        mpr.append('DW="0"')
        mpr.append('MAT="HOMAG"')
        mpr.append('INCH="0"')
        mpr.append('VIEW="NOMIRROR"')
        mpr.append('ANZ="1"')
        mpr.append('BES="0"')
        mpr.append('ENT="0"')
        
        # Dimensões da peça
        mpr.append(f'_BSX={largura:.6f}')
        mpr.append(f'_BSY={comprimento:.6f}')
        mpr.append(f'_BSZ={espessura:.6f}')
        mpr.append('_FNX=0.000000')
        mpr.append('_FNY=0.000000')
        mpr.append('_RNX=0.000000')
        mpr.append('_RNY=0.000000')
        mpr.append('_RNZ=0.000000')
        mpr.append(f'_RX={largura:.6f}')
        mpr.append(f'_RY={comprimento:.6f}')
        
        # ===== PROGRAMA =====
        mpr.append('[001')
        mpr.append(f'x="{int(largura)}"')
        mpr.append('KM=""')
        mpr.append(f'y="{int(comprimento)}"')
        mpr.append('KM=""')
        mpr.append(f'z="{int(espessura)}"')
        mpr.append('KM=""')
        
        # ===== DEFINIÇÃO DA PEÇA =====
        mpr.append('<100 \\WerkStck\\')
        mpr.append('LA="x"')
        mpr.append('BR="y"')
        mpr.append('DI="z"')
        mpr.append('FNX="0"')
        mpr.append('FNY="0"')
        mpr.append('AX="0"')
        mpr.append('AY="0"')
        
        # ===== FUROS VERTICAIS =====
        for furo in furos_verticais:
            mpr.extend(self._gerar_furo_vertical(furo))
        
        return '\n'.join(mpr)
    
    def _gerar_furo_vertical(self, furo: Dict) -> List[str]:
        """Gera linhas para um furo vertical"""
        
        x = float(furo['x'])
        y = float(furo['y'])
        diametro = float(furo['diametro'])
        profundidade = float(furo.get('profundidade', 0))
        
        # Determinar tipo
        if profundidade == 0:
            bm = "LSL"  # Passante
            linhas_furo = [
                '<102 \\BohrVert\\',
                f'XA="{int(x)}"',
                f'YA="{int(y)}"',
                'BM="LSL"',
                f'DU="{diametro}"',
                'AN="2"',
                'MI="0"',
                'S_="1"',
                'AB="192"',
                'WI="90"',
            ]
        else:
            bm = "LSU"  # Sacado
            linhas_furo = [
                '<102 \\BohrVert\\',
                f'XA="{int(x)}"',
                f'YA="{int(y)}"',
                'BM="LSU"',
                f'TI="{profundidade}"',
                f'DU="{diametro}"',
                'AN="2"',
                'MI="0"',
                'S_="1"',
                'AB="192"',
                'WI="90"',
            ]
        
        # Parâmetros padrão
        linhas_furo.extend([
            'ZT="0"',
            'RM="0"',
            'VW="0"',
            'HP="0"',
            'SP="0"',
            'YVE="0"',
            'WW="60,61,62,88,90,91,92,150"',
            'ASG="2"',
            'KAT="Bohren vertikal"',
            'MNM="Furo vertical"',
            'ORI=""',
            'MX="0"',
            'MY="0"',
            'MZ="0"',
            'MXF="1"',
            'MYF="1"',
            'MZF="1"',
            'SYA="0"',
            'SYV="0"',
            'KO="00"',
        ])
        
        return linhas_furo


# Teste
if __name__ == "__main__":
    gerador = GeradorMPR()
    
    peca_teste = {
        'nome': 'TESTE_01',
        'largura': 300,
        'comprimento': 800,
        'espessura': 15,
        'furos': [
            {'tipo': 'vertical', 'x': 50, 'y': 100, 'diametro': 5, 'profundidade': 0},
            {'tipo': 'vertical', 'x': 250, 'y': 100, 'diametro': 8, 'profundidade': 12},
        ]
    }
    
    mpr_content = gerador.gerar_mpr(peca_teste)
    print(mpr_content)