from datetime import datetime
from typing import List, Dict

class GeradorMPR:
    """Gera arquivos MPR no formato HOMAG"""
    
    def __init__(self):
        self.version = "4.0 Alpha"
        self.ww = "6.0.18"

    def _agrupar_furos_sequenciais(self, furos: List[Dict]) -> List[Dict]:
        """Agrupa furos que estão em sequência"""
        if not furos:
            return []
        
        grupos = []
        furos_ordenados = sorted(furos, key=lambda f: (f['y'], f['x']))
        
        i = 0
        while i < len(furos_ordenados):
            grupo = {
                **furos_ordenados[i],
                'quantidade': 1,
                'distancia': 0,
                'direcao_replicacao': 'x'
            }
            
            # Verificar furos sequenciais
            j = i + 1
            while j < len(furos_ordenados):
                f_atual = furos_ordenados[j-1]
                f_prox = furos_ordenados[j]
                
                # Mesmo Y, X sequencial?
                if (f_prox['y'] == f_atual['y'] and 
                    f_prox['diametro'] == f_atual['diametro'] and
                    f_prox['profundidade'] == f_atual['profundidade']):
                    
                    dist = f_prox['x'] - f_atual['x']
                    if grupo['quantidade'] == 1:
                        grupo['distancia'] = dist
                        grupo['quantidade'] = 2
                    elif abs(dist - grupo['distancia']) < 0.1:
                        grupo['quantidade'] += 1
                    else:
                        break
                    j += 1
                else:
                    break
            
            grupos.append(grupo)
            i = j if j > i + 1 else i + 1
        
        return grupos    
    
    def gerar_mpr(self, peca_data: Dict) -> str:
        """Gera conteúdo do arquivo MPR"""
        
        largura = float(peca_data['largura'])
        comprimento = float(peca_data['comprimento'])
        espessura = float(peca_data['espessura'])
        furos = peca_data.get('furos', [])
        
        # Separar por tipo
        furos_verticais = [f for f in furos if f.get('tipo') == 'vertical']
        furos_horizontais = [f for f in furos if f.get('tipo') == 'horizontal']
                
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
        mpr.append(f'_BSX={comprimento:.6f}')
        mpr.append(f'_BSY={largura:.6f}')
        mpr.append(f'_BSZ={espessura:.6f}')
        mpr.append('_FNX=0.000000')
        mpr.append('_FNY=0.000000')
        mpr.append('_RNX=0.000000')
        mpr.append('_RNY=0.000000')
        mpr.append('_RNZ=0.000000')
        mpr.append(f'_RX={comprimento:.6f}')
        mpr.append(f'_RY={largura:.6f}')
        
        # ===== PROGRAMA =====
        mpr.append('')  # Linha em branco
        mpr.append('[001')
        mpr.append(f'x="{int(comprimento)}"')
        mpr.append('KM=""')
        mpr.append(f'y="{int(largura)}"')
        mpr.append('KM=""')
        mpr.append(f'z="{int(espessura)}"')
        mpr.append('KM=""')
        
        # ===== DEFINIÇÃO DA PEÇA =====
        mpr.append('')  # Linha em branco
        mpr.append('<100 \\WerkStck\\')
        mpr.append('LA="x"')
        mpr.append('BR="y"')
        mpr.append('DI="z"')
        mpr.append('FNX="0"')
        mpr.append('FNY="0"')
        mpr.append('AX="0"')
        mpr.append('AY="0"')

        # Agrupar furos sequenciais
        furos_agrupados = self._agrupar_furos_sequenciais(furos_verticais)
        
        # ===== FUROS VERTICAIS =====
        for furo in furos_agrupados:
            mpr.append('')  # Linha em branco
            mpr.extend(self._gerar_furo_vertical(furo, largura))
        
        # ===== FUROS HORIZONTAIS =====
        for furo in furos_horizontais:
            mpr.append('')  # Linha em branco
            mpr.extend(self._gerar_furo_horizontal(furo, largura))
        
        # ===== COMENTÁRIOS (depois dos furos) =====
        comentarios = peca_data.get('comentarios', [])
        if comentarios:
            mpr.append('')  # Linha em branco
            mpr.append('<101 \\Kommentar\\')
            for comentario in comentarios:
                mpr.append(f'KM="{comentario}"')
            mpr.append('KAT="Kommentar"')
            mpr.append('MNM="Comentário"')
            mpr.append('ORI=""')
        
        # ===== COMPONENTE MACRO =====
        mpr.append('')  # Linha em branco
        mpr.append('<139 \\Komponente\\')
        mpr.append('IN="ZP500.mpr"')
        mpr.append('XA="0.0"')
        mpr.append('YA="0.0"')
        mpr.append('ZA="0.0"')
        mpr.append('EM="0"')
        mpr.append('VA="X1 125"')
        mpr.append('VA="X2 _BSX-125"')
        mpr.append('VA="Y1 70"')
        mpr.append('VA="F1 0"')
        mpr.append('VA="F2 0"')
        mpr.append('VA="F21 0"')
        mpr.append('VA="F3 100"')
        mpr.append('VA="F4 100"')
        mpr.append('KAT="Komponentenmakro"')
        mpr.append('MNM="Macro Componentes"')
        mpr.append('ORI=""')
        mpr.append('KO="00"')
        
        # Adicionar terminador
        mpr.append('!')

        return '\r\n'.join(mpr)
    
    def gerar_mpr_from_step(self, dados_step: Dict) -> str:
        """
        Gera MPR a partir dos dados do parse_step_multipart.
        
        Espera:
        {
            "pecas": [ { peca_data } ],
            "acessorios": [...],
            "resumo": {...}
        }
        """
        pecas = dados_step.get("pecas", [])

        if not pecas:
            raise ValueError("Nenhuma peça encontrada para gerar MPR")

        mpr_total = []

        for peca in pecas:
            # Garantir estrutura mínima
            peca_data = {
                "nome": peca.get("nome", "SEM_NOME"),
                "largura": peca["largura"],
                "comprimento": peca["comprimento"],
                "espessura": peca["espessura"],
                "furos": peca.get("furos", [])
            }

            mpr_total.append(self.gerar_mpr(peca_data))

        # Se houver múltiplas peças, concatena
        return "\r\n".join(mpr_total)

    
    def _determinar_tipo_furo(self, furo: Dict, peca: Dict) -> str:
        """Determina se o furo é vertical ou horizontal."""
        z = furo.get('z', 0)
        espessura = peca['thickness']
        tolerancia = 2.0
        
        # Se Z está no topo ou fundo, é vertical
        if z <= tolerancia or z >= espessura - tolerancia:
            return 'vertical'
        
        # Verifica se está na borda (horizontal)
        x = furo['x']
        y = furo['y']
        largura = peca['width']
        altura = peca['height']
        
        if x <= tolerancia or x >= largura - tolerancia:
            return 'horizontal'
        if y <= tolerancia or y >= altura - tolerancia:
            return 'horizontal'
        
        return 'vertical'
    
    def _determinar_lado(self, furo: Dict, peca: Dict) -> str:
        """Determina o lado do furo horizontal (XP, XM, YP, YM)."""
        x = furo['x']
        y = furo['y']
        largura = peca['width']
        altura = peca['height']
        tolerancia = 1.0
        
        if x <= tolerancia:
            return "XP"
        elif x >= largura - tolerancia:
            return "XM"
        elif y <= tolerancia:
            return "YP"
        elif y >= altura - tolerancia:
            return "YM"
        
        return "XP"
    
    def _gerar_furo_vertical(self, furo: Dict, largura: float) -> List[str]:
        x = float(furo['x'])
        y = largura - float(furo['y'])  # Inverter Y para WoodWop
        diametro = float(furo['diametro'])
        profundidade = float(furo.get('profundidade', 0))
        lado = furo.get('lado', 'LS')  # ← pega o lado do furo
        
        # Suporte a replicação
        quantidade = int(furo.get('quantidade', 1))
        distancia = float(furo.get('distancia', 0))
        direcao_replicacao = furo.get('direcao_replicacao', 'x')  # 'x' ou 'y'
        
        wi = "0" if direcao_replicacao == 'x' else "90"
        
        # Formatar valores - manter decimal se necessário
        def formatar(valor):
            if valor == int(valor):
                return str(int(valor))
            else:
                return f"{valor:.1f}"
        
        linhas = [
            '<102 \\BohrVert\\',
            f'XA="{formatar(x)}"',
            f'YA="{formatar(y)}"',
            f'BM="{lado}"',  # ← usa o lado passado
            f'DU="{formatar(diametro)}"',
        ]
        
        # Adiciona profundidade se não for passante
        if profundidade > 0:
            linhas.append(f'TI="{formatar(profundidade)}"')
        
        linhas.extend([
            f'AN="{quantidade}"',
            'MI="0"',
            'S_="1"',
            f'AB="{formatar(distancia)}"',
            f'WI="{wi}"',
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
        
        return linhas
    
    def _gerar_furo_horizontal(self, furo: Dict, largura: float) -> List[str]:
        """Gera linhas para um furo horizontal (operação 103)"""
        x = furo.get('x', 0)
        y = largura - float(furo['y'])  # Inverter Y para WoodWop
        z = float(furo.get('z', 7.5))
        diametro = float(furo['diametro'])
        profundidade = float(furo.get('profundidade', 22))
        lado = furo.get('lado', 'XP')
        
        # Suporte a replicação
        quantidade = int(furo.get('quantidade', 1))
        distancia = float(furo.get('distancia', 0))
        
        # Formatar valores - manter decimal se necessário
        def formatar(valor):
            if valor == int(valor):
                return str(int(valor))
            else:
                return f"{valor:.1f}"
        
        # XA pode ser número ou "x" (lado oposto)
        if x == 'x':
            xa_valor = 'x'
        elif x == 0:
            xa_valor = '0'
        else:
            xa_valor = formatar(float(x))
        
        linhas_furo = [
            '<103 \\BohrHoriz\\',
            'MI="0"',
            f'XA="{xa_valor}"',
            f'YA="{formatar(y)}"',
            f'ZA="{formatar(z)}"',
            f'DU="{formatar(diametro)}"',
            f'TI="{formatar(profundidade)}"',
            'ANA="20"',
            f'BM="{lado}"',
            f'AN="{quantidade}"',
            f'AB="{formatar(distancia)}"',
            'BM2="STD"',
            'ZT="0"',
            'RM="0"',
            'VW="0"',
            'HP="0"',
            'SP="0"',
            'YVE="0"',
            'WW="50,51,52,53,93,94,95,56,153,151"',
            'ASG="2"',
            'KAT="Horizontalbohren"',
            'MNM="Furo horizontal"',
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
        ]
        
        return linhas_furo
    
    def gerar_multiplos_mprs(self, dados_parser: dict):
        arquivos = []

        for idx, peca in enumerate(dados_parser["pecas"], start=1):
            nome = peca.get("nome", f"peca_{idx}")

            conteudo = self.gerar_mpr({
                "largura": peca["largura"],
                "comprimento": peca["comprimento"],
                "espessura": peca["espessura"],
                "furos": peca.get("furos", [])
            })

            arquivos.append({
                "filename": f"{nome}.mpr",
                "content": conteudo
            })

        return arquivos


if __name__ == "__main__":
    gerador = GeradorMPR()

    print("\n=== TESTE PEÇA ÚNICA ===\n")
    peca_teste = {
        'nome': 'TESTE_01',
        'largura': 300,
        'comprimento': 800,
        'espessura': 15,
        'furos': []
    }

    mpr_content = gerador.gerar_mpr(peca_teste)
    print(mpr_content[:300])  # só um trecho

    print("\n=== TESTE MÚLTIPLAS PEÇAS ===\n")

    dados_parser = {
        "pecas": [
            {
                "nome": "BASE",
                "largura": 499.99,
                "comprimento": 1199.98,
                "espessura": 30.0,
                "furos": []
            },
            {
                "nome": "LATERAL_DIREITA",
                "largura": 497.99,
                "comprimento": 885.0,
                "espessura": 30.0,
                "furos": []
            }
        ]
    }

    mprs = gerador.gerar_multiplos_mprs(dados_parser)

    print(f"Total de arquivos gerados: {len(mprs)}\n")

    for mpr in mprs:
        print("Arquivo:", mpr["filename"])
        print("Conteúdo (primeiras linhas):")
        print("\n".join(mpr["content"].splitlines()[:5]))
        print("-" * 40)

if __name__ == "__main__":
    gerador = GeradorMPR()

    print("\n=== TESTE NOVO FORMATO (furos dentro da peça) ===\n")

    peca_com_furo = {
        "nome": "PECA_FURO",
        "largura": 500,
        "comprimento": 1200,
        "espessura": 18,
        "furos": [
            {
                "tipo": "vertical",
                "x": 100,
                "y": 50,
                "diametro": 8,
                "profundidade": 12
            },
            {
                "tipo": "vertical",
                "x": 300,
                "y": 50,
                "diametro": 8,
                "profundidade": 12
            }
        ]
    }

    mpr = gerador.gerar_mpr(peca_com_furo)

    print(mpr)
