"""
STEP Hole Parser para CoreWood
==============================
Extrai informações de furações de arquivos STEP.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


@dataclass
class Hole:
    """Representa um furo extraído do arquivo STEP."""
    diameter: float
    radius: float
    center_x: float
    center_y: float
    center_z: float
    depth: float
    axis: tuple = (0, 0, 1)
    is_through: bool = False


class StepParser:
    """Parser de arquivos STEP focado em extração de furações."""
    
    def __init__(self, content: str):
        self.content = content
        self.entities: dict = {}
        self._parse_entities()
    
    def _parse_entities(self):
        """Extrai todas as entidades do arquivo STEP."""
        data_section = re.search(r'DATA;(.+?)ENDSEC;', self.content, re.DOTALL)
        if not data_section:
            raise ValueError("Seção DATA não encontrada no arquivo STEP")
        
        data = data_section.group(1)
        data = data.replace('\n', ' ').replace('\r', '')
        
        pattern = r'#(\d+)\s*=\s*'
        starts = [(m.start(), m.end(), int(m.group(1))) for m in re.finditer(pattern, data)]
        
        for i, (start, content_start, entity_id) in enumerate(starts):
            paren_depth = 0
            end_pos = content_start
            
            while end_pos < len(data):
                char = data[end_pos]
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == ';' and paren_depth == 0:
                    break
                end_pos += 1
            
            entity_body = data[content_start:end_pos].strip()
            
            if entity_body.startswith('('):
                self.entities[entity_id] = {
                    'type': 'COMPLEX',
                    'raw': entity_body
                }
            else:
                type_match = re.match(r'(\w+)\s*\((.*)$', entity_body)
                if type_match:
                    entity_type = type_match.group(1)
                    params_str = type_match.group(2).rstrip(')')
                    self.entities[entity_id] = {
                        'type': entity_type,
                        'params': params_str,
                        'raw': entity_body
                    }
    
    def _get_entity(self, entity_id: int) -> Optional[dict]:
        return self.entities.get(entity_id)
    
    def _parse_cartesian_point(self, entity_id: int) -> Optional[tuple]:
        entity = self._get_entity(entity_id)
        if not entity or entity['type'] != 'CARTESIAN_POINT':
            return None
        
        raw = entity.get('raw', entity.get('params', ''))
        coords_match = re.search(r'\(\s*([-\d.E]+)\s*,\s*([-\d.E]+)\s*,\s*([-\d.E]+)\s*\)', raw)
        if coords_match:
            return (
                float(coords_match.group(1)),
                float(coords_match.group(2)),
                float(coords_match.group(3))
            )
        return None
    
    def _parse_direction(self, entity_id: int) -> Optional[tuple]:
        entity = self._get_entity(entity_id)
        if not entity or entity['type'] != 'DIRECTION':
            return None
        
        raw = entity.get('raw', entity.get('params', ''))
        dir_match = re.search(r'\(\s*([-\d.E]+)\s*,\s*([-\d.E]+)\s*,\s*([-\d.E]+)\s*\)', raw)
        if dir_match:
            return (
                float(dir_match.group(1)),
                float(dir_match.group(2)),
                float(dir_match.group(3))
            )
        return None
    
    def _parse_axis2_placement_3d(self, entity_id: int) -> Optional[dict]:
        entity = self._get_entity(entity_id)
        if not entity or entity['type'] != 'AXIS2_PLACEMENT_3D':
            return None
        
        raw = entity.get('raw', entity.get('params', ''))
        refs = re.findall(r'#(\d+)', raw)
        if len(refs) >= 1:
            point = self._parse_cartesian_point(int(refs[0]))
            direction = self._parse_direction(int(refs[1])) if len(refs) > 1 else (0, 0, 1)
            return {
                'location': point,
                'axis': direction
            }
        return None
    
    def _find_hole_depth(self, cylinder: dict) -> float:
        circles_z = []
        
        for entity_id, entity in self.entities.items():
            if entity.get('type') == 'CIRCLE':
                match = re.search(r"'[^']*'\s*,\s*#(\d+)\s*,\s*([-\d.E]+)", entity.get('raw', ''))
                if match:
                    radius = float(match.group(2))
                    if abs(radius - cylinder['radius']) < 0.001:
                        axis_id = int(match.group(1))
                        placement = self._parse_axis2_placement_3d(axis_id)
                        if placement and placement['location']:
                            circles_z.append(placement['location'][2])
        
        if len(circles_z) >= 2:
            return abs(max(circles_z) - min(circles_z))
        
        return 0.0
    
    def get_bounding_box(self) -> dict:
        all_points = []
        
        for entity_id, entity in self.entities.items():
            if entity.get('type') == 'CARTESIAN_POINT':
                point = self._parse_cartesian_point(entity_id)
                if point:
                    all_points.append(point)
        
        if not all_points:
            return {}
        
        x_coords = [p[0] for p in all_points]
        y_coords = [p[1] for p in all_points]
        z_coords = [p[2] for p in all_points]
        
        return {
            'x_min': min(x_coords),
            'x_max': max(x_coords),
            'y_min': min(y_coords),
            'y_max': max(y_coords),
            'z_min': min(z_coords),
            'z_max': max(z_coords),
            'width': max(x_coords) - min(x_coords),
            'height': max(y_coords) - min(y_coords),
            'thickness': max(z_coords) - min(z_coords)
        }
    
    def extract_holes(self) -> List[Hole]:
        holes = []
        bbox = self.get_bounding_box()
        x_offset = bbox.get('x_min', 0)
        y_offset = bbox.get('y_min', 0)
        
        for entity_id, entity in self.entities.items():
            if entity.get('type') == 'CYLINDRICAL_SURFACE':
                params = entity.get('raw', '')
                match = re.search(r"'[^']*'\s*,\s*#(\d+)\s*,\s*([-\d.E]+)", params)
                if match:
                    axis_id = int(match.group(1))
                    radius = float(match.group(2))
                    
                    placement = self._parse_axis2_placement_3d(axis_id)
                    if placement and placement['location']:
                        cylinder = {'radius': radius, 'location': placement['location']}
                        depth = self._find_hole_depth(cylinder)
                        
                        hole = Hole(
                            diameter=radius * 2,
                            radius=radius,
                            center_x=placement['location'][0] - x_offset,
                            center_y=placement['location'][1] - y_offset,
                            center_z=placement['location'][2],
                            depth=depth,
                            axis=placement['axis'] or (0, 0, 1),
                            is_through=(depth == 0)
                        )
                        holes.append(hole)
        
        return holes
    
    def to_corewood_format(self) -> dict:
        """Retorna dados no formato CoreWood."""
        holes = self.extract_holes()
        bbox = self.get_bounding_box()
        
        drilling_data = []
        for i, hole in enumerate(holes, 1):
            drilling_data.append({
                'id': i,
                'x': round(hole.center_x, 2),
                'y': round(hole.center_y, 2),
                'z': round(hole.center_z, 2),
                'diameter': round(hole.diameter, 2),
                'depth': round(hole.depth, 2),
                'face': self._determine_face(hole, bbox)
            })
        
        return {
            'part': {
                'width': round(bbox.get('width', 0), 2),
                'height': round(bbox.get('height', 0), 2),
                'thickness': round(bbox.get('thickness', 0), 2)
            },
            'drilling': drilling_data
        }
    
    def _determine_face(self, hole: Hole, bbox: dict) -> str:
        thickness = bbox.get('thickness', 0)
        z_max = bbox.get('z_max', 0)
        z_min = bbox.get('z_min', 0)
        
        if abs(hole.axis[2]) > 0.9:
            if hole.center_z >= z_max - 0.1:
                return 'TOP'
            elif hole.center_z <= z_min + 0.1:
                return 'BOTTOM'
        
        if abs(hole.axis[0]) > 0.9:
            return 'SIDE_X'
        if abs(hole.axis[1]) > 0.9:
            return 'SIDE_Y'
        
        return 'UNKNOWN'


def parse_step(content: str) -> dict:
    """
    Função principal para parse de arquivo STEP.
    
    Args:
        content: Conteúdo do arquivo STEP como string
        
    Returns:
        Dicionário no formato CoreWood
    """
    parser = StepParser(content)
    return parser.to_corewood_format()