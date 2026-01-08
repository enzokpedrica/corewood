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
        
        # O mapeamento de eixos vai identificar qual dimensão é a espessura
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
            dim_x = abs(peca.x_max - peca.x_min)
            dim_y = abs(peca.y_max - peca.y_min)
            dim_z = abs(peca.z_max - peca.z_min)
            
            # Espessura é sempre a menor dimensão (15, 18, etc)
            dims = [(dim_x, 'x'), (dim_y, 'y'), (dim_z, 'z')]
            dims_sorted = sorted(dims, key=lambda d: d[0])

            eixo_espessura = dims_sorted[0][1]  # Menor = espessura
            esp_dim_valor = dims_sorted[0][0]

            # Pegar os dois eixos restantes (candidatos a comprimento/largura)
            eixos_restantes = [(d, e) for d, e in dims_sorted[1:]]

            # Buscar cilindros para detectar furos horizontais
            cilindros = self._find_cylinders_for_solid(solid_id)

            # Função para obter coordenada de um cilindro em um eixo específico
            def get_coord(cil, eixo):
                if eixo == 'x':
                    return cil['x'] - peca.x_min
                elif eixo == 'y':
                    return cil['y'] - peca.y_min
                else:
                    return cil['z'] - peca.z_min

            def get_dim(eixo):
                if eixo == 'x':
                    return dim_x
                elif eixo == 'y':
                    return dim_y
                else:
                    return dim_z

            # Contar furos horizontais em cada eixo candidato
            # Furos horizontais têm: coordenada na borda E z no meio da espessura
            z_meio = esp_dim_valor / 2
            tolerancia_borda = 2.0
            tolerancia_z = 3.0

            furos_por_eixo = {eixos_restantes[0][1]: 0, eixos_restantes[1][1]: 0}

            for cil in cilindros:
                # Verificar se Z está no meio (indicando furo horizontal)
                coord_esp = get_coord(cil, eixo_espessura)
                if abs(coord_esp - z_meio) > tolerancia_z:
                    continue  # Não é furo horizontal
                
                # Verificar em qual eixo está na borda
                for dim_valor, eixo in eixos_restantes:
                    coord = get_coord(cil, eixo)
                    dim_total = get_dim(eixo)
                    if coord <= tolerancia_borda or coord >= (dim_total - tolerancia_borda):
                        furos_por_eixo[eixo] += 1

            # Decidir comprimento/largura
            # Se há furos horizontais, o eixo COM MAIS furos na borda é provavelmente onde entram
            # os furos, então o OUTRO eixo é o comprimento (furos entram pela largura no MPR)
            eixo_a, eixo_b = eixos_restantes[0][1], eixos_restantes[1][1]
            dim_a, dim_b = eixos_restantes[0][0], eixos_restantes[1][0]

            if furos_por_eixo[eixo_a] > 0 or furos_por_eixo[eixo_b] > 0:
                # Tem furos horizontais - usar para determinar eixos
                if furos_por_eixo[eixo_a] > furos_por_eixo[eixo_b]:
                    # Eixo A tem mais furos na borda = é o COMPRIMENTO (no MPR, furos H entram por X)
                    eixo_comprimento = eixo_a
                    eixo_largura = eixo_b
                    #print(f"   📐 Eixos definidos por FUROS HORIZONTAIS: comp={eixo_comprimento}, larg={eixo_largura}")
                elif furos_por_eixo[eixo_b] > furos_por_eixo[eixo_a]:
                    eixo_comprimento = eixo_b
                    eixo_largura = eixo_a
                    #print(f"   📐 Eixos definidos por FUROS HORIZONTAIS: comp={eixo_comprimento}, larg={eixo_largura}")
                else:
                    # Empate - usar dimensão maior como comprimento
                    if dim_a >= dim_b:
                        eixo_comprimento = eixo_a
                        eixo_largura = eixo_b
                    else:
                        eixo_comprimento = eixo_b
                        eixo_largura = eixo_a
                    #print(f"   📐 Eixos definidos por DIMENSÃO (empate furos): comp={eixo_comprimento}, larg={eixo_largura}")
            else:
                # Sem furos horizontais - usar dimensão maior como comprimento (fallback)
                if dim_a >= dim_b:
                    eixo_comprimento = eixo_a
                    eixo_largura = eixo_b
                else:
                    eixo_comprimento = eixo_b
                    eixo_largura = eixo_a
            
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
                        
            # Função para obter coordenadas no sistema MPR
            def get_mpr_coords(cil):
                """Converte coordenadas STEP para sistema MPR (X=comprimento, Y=largura, Z=espessura)"""
                step_coords = {'x': cil['x'], 'y': cil['y'], 'z': cil['z']}
                
                mpr_comprimento = step_coords[eixo_comprimento] - comp_min
                mpr_largura = step_coords[eixo_largura] - larg_min
                mpr_espessura = step_coords[eixo_espessura] - esp_min
                
                return mpr_comprimento, mpr_largura, mpr_espessura
            
            # Primeiro passo: identificar furos horizontais e seus fundos
            furos_horizontais_coords = set()
            furos_horizontais_info = []  # Lista com info completa para calcular fundos

            for cil in cilindros:
                mpr_x, mpr_y, mpr_z = get_mpr_coords(cil)
                raio_round = round(cil['raio'], 2)
                x_round = round(mpr_x, 0)
                y_round = round(mpr_y, 0)
                
                # Verificar se Z está no meio (indicando furo horizontal)
                if abs(mpr_z - (esp_dim / 2)) > 3.0:
                    continue
                
                # Se está na borda Y (YP ou YM)
                if mpr_y <= 2.0:
                    furos_horizontais_coords.add((x_round, raio_round, 'YP'))
                    furos_horizontais_info.append({'eixo': 'Y', 'lado': 'YP', 'coord_fixa': x_round, 'raio': raio_round, 'borda': 0})
                elif mpr_y >= (larg_dim - 2.0):
                    furos_horizontais_coords.add((x_round, raio_round, 'YM'))
                    furos_horizontais_info.append({'eixo': 'Y', 'lado': 'YM', 'coord_fixa': x_round, 'raio': raio_round, 'borda': larg_dim})
                
                # Se está na borda X (XP ou XM)
                if mpr_x <= 2.0:
                    furos_horizontais_coords.add((y_round, raio_round, 'XP'))
                    furos_horizontais_info.append({'eixo': 'X', 'lado': 'XP', 'coord_fixa': y_round, 'raio': raio_round, 'borda': 0})
                elif mpr_x >= (comp_dim - 2.0):
                    furos_horizontais_coords.add((y_round, raio_round, 'XM'))
                    furos_horizontais_info.append({'eixo': 'X', 'lado': 'XM', 'coord_fixa': y_round, 'raio': raio_round, 'borda': comp_dim})

            # Função para verificar se um cilindro é fundo de furo horizontal
            def is_fundo_furo_horizontal(mpr_x, mpr_y, raio):
                raio_round = round(raio, 2)
                x_round = round(mpr_x, 0)
                y_round = round(mpr_y, 0)
                
                tolerancia_coord = 2.0  # Tolerância para coordenada fixa
                max_profundidade = 35.0  # Profundidade máxima de furo horizontal
                
                for info in furos_horizontais_info:
                    if round(info['raio'], 2) != raio_round:
                        continue
                    
                    if info['eixo'] == 'X':
                        # Furo entra por X, coord_fixa é Y
                        if abs(y_round - info['coord_fixa']) > tolerancia_coord:
                            continue
                        # Verificar se X está dentro da profundidade do furo
                        if info['lado'] == 'XP' and mpr_x > 0 and mpr_x <= max_profundidade:
                            return True
                        if info['lado'] == 'XM' and mpr_x < comp_dim and mpr_x >= (comp_dim - max_profundidade):
                            return True
                    
                    elif info['eixo'] == 'Y':
                        # Furo entra por Y, coord_fixa é X
                        if abs(x_round - info['coord_fixa']) > tolerancia_coord:
                            continue
                        # Verificar se Y está dentro da profundidade do furo
                        if info['lado'] == 'YP' and mpr_y > 0 and mpr_y <= max_profundidade:
                            return True
                        if info['lado'] == 'YM' and mpr_y < larg_dim and mpr_y >= (larg_dim - max_profundidade):
                            return True
                
                return False

            print(f"   🔍 Furos horizontais encontrados: {len(furos_horizontais_info)}")

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
                z_meio = esp_dim / 2
                tolerancia_z_meio = 3.0
                
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
                    if is_fundo_furo_horizontal(mpr_x, mpr_y, cil['raio']):
                        #print(f"      ⏭️ Ignorando fundo de furo H: X={x_round}, Y={y_round}, Ø{round(cil['raio']*2, 2)}")
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

# Compatibilidade com endpoints antigos
parse_step = parse_step_multipart        


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        result = parse_step_multipart(content)
                
    else:
        print("Uso: python step_parser.py <arquivo.step>")