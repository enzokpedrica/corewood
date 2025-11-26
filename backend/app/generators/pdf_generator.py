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
                          mostrar_x: bool = True, mostrar_y: bool = True):
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
        
        offset_externo = 15  # Distância para fora da peça
        
        # COTA HORIZONTAL (X) - sai do furo para CIMA
        if mostrar_x and distancia_x > 0:
            # Borda superior da peça
            y_borda_superior = y_origem_peca + altura_peca
            
            # Linha do furo até fora da peça

            c.line(x_furo, y_furo, x_furo, y_borda_superior + offset_externo)
            c.setDash()  # Sólida
            
            # Texto VERTICAL acima
            c.setFont("Helvetica", 14)
            c.setFillColor(colors.HexColor("#000000"))
            c.saveState()
            x_texto = x_furo
            y_texto = y_borda_superior + offset_externo + 8
            c.translate(x_texto, y_texto)
            c.rotate(90)
            c.drawCentredString(0, 0, self.formatar_cota(distancia_x))
            c.restoreState()
        
        # COTA VERTICAL (Y) - sai do furo para a ESQUERDA
        if mostrar_y and distancia_y > 0:
            # Borda esquerda da peça
            x_borda_esquerda = x_origem_peca
            
            # Linha do furo até fora da peça
            c.line(x_furo, y_furo, x_borda_esquerda - offset_externo, y_furo)
            c.setDash()  # Sólida
            
            # Texto HORIZONTAL à esquerda
            c.setFont("Helvetica", 14)
            c.setFillColor(colors.HexColor("#000000"))
            y_texto = y_furo
            x_texto = x_borda_esquerda - offset_externo - 8
            c.drawRightString(x_texto, y_texto - 3, self.formatar_cota(distancia_y))
        
        c.setFillColor(colors.black)  # Restaura cor
    
    def desenhar_furo_vertical(self, c: canvas.Canvas, x_origem: float, y_origem: float,
                               furo: FuroVertical, escala: float):
        """
        Desenha marcação de furo vertical (vista de topo)
        
        Args:
            x_origem, y_origem: origem do desenho da peça
            furo: dados do furo
            escala: escala do desenho
        """
        # Posição do furo no desenho
        x_furo = x_origem + (furo.x * mm * escala)
        y_furo = y_origem + (furo.y * mm * escala)
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
        if furo.profundidade == 0:
            c.setFont("Helvetica", 12)
            texto = f"Ø{self.formatar_cota(furo.diametro)}"
        else:
            c.setFont("Helvetica", 12)
            texto = f"Ø{self.formatar_cota(furo.diametro)}X{self.formatar_cota(furo.profundidade)}"
        
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
        
        offset_externo = 25  # Distância para fora da peça (um pouco mais que os furos)
        
        # COTA 1: VERTICAL (297) - linha sai para CIMA do canto direito
        x_borda_direita = x_origem + largura
        y_topo = y_origem + altura

        # Linha tracejada para cima
        c.line(x_borda_direita, y_topo, x_borda_direita, y_topo + offset_externo)
        c.setDash()

        # Texto VERTICAL (rotacionado) - COTA DE 297
        c.setFont("Helvetica", 14)
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
        c.setFont("Helvetica", 14)
        c.setFillColor(colors.HexColor("#000000"))
        c.drawRightString(x_esquerda - offset_externo - 8, y_base - 3, f"{altura_real:.0f}")
        
        c.setFillColor(colors.black)  # Restaura cor
    
    def desenhar_vista_lateral(self, c: canvas.Canvas, x_origem: float, y_origem: float,
                        peca: Peca, lado: str, largura_disponivel: float, 
                        altura_disponivel: float, espelhado: bool = False):
        """
        Desenha vista lateral da peça mostrando furos horizontais
        AGORA COM ESCALA DINÂMICA!
        
        Args:
            x_origem, y_origem: posição base da vista
            peca: dados da peça
            lado: 'esquerda' ou 'direita'
            largura_disponivel: espaço horizontal disponível
            altura_disponivel: espaço vertical disponível
            espelhado: se a peça foi espelhada
        """

        espessura_peca = float(peca.dimensoes.espessura)
        altura_peca = float(peca.dimensoes.comprimento)
        
        # ===== ESCALA DINÂMICA =====
        # Calcular escala baseado no espaço disponível
        escala = self.calcular_escala(
            largura_peca=espessura_peca,
            comprimento_peca=altura_peca,
            largura_disponivel=largura_disponivel,
            altura_disponivel=altura_disponivel,
            margem_seguranca=0.8  # 80% do espaço disponível
        )
        
        largura_vista = espessura_peca * mm * escala
        altura_vista = altura_peca * mm * escala
        
        # ===== CENTRALIZAR VISTA =====
        # Centralizar horizontalmente no espaço disponível
        offset_x = (largura_disponivel - largura_vista) / 2
        x_origem_centralizado = x_origem + offset_x
        
        # Centralizar verticalmente
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
            
            c.setFont("Helvetica", 14)
            c.setFillColor(colors.HexColor("#000000"))
            c.saveState()
            c.translate(x_texto_final, y_inicio + altura_linha_vertical + 8)
            c.rotate(90)
            c.drawCentredString(0, 0, self.formatar_cota(espessura_peca))
            c.restoreState()

        elif lado == 'direita':
            x_inicio = x_origem_centralizado
            y_inicio = y_origem_centralizado + altura_vista
            x_texto_final = x_inicio - 15
            altura_linha_vertical = 15
            
            c.setStrokeColor(colors.HexColor('#A5A6A68A'))
            c.setLineWidth(0.5)
            c.setDash()
            c.line(x_inicio, y_inicio, x_inicio, y_inicio + altura_linha_vertical)
            c.line(x_inicio, y_inicio + altura_linha_vertical, x_texto_final, y_inicio + altura_linha_vertical)
            c.setDash()
            
            c.setFont("Helvetica", 14)
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
            
            # Linha de cota Y
            offset_externo = 25
            c.setStrokeColor(colors.HexColor('#A5A6A68A'))
            c.setLineWidth(0.5)
            c.setDash()
            c.line(x_furo_desenho - raio_furo, y_furo_desenho, x_origem_centralizado - offset_externo, y_furo_desenho)
            c.setDash()
            
            # Texto cota Y
            c.setFont("Helvetica", 14)
            c.setFillColor(colors.HexColor("#000000"))
            c.drawRightString(x_origem_centralizado - offset_externo - 8, y_furo_desenho - 2, self.formatar_cota(y_furo_real))
            
            # Cota Z (só para furo mais próximo do topo)
            if id(furo) in furos_com_cota_z:
                offset_topo = 23
                c.setStrokeColor(colors.HexColor('#A5A6A68A'))
                c.setLineWidth(0.5)
                c.setDash()
                c.line(x_furo_desenho, y_furo_desenho + raio_furo, x_furo_desenho, y_origem_centralizado + altura_vista + offset_topo)
                c.setDash()
                
                c.setFont("Helvetica", 14)
                c.setFillColor(colors.HexColor("#000000"))
                c.saveState()
                c.translate(x_furo_desenho, y_origem_centralizado + altura_vista + offset_topo + 8)
                c.rotate(90)
                c.drawCentredString(0, 0, self.formatar_cota(z_furo_real))
                c.restoreState()
            
            # Especificação do furo
            if furo.profundidade == 0:
                texto_spec = f"Ø{self.formatar_cota(furo.diametro)}"
            else:
                texto_spec = f"Ø{self.formatar_cota(furo.diametro)}X{self.formatar_cota(furo.profundidade)}"
            
            offset_x = largura_vista + 10
            x_texto_inicio = x_origem_centralizado + offset_x
            y_texto = y_furo_desenho - 2
            
            # Linha com seta
            c.setStrokeColor(colors.grey)
            c.setLineWidth(0.5)
            c.line(x_furo_desenho + raio_furo, y_furo_desenho, x_texto_inicio - 2, y_furo_desenho)
            
            tamanho_seta = 2
            c.line(x_texto_inicio - 2, y_furo_desenho, x_texto_inicio - 2 - tamanho_seta, y_furo_desenho + tamanho_seta)
            c.line(x_texto_inicio - 2, y_furo_desenho, x_texto_inicio - 2 - tamanho_seta, y_furo_desenho - tamanho_seta)
            
            c.setStrokeColor(colors.black)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 12)
            c.drawString(x_texto_inicio, y_texto, texto_spec)
        
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
        while tamanho > 6:
            if c.stringWidth(texto, fonte, tamanho) <= largura_max:
                return tamanho
            tamanho -= 1
        return 6    
    
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
                    valor = "---"
                elif campo_nome == "Página":
                    valor = "2/2"
                elif campo_nome == "Conferente":
                    valor = "TARCÍSIO"
                elif campo_nome == "Status":
                    valor = "CÓPIA AUTENTICADA"                   
                    
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
                c.setFont("Helvetica", 15)    
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
                tamanho_fonte = self.calcular_tamanho_fonte_dinamico(c, valor, largura_celula - 8, "Helvetica")
                c.setFont("Helvetica", tamanho_fonte)
            elif label == "Responsável":
                tamanho_fonte = self.calcular_tamanho_fonte_dinamico(c, valor, largura_celula - 5, "Helvetica", tamanho_base=10)
                c.setFont("Helvetica", tamanho_fonte)
            elif label == "Conferente":
                c.setFont("Helvetica", 10)
            elif label == "Status":
                tamanho_fonte = self.calcular_tamanho_fonte_dinamico(c, valor, largura_celula - 8, "Helvetica", tamanho_base=10)
                c.setFont("Helvetica", tamanho_fonte)
                if valor == "CÓPIA CONTROLADA":
                    c.setFillColor(colors.HexColor("#0000FF"))  # Azul
                else:
                    c.setFillColor(colors.HexColor("#FF0000"))  # Vermelho              
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
        Gera PDF com desenho técnico da peça
        
        Args:
            peca: objeto Peca com os dados
            arquivo_saida: caminho do arquivo PDF a ser criado
            dados_adicionais: dados extras como código, revisão, etc
        """
        import json
        import os
        
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
        
        # Rotacionar peça baseado no ângulo escolhido
        angulo = dados_adicionais.get('angulo_rotacao', 0)
        if angulo != 0:
            peca = self.aplicar_rotacao(peca, angulo)

        # Espelhar se necessário (E se não rotacionou, pois rotação já muda tudo)
        if dados_adicionais.get('espelhar_peca', False) and angulo == 0:
            peca = self.espelhar_verticalmente(peca)

        c = canvas.Canvas(arquivo_saida, pagesize=landscape(A4))
        largura_pagina, altura_pagina = landscape(A4)
        
        # ===== CALCULAR ESPAÇOS =====
        altura_pagina_util = altura_pagina - (2 * self.margem)  # ~550pts

        # Distribuição:
        altura_tabela = 80
        altura_vistas_laterais = 150
        altura_vista_principal = altura_pagina_util - altura_tabela - altura_vistas_laterais - 30

        largura_disponivel = largura_pagina - 2 * self.margem

        # Calcular escala DINÂMICA para vista principal
        escala = self.calcular_escala(
            peca.dimensoes.largura,
            peca.dimensoes.comprimento,
            largura_disponivel,
            altura_vista_principal,
            margem_seguranca=0.75
        )

        # Dimensões da peça em escala
        largura_desenhada = peca.dimensoes.largura * mm * escala
        altura_desenhada = peca.dimensoes.comprimento * mm * escala

        # Posição Y da vista principal (acima das vistas laterais)
        y_origem_principal = self.margem + altura_tabela + altura_vistas_laterais + 50

        # Centralizar horizontalmente
        x_origem = self.margem + (largura_disponivel - largura_desenhada) / 2
        y_origem = y_origem_principal

        # Título da vista principal - CENTRALIZADO
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.black)
        texto_titulo = "PLANO DE FURAÇÃO"
        largura_texto = c.stringWidth(texto_titulo, "Helvetica-Bold", 16)
        titulo_x = (largura_pagina - largura_texto) / 2
        titulo_y = y_origem + altura_desenhada + 60
        c.drawCentredString(largura_pagina / 2, titulo_y, texto_titulo)

        # Desenhar peça (vista de topo)
        self.desenhar_retangulo_peca(c, x_origem, y_origem, largura_desenhada, altura_desenhada)
        
       # Desenhar bordas coloridas se configurado
        if dados_adicionais:
            # Pegar bordas originais (novo formato)
            bordas_originais = dados_adicionais.get('bordas', {
                'top': None,
                'bottom': None,
                'left': None,
                'right': None
            })

            # Garantir que bordas_originais é um dict válido
            if not isinstance(bordas_originais, dict):
                bordas_originais = {'top': None, 'bottom': None, 'left': None, 'right': None}
            
            # Transformar bordas baseado em rotação/espelhamento
            angulo = dados_adicionais.get('angulo_rotacao', 0)
            espelhado = dados_adicionais.get('espelhar_peca', False)
            bordas_config = self.transformar_bordas(bordas_originais, angulo, espelhado)

            # Desenhar se tiver pelo menos uma borda
            if any([
                bordas_config.get('top'),
                bordas_config.get('bottom'),
                bordas_config.get('left'),
                bordas_config.get('right')
            ]):
                self.desenhar_bordas_batente(
                    c,
                    x_origem,
                    y_origem,
                    largura_desenhada,
                    altura_desenhada,
                    bordas_config
                )

        # Desenhar cotas principais (MESMO ESTILO das cotas dos furos)
        offset_cota = 40
        # Usar dimensões da peça (já rotacionadas se aplicável)
        largura_real_atual = float(peca.dimensoes.largura)
        comprimento_real_atual = float(peca.dimensoes.comprimento)

        self.desenhar_cota_principal(c, x_origem, y_origem, largura_desenhada, altura_desenhada,
                                    largura_real_atual, comprimento_real_atual, offset_cota)
        
        # Desenhar furos verticais com cotas de posição
        furos_por_y = {}
        for furo in peca.furos_verticais:
            y_key = round(float(furo.y), 1)
            if y_key not in furos_por_y:
                furos_por_y[y_key] = []
            furos_por_y[y_key].append(furo)

        # Agrupar furos por posição X (mesma linha vertical)
        furos_por_x = {}
        for furo in peca.furos_verticais:
            x_key = round(float(furo.x), 1)
            if x_key not in furos_por_x:
                furos_por_x[x_key] = []
            furos_por_x[x_key].append(furo)

        # Para cada linha Y, pegar apenas o furo mais à esquerda (menor X)
        furos_com_cota_y = set()
        for y_pos, furos_na_linha in furos_por_y.items():
            furo_mais_esquerda = min(furos_na_linha, key=lambda f: float(f.x))
            furos_com_cota_y.add(id(furo_mais_esquerda))

        # Para cada linha X, pegar apenas o furo mais próximo do topo (maior Y)
        furos_com_cota_x = set()
        for x_pos, furos_na_coluna in furos_por_x.items():
            furo_mais_proximo_topo = max(furos_na_coluna, key=lambda f: float(f.y))
            furos_com_cota_x.add(id(furo_mais_proximo_topo))

        # Desenhar furos verticais com cotas inteligentes
        for i, furo in enumerate(peca.furos_verticais):
            x_furo, y_furo = self.desenhar_furo_vertical(c, x_origem, y_origem, furo, escala)
            
            # Mostrar cota X apenas se for o mais próximo do topo na coluna
            mostrar_x = id(furo) in furos_com_cota_x
            
            # Mostrar cota Y apenas se for o mais à esquerda da linha
            mostrar_y = id(furo) in furos_com_cota_y
            
            self.desenhar_cota_furo(c, x_origem, y_origem, x_furo, y_furo, 
                                furo.x, furo.y,
                                largura_desenhada, altura_desenhada,
                                escala, mostrar_x, mostrar_y)
            
        # Tabela horizontal abaixo do desenho
        largura_tabela = largura_pagina - 2 * self.margem
        altura_tabela = 80
        x_tabela = self.margem
        y_tabela = self.margem - 40
        self.desenhar_tabela_horizontal(c, x_tabela, y_tabela, largura_tabela, altura_tabela,
                                     peca, config, dados_adicionais)
        
        # ===== MARGEM EXTERNA (envolve tudo) =====
        # Usar EXATAMENTE a mesma largura e posição X da tabela
        largura_logo = 80
        larguras_linha_1 = [250, 100, 70, 70, 80, 60, 70]
        larguras_linha_2 = [250, 65, 95, 100, 70, 120]  
        largura_total_tabela = largura_logo + max(sum(larguras_linha_1), sum(larguras_linha_2))
        x_margem = (841.89 - largura_total_tabela) / 2

        # Altura: do fundo da tabela até acima do título
        y_margem_inferior = y_tabela
        y_margem_superior = titulo_y + 20

        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.rect(
            x_margem, 
            y_margem_inferior, 
            largura_total_tabela, 
            y_margem_superior - y_margem_inferior, 
            stroke=1, 
            fill=0
        )
            
        # Desenhar alerta de atenção (se houver)
        texto_alerta = dados_adicionais.get('alerta', None)  # Vem do usuário
        if texto_alerta:
            x_alerta = x_tabela - 35
            y_alerta = y_tabela + altura_tabela + 10  # 10 pontos acima da tabela
            self.desenhar_alerta_atencao(c, x_alerta, y_alerta, texto_alerta)    
   
        # Desenhar vistas laterais (se houver furos horizontais)
        if len(peca.furos_horizontais) > 0:
            # ===== LAYOUT DAS VISTAS LATERAIS =====
            y_vistas = self.margem + 50
            altura_vistas = 200  # Altura disponível para vistas laterais
            
            # Largura para cada vista lateral (mais espaço!)
            largura_vista_lateral = 80  # Aumentado de 20 para 100
            espaco_entre_vistas = 20
            
            # Largura disponível para vista principal (centro)
            largura_vista_principal = largura_pagina - (2 * self.margem) - (2 * largura_vista_lateral) - (2 * espaco_entre_vistas)
            
            # Posições BASE (sem alerta)
            x_vista_esquerda = self.margem + 30
            x_vista_principal = x_vista_esquerda + largura_vista_lateral + espaco_entre_vistas
            x_vista_direita = x_vista_principal + largura_vista_principal + espaco_entre_vistas

            # Se tiver alerta, desloca APENAS a vista esquerda
            if dados_adicionais and dados_adicionais.get('alerta'):
                offset_alerta = 120
                x_vista_esquerda += offset_alerta  # Só a esquerda se move!
            
            # Verificar se foi espelhado
            foi_espelhado = dados_adicionais.get('espelhar_peca', False)

            # Desenhar vista lateral ESQUERDA
            self.desenhar_vista_lateral(
                c, x_vista_esquerda, y_vistas, 
                peca, 'esquerda', 
                largura_vista_lateral, 
                altura_vistas,  # ← ADICIONAR altura!
                foi_espelhado
            )
            
            # Desenhar vista lateral DIREITA
            self.desenhar_vista_lateral(
                c, x_vista_direita, y_vistas, 
                peca, 'direita', 
                largura_vista_lateral,
                altura_vistas,  # ← ADICIONAR altura!
                foi_espelhado
            )

        c.save()

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