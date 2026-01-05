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
        """Calcula bounding box de um sólido"""
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
            if self._is_acessorio(nome):
                if nome not in acessorios_count:
                    acessorios_count[nome] = 0
                acessorios_count[nome] += 1
                continue
            
            bbox = self._calculate_bounding_box(solid_id)
            
            peca = Peca(
                nome=nome,
                entity_id=solid_id,
                x_min=bbox[0], x_max=bbox[1],
                y_min=bbox[2], y_max=bbox[3],
                z_min=bbox[4], z_max=bbox[5]
            )
            
            # Dimensões brutas do bounding box
            dim_x = abs(peca.x_max - peca.x_min)  # Comprimento
            dim_y = abs(peca.y_max - peca.y_min)  # Largura
            dim_z = abs(peca.z_max - peca.z_min)  # Espessura
            
            cilindros = self._find_cylinders_for_solid(solid_id)
            
            # Primeiro passo: identificar furos horizontais (nas bordas X)
            furos_horizontais_coords = set()
            
            for cil in cilindros:
                x_rel = cil['x'] - peca.x_min
                y_round = round(cil['y'], 0)
                raio_round = round(cil['raio'], 2)
                
                # Se está na borda X (entrada do furo horizontal)
                if x_rel <= 2.0 or x_rel >= (dim_x - 2.0):
                    furos_horizontais_coords.add((y_round, raio_round))
            
            # Segundo passo: filtrar cilindros
            cilindros_unicos = []
            coords_vistas = set()

            for cil in cilindros:
                # NOVO: Ignorar cilindros fora do bounding box da peça
                margem = 5.0  # Tolerância de 5mm
                if (cil['z'] < peca.z_min - margem or cil['z'] > peca.z_max + margem):
                    continue  # Cilindro fora da peça no eixo Z
                if (cil['x'] < peca.x_min - margem or cil['x'] > peca.x_max + margem):
                    continue  # Cilindro fora da peça no eixo X
                if (cil['y'] < peca.y_min - margem or cil['y'] > peca.y_max + margem):
                    continue  # Cilindro fora da peça no eixo Y

                # DEBUG - Adicione isto:
                print(f"🔍 Cilindro: X={cil['x']}, Y={cil['y']}, Z={cil['z']}, R={cil['raio']}")
                print(f"   Peça bounds: X=[{peca.x_min}, {peca.x_max}], Y=[{peca.y_min}, {peca.y_max}], Z=[{peca.z_min}, {peca.z_max}]")
                
                x_rel = cil['x'] - peca.x_min
                y_round = round(cil['y'], 0)
                z_round = round(cil['z'], 0)
                raio_round = round(cil['raio'], 2)
                
                # Se está na borda X = é entrada de furo horizontal
                if x_rel <= 2.0 or x_rel >= (dim_x - 2.0):
                    key = ('H', y_round, raio_round, 'XP' if x_rel <= 2.0 else 'XM')
                    if key not in coords_vistas:
                        coords_vistas.add(key)
                        cilindros_unicos.append(cil)
                else:
                    # Verificar se é fundo de furo horizontal (mesmo Y e raio)
                    if (y_round, raio_round) in furos_horizontais_coords:
                        # É o fundo de um furo horizontal - IGNORAR
                        continue
                    
                    # Furo vertical legítimo
                    key = ('V', y_round, raio_round)
                    if key not in coords_vistas:
                        coords_vistas.add(key)
                        cilindros_unicos.append(cil)

            furo_id = 1
            for cil in cilindros_unicos:
                x_rel = round(cil['x'] - peca.x_min, 2)
                y_rel = round(cil['y'] - peca.y_min, 2)
                z_rel = round(cil['z'] - peca.z_min, 2)
                
                diametro = round(cil['raio'] * 2, 2)

                tolerancia = 2.0
                
                # Distâncias das faces
                dist_comp_min = x_rel
                dist_comp_max = dim_x - x_rel
                dist_larg_min = y_rel
                dist_larg_max = dim_y - y_rel
                dist_esp_inf = z_rel
                dist_esp_sup = dim_z - z_rel
                
                # Encontrar a menor distância para classificar o furo
                min_dist = min(dist_esp_inf, dist_esp_sup, dist_larg_min, dist_larg_max, dist_comp_min, dist_comp_max)
                
                if min_dist > tolerancia:
                    # Furo não está perto de nenhuma face - provavelmente é vertical no meio
                    tipo = 'vertical'
                    lado = 'LS'
                    profundidade = 0 if diametro <= 6 else 11.0
                    mpr_x = x_rel
                    mpr_y = y_rel
                    mpr_z = z_rel
                    
                elif dist_esp_inf <= tolerancia or dist_esp_sup <= tolerancia:
                    # Furo VERTICAL - entra pela face superior ou inferior
                    tipo = 'vertical'
                    lado = 'LS' if dist_esp_sup <= tolerancia else 'LI'
                    profundidade = 0 if diametro <= 6 else 11.0
                    mpr_x = x_rel
                    mpr_y = y_rel
                    mpr_z = round(dim_z / 2, 1)
                    
                elif dist_larg_min <= tolerancia:
                    # Furo HORIZONTAL - entra pela lateral Y=0
                    tipo = 'horizontal'
                    lado = 'YP'
                    profundidade = 22.0
                    mpr_x = x_rel
                    mpr_y = 0
                    mpr_z = z_rel
                    
                elif dist_larg_max <= tolerancia:
                    # Furo HORIZONTAL - entra pela lateral Y=max
                    tipo = 'horizontal'
                    lado = 'YM'
                    profundidade = 22.0
                    mpr_x = x_rel
                    mpr_y = dim_y
                    mpr_z = z_rel
                    
                elif dist_comp_min <= tolerancia:
                    # Furo HORIZONTAL - entra pela frente X=0
                    tipo = 'horizontal'
                    lado = 'XP'
                    profundidade = 22.0
                    mpr_x = 0
                    mpr_y = y_rel
                    mpr_z = z_rel
                    
                elif dist_comp_max <= tolerancia:
                    # Furo HORIZONTAL - entra pela traseira X=max
                    tipo = 'horizontal'
                    lado = 'XM'
                    profundidade = 22.0
                    mpr_x = dim_x
                    mpr_y = y_rel
                    mpr_z = z_rel
                
                else:
                    # Fallback - assumir vertical
                    tipo = 'vertical'
                    lado = 'LS'
                    profundidade = 0 if diametro <= 6 else 11.0
                    mpr_x = x_rel
                    mpr_y = y_rel
                    mpr_z = z_rel
                
                furo = Furo(
                    id=furo_id,
                    x=mpr_x,
                    y=mpr_y,
                    z=mpr_z,
                    diametro=diametro,
                    profundidade=profundidade,
                    face='superior' if tipo == 'vertical' else lado,
                    tipo=tipo,
                    lado=lado
                )
                peca.furos.append(furo)
                furo_id += 1
            
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
        
        print(f"\n✅ Processamento concluído!")
        print(f"   Peças: {result['resumo']['total_pecas']}")
        print(f"   Acessórios: {result['resumo']['total_acessorios']}")
        print(f"   Furos: {result['resumo']['total_furos']}")
        
        print("\n📦 Detalhes das peças:")
        for p in result['pecas']:
            print(f"   - {p['nome']}: {p['largura']}x{p['comprimento']}x{p['espessura']}mm ({len(p['furos'])} furos)")
        
        if result['acessorios']:
            print("\n🔩 Acessórios:")
            for a in result['acessorios']:
                print(f"   - {a['nome']}: {a['quantidade']} un")
    else:
        print("Uso: python step_parser.py <arquivo.step>")