from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from ..models.peca import Peca, FuroVertical, FuroHorizontal



class GeradorDesenhoTecnico:
    """Gera desenhos técnicos 2D em PDF"""
    
    def __init__(self):
        self.margem = 20 * mm
        self.escala = 1.0  # Será calculada dinamicamente

    def calcular_batente(self, peca: Peca) -> float:
        """
        Calcula o Y do batente baseado no primeiro furo (vertical ou horizontal).
        Leitura: de cima para baixo (menor Y primeiro), da esquerda para direita (menor X primeiro)
        
        Args:
            peca: objeto Peca com furos verticais e horizontais
            
        Returns:
            Y do batente (primeiro furo encontrado)
        """
        todos_furos = []
        
        # Adicionar furos verticais
        for furo in peca.furos_verticais:
            todos_furos.append({'x': float(furo.x), 'y': float(furo.y)})
        
        # Adicionar furos horizontais
        for furo in peca.furos_horizontais:
            x = 0 if furo.x == 'x' else float(furo.x)
            todos_furos.append({'x': x, 'y': float(furo.y)})
        
        if not todos_furos:
            return 0
        
        # Ordenar: menor Y primeiro (topo), depois menor X (esquerda)
        furos_ordenados = sorted(todos_furos, key=lambda f: (f['y'], f['x']))
        return furos_ordenados[0]['y']

    def calcular_mandril(self, y_furo: float, y_batente: float) -> int:
        """
        Calcula o número do mandril baseado na posição Y do furo.
        Mandris espaçados de 32mm.
        
        Args:
            y_furo: posição Y do furo
            y_batente: posição Y do batente (primeiro furo)
            
        Returns:
            Número do mandril (1-20)
        """
        diferenca = abs(float(y_furo) - float(y_batente))
        mandril = int(diferenca / 32) + 1
        return max(1, min(20, mandril))  # Limita entre 1 e 20   

    def detectar_conflitos_100mm(self, furos_verticais: list) -> dict:
        """
        Detecta furos com menos de 100mm de distância no eixo X.
        
        Args:
            furos_verticais: lista de FuroVertical
            
        Returns:
            dict com análise dos conflitos
        """
        if not furos_verticais:
            return {'tem_conflito': False, 'grupos': []}
        
        # Ordenar por X
        furos_ordenados = sorted(furos_verticais, key=lambda f: float(f.x))
        
        # Encontrar grupos de furos próximos (<100mm)
        grupos_conflito = []
        grupo_atual = [furos_ordenados[0]]
        
        for i in range(1, len(furos_ordenados)):
            furo_atual = furos_ordenados[i]
            furo_anterior = furos_ordenados[i - 1]
            
            distancia_x = abs(float(furo_atual.x) - float(furo_anterior.x))
            
            if distancia_x < 100:
                # Está próximo, adiciona ao grupo atual
                grupo_atual.append(furo_atual)
            else:
                # Distante, salva grupo anterior se tem conflito
                if len(grupo_atual) > 1:
                    grupos_conflito.append(grupo_atual)
                grupo_atual = [furo_atual]
        
        # Verificar último grupo
        if len(grupo_atual) > 1:
            grupos_conflito.append(grupo_atual)
        
        return {
            'tem_conflito': len(grupos_conflito) > 0,
            'grupos': grupos_conflito,
            'total_conflitos': len(grupos_conflito)
        }

    def agrupar_por_linha_furacao(self, furos_verticais: list) -> dict:
        """
        Agrupa furos por linha de furação (mesmo X).
        
        Args:
            furos_verticais: lista de FuroVertical
            
        Returns:
            dict: {x_posicao: [lista de furos]}
        """
        linhas = {}
        for furo in furos_verticais:
            x_key = round(float(furo.x), 1)
            if x_key not in linhas:
                linhas[x_key] = []
            linhas[x_key].append(furo)
        return linhas


    def verificar_conflito_100mm(self, linhas_x: list) -> bool:
        """
        Verifica se existe conflito de 100mm entre as linhas de furação.
        
        Args:
            linhas_x: lista de posições X das linhas
            
        Returns:
            True se tem conflito, False se não tem
        """
        linhas_ordenadas = sorted(linhas_x)
        
        for i in range(len(linhas_ordenadas) - 1):
            distancia = linhas_ordenadas[i + 1] - linhas_ordenadas[i]
            if distancia < 100:
                return True
        
        return False


    def distribuir_furos_superior_inferior(self, furos_verticais: list) -> dict:
        """
        Distribui furos entre INFERIOR e SUPERIOR respeitando regra dos 100mm.
        
        Lógica:
        1. Agrupar furos por características (diâmetro + profundidade)
        2. Para cada grupo, verificar se cabe sozinho (sem conflito interno)
        3. Distribuir grupos entre INFERIOR e SUPERIOR
        4. Se não couber, criar 2ª PASSADA
        
        Args:
            furos_verticais: lista de FuroVertical
            
        Returns:
            dict com distribuição dos furos
        """
        if not furos_verticais:
            return {
                'inferior': [],
                'superior': [],
                'segunda_furacao': [],
                'precisa_segunda_furacao': False
            }
        
        # Verificar se tem conflito geral
        linhas_todas = self.agrupar_por_linha_furacao(furos_verticais)
        if not self.verificar_conflito_100mm(list(linhas_todas.keys())):
            # Sem conflito - tudo vai para inferior
            return {
                'inferior': furos_verticais,
                'superior': [],
                'segunda_furacao': [],
                'precisa_segunda_furacao': False
            }
        
        # TEM CONFLITO - Agrupar por características (diâmetro + profundidade)
        grupos = {}
        for furo in furos_verticais:
            chave = (round(float(furo.diametro), 1), round(float(furo.profundidade), 1))
            if chave not in grupos:
                grupos[chave] = []
            grupos[chave].append(furo)
        
        # Para cada grupo, pegar as linhas X
        grupos_com_linhas = []
        for chave, furos_grupo in grupos.items():
            linhas_grupo = self.agrupar_por_linha_furacao(furos_grupo)
            linhas_x = sorted(linhas_grupo.keys())
            tem_conflito_interno = self.verificar_conflito_100mm(linhas_x)
            
            diametro = chave[0]  # chave = (diâmetro, profundidade)
            
            grupos_com_linhas.append({
                'chave': chave,
                'furos': furos_grupo,
                'linhas_x': linhas_x,
                'tem_conflito_interno': tem_conflito_interno,
                'diametro': diametro
            })

        # Ordenar grupos: primeiro os sem conflito interno, depois por DIÂMETRO (menor primeiro)
        grupos_com_linhas.sort(key=lambda g: (g['tem_conflito_interno'], g['diametro']))
        
        # Distribuir grupos entre INFERIOR e SUPERIOR
        linhas_inferior = []
        linhas_superior = []
        linhas_segunda = []
        
        furos_inferior = []
        furos_superior = []
        furos_segunda = []
        
        for grupo in grupos_com_linhas:
            linhas_x = grupo['linhas_x']
            furos_grupo = grupo['furos']
            
            # Tentar colocar o grupo inteiro em INFERIOR
            pode_inferior = self._grupo_cabe_no_lado(linhas_x, linhas_inferior, max_linhas=6)
            
            if pode_inferior:
                linhas_inferior.extend(linhas_x)
                furos_inferior.extend(furos_grupo)
                continue
            
            # Tentar colocar o grupo inteiro em SUPERIOR
            pode_superior = self._grupo_cabe_no_lado(linhas_x, linhas_superior, max_linhas=4)
            
            if pode_superior:
                linhas_superior.extend(linhas_x)
                furos_superior.extend(furos_grupo)
                continue
            
            # Não coube inteiro - vai para 2ª PASSADA
            linhas_segunda.extend(linhas_x)
            furos_segunda.extend(furos_grupo)
        
        return {
            'inferior': furos_inferior,
            'superior': furos_superior,
            'segunda_furacao': furos_segunda,
            'precisa_segunda_furacao': len(furos_segunda) > 0
        }


    def _grupo_cabe_no_lado(self, linhas_novas: list, linhas_existentes: list, max_linhas: int) -> bool:
        """
        Verifica se um grupo de linhas cabe em um lado (inferior/superior).
        
        Args:
            linhas_novas: linhas X do grupo a adicionar
            linhas_existentes: linhas X já no lado
            max_linhas: máximo de linhas permitidas (6 inferior, 4 superior)
            
        Returns:
            True se cabe, False se não cabe
        """
        # Verificar limite de linhas
        if len(linhas_existentes) + len(linhas_novas) > max_linhas:
            return False
        
        # Verificar conflito de 100mm com linhas existentes
        for x_nova in linhas_novas:
            for x_existente in linhas_existentes:
                if abs(x_nova - x_existente) < 100:
                    return False
        
        return True

    def formatar_cota(self, valor):
        """
        Formata valor da cota:
        - Se inteiro: sem casas decimais
        - Se decimal: com 1 casa decimal
        """
        if valor == int(valor):
            return f"{int(valor)}"
        else:
            return f"{valor:.1f}"
        
    def calcular_escala(self, largura_peca: float, comprimento_peca: float, 
                   largura_disponivel: float, altura_disponivel: float,
                   margem_seguranca: float = 0.85) -> float:
        """
        Calcula escala inteligente para caber a peça na área disponível
        
        Args:
            largura_peca, comprimento_peca: dimensões em mm
            largura_disponivel, altura_disponivel: espaço disponível em points
            margem_seguranca: percentual do espaço a usar (0.85 = 85%)
            
        Returns:
            Fator de escala otimizado
        """
        largura_peca_pts = largura_peca * mm
        comprimento_peca_pts = comprimento_peca * mm
        
        # Calcular escalas necessárias
        escala_x = largura_disponivel / largura_peca_pts
        escala_y = altura_disponivel / comprimento_peca_pts
        
        # Usar a menor escala e aplicar margem de segurança
        escala = min(escala_x, escala_y) * margem_seguranca
        
        # Limitar escala mínima e máxima para evitar extremos
        escala_minima = 0.1   # Não deixa ficar muito pequeno
        escala_maxima = 3.0   # Não deixa ficar gigante
        
        escala = max(escala_minima, min(escala, escala_maxima))
        
        
        return escala
    
    def espelhar_verticalmente(self, peca: Peca) -> Peca:
        """
        Espelha a peça verticalmente (inverte de cima para baixo)
        Borda inferior vai para cima
        """
        from copy import deepcopy
        
        peca_espelhada = deepcopy(peca)
        
        comprimento = float(peca.dimensoes.comprimento)
        espessura = float(peca.dimensoes.espessura)
        
        # Criar dicionário: Y_original → lista de furos
        furos_por_y_original = {}
        for furo in peca.furos_horizontais:  # ← Usar ORIGINAL, não espelhada
            y_orig = float(furo.y)
            if y_orig not in furos_por_y_original:
                furos_por_y_original[y_orig] = []
            furos_por_y_original[y_orig].append(furo)
        
        # Para cada Y original, inverter e manter as propriedades
        for y_original, furos_grupo in furos_por_y_original.items():
            y_invertido = comprimento - y_original
            
            # Achar furos na lista espelhada com esse Y invertido
            for furo_espelhado in peca_espelhada.furos_horizontais:
                if abs(float(furo_espelhado.y) - y_invertido) < 0.01:  # Tolerância float
                    # Encontrar o furo correspondente no grupo original
                    for furo_orig in furos_grupo:
                        if (abs(float(furo_orig.x if isinstance(furo_orig.x, float) else 0) - 
                                float(furo_espelhado.x if isinstance(furo_espelhado.x, float) else 0)) < 0.01 and
                            furo_orig.lado == furo_espelhado.lado):
                            # Copiar profundidade do original
                            furo_espelhado.profundidade = furo_orig.profundidade
                            break
        
        return peca_espelhada   
    
    def aplicar_rotacao(self, peca: Peca, angulo: int) -> Peca:
        """
        Aplica rotação na peça (0, 90, 180, 270 graus)
        Recalcula coordenadas dos furos e dimensões
        Origem final: canto superior esquerdo
        
        Args:
            peca: Peça original
            angulo: Ângulo de rotação (0, 90, 180, 270)
            
        Returns:
            Peça rotacionada com nova origem
        """
        from copy import deepcopy
        
        if angulo == 0:
            return peca  # Sem rotação
        
        peca_rotacionada = deepcopy(peca)
        
        largura = float(peca.dimensoes.largura)
        comprimento = float(peca.dimensoes.comprimento)
        
        if angulo == 90:
            # 90° horário
            peca_rotacionada.dimensoes.largura = comprimento
            peca_rotacionada.dimensoes.comprimento = largura
            
            # Rotacionar furos verticais
            for furo in peca_rotacionada.furos_verticais:
                try:
                    x_original = float(furo.x)
                    y_original = float(furo.y)
                    furo.x = comprimento - y_original
                    furo.y = x_original
                except:
                    continue
            
            # Rotacionar furos horizontais
            for furo in peca_rotacionada.furos_horizontais:
                try:
                    if isinstance(furo.x, str):
                        continue
                    x_original = float(furo.x)
                    y_original = float(furo.y)
                    furo.x = comprimento - y_original
                    furo.y = x_original
                except:
                    continue
                    
        elif angulo == 180:
            # 180°
            # Dimensões não mudam
            
            # Rotacionar furos verticais
            for furo in peca_rotacionada.furos_verticais:
                try:
                    x_original = float(furo.x)
                    y_original = float(furo.y)
                    furo.x = largura - x_original
                    furo.y = comprimento - y_original
                except:
                    continue
            
            # Rotacionar furos horizontais
            for furo in peca_rotacionada.furos_horizontais:
                try:
                    if isinstance(furo.x, str):
                        continue
                    x_original = float(furo.x)
                    y_original = float(furo.y)
                    furo.x = largura - x_original
                    furo.y = comprimento - y_original
                except:
                    continue
                    
        elif angulo == 270:
            # 270° horário (90° anti-horário)
            peca_rotacionada.dimensoes.largura = comprimento
            peca_rotacionada.dimensoes.comprimento = largura
            
            # Rotacionar furos verticais
            for furo in peca_rotacionada.furos_verticais:
                try:
                    x_original = float(furo.x)
                    y_original = float(furo.y)
                    furo.x = y_original
                    furo.y = largura - x_original
                except:
                    continue
            
            # Rotacionar furos horizontais
            for furo in peca_rotacionada.furos_horizontais:
                try:
                    if isinstance(furo.x, str):
                        continue
                    x_original = float(furo.x)
                    y_original = float(furo.y)
                    furo.x = y_original
                    furo.y = largura - x_original
                except:
                    continue
        
        return peca_rotacionada
    
    def desenhar_retangulo_peca(self, c: canvas.Canvas, x_origem: float, y_origem: float,
                                largura: float, altura: float):
        """Desenha o contorno da peça"""
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x_origem, y_origem, largura, altura, stroke=1, fill=0)
    
    def desenhar_cota_furo(self, c: canvas.Canvas, x_origem_peca: float, y_origem_peca: float,
                      x_furo: float, y_furo: float, distancia_x: float, distancia_y: float,
                      largura_peca: float, altura_peca: float, escala: float, 
                      mostrar_x: bool = True, mostrar_y: bool = True,
                      offset_externo_x: float = 25, offset_externo_y: float = 25):
        """
        Desenha cotas de posição do furo em relação às bordas
        Cotas saem DO FURO para FORA da peça
        
        Args:
            x_origem_peca, y_origem_peca: origem do desenho da peça
            x_furo, y_furo: posição do furo no desenho (já em escala)
            distancia_x, distancia_y: distâncias reais em mm
            largura_peca, altura_peca: dimensões da peça desenhada
            escala: escala do desenho
            mostrar_x, mostrar_y: quais cotas mostrar
        """
        c.setStrokeColor(colors.HexColor("#A5A6A68A"))
        c.setLineWidth(0.3)
        
        # COTA HORIZONTAL (X) - sai do furo para CIMA
        if mostrar_x and distancia_x > 0:
            # Borda superior da peça
            y_borda_superior = y_origem_peca + altura_peca
            
            # Linha do furo até fora da peça
            c.line(x_furo, y_furo, x_furo, y_borda_superior + offset_externo_x)
            c.setDash()  # Sólida
            
            # Texto VERTICAL acima
            c.setFont("Helvetica", 11)
            c.setFillColor(colors.HexColor("#000000"))
            c.saveState()
            x_texto = x_furo - 3
            y_texto = y_borda_superior + offset_externo_x + 10
            c.translate(x_texto, y_texto)
            c.rotate(90)
            c.drawCentredString(0, 0, self.formatar_cota(distancia_x))
            c.restoreState()

        # COTA VERTICAL (Y) - sai do furo para a ESQUERDA
        if mostrar_y and distancia_y > 0:
            # Borda esquerda da peça
            x_borda_esquerda = x_origem_peca
            
            # Linha do furo até fora da peça
            c.line(x_furo, y_furo, x_borda_esquerda - offset_externo_y, y_furo)
            c.setDash()  # Sólida
            
            # Texto HORIZONTAL à esquerda
            c.setFont("Helvetica", 11)
            c.setFillColor(colors.HexColor("#000000"))
            y_texto = y_furo
            x_texto = x_borda_esquerda - offset_externo_y - 10
            c.drawRightString(x_texto, y_texto - 3, self.formatar_cota(distancia_y))

        c.setFillColor(colors.black)  # Restaura cor
    
    def desenhar_furo_vertical(self, c: canvas.Canvas, x_origem: float, y_origem: float,
                       furo: FuroVertical, escala: float, altura_peca: float,
                       mandril: int = None):
        """
        Desenha marcação de furo vertical (vista de topo)
        
        Args:
            x_origem, y_origem: origem do desenho da peça
            furo: dados do furo
            escala: escala do desenho
        """
        # Posição do furo no desenho
        x_furo = x_origem + (furo.x * mm * escala)
        y_furo = y_origem + altura_peca - (furo.y * mm * escala)
        raio = (furo.diametro / 2) * mm * escala
        
        # Desenhar círculo do furo
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.circle(x_furo, y_furo, raio, stroke=1, fill=0)
        
        # # Desenhar linhas cruzadas no centro
        # c.setLineWidth(0.2)
        # c.line(x_furo - raio * 1.5, y_furo, x_furo + raio * 1.5, y_furo)
        # c.line(x_furo, y_furo - raio * 1.5, x_furo, y_furo + raio * 1.5)
        
        # Adicionar texto com especificações
        c.setFont("Helvetica", 10)
        if furo.profundidade == 0:
            texto = f"Ø{self.formatar_cota(furo.diametro)}"
        else:
            texto = f"Ø{self.formatar_cota(furo.diametro)}X{self.formatar_cota(furo.profundidade)}"

        # Adicionar mandril se disponível
        if mandril:
            texto = f"{texto},M{mandril}"
        
        # Posicionar texto ao lado do furo
        offset_x = raio * 8.5
        offset_y = raio * 0.2
        x_texto_inicio = x_furo + offset_x
        y_texto = y_furo + offset_y

        # Linha discreta do furo até o texto
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.line(x_furo + raio, y_furo, x_texto_inicio - 2, y_furo)

        # Setinha pequena no final
        tamanho_seta = 2
        c.line(x_texto_inicio - 2, y_furo, x_texto_inicio - 2 - tamanho_seta, y_furo + tamanho_seta)
        c.line(x_texto_inicio - 2, y_furo, x_texto_inicio - 2 - tamanho_seta, y_furo - tamanho_seta)

        # Restaurar cor preta para o texto
        c.setStrokeColor(colors.black)

        # Desenhar texto
        c.setFillColor(colors.black)
        c.drawString(x_texto_inicio, y_texto, texto)
        
        # Retornar posição para desenhar cotas depois
        return (x_furo, y_furo)
    
    def desenhar_cota_principal(self, c: canvas.Canvas, x_origem: float, y_origem: float,
                           largura: float, altura: float, largura_real: float, 
                           altura_real: float, offset: float):
        """
        Desenha cotas principais da peça (MESMO ESTILO das cotas dos furos)
        """
        
        c.setStrokeColor(colors.HexColor('#A5A6A68A'))
        c.setLineWidth(0.3)
        
        offset_externo = 15  # Distância para fora da peça (um pouco mais que os furos)
        
        # COTA 1: VERTICAL (297) - linha sai para CIMA do canto direito
        x_borda_direita = x_origem + largura
        y_topo = y_origem + altura

        # Linha tracejada para cima
        c.line(x_borda_direita, y_topo, x_borda_direita, y_topo + offset_externo)
        c.setDash()

        # Texto VERTICAL (rotacionado) - COTA DE 297
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#000000"))
        c.saveState()
        c.translate(x_borda_direita, y_topo + offset_externo + 8)
        c.rotate(90)
        c.drawCentredString(0, 0, f"{largura_real:.0f}")  # ← 297
        c.restoreState()

        # COTA 2: HORIZONTAL (269) - linha sai para BAIXO da esquerda
        x_esquerda = x_origem
        y_base = y_origem  # ← BASE (ponto zero)
        
        # Linha tracejada para baixo
        c.line(x_esquerda, y_base, x_esquerda - offset_externo, y_base)
        c.setDash()
        
        # Texto HORIZONTAL à esquerda - COTA DE 269
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#000000"))
        c.drawRightString(x_esquerda - offset_externo - 8, y_base - 3, f"{altura_real:.0f}")
        
        c.setFillColor(colors.black)  # Restaura cor
    
    def desenhar_vista_lateral(self, c: canvas.Canvas, x_origem: float, y_origem: float,
                        peca: Peca, lado: str, largura_disponivel: float, 
                        altura_disponivel: float, espelhado: bool = False,
                        batente: float = None):
        """
        Desenha vista lateral da peça mostrando furos horizontais
        AGORA COM ESCALA DINÂMICA E MANDRIL!
        
        Args:
            x_origem, y_origem: posição base da vista
            peca: dados da peça
            lado: 'esquerda' ou 'direita'
            largura_disponivel: espaço horizontal disponível
            altura_disponivel: espaço vertical disponível
            espelhado: se a peça foi espelhada
            batente: valor Y do batente para cálculo do mandril
        """

        espessura_peca = float(peca.dimensoes.espessura)
        altura_peca = float(peca.dimensoes.comprimento)
        
        # Calcular batente se não foi passado
        if batente is None:
            batente = self.calcular_batente(peca)
        
        # ===== ESCALA DINÂMICA =====
        escala = self.calcular_escala(
            largura_peca=espessura_peca,
            comprimento_peca=altura_peca,
            largura_disponivel=largura_disponivel,
            altura_disponivel=altura_disponivel,
            margem_seguranca=0.50
        )

        print(f"🔍 DEBUG VISTA LATERAL ({lado}):")
        print(f"   espessura_peca: {espessura_peca}")
        print(f"   altura_peca: {altura_peca}")
        print(f"   largura_disponivel: {largura_disponivel}")
        print(f"   altura_disponivel: {altura_disponivel}")
        print(f"   escala calculada: {escala}")
        
        largura_vista = espessura_peca * mm * escala
        altura_vista = altura_peca * mm * escala
        
        # ===== CENTRALIZAR VISTA =====
        offset_x = (largura_disponivel - largura_vista) / 2
        x_origem_centralizado = x_origem + offset_x
        
        offset_y = (altura_disponivel - altura_vista) / 2
        y_origem_centralizado = y_origem + offset_y
                
        # Desenhar retângulo da vista
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x_origem_centralizado, y_origem_centralizado, largura_vista, altura_vista, stroke=1, fill=0)
        
        # ===== COTA DA ESPESSURA =====
        if lado == 'esquerda':
            x_inicio = x_origem_centralizado + largura_vista
            y_inicio = y_origem_centralizado + altura_vista
            x_texto_final = x_inicio + 15
            altura_linha_vertical = 15
            
            c.setStrokeColor(colors.HexColor("#A5A6A68A"))
            c.setLineWidth(0.5)
            c.setDash()
            c.line(x_inicio, y_inicio, x_inicio, y_inicio + altura_linha_vertical)
            c.line(x_inicio, y_inicio + altura_linha_vertical, x_texto_final, y_inicio + altura_linha_vertical)
            c.setDash()
            
            c.setFont("Helvetica", 11)
            c.setFillColor(colors.HexColor("#000000"))
            c.saveState()
            c.translate(x_texto_final, y_inicio + altura_linha_vertical + 8)
            c.rotate(90)
            c.drawCentredString(0, 0, self.formatar_cota(espessura_peca))
            c.restoreState()

        elif lado == 'direita':
            # Cota da espessura à DIREITA
            x_inicio = x_origem_centralizado + largura_vista
            y_inicio = y_origem_centralizado + altura_vista
            x_texto_final = x_inicio + 15
            altura_linha_vertical = 15
            
            c.setStrokeColor(colors.HexColor('#A5A6A68A'))
            c.setLineWidth(0.5)
            c.setDash()
            c.line(x_inicio, y_inicio, x_inicio, y_inicio + altura_linha_vertical)
            c.line(x_inicio, y_inicio + altura_linha_vertical, x_texto_final, y_inicio + altura_linha_vertical)
            c.setDash()
            
            c.setFont("Helvetica", 11)
            c.setFillColor(colors.HexColor("#000000"))
            c.saveState()
            c.translate(x_texto_final, y_inicio + altura_linha_vertical + 8)
            c.rotate(90)
            c.drawCentredString(0, 0, self.formatar_cota(espessura_peca))
            c.restoreState()
        
        # ===== FILTRAR E DESENHAR FUROS =====
        furos_lado = [f for f in peca.furos_horizontais 
                    if (lado == 'esquerda' and f.lado in ['XP', 'YP']) or
                        (lado == 'direita' and f.lado in ['XM', 'YM'])]
                
        # Ordenar por Y decrescente
        furos_lado = sorted(furos_lado, key=lambda f: float(f.y), reverse=True)
        
        # Agrupar por Z para cotas
        furos_por_x = {}
        for furo in furos_lado:
            x_key = round(float(furo.z), 1)
            if x_key not in furos_por_x:
                furos_por_x[x_key] = []
            furos_por_x[x_key].append(furo)

        furos_com_cota_z = set()
        for x_pos, furos_na_coluna in furos_por_x.items():
            furo_mais_proximo_topo = min(furos_na_coluna, key=lambda f: float(f.y))
            furos_com_cota_z.add(id(furo_mais_proximo_topo))
        
        # Desenhar furos
        for furo in furos_lado:
            y_furo_real = float(furo.y)
            z_furo_real = float(furo.z)
            
            y_furo_desenho = y_origem_centralizado + altura_vista - (y_furo_real * mm * escala)
            x_furo_desenho = x_origem_centralizado + (z_furo_real * mm * escala)
            
            # Raio proporcional à escala (mínimo 1.3, máximo 3)
            raio_furo = max(1.3, min(3, 1.3 * escala))
            
            c.setStrokeColor(colors.black)
            c.setFillColor(colors.black)
            c.circle(x_furo_desenho, y_furo_desenho, raio_furo, stroke=1, fill=0)
            
            # ===== COTA Y - DEPENDE DO LADO =====
            offset_externo = 15
            c.setStrokeColor(colors.HexColor('#A5A6A68A'))
            c.setLineWidth(0.5)
            c.setDash()
            
            if lado == 'esquerda':
                # Cota Y à ESQUERDA
                c.line(x_furo_desenho - raio_furo, y_furo_desenho, x_origem_centralizado - offset_externo, y_furo_desenho)
                c.setDash()
                
                c.setFont("Helvetica", 11)
                c.setFillColor(colors.HexColor("#000000"))
                c.drawRightString(x_origem_centralizado - offset_externo - 8, y_furo_desenho - 2, self.formatar_cota(y_furo_real))
            else:
                # Cota Y à DIREITA
                x_borda_direita = x_origem_centralizado + largura_vista
                c.line(x_furo_desenho + raio_furo, y_furo_desenho, x_borda_direita + offset_externo, y_furo_desenho)
                c.setDash()
                
                c.setFont("Helvetica", 11)
                c.setFillColor(colors.HexColor("#000000"))
                c.drawString(x_borda_direita + offset_externo + 8, y_furo_desenho - 2, self.formatar_cota(y_furo_real))
            
            # ===== COTA Z (só para furo mais próximo do topo) =====
            if id(furo) in furos_com_cota_z:
                offset_topo = 15
                c.setStrokeColor(colors.HexColor('#A5A6A68A'))
                c.setLineWidth(0.5)
                c.setDash()
                c.line(x_furo_desenho, y_furo_desenho + raio_furo, x_furo_desenho, y_origem_centralizado + altura_vista + offset_topo)
                c.setDash()
                
                c.setFont("Helvetica", 11)
                c.setFillColor(colors.HexColor("#000000"))
                c.saveState()
                c.translate(x_furo_desenho, y_origem_centralizado + altura_vista + offset_topo + 8)
                c.rotate(90)
                c.drawCentredString(0, 0, self.formatar_cota(z_furo_real))
                c.restoreState()
            
            # ===== CALCULAR MANDRIL =====
            mandril = self.calcular_mandril(y_furo_real, batente)
            
            # Especificação do furo COM MANDRIL
            if furo.profundidade == 0:
                texto_spec = f"Ø{self.formatar_cota(furo.diametro)} M{mandril}"
            else:
                texto_spec = f"Ø{self.formatar_cota(furo.diametro)}X{self.formatar_cota(furo.profundidade)},M{mandril}"
            
            y_texto = y_furo_desenho - 2
            
            # ===== ESPECIFICAÇÕES - DIREÇÃO DEPENDE DO LADO =====
            c.setStrokeColor(colors.grey)
            c.setLineWidth(0.5)
            
            if lado == 'esquerda':
                # Especificações à DIREITA da vista
                offset_x_spec = largura_vista + 10
                x_texto_inicio = x_origem_centralizado + offset_x_spec
                
                c.line(x_furo_desenho + raio_furo, y_furo_desenho, x_texto_inicio - 2, y_furo_desenho)
                
                tamanho_seta = 2
                c.line(x_texto_inicio - 2, y_furo_desenho, x_texto_inicio - 2 - tamanho_seta, y_furo_desenho + tamanho_seta)
                c.line(x_texto_inicio - 2, y_furo_desenho, x_texto_inicio - 2 - tamanho_seta, y_furo_desenho - tamanho_seta)
                
                c.setStrokeColor(colors.black)
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 11)
                c.drawString(x_texto_inicio, y_texto, texto_spec)
            
            else:
                # Especificações à ESQUERDA da vista (lado == 'direita')
                offset_x_spec = 10
                x_texto_fim = x_origem_centralizado - offset_x_spec
                
                c.line(x_furo_desenho - raio_furo, y_furo_desenho, x_texto_fim + 2, y_furo_desenho)
                
                tamanho_seta = 2
                c.line(x_texto_fim + 2, y_furo_desenho, x_texto_fim + 2 + tamanho_seta, y_furo_desenho + tamanho_seta)
                c.line(x_texto_fim + 2, y_furo_desenho, x_texto_fim + 2 + tamanho_seta, y_furo_desenho - tamanho_seta)
                
                c.setStrokeColor(colors.black)
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 11)
                c.drawRightString(x_texto_fim, y_texto, texto_spec)
        
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
    
    def desenhar_alerta_atencao(self, c: canvas.Canvas, x: float, y: float, 
                            texto_atencao: str = None):
        """
        Desenha triângulo de atenção com texto (usando imagem)
        
        Args:
            x, y: posição onde desenhar (canto esquerdo)
            texto_atencao: texto do alerta (opcional)
        """
        if not texto_atencao:
            return  # Não desenha se não tiver texto
        
        import os
        
        # Caminho da imagem do triângulo
        caminho_triangulo = 'triangulo_atencao.png'  # ou .jpg, .svg
        
        # Se não especificou caminho absoluto, busca na pasta do projeto
        if not os.path.isabs(caminho_triangulo):
            caminho_triangulo = os.path.join(os.path.dirname(__file__), '..', '..', caminho_triangulo)
        
        # Desenhar a imagem do triângulo
        if os.path.exists(caminho_triangulo):
            try:
                tamanho_triangulo = 120  # Ajuste o tamanho aqui

                x_ajustado = x - 15
                y_ajustado = y - 15 

                c.drawImage(caminho_triangulo, x_ajustado, y_ajustado, 
                        width=tamanho_triangulo, 
                        height=tamanho_triangulo,
                        preserveAspectRatio=True, 
                        mask='auto')
            except Exception as e:
                # Fallback: desenha texto se não carregar
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 20)
                c.drawString(x, y, "⚠")
        
        # TEXTO DE ATENÇÃO
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)
        x_texto = x_ajustado + 130  # Distância da imagem
        y_texto = y_ajustado + 50  # Alinhamento vertical
        c.drawString(x_texto, y_texto, "ATENÇÃO:")
        
        c.setFont("Helvetica", 10)
        c.drawString(x_texto + 60, y_texto, texto_atencao)
        
        c.setFillColor(colors.black)

    def calcular_tamanho_fonte_dinamico(self, c, texto: str, largura_max: float, fonte: str, tamanho_base: int = 12) -> int:
        """Reduz fonte até caber na célula"""
        tamanho = tamanho_base
        while tamanho > 7:
            if c.stringWidth(texto, fonte, tamanho) <= largura_max:
                return tamanho
            tamanho -= 1
        return 7    
    
    def desenhar_tabela_horizontal(self, c: canvas.Canvas, x: float, y: float, 
                                largura: float, altura: float, peca: Peca, 
                                config: dict, dados_adicionais: dict = None):
        """
        Desenha tabela HORIZONTAL com informações técnicas (abaixo do desenho)
        
        Args:
            c: Canvas do ReportLab
            x, y: posição inferior esquerda da tabela
            largura, altura: dimensões da tabela
            peca: objeto Peca com dados
            config: configurações do arquivo JSON
            dados_adicionais: dados extras passados manualmente
        """
        from datetime import datetime
        from reportlab.lib.utils import ImageReader
        import os
        
        if dados_adicionais is None:
            dados_adicionais = {}
        
        # Configurações visuais
        visual = config.get('visual', {})
        fonte = visual.get('fonte_tabela', 'Helvetica')
        
        campos_padrao = config.get('campos_padrao', {})
        campos_config = config.get('campos_tabela', [])
        
        # PREPARAR DADOS
        dados_tabela = []
        
        for campo in campos_config:
            label = campo['label']
            source = campo['source']
            campo_nome = campo['campo']
            
            valor = ""
            
            if source == "auto":
                # Dados automáticos do sistema/arquivo
                if campo_nome == "Material (mm)":
                    valor = f"MDF {int(peca.dimensoes.espessura)}"
                elif campo_nome == "Dimensões (mm)":
                    valor = f"{int(peca.dimensoes.largura)}x{int(peca.dimensoes.comprimento)}x{int(peca.dimensoes.espessura)}"
                elif campo_nome == "Data":
                    valor = datetime.now().strftime("%d/%m/%Y")
                elif campo_nome == "Código":
                    # Tenta pegar de dados_adicionais, senão usa padrão
                    codigo = dados_adicionais.get('codigo_peca', '')
                    nome = dados_adicionais.get('nome_peca', '')
                    valor = f"{codigo} - {nome}" if codigo and nome else "---"
                elif campo_nome == "Nome_Produto":
                    cod_prod = dados_adicionais.get('codigo_produto', '')
                    nome_prod = dados_adicionais.get('nome_produto', '')
                    valor = f"{cod_prod} - {nome_prod}" if cod_prod and nome_prod else "---"
                elif campo_nome == "responsavel":
                    print(f"DEBUG - campo_nome: {campo_nome}")
                    print(f"DEBUG - dados_adicionais: {dados_adicionais.get('responsavel')}")
                    valor = dados_adicionais.get('responsavel', '---')
                elif campo_nome == "Deslocamento":
                    valor = "---"
                elif campo_nome == "Batente":
                    batente = self.calcular_batente(peca)
                    valor = f"{self.formatar_cota(batente)}" if batente > 0 else "---"
                elif campo_nome == "Página":
                    pagina_atual = dados_adicionais.get('pagina_atual', 1)
                    total_paginas = dados_adicionais.get('total_paginas', 1)
                    valor = f"{pagina_atual}/{total_paginas}"
                elif campo_nome == "Conferente":
                    valor = "TARCÍSIO"
                elif campo_nome == "Status":
                    valor = dados_adicionais.get('status', 'CÓPIA CONTROLADA')                
                    
            elif source == "config":
                # Dados do arquivo de configuração
                valor = campos_padrao.get(campo_nome, "")
                
            elif source == "manual":
                # Dados passados manualmente
                valor = dados_adicionais.get(campo_nome, "")
            
            if valor:  # Só adiciona se tiver valor
                dados_tabela.append((label, str(valor)))
        
        # CALCULAR LAYOUT - Dividir em colunas
        num_campos = len(dados_tabela)
        
        largura_logo = 80

        # ===== CONFIGURAÇÃO DE COLUNAS POR LINHA =====
        # Defina quantas colunas cada linha tem
        colunas_linha_1 = 7
        colunas_linha_2 = 6

        # Defina as larguras para cada linha separadamente
        larguras_linha_1 = [250, 100, 70, 70, 80, 60, 70]  # 7 colunas
        larguras_linha_2 = [250, 65, 95, 100, 70, 120]       # 6 colunas     

        # Dimensões
        num_linhas = 2
        altura_linha = altura / num_linhas

        # Calcular largura total usando a linha mais larga
        largura_conteudo = max(sum(larguras_linha_1), sum(larguras_linha_2))
        largura_total = largura_logo + largura_conteudo
        
        # Margem a esquerda
        largura_total = largura_logo + max(sum(larguras_linha_1), sum(larguras_linha_2))
        x = (841.89 - largura_total) / 2
        x_conteudo = x + largura_logo

        # DESENHAR BORDA EXTERNA
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x, y, largura_total, altura, stroke=1, fill=0)

        # ===== ÁREA DO LOGO =====
        # Desenhar borda da área do logo
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(x + largura_logo, y, x + largura_logo, y + altura)  # Linha vertical separadora
        
        # Carregar e desenhar o logo
        caminho_logo = config.get('visual', {}).get('logo', 'logo.png')
        
        # Se não especificou no config, tenta buscar na pasta do projeto
        if not os.path.isabs(caminho_logo):
            caminho_logo = os.path.join(os.path.dirname(__file__), '..', '..', caminho_logo)
        
        # Desenhar o logo (se existir)
        if os.path.exists(caminho_logo):
            try:
                # Área disponível para o logo (com margem interna)
                margem_logo = 5
                logo_x = x + margem_logo
                logo_y = y + margem_logo
                logo_largura = largura_logo - (2 * margem_logo)
                logo_altura = altura - (2 * margem_logo)
                
                # Desenhar imagem mantendo proporção
                c.drawImage(caminho_logo, logo_x, logo_y, 
                        width=logo_largura, height=logo_altura, 
                        preserveAspectRatio=True, mask='auto')
            except Exception as e:
                # Se der erro ao carregar, desenha um texto placeholder
                c.setFillColor(colors.grey)
                c.setFont(fonte, 8)
                c.drawCentredString(x + largura_logo/2, y + altura/2, "LOGO")
                c.setFillColor(colors.black)
        else:
            # Se não encontrar o arquivo, desenha placeholder
            c.setFillColor(colors.lightgrey)
            c.rect(x + 10, y + 10, largura_logo - 20, altura - 20, stroke=1, fill=1)
            c.setFillColor(colors.grey)
            c.setFont(fonte, 10)
            c.drawCentredString(x + largura_logo/2, y + altura/2, "LOGO")
            c.setFillColor(colors.black)
        
        # DESENHAR CÉLULAS
        y_atual = y + altura
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)

        indice_dados = 0  # Controla qual dado estamos desenhando

        # LINHA 1 - 7 colunas
        for coluna in range(colunas_linha_1):
            if indice_dados >= len(dados_tabela):
                break
            
            label, valor = dados_tabela[indice_dados]
            
            # Calcular X da célula (após o logo)
            x_celula = x_conteudo + sum(larguras_linha_1[:coluna])
            largura_celula = larguras_linha_1[coluna]
            y_celula = y_atual - altura_linha
            
            # Linhas da grade
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            
            # Linha horizontal inferior
            c.line(x_celula, y_celula, x_celula + largura_celula, y_celula)
            
            # Linha vertical direita (exceto última coluna)
            if coluna < colunas_linha_1 - 1:
                c.line(x_celula + largura_celula, y_celula, 
                    x_celula + largura_celula, y_celula + altura_linha)

            # Calcular quantos caracteres cabem na célula
            max_chars_label = int((largura_celula - 8) / 4)
            label_exibido = label[:max_chars_label] + "..." if len(label) > max_chars_label else label  

            # DESENHAR LABEL
            c.setFillColor(colors.HexColor("#000000"))

            # Aumentar fonte de uma célula específica
            if label == "PLANO DE FURAÇÃO":
                c.setFont(f"{fonte}-Bold", 12) 
                y_label = y_celula + altura_linha - 15
                x_centro = x_celula + largura_celula / 2
                c.drawCentredString(x_centro, y_label, label_exibido)
            else:
                c.setFont(f"{fonte}-Bold", 9)
                y_label = y_celula + altura_linha - 9
                c.drawString(x_celula + 4, y_label, label_exibido)

            
            # DESENHAR VALOR (normal, maior, embaix)
            c.setFillColor(colors.black)

            # Fonte varia por campo
            if label == "PLANO DE FURAÇÃO":
                tamanho_fonte = self.calcular_tamanho_fonte_dinamico(c, valor, largura_celula - 8, "Helvetica", tamanho_base=10)
                c.setFont("Helvetica", tamanho_fonte)
            elif label == "Página":
                c.setFont("Helvetica", 12)    
            else:
                c.setFont(fonte, 12)
            
            # Centralizar valor horizontal e verticalmente
            x_centro_valor = x_celula + largura_celula / 2
            y_centro_valor = y_celula + (altura_linha / 4)  # Ajuste fino da altura
            c.drawCentredString(x_centro_valor, y_centro_valor, valor)
            
            indice_dados += 1

        # LINHA 2 - 6 colunas
        y_atual -= altura_linha

        for coluna in range(colunas_linha_2):
            if indice_dados >= len(dados_tabela):
                break
            
            label, valor = dados_tabela[indice_dados]
            
            # Calcular X da célula (após o logo)
            x_celula = x_conteudo + sum(larguras_linha_2[:coluna])
            largura_celula = larguras_linha_2[coluna]
            y_celula = y_atual - altura_linha
            
            # Linhas da grade
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            
            # Linha horizontal inferior
            c.line(x_celula, y_celula, x_celula + largura_celula, y_celula)
            
            # Linha vertical direita (exceto última coluna)
            if coluna < colunas_linha_2 - 1:
                c.line(x_celula + largura_celula, y_celula, 
                    x_celula + largura_celula, y_celula + altura_linha)
            
            # DESENHAR LABEL (negrito, pequeno, em cima)
            c.setFillColor(colors.HexColor("#000000"))
            c.setFont(f"{fonte}-Bold", 9)
            
            # Calcular quantos caracteres cabem na célula
            max_chars_label = int((largura_celula - 8) / 4)
            label_exibido = label[:max_chars_label] + "..." if len(label) > max_chars_label else label
            c.drawString(x_celula + 4, y_celula + altura_linha - 9, label_exibido)
            
            # DESENHAR VALOR (normal, maior, embaixo)
            c.setFillColor(colors.black)
            
            # Fonte varia por campo
            if label == "Código/Descrição Peça":
                tamanho_fonte = self.calcular_tamanho_fonte_dinamico(c, valor, largura_celula - 5, "Helvetica")
                c.setFont("Helvetica", tamanho_fonte)
            elif label == "Responsável":
                tamanho_fonte = self.calcular_tamanho_fonte_dinamico(c, valor, largura_celula - 3, "Helvetica", tamanho_base=11)
                c.setFont("Helvetica", tamanho_fonte)
            elif label == "Conferente":
                c.setFont("Helvetica", 10)
            elif label == "Status":
                tamanho_fonte = self.calcular_tamanho_fonte_dinamico(c, valor, largura_celula - 3, "Helvetica", tamanho_base=11)
                c.setFont("Helvetica", tamanho_fonte)
                if valor == "CÓPIA CONTROLADA":
                    c.setFillColor(colors.HexColor("#0000FF"))  # Azul
                else:
                    c.setFillColor(colors.HexColor("#FF0000"))  # Vermelho              
            elif label == "Borda":
                # Desenhar legenda colorida para bordas
                c.setFont(fonte, 11)
                
                # Textos
                texto_cor = "COR"
                texto_pardo = "PARDO"
                espaco_entre = 20
                
                # Calcular larguras
                largura_cor = c.stringWidth(texto_cor, fonte, 11)
                largura_pardo = c.stringWidth(texto_pardo, fonte, 11)
                largura_total = largura_cor + espaco_entre + largura_pardo
                
                # Posição inicial centralizada
                x_inicio = x_celula + (largura_celula - largura_total) / 2
                y_texto = y_celula + (altura_linha / 4)
                
                # Desenhar "COR"
                c.setFillColor(colors.black)
                c.drawString(x_inicio, y_texto, texto_cor)
                
                # Traço verde abaixo de "COR"
                c.setStrokeColor(colors.HexColor("#32CD32"))  # Verde limão
                c.setLineWidth(3)
                c.line(x_inicio, y_texto - 5, x_inicio + largura_cor, y_texto - 5)
                
                # Desenhar "PARDO"
                x_pardo = x_inicio + largura_cor + espaco_entre
                c.setFillColor(colors.black)
                c.drawString(x_pardo, y_texto, texto_pardo)
                
                # Traço laranja abaixo de "PARDO"
                c.setStrokeColor(colors.HexColor("#FF8C00"))  # Laranja
                c.setLineWidth(3)
                c.line(x_pardo, y_texto - 5, x_pardo + largura_pardo, y_texto - 5)
                
                # Resetar cores e linha
                c.setStrokeColor(colors.black)
                c.setLineWidth(0.5)
                c.setFillColor(colors.black)
                
                # Pular o desenho normal do valor (já foi desenhado acima)
                indice_dados += 1
                continue
            else:
                c.setFont(fonte, 12)
            
            # Calcular quantos caracteres cabem na célula
            max_chars_valor = int((largura_celula - 8) / 5)
            valor_exibido = valor[:max_chars_valor] + "..." if len(valor) > max_chars_valor else valor
            
            # Centralizar valor horizontal e verticalmente
            x_centro_valor = x_celula + largura_celula / 2
            y_centro_valor = y_celula + (altura_linha / 4)  # Ajuste fino da altura
            c.drawCentredString(x_centro_valor, y_centro_valor, valor_exibido)            
            
            indice_dados += 1

        c.setFillColor(colors.black)  # Restaura cor
    
    def desenhar_seta(self, c: canvas.Canvas, x: float, y: float, angulo: float):
        """Desenha uma pequena seta"""
        from math import cos, sin, radians
        tamanho = 3
        ang_rad = radians(angulo)
        
        # Ponta da seta
        x1 = x + tamanho * cos(ang_rad + radians(150))
        y1 = y + tamanho * sin(ang_rad + radians(150))
        x2 = x + tamanho * cos(ang_rad - radians(150))
        y2 = y + tamanho * sin(ang_rad - radians(150))
        
        c.line(x, y, x1, y1)
        c.line(x, y, x2, y2)

    
    def desenhar_bordas_batente(self, c: canvas.Canvas, x_origem: float, y_origem: float,
                       largura: float, altura: float, bordas: dict):
        """
        Desenha bordas com cor destacada (verde=COR, laranja=PARDO)
        Suporta múltiplas bordas (1, 2, 3 ou 4 lados)
        
        Args:
            bordas: {'top': 'cor'/'pardo'/None, 'bottom': ..., 'left': ..., 'right': ...}
        """
        
        espessura = 1  # Linha grossa para destacar
        
        # Mapear cores
        cores = {
            'cor': colors.HexColor("#2FFF00"),     # Verde
            'pardo': colors.HexColor("#FF8C00")    # Laranja
        }
        
        # Desenhar cada borda se existir
        
        # TOPO
        if bordas.get('top'):
            cor = cores.get(bordas['top'], colors.HexColor("#2FFF00"))
            c.setStrokeColor(cor)
            c.setLineWidth(espessura)
            c.line(x_origem, y_origem + altura, x_origem + largura, y_origem + altura)

        # BAIXO
        if bordas.get('bottom'):
            cor = cores.get(bordas['bottom'], colors.HexColor("#2FFF00"))
            c.setStrokeColor(cor)
            c.setLineWidth(espessura)
            c.line(x_origem, y_origem, x_origem + largura, y_origem)
        
        # ESQUERDA
        if bordas.get('left'):
            cor = cores.get(bordas['left'], cores['cor'])
            c.setStrokeColor(cor)
            c.setLineWidth(espessura)
            c.line(x_origem, y_origem, x_origem, y_origem + altura)
        
        # DIREITA
        if bordas.get('right'):
            cor = cores.get(bordas['right'], cores['cor'])
            c.setStrokeColor(cor)
            c.setLineWidth(espessura)
            c.line(x_origem + largura, y_origem, x_origem + largura, y_origem + altura)
        
        # Restaurar cores padrão
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)

    
    
    def gerar_pdf(self, peca: Peca, arquivo_saida: str, dados_adicionais: dict = None):
        """
        Gera PDF com desenho técnico da peça.
        Pode gerar múltiplas páginas se houver conflitos de furação.
        
        Args:
            peca: objeto Peca com os dados
            arquivo_saida: caminho do arquivo PDF a ser criado
            dados_adicionais: dados extras como código, revisão, etc
        """
        import json
        import os
        from copy import deepcopy
        
        # Carregar configurações
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            config = {
                'campos_padrao': {'borda': 'Cor PARDO', 'responsavel': 'ENZO PEDRICA'},
                'visual': {'cor_tabela': '#0066CC', 'fonte_tabela': 'Helvetica'},
                'campos_tabela': []
            }
        
        if dados_adicionais is None:
            dados_adicionais = {}
        
        # Rotacionar peça baseado no ângulo escolhido
        angulo = dados_adicionais.get('angulo_rotacao', 0)
        if angulo != 0:
            peca = self.aplicar_rotacao(peca, angulo)

        # Espelhar se necessário
        if dados_adicionais.get('espelhar_peca', False) and angulo == 0:
            peca = self.espelhar_verticalmente(peca)

        # ===== ANALISAR DISTRIBUIÇÃO DE FUROS =====
        distribuicao = self.distribuir_furos_superior_inferior(peca.furos_verticais)
        
        furos_inferior = distribuicao['inferior']
        furos_superior = distribuicao['superior']
        furos_segunda = distribuicao['segunda_furacao']
        
        # Determinar quais páginas gerar
        paginas = []

        if furos_inferior:
            paginas.append({
                'tipo': 'INFERIOR',
                'titulo': 'FURAÇÃO INFERIOR',
                'furos': furos_inferior
            })

        if furos_superior:
            paginas.append({
                'tipo': 'SUPERIOR',
                'titulo': 'FURAÇÃO SUPERIOR',
                'furos': furos_superior
            })

        # Se tiver 2ª passada, adicionar ao alerta em vez de criar nova página
        if furos_segunda:
            # Adicionar furos da 2ª passada aos inferiores e marcar alerta
            if dados_adicionais is None:
                dados_adicionais = {}
            
            alerta_existente = dados_adicionais.get('alerta', '')
            coords_segunda = ', '.join([f"X={int(f.x)}" for f in furos_segunda])
            novo_alerta = f"2ª PASSADA NECESSÁRIA: {coords_segunda}"
            
            if alerta_existente:
                dados_adicionais['alerta'] = f"{alerta_existente} | {novo_alerta}"
            else:
                dados_adicionais['alerta'] = novo_alerta
        
        # Se não tem furos verticais, gera página única
        if not paginas:
            paginas.append({
                'tipo': 'NORMAL',
                'titulo': 'PLANO DE FURAÇÃO',
                'furos': []
            })
        
        # Criar canvas
        c = canvas.Canvas(arquivo_saida, pagesize=landscape(A4))
        largura_pagina, altura_pagina = landscape(A4)
        
        total_paginas = len(paginas)
        
        # Gerar cada página
        for idx, pagina_info in enumerate(paginas):
            pagina_atual = idx + 1
            
            # Criar cópia da peça com apenas os furos desta página
            peca_pagina = deepcopy(peca)
            peca_pagina.furos_verticais = pagina_info['furos']
            
            # Dados adicionais com info da página
            dados_pagina = deepcopy(dados_adicionais)
            dados_pagina['pagina_atual'] = pagina_atual
            dados_pagina['total_paginas'] = total_paginas
            dados_pagina['tipo_furacao'] = pagina_info['tipo']
            
            # Desenhar a página
            self._desenhar_pagina_furacao(
                c, peca_pagina, pagina_info['titulo'], 
                config, dados_pagina, largura_pagina, altura_pagina
            )
            
            # Nova página se não for a última
            if idx < len(paginas) - 1:
                c.showPage()
        
        c.save()


    def _desenhar_pagina_furacao(self, c: canvas.Canvas, peca: Peca, titulo: str,
                              config: dict, dados_adicionais: dict,
                              largura_pagina: float, altura_pagina: float):
        """
        Desenha uma página de furação completa.
        Layout: [Vista Esquerda] [Vista Principal] [Vista Direita] - alinhados horizontalmente
        """
        
        # Verificar se tem furos horizontais E se é a página INFERIOR para definir layout
        tipo_furacao = dados_adicionais.get('tipo_furacao', 'NORMAL')
        tem_furos_horizontais = len(peca.furos_horizontais) > 0 and tipo_furacao in ['INFERIOR', 'NORMAL']
        
        # ===== CALCULAR ESPAÇOS =====
        altura_tabela = 80
        y_tabela = self.margem - 40
        
        # Área útil acima da tabela
        altura_area_vistas = altura_pagina - self.margem - altura_tabela - 60
        
        largura_disponivel = largura_pagina - 2 * self.margem
        
        # ===== TÍTULO =====
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        titulo_y = altura_pagina - self.margem + 15
        c.drawCentredString(largura_pagina / 2, titulo_y, titulo)
        
        # Calcular batente (precisa antes das vistas)
        batente = self.calcular_batente(peca)
        
        if tem_furos_horizontais:
            # ===== LAYOUT COM VISTAS LATERAIS (horizontal) =====
            
            # Calcular proporção ideal baseado nas dimensões da peça
            espessura = float(peca.dimensoes.espessura)
            largura = float(peca.dimensoes.largura)
            comprimento = float(peca.dimensoes.comprimento)
            
            # Largura mínima para vistas laterais (proporcional à espessura)
            largura_vista_lateral = max(80, min(120, espessura * 6))
            
            espaco_entre = 30
            largura_vista_principal = largura_disponivel - (2 * largura_vista_lateral) - (2 * espaco_entre)
            
            # DEBUG
            print(f"🔍 DEBUG VISTAS:")
            print(f"   Peça: {comprimento}x{largura}x{espessura}")
            print(f"   largura_disponivel: {largura_disponivel}")
            print(f"   largura_vista_lateral: {largura_vista_lateral}")
            print(f"   largura_vista_principal: {largura_vista_principal}")
            
            # Calcular largura total das 3 vistas + espaços
            largura_total_vistas = (2 * largura_vista_lateral) + largura_vista_principal + (2 * espaco_entre)

            # Centralizar tudo na página
            x_inicio_centralizado = (largura_pagina - largura_total_vistas) / 2

            # Posições X
            x_vista_esquerda = x_inicio_centralizado
            x_vista_principal = x_vista_esquerda + largura_vista_lateral + espaco_entre
            x_vista_direita = x_vista_principal + largura_vista_principal + espaco_entre
            
            # Posição Y (todas na mesma altura)
            y_base_vistas = y_tabela + altura_tabela + 30
            altura_vistas = altura_area_vistas - 50
            
            # ===== VISTA PRINCIPAL (centro) =====
            escala = self.calcular_escala(
                peca.dimensoes.largura,
                peca.dimensoes.comprimento,
                largura_vista_principal,
                altura_vistas,
                margem_seguranca=0.55
            )
            
            largura_desenhada = peca.dimensoes.largura * mm * escala
            altura_desenhada = peca.dimensoes.comprimento * mm * escala
            
            # Centralizar vista principal na sua área
            x_origem = x_vista_principal + (largura_vista_principal - largura_desenhada) / 2
            y_origem = y_base_vistas + (altura_vistas - altura_desenhada) / 2
            
            # Desenhar peça (vista de topo)
            self.desenhar_retangulo_peca(c, x_origem, y_origem, largura_desenhada, altura_desenhada)
            
            # Bordas coloridas
            if dados_adicionais:
                bordas_originais = dados_adicionais.get('bordas', {
                    'top': None, 'bottom': None, 'left': None, 'right': None
                })
                if not isinstance(bordas_originais, dict):
                    bordas_originais = {'top': None, 'bottom': None, 'left': None, 'right': None}
                
                angulo = dados_adicionais.get('angulo_rotacao', 0)
                espelhado = dados_adicionais.get('espelhar_peca', False)
                bordas_config = self.transformar_bordas(bordas_originais, angulo, espelhado)
                
                if any([bordas_config.get('top'), bordas_config.get('bottom'),
                        bordas_config.get('left'), bordas_config.get('right')]):
                    self.desenhar_bordas_batente(c, x_origem, y_origem,
                                                largura_desenhada, altura_desenhada, bordas_config)
            
            # Cotas principais
            offset_cota = 40
            largura_real_atual = float(peca.dimensoes.largura)
            comprimento_real_atual = float(peca.dimensoes.comprimento)
            self.desenhar_cota_principal(c, x_origem, y_origem, largura_desenhada, altura_desenhada,
                                        largura_real_atual, comprimento_real_atual, offset_cota)
            
            # ===== FUROS VERTICAIS =====
            if peca.furos_verticais:
                self._desenhar_furos_verticais(c, peca, x_origem, y_origem, 
                                            largura_desenhada, altura_desenhada, escala, batente)
            
            # ===== VISTAS LATERAIS =====
            foi_espelhado = dados_adicionais.get('espelhar_peca', False) if dados_adicionais else False
            
            # Vista esquerda
            self.desenhar_vista_lateral(c, x_vista_esquerda, y_base_vistas, 
                                        peca, 'esquerda', largura_vista_lateral, 
                                        altura_vistas, foi_espelhado, batente)
            
            # Vista direita
            self.desenhar_vista_lateral(c, x_vista_direita, y_base_vistas, 
                                        peca, 'direita', largura_vista_lateral,
                                        altura_vistas, foi_espelhado, batente)
        
        else:
            # ===== LAYOUT SEM VISTAS LATERAIS (vista principal centralizada) =====
            escala = self.calcular_escala(
                peca.dimensoes.largura,
                peca.dimensoes.comprimento,
                largura_disponivel,
                altura_area_vistas,
                margem_seguranca=0.65
            )
            
            largura_desenhada = peca.dimensoes.largura * mm * escala
            altura_desenhada = peca.dimensoes.comprimento * mm * escala
            
            x_origem = self.margem + (largura_disponivel - largura_desenhada) / 2
            y_origem = y_tabela + altura_tabela + 30 + (altura_area_vistas - altura_desenhada) / 2
            
            # Desenhar peça
            self.desenhar_retangulo_peca(c, x_origem, y_origem, largura_desenhada, altura_desenhada)
            
            # Bordas coloridas
            if dados_adicionais:
                bordas_originais = dados_adicionais.get('bordas', {
                    'top': None, 'bottom': None, 'left': None, 'right': None
                })
                if not isinstance(bordas_originais, dict):
                    bordas_originais = {'top': None, 'bottom': None, 'left': None, 'right': None}
                
                angulo = dados_adicionais.get('angulo_rotacao', 0)
                espelhado = dados_adicionais.get('espelhar_peca', False)
                bordas_config = self.transformar_bordas(bordas_originais, angulo, espelhado)
                
                if any([bordas_config.get('top'), bordas_config.get('bottom'),
                        bordas_config.get('left'), bordas_config.get('right')]):
                    self.desenhar_bordas_batente(c, x_origem, y_origem,
                                                largura_desenhada, altura_desenhada, bordas_config)
            
            # Cotas principais
            offset_cota = 40
            largura_real_atual = float(peca.dimensoes.largura)
            comprimento_real_atual = float(peca.dimensoes.comprimento)
            self.desenhar_cota_principal(c, x_origem, y_origem, largura_desenhada, altura_desenhada,
                                        largura_real_atual, comprimento_real_atual, offset_cota)
            
            # Furos verticais
            if peca.furos_verticais:
                self._desenhar_furos_verticais(c, peca, x_origem, y_origem,
                                            largura_desenhada, altura_desenhada, escala, batente)
        
        # ===== TABELA =====
        largura_tabela = largura_pagina - 2 * self.margem
        x_tabela = self.margem
        self.desenhar_tabela_horizontal(c, x_tabela, y_tabela, largura_tabela, altura_tabela,
                                        peca, config, dados_adicionais)
        
        # ===== MARGEM EXTERNA =====
        largura_logo = 80
        larguras_linha_1 = [250, 100, 70, 70, 80, 60, 70]
        larguras_linha_2 = [250, 65, 95, 100, 70, 120]  
        largura_total_tabela = largura_logo + max(sum(larguras_linha_1), sum(larguras_linha_2))
        x_margem = (841.89 - largura_total_tabela) / 2

        y_margem_inferior = y_tabela
        y_margem_superior = titulo_y + 20

        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.rect(x_margem, y_margem_inferior, largura_total_tabela, 
            y_margem_superior - y_margem_inferior, stroke=1, fill=0)
        
        # ===== ALERTA =====
        texto_alerta = dados_adicionais.get('alerta', None) if dados_adicionais else None
        if texto_alerta:
            x_alerta = x_tabela - 35
            y_alerta = y_tabela + altura_tabela + 10
            self.desenhar_alerta_atencao(c, x_alerta, y_alerta, texto_alerta)


    def _desenhar_furos_verticais(self, c: canvas.Canvas, peca: Peca, 
                                x_origem: float, y_origem: float,
                                largura_desenhada: float, altura_desenhada: float,
                                escala: float, batente: float):
        """
        Desenha os furos verticais com cotas e mandris.
        Função auxiliar para evitar duplicação de código.
        """
        # Agrupar furos por Y
        furos_por_y = {}
        for furo in peca.furos_verticais:
            y_key = round(float(furo.y), 1)
            if y_key not in furos_por_y:
                furos_por_y[y_key] = []
            furos_por_y[y_key].append(furo)

        # Agrupar furos por X
        furos_por_x = {}
        for furo in peca.furos_verticais:
            x_key = round(float(furo.x), 1)
            if x_key not in furos_por_x:
                furos_por_x[x_key] = []
            furos_por_x[x_key].append(furo)

        # Furos com cota Y (mais à esquerda de cada linha)
        furos_com_cota_y = set()
        for y_pos, furos_na_linha in furos_por_y.items():
            furo_mais_esquerda = min(furos_na_linha, key=lambda f: float(f.x))
            furos_com_cota_y.add(id(furo_mais_esquerda))

        # Furos com cota X (mais próximo do topo de cada coluna)
        furos_com_cota_x = set()
        for x_pos, furos_na_coluna in furos_por_x.items():
            furo_mais_proximo_topo = max(furos_na_coluna, key=lambda f: float(f.y))
            furos_com_cota_x.add(id(furo_mais_proximo_topo))

        # Escalonar offsets Y
        furos_com_cota_y_lista = [f for f in peca.furos_verticais if id(f) in furos_com_cota_y]
        furos_com_cota_y_lista = sorted(furos_com_cota_y_lista, key=lambda f: float(f.y))

        offset_cota_y = {}
        distancia_minima = 15
        offset_base = 15
        offset_incremento = 12

        for i, furo in enumerate(furos_com_cota_y_lista):
            if i == 0:
                offset_cota_y[id(furo)] = offset_base
            else:
                furo_anterior = furos_com_cota_y_lista[i - 1]
                diferenca_y = abs(float(furo.y) - float(furo_anterior.y))
                
                if diferenca_y < distancia_minima:
                    offset_anterior = offset_cota_y[id(furo_anterior)]
                    offset_cota_y[id(furo)] = offset_anterior + offset_incremento
                else:
                    offset_cota_y[id(furo)] = offset_base

        # Escalonar offsets X
        furos_com_cota_x_lista = [f for f in peca.furos_verticais if id(f) in furos_com_cota_x]
        furos_com_cota_x_lista = sorted(furos_com_cota_x_lista, key=lambda f: float(f.x))

        offset_cota_x = {}

        for i, furo in enumerate(furos_com_cota_x_lista):
            if i == 0:
                offset_cota_x[id(furo)] = offset_base
            else:
                furo_anterior = furos_com_cota_x_lista[i - 1]
                diferenca_x = abs(float(furo.x) - float(furo_anterior.x))
                
                if diferenca_x < distancia_minima:
                    offset_anterior = offset_cota_x[id(furo_anterior)]
                    offset_cota_x[id(furo)] = offset_anterior + offset_incremento
                else:
                    offset_cota_x[id(furo)] = offset_base    

        # Desenhar furos verticais
        for furo in peca.furos_verticais:
            mandril = self.calcular_mandril(furo.y, batente)
            x_furo, y_furo = self.desenhar_furo_vertical(c, x_origem, y_origem, furo, escala, altura_desenhada, mandril)
            
            mostrar_x = id(furo) in furos_com_cota_x
            mostrar_y = id(furo) in furos_com_cota_y
            
            offset_x = offset_cota_x.get(id(furo), 25)
            offset_y = offset_cota_y.get(id(furo), 25)
            
            self.desenhar_cota_furo(c, x_origem, y_origem, x_furo, y_furo, 
                                    furo.x, furo.y,
                                    largura_desenhada, altura_desenhada,
                                    escala, mostrar_x, mostrar_y,
                                    offset_x, offset_y)

    def transformar_bordas(self, bordas: dict, angulo: int, espelhado: bool) -> dict:
        """
        Transforma posições das bordas baseado em rotação/espelhamento
        Agora suporta múltiplas bordas com tipos (cor/pardo)
        
        Args:
            bordas: {'top': 'cor'/'pardo'/None, 'bottom': ..., 'left': ..., 'right': ...}
            angulo: 0, 90, 180, 270
            espelhado: True/False
            
        Returns:
            Bordas transformadas com mesma estrutura
        """
        if not bordas or not isinstance(bordas, dict):
            return {'top': None, 'bottom': None, 'left': None, 'right': None}
        
        top = bordas.get('top')
        bottom = bordas.get('bottom')
        left = bordas.get('left')
        right = bordas.get('right')
        
        # Aplicar espelhamento PRIMEIRO (inverte top <-> bottom)
        if espelhado:
            top, bottom = bottom, top
        
        # Aplicar rotação
        if angulo == 90:
            # 90° horário: top→right, right→bottom, bottom→left, left→top
            return {
                'top': left,
                'right': top,
                'bottom': right,
                'left': bottom
            }
        elif angulo == 180:
            # 180°: inverte opostos
            return {
                'top': bottom,
                'bottom': top,
                'left': right,
                'right': left
            }
        elif angulo == 270:
            # 270° horário: top→left, left→bottom, bottom→right, right→top
            return {
                'top': right,
                'left': top,
                'bottom': left,
                'right': bottom
            }
        
        # 0° ou sem rotação
        return {
            'top': top,
            'bottom': bottom,
            'left': left,
            'right': right
        }


if __name__ == "__main__":
    # Teste básico
    from furacao_parser import Dimensoes, FuroVertical
    
    peca_teste = Peca(
        nome="Teste",
        dimensoes=Dimensoes(largura=269, comprimento=297, espessura=15),
        furos_verticais=[
            FuroVertical(x=24, y=65, diametro=12, profundidade=11),
            FuroVertical(x=245, y=65, diametro=12, profundidade=11),
        ],
        furos_horizontais=[],
        comentarios=["Teste de geração"]
    )
    
    gerador = GeradorDesenhoTecnico()
    gerador.gerar_pdf(peca_teste, "/home/claude/teste.pdf")