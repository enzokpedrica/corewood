"""
Parser STEP Multi-Peças para CoreWood v2
- Separa peças de acessórios (parafusos, bordas, ferragens)
- Gera 1 MPR por peça
- Gera TXT com lista de corte + acessórios
- Integração com FastAPI
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
import io


@dataclass
class Furo:
    """Representa um furo detectado"""
    id: int
    x: float
    y: float
    z: float
    diametro: float
    profundidade: float = 15.0
    face: str = "superior"
    tipo: str = "vertical"
    lado: str = "LS"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'diametro': self.diametro,
            'profundidade': self.profundidade,
            'face': self.face,
            'tipo': self.tipo,
            'lado': self.lado
        }


@dataclass
class Peca:
    """Representa uma peça do STEP"""
    nome: str
    entity_id: int
    x_min: float = 0
    x_max: float = 0
    y_min: float = 0
    y_max: float = 0
    z_min: float = 0
    z_max: float = 0
    furos: List[Furo] = field(default_factory=list)
    
    @property
    def largura(self) -> float:
        return round(abs(self.x_max - self.x_min), 2)
    
    @property
    def comprimento(self) -> float:
        return round(abs(self.y_max - self.y_min), 2)
    
    @property
    def espessura(self) -> float:
        return round(abs(self.z_max - self.z_min), 2)
    
    @property
    def dimensoes_ordenadas(self) -> tuple:
        """Retorna (largura, comprimento, espessura) - maior dim = comprimento"""
        dims = sorted([self.largura, self.comprimento, self.espessura], reverse=True)
        return (dims[1], dims[0], dims[2])  # L x C x E
    
    def to_dict(self) -> dict:
        dims = self.dimensoes_ordenadas
        return {
            'nome': self.nome,
            'largura': dims[0],
            'comprimento': dims[1],
            'espessura': dims[2],
            'furos': [f.to_dict() for f in self.furos]
        }


@dataclass 
class Acessorio:
    """Representa um acessório (parafuso, borda, etc)"""
    nome: str
    quantidade: int = 1
    
    def to_dict(self) -> dict:
        return {'nome': self.nome, 'quantidade': self.quantidade}


class StepMultiPartParser:
    """Parser que separa múltiplas peças de um arquivo STEP"""
    
    ACESSORIOS_KEYWORDS = [
        'parafuso', 'screw', 'bolt', 
        'borda', 'edge', 'fita',
        'ferragem', 'hardware',
        'dobradica', 'hinge',
        'puxador', 'handle',
        'corrediça', 'slide',
        'cavilha', 'dowel',
        'prego', 'nail'
    ]
    
    def __init__(self, step_content: str):
        self.content = step_content
        self.entities: Dict[int, dict] = {}
        self.pecas: List[Peca] = []
        self.acessorios: List[Acessorio] = []
        self._parse_entities()
    
    def _parse_entities(self):
        """Extrai todas as entidades do STEP"""
        pattern = r'#(\d+)\s*=\s*([A-Z][A-Z0-9_]*)\s*\((.*?)\)\s*;'
        
        for match in re.finditer(pattern, self.content, re.DOTALL):
            entity_id = int(match.group(1))
            entity_type = match.group(2)
            entity_data = match.group(3).strip()
            self.entities[entity_id] = {'type': entity_type, 'data': entity_data}
    
    def _get_entity(self, entity_id: int) -> Optional[dict]:
        return self.entities.get(entity_id)
    
    def _parse_cartesian_point(self, entity_id: int) -> Optional[tuple]:
        """Extrai coordenadas de um CARTESIAN_POINT"""
        entity = self._get_entity(entity_id)
        if not entity or entity['type'] != 'CARTESIAN_POINT':
            return None
        coords_match = re.search(r'\(\s*([-\d.E+]+)\s*,\s*([-\d.E+]+)\s*,\s*([-\d.E+]+)\s*\)', entity['data'])
        if coords_match:
            return (
                float(coords_match.group(1)),
                float(coords_match.group(2)),
                float(coords_match.group(3))
            )
        return None
    
    def _is_acessorio(self, nome: str) -> bool:
        """Verifica se o nome indica um acessório"""
        nome_lower = nome.lower()
        return any(keyword in nome_lower for keyword in self.ACESSORIOS_KEYWORDS)
    
    def _extract_manifold_solids(self) -> Dict[int, str]:
        """Extrai todos os MANIFOLD_SOLID_BREP e seus nomes"""
        solids = {}
        
        for entity_id, entity in self.entities.items():
            if entity['type'] == 'ADVANCED_BREP_SHAPE_REPRESENTATION':
                match = re.match(r"'([^']*)'", entity['data'])
                nome_repr = match.group(1) if match else f"Peça_{entity_id}"
                
                refs = re.findall(r'#(\d+)', entity['data'])
                for ref_id in refs:
                    ref_entity = self._get_entity(int(ref_id))
                    if ref_entity and ref_entity['type'] == 'MANIFOLD_SOLID_BREP':
                        solid_match = re.match(r"'([^']*)'", ref_entity['data'])
                        solid_nome = solid_match.group(1) if solid_match else nome_repr
                        
                        if solid_nome and solid_nome.strip():
                            solids[int(ref_id)] = solid_nome
                        else:
                            solids[int(ref_id)] = nome_repr
        
        return solids
    
    def _find_cylinders_for_solid(self, solid_id: int) -> List[dict]:
        """Encontra cilindros (furos) através de CIRCLE entities"""
        cilindros = []
        
        for entity_id, entity in self.entities.items():
            if entity['type'] == 'CIRCLE':
                match = re.match(r"'[^']*'\s*,\s*#(\d+)\s*,\s*([\d.E+-]+)", entity['data'])
                if match:
                    axis_id = int(match.group(1))
                    raio = float(match.group(2))
                    
                    axis = self._get_entity(axis_id)
                    if axis and axis['type'] == 'AXIS2_PLACEMENT_3D':
                        point_match = re.search(r"'[^']*'\s*,\s*#(\d+)", axis['data'])
                        if point_match:
                            point_id = int(point_match.group(1))
                            coords = self._parse_cartesian_point(point_id)
                            if coords:
                                cilindros.append({
                                    'x': coords[0],
                                    'y': coords[1],
                                    'z': coords[2],
                                    'raio': raio
                                })
        
        return cilindros
    
    def _calculate_bounding_box(self, solid_id: int) -> tuple:
        """Calcula bounding box de um sólido, corrigindo Z para espessura real"""
        solid = self._get_entity(solid_id)
        if not solid:
            return (0, 0, 0, 0, 0, 0)
        
        shell_match = re.search(r'#(\d+)', solid['data'])
        if not shell_match:
            return (0, 0, 0, 0, 0, 0)
        
        shell = self._get_entity(int(shell_match.group(1)))
        if not shell:
            return (0, 0, 0, 0, 0, 0)
        
        points = []
        face_refs = re.findall(r'#(\d+)', shell['data'])
        visited = set()
        to_visit = [int(ref) for ref in face_refs]
        
        while to_visit:
            current_id = to_visit.pop()
            if current_id in visited:
                continue
            visited.add(current_id)
            
            entity = self._get_entity(current_id)
            if not entity:
                continue
            
            if entity['type'] == 'CARTESIAN_POINT':
                coords = self._parse_cartesian_point(current_id)
                if coords:
                    points.append(coords)
            else:
                refs = re.findall(r'#(\d+)', entity['data'])
                for ref in refs:
                    ref_id = int(ref)
                    if ref_id not in visited:
                        to_visit.append(ref_id)
        
        if not points:
            return (0, 0, 0, 0, 0, 0)
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        z_coords = [p[2] for p in points]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Usar os valores Z absolutos min e max
        z_min = min(z_coords)
        z_max = max(z_coords)
        
        # Calcular espessura bruta
        espessura_bruta = z_max - z_min
        
        # NÃO ajustar mais o bounding box - usar valores brutos
        # O mapeamento de eixos vai identificar qual dimensão é a espessura

        print(f"   📐 BBox bruto: X({min(x_coords):.1f} a {max(x_coords):.1f}), Y({min(y_coords):.1f} a {max(y_coords):.1f}), Z({min(z_coords):.1f} a {max(z_coords):.1f})")
        print(f"   📐 BBox ajustado: X({x_min:.1f} a {x_max:.1f}), Y({y_min:.1f} a {y_max:.1f}), Z({z_min:.1f} a {z_max:.1f})")

        return (
            x_min, x_max,
            y_min, y_max,
            z_min, z_max
        )

    def _calculate_bounding_box_fallback(self, solid_id: int) -> tuple:
        """Método fallback - usa todos os pontos"""
        solid = self._get_entity(solid_id)
        if not solid:
            return (0, 0, 0, 0, 0, 0)
        
        shell_match = re.search(r'#(\d+)', solid['data'])
        if not shell_match:
            return (0, 0, 0, 0, 0, 0)
        
        shell = self._get_entity(int(shell_match.group(1)))
        if not shell:
            return (0, 0, 0, 0, 0, 0)
        
        points = []
        face_refs = re.findall(r'#(\d+)', shell['data'])
        visited = set()
        to_visit = [int(ref) for ref in face_refs]
        
        while to_visit:
            current_id = to_visit.pop()
            if current_id in visited:
                continue
            visited.add(current_id)
            
            entity = self._get_entity(current_id)
            if not entity:
                continue
            
            if entity['type'] == 'CARTESIAN_POINT':
                coords = self._parse_cartesian_point(current_id)
                if coords:
                    points.append(coords)
            else:
                refs = re.findall(r'#(\d+)', entity['data'])
                for ref in refs:
                    ref_id = int(ref)
                    if ref_id not in visited:
                        to_visit.append(ref_id)
        
        if not points:
            return (0, 0, 0, 0, 0, 0)
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        z_coords = [p[2] for p in points]
        
        return (
            min(x_coords), max(x_coords),
            min(y_coords), max(y_coords),
            min(z_coords), max(z_coords)
        )
    
    def parse(self) -> tuple:
        """Processa o STEP e retorna (peças, acessórios)"""
        solids = self._extract_manifold_solids()
        acessorios_count = {}
        
        for solid_id, nome in solids.items():
            # Ignorar bordas e acessórios
            nome_lower = nome.lower().strip()
            if self._is_acessorio(nome) or nome_lower == 'borda' or nome_lower.startswith('borda '):
                print(f"⏭️ Ignorando acessório/borda: {nome}")
                if nome not in acessorios_count:
                    acessorios_count[nome] = 0
                acessorios_count[nome] += 1
                continue
            
            bbox = self._calculate_bounding_box(solid_id)

            print(f"\n📦 Processando peça: {nome}")
            print(f"   BBox X: {bbox[0]:.1f} a {bbox[1]:.1f} (dim: {bbox[1]-bbox[0]:.1f})")
            print(f"   BBox Y: {bbox[2]:.1f} a {bbox[3]:.1f} (dim: {bbox[3]-bbox[2]:.1f})")
            print(f"   BBox Z: {bbox[4]:.1f} a {bbox[5]:.1f} (dim: {bbox[5]-bbox[4]:.1f})")

            
            peca = Peca(
                nome=nome,
                entity_id=solid_id,
                x_min=bbox[0], x_max=bbox[1],
                y_min=bbox[2], y_max=bbox[3],
                z_min=bbox[4], z_max=bbox[5]
            )
            
            # Dimensões brutas do bounding box
            dim_x = abs(peca.x_max - peca.x_min)
            dim_y = abs(peca.y_max - peca.y_min)
            dim_z = abs(peca.z_max - peca.z_min)
            
            # NOVO: Detectar qual eixo é qual baseado nas dimensões
            # Espessura é sempre a menor dimensão (15, 18, etc)
            # Comprimento é a maior dimensão
            dims = [(dim_x, 'x'), (dim_y, 'y'), (dim_z, 'z')]
            dims_sorted = sorted(dims, key=lambda d: d[0])
            
            eixo_espessura = dims_sorted[0][1]  # Menor = espessura
            eixo_largura = dims_sorted[1][1]    # Médio = largura
            eixo_comprimento = dims_sorted[2][1] # Maior = comprimento
            
            print(f"🔍 Mapeamento de eixos para {nome}:")
            print(f"   Espessura ({dims_sorted[0][0]:.1f}mm): eixo {eixo_espessura}")
            print(f"   Largura ({dims_sorted[1][0]:.1f}mm): eixo {eixo_largura}")
            print(f"   Comprimento ({dims_sorted[2][0]:.1f}mm): eixo {eixo_comprimento}")
            
            # Valores min/max para cada dimensão lógica
            def get_dim_bounds(eixo):
                if eixo == 'x':
                    return peca.x_min, peca.x_max, dim_x
                elif eixo == 'y':
                    return peca.y_min, peca.y_max, dim_y
                else:
                    return peca.z_min, peca.z_max, dim_z
            
            esp_min, esp_max, esp_dim = get_dim_bounds(eixo_espessura)
            larg_min, larg_max, larg_dim = get_dim_bounds(eixo_largura)
            comp_min, comp_max, comp_dim = get_dim_bounds(eixo_comprimento)
            
            cilindros = self._find_cylinders_for_solid(solid_id)
            
            # Função para obter coordenadas no sistema MPR
            def get_mpr_coords(cil):
                """Converte coordenadas STEP para sistema MPR (X=comprimento, Y=largura, Z=espessura)"""
                step_coords = {'x': cil['x'], 'y': cil['y'], 'z': cil['z']}
                
                mpr_comprimento = step_coords[eixo_comprimento] - comp_min
                mpr_largura = step_coords[eixo_largura] - larg_min
                mpr_espessura = step_coords[eixo_espessura] - esp_min
                
                return mpr_comprimento, mpr_largura, mpr_espessura
            
            # Primeiro passo: identificar furos horizontais (nas bordas do comprimento ou largura)
            furos_horizontais_coords = set()
            
            for cil in cilindros:
                mpr_x, mpr_y, mpr_z = get_mpr_coords(cil)
                
                # Se está na borda do comprimento (entrada do furo horizontal)
                if mpr_x <= 2.0 or mpr_x >= (comp_dim - 2.0):
                    furos_horizontais_coords.add((round(mpr_y, 0), round(cil['raio'], 2)))
            
            # Segundo passo: filtrar e classificar cilindros
            cilindros_unicos = []
            coords_vistas = set()

            for cil in cilindros:
                mpr_x, mpr_y, mpr_z = get_mpr_coords(cil)
                
                # Ignorar cilindros fora do bounding box
                margem = 5.0
                if mpr_z < -margem or mpr_z > esp_dim + margem:
                    continue
                if mpr_x < -margem or mpr_x > comp_dim + margem:
                    continue
                if mpr_y < -margem or mpr_y > larg_dim + margem:
                    continue

                y_round = round(mpr_y, 0)
                x_round = round(mpr_x, 0)
                z_round = round(mpr_z, 0)
                raio_round = round(cil['raio'], 2)
                
                tolerancia_borda = 2.0
                z_meio = esp_dim / 2  # 7.5 para espessura 15
                tolerancia_z_meio = 3.0  # Z deve estar próximo do meio
                
                # Verificar se Z está no meio da espessura (indica furo horizontal)
                z_no_meio = abs(mpr_z - z_meio) <= tolerancia_z_meio
                
                # Se está na borda X = é entrada de furo horizontal XP/XM
                if mpr_x <= tolerancia_borda and z_no_meio:
                    key = ('H', y_round, raio_round, 'XP')
                    if key not in coords_vistas:
                        coords_vistas.add(key)
                        cilindros_unicos.append({**cil, 'mpr': (mpr_x, mpr_y, mpr_z), 'tipo_detectado': 'H_XP'})
                elif mpr_x >= (comp_dim - tolerancia_borda) and z_no_meio:
                    key = ('H', y_round, raio_round, 'XM')
                    if key not in coords_vistas:
                        coords_vistas.add(key)
                        cilindros_unicos.append({**cil, 'mpr': (mpr_x, mpr_y, mpr_z), 'tipo_detectado': 'H_XM'})
                # Se está na borda Y = é entrada de furo horizontal YP/YM
                elif mpr_y <= tolerancia_borda and z_no_meio:
                    key = ('H', x_round, raio_round, 'YP')
                    if key not in coords_vistas:
                        coords_vistas.add(key)
                        cilindros_unicos.append({**cil, 'mpr': (mpr_x, mpr_y, mpr_z), 'tipo_detectado': 'H_YP'})
                elif mpr_y >= (larg_dim - tolerancia_borda) and z_no_meio:
                    key = ('H', x_round, raio_round, 'YM')
                    if key not in coords_vistas:
                        coords_vistas.add(key)
                        cilindros_unicos.append({**cil, 'mpr': (mpr_x, mpr_y, mpr_z), 'tipo_detectado': 'H_YM'})
                else:
                    # Verificar se é fundo de furo horizontal (ignorar)
                    if (y_round, raio_round) in furos_horizontais_coords:
                        continue
                    if (x_round, raio_round) in furos_horizontais_coords:
                        continue
                    
                    # Furo vertical
                    key = ('V', x_round, y_round, raio_round)
                    if key not in coords_vistas:
                        coords_vistas.add(key)
                        cilindros_unicos.append({**cil, 'mpr': (mpr_x, mpr_y, mpr_z), 'tipo_detectado': 'V'})

            furo_id = 1
            for cil in cilindros_unicos:
                mpr_x, mpr_y, mpr_z = cil['mpr']
                diametro = round(cil['raio'] * 2, 2)
                tipo_detectado = cil['tipo_detectado']

                # DEBUG - ver distâncias das bordas
                print(f"   🔎 Cilindro Ø{diametro}: mpr_x={mpr_x:.1f}, mpr_y={mpr_y:.1f}, mpr_z={mpr_z:.1f}")
                print(f"      Dist X: min={mpr_x:.1f}, max={comp_dim-mpr_x:.1f}")
                print(f"      Dist Y: min={mpr_y:.1f}, max={larg_dim-mpr_y:.1f}")
                print(f"      Dist Z: min={mpr_z:.1f}, max={esp_dim-mpr_z:.1f}")
                
                if tipo_detectado == 'V':
                    tipo = 'vertical'
                    lado = 'LS'
                    profundidade = 0 if diametro <= 6 else 11.0
                    final_x = round(mpr_x, 2)
                    final_y = round(mpr_y, 2)
                    final_z = round(mpr_z, 2)
                    
                elif tipo_detectado == 'H_XP':
                    tipo = 'horizontal'
                    lado = 'XP'
                    profundidade = 22.0
                    final_x = 0
                    final_y = round(mpr_y, 2)
                    final_z = round(mpr_z, 2)
                    
                elif tipo_detectado == 'H_XM':
                    tipo = 'horizontal'
                    lado = 'XM'
                    profundidade = 22.0
                    final_x = comp_dim
                    final_y = round(mpr_y, 2)
                    final_z = round(mpr_z, 2)
                    
                elif tipo_detectado == 'H_YP':
                    tipo = 'horizontal'
                    lado = 'YP'
                    profundidade = 22.0
                    final_x = round(mpr_x, 2)
                    final_y = 0
                    final_z = round(mpr_z, 2)
                    
                elif tipo_detectado == 'H_YM':
                    tipo = 'horizontal'
                    lado = 'YM'
                    profundidade = 22.0
                    final_x = round(mpr_x, 2)
                    final_y = larg_dim
                    final_z = round(mpr_z, 2)
                
                furo = Furo(
                    id=furo_id,
                    x=final_x,
                    y=final_y,
                    z=final_z,
                    diametro=diametro,
                    profundidade=profundidade,
                    face='superior' if tipo == 'vertical' else lado,
                    tipo=tipo,
                    lado=lado
                )
                peca.furos.append(furo)
                furo_id += 1
                
                # Debug
                tipo_emoji = "🔴V" if tipo == 'vertical' else "🔵H"
                print(f"   {tipo_emoji}#{furo_id-1} X:{final_x} Y:{final_y} Z:{final_z} Ø{diametro} ({lado})")
            
            self.pecas.append(peca)
        
        for nome, qtd in acessorios_count.items():
            self.acessorios.append(Acessorio(nome=nome, quantidade=qtd))
        
        return self.pecas, self.acessorios


class TXTReportGenerator:
    """Gera relatório TXT com lista de corte e acessórios"""
    
    def generate(self, pecas: List[Peca], acessorios: List[Acessorio], nome_projeto: str = "Projeto") -> str:
        lines = [
            "=" * 60,
            f"LISTA DE CORTE E ACESSÓRIOS - {nome_projeto.upper()}",
            "=" * 60,
            "",
            "-" * 60,
            "PEÇAS PARA USINAGEM",
            "-" * 60,
            ""
        ]
        
        for i, peca in enumerate(pecas, 1):
            dims = peca.dimensoes_ordenadas
            lines.extend([
                f"{i}. {peca.nome}",
                f"   Dimensões: {dims[0]} x {dims[1]} x {dims[2]} mm (L x C x E)",
                f"   Furos: {len(peca.furos)}",
            ])
            
            if peca.furos:
                for furo in peca.furos:
                    lines.append(f"      - Furo Ø{furo.diametro}mm em X={furo.x}, Y={furo.y}")
            
            lines.append("")
        
        if acessorios:
            lines.extend([
                "-" * 60,
                "ACESSÓRIOS E FERRAGENS",
                "-" * 60,
                ""
            ])
            for acessorio in acessorios:
                lines.append(f"• {acessorio.nome}: {acessorio.quantidade} un")
            lines.append("")
        
        total_furos = sum(len(p.furos) for p in pecas)
        lines.extend([
            "-" * 60,
            "RESUMO",
            "-" * 60,
            f"Total de peças: {len(pecas)}",
            f"Total de furos: {total_furos}",
            f"Total de acessórios: {sum(a.quantidade for a in acessorios)}",
            "=" * 60
        ])
        
        return "\n".join(lines)


def parse_step_multipart(content: str) -> Dict[str, Any]:
    """
    Função principal para integração com FastAPI
    Retorna JSON com peças, acessórios e estatísticas
    """
    parser = StepMultiPartParser(content)
    pecas, acessorios = parser.parse()
    
    return {
        'pecas': [p.to_dict() for p in pecas],
        'acessorios': [a.to_dict() for a in acessorios],
        'resumo': {
            'total_pecas': len(pecas),
            'total_acessorios': sum(a.quantidade for a in acessorios),
            'total_furos': sum(len(p.furos) for p in pecas)
        }
    }


def generate_report_txt(content: str, nome_projeto: str = "Projeto") -> str:
    """Gera relatório TXT com lista de corte"""
    parser = StepMultiPartParser(content)
    pecas, acessorios = parser.parse()
    
    txt_gen = TXTReportGenerator()
    return txt_gen.generate(pecas, acessorios, nome_projeto)


# Compatibilidade com endpoints antigos
parse_step = parse_step_multipart        


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        result = parse_step_multipart(content)
                
        print("\n📦 Detalhes das peças:")
        for p in result['pecas']:
            print(f"   - {p['nome']}: {p['largura']}x{p['comprimento']}x{p['espessura']}mm ({len(p['furos'])} furos)")
        
        if result['acessorios']:
            print("\n🔩 Acessórios:")
            for a in result['acessorios']:
                print(f"   - {a['nome']}: {a['quantidade']} un")
    else:
        print("Uso: python step_parser.py <arquivo.step>")