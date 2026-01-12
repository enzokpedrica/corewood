"""
Parser STEP usando pythonOCC para CoreWood
- Leitura robusta de arquivos STEP
- Detecção precisa de furos (cilindros)
- Identificação de furos verticais e horizontais
"""

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.TopoDS import topods
from OCC.Core.gp import gp_Pnt, gp_Dir
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import math


@dataclass
class Furo:
    """Representa um furo detectado"""
    id: int
    x: float
    y: float
    z: float
    diametro: float
    profundidade: float = 15.0
    tipo: str = "vertical"  # vertical ou horizontal
    lado: str = "LS"  # LS, LSU, XP, XM, YP, YM
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'x': round(self.x, 2),
            'y': round(self.y, 2),
            'z': round(self.z, 2),
            'diametro': round(self.diametro, 2),
            'profundidade': round(self.profundidade, 2),
            'tipo': self.tipo,
            'lado': self.lado
        }


@dataclass
class Peca:
    """Representa uma peça extraída do STEP"""
    nome: str
    comprimento: float = 0
    largura: float = 0
    espessura: float = 0
    furos: List[Furo] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'nome': self.nome,
            'comprimento': round(self.comprimento, 2),
            'largura': round(self.largura, 2),
            'espessura': round(self.espessura, 2),
            'furos': [f.to_dict() for f in self.furos]
        }


class StepParserOCC:
    """Parser STEP usando pythonOCC"""
    
    def __init__(self, filepath: str = None, content: str = None):
        self.filepath = filepath
        self.content = content
        self.shape = None
        self.pecas: List[Peca] = []
        
    def load(self) -> bool:
        """Carrega o arquivo STEP"""
        reader = STEPControl_Reader()
        
        if self.filepath:
            status = reader.ReadFile(self.filepath)
        else:
            # Para conteúdo em string, precisa salvar temporariamente
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.step', delete=False) as f:
                f.write(self.content)
                temp_path = f.name
            status = reader.ReadFile(temp_path)
            os.unlink(temp_path)
        
        if status != 1:  # IFSelect_RetDone
            print(f"❌ Erro ao ler arquivo STEP: status {status}")
            return False
        
        reader.TransferRoots()
        self.shape = reader.OneShape()
        print(f"✅ STEP carregado com sucesso")
        return True
    
    def _get_bounding_box(self, shape) -> Tuple[float, float, float, float, float, float]:
        """Calcula bounding box de um shape"""
        bbox = Bnd_Box()
        brepbndlib.Add(shape, bbox)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
        return xmin, ymin, zmin, xmax, ymax, zmax
    
    def _get_dimensions(self, shape) -> Tuple[float, float, float]:
        """Retorna (comprimento, largura, espessura) ordenados"""
        xmin, ymin, zmin, xmax, ymax, zmax = self._get_bounding_box(shape)
        
        dim_x = abs(xmax - xmin)
        dim_y = abs(ymax - ymin)
        dim_z = abs(zmax - zmin)
        
        # Ordenar: maior = comprimento, médio = largura, menor = espessura
        dims = sorted([dim_x, dim_y, dim_z], reverse=True)
        return dims[0], dims[1], dims[2]
    
    def _find_cylinders(self, shape) -> List[Dict]:
        """Encontra todas as faces cilíndricas (furos)"""
        cylinders = []
        
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        while explorer.More():
            face = topods.Face(explorer.Current())
            
            try:
                surface = BRepAdaptor_Surface(face)
                
                if surface.GetType() == GeomAbs_Cylinder:
                    cylinder = surface.Cylinder()
                    
                    # Extrair informações do cilindro
                    location = cylinder.Location()
                    axis = cylinder.Axis().Direction()
                    radius = cylinder.Radius()
                    
                    # Calcular centro e direção
                    cylinders.append({
                        'x': location.X(),
                        'y': location.Y(),
                        'z': location.Z(),
                        'radius': radius,
                        'dir_x': axis.X(),
                        'dir_y': axis.Y(),
                        'dir_z': axis.Z()
                    })
            except Exception as e:
                pass  # Ignorar faces que não podem ser analisadas
            
            explorer.Next()
        
        return cylinders
    
    def _classify_hole(self, cyl: Dict, dims: Tuple[float, float, float], 
                       bbox: Tuple[float, float, float, float, float, float]) -> Optional[Furo]:
        """Classifica um cilindro como furo vertical ou horizontal"""
        
        xmin, ymin, zmin, xmax, ymax, zmax = bbox
        comprimento, largura, espessura = dims
        
        dir_x = abs(cyl['dir_x'])
        dir_y = abs(cyl['dir_y'])
        dir_z = abs(cyl['dir_z'])
        
        diametro = cyl['radius'] * 2
        
        # Tolerâncias
        tol_dir = 0.7  # Tolerância para direção (aumentada)
        tol_borda = 5.0  # Tolerância para considerar na borda
        
        # Coordenadas relativas ao bounding box
        rel_x = cyl['x'] - xmin
        rel_y = cyl['y'] - ymin
        rel_z = cyl['z'] - zmin
        
        dim_x = xmax - xmin
        dim_y = ymax - ymin
        dim_z = zmax - zmin
        
        # Determinar qual eixo é qual dimensão
        # Mapear eixos para comprimento/largura/espessura
        dims_map = [
            (dim_x, 'x', rel_x, dir_x),
            (dim_y, 'y', rel_y, dir_y),
            (dim_z, 'z', rel_z, dir_z)
        ]
        dims_sorted = sorted(dims_map, key=lambda d: d[0], reverse=True)
        
        eixo_comp = dims_sorted[0][1]
        eixo_larg = dims_sorted[1][1]
        eixo_esp = dims_sorted[2][1]
        
        # Coordenadas no sistema MPR
        def get_coord(eixo):
            if eixo == 'x': return rel_x
            if eixo == 'y': return rel_y
            return rel_z
        
        def get_dim(eixo):
            if eixo == 'x': return dim_x
            if eixo == 'y': return dim_y
            return dim_z
        
        def get_dir(eixo):
            if eixo == 'x': return dir_x
            if eixo == 'y': return dir_y
            return dir_z
        
        mpr_x = get_coord(eixo_comp)  # X = comprimento
        mpr_y = get_coord(eixo_larg)  # Y = largura
        mpr_z = get_coord(eixo_esp)   # Z = espessura
        
        comp_total = get_dim(eixo_comp)
        larg_total = get_dim(eixo_larg)
        esp_total = get_dim(eixo_esp)
        
        # Verificar direção do cilindro
        dir_comp = get_dir(eixo_comp)
        dir_larg = get_dir(eixo_larg)
        dir_esp = get_dir(eixo_esp)
        
        # Encontrar a direção dominante
        max_dir = max(dir_comp, dir_larg, dir_esp)
        
        # FURO VERTICAL: direção paralela ao eixo da espessura
        if dir_esp == max_dir and dir_esp > tol_dir:
            # É um furo vertical
            # LS = furo de cima pra baixo (Z perto do topo)
            # LSU = furo de baixo pra cima (Z perto da base)
            lado = 'LS' if mpr_z > esp_total / 2 else 'LSU'
            
            return Furo(
                id=0,
                x=mpr_x,
                y=mpr_y,
                z=mpr_z,
                diametro=diametro,
                profundidade=0 if diametro <= 6 else 11.0,
                tipo='vertical',
                lado=lado
            )
        
        # FURO HORIZONTAL na direção do comprimento (XP ou XM)
        elif dir_comp == max_dir and dir_comp > tol_dir:
            # Verificar se Z está no meio da espessura (furo horizontal típico)
            z_meio = esp_total / 2
            if abs(mpr_z - z_meio) > esp_total * 0.4:
                return None  # Z muito longe do meio, provavelmente não é furo H
            
            # Furo entra pela face do comprimento (XP ou XM)
            if mpr_x <= tol_borda:
                lado = 'XP'
                x_final = 0
            elif mpr_x >= comp_total - tol_borda:
                lado = 'XM'
                x_final = comp_total
            else:
                return None  # Não está na borda
            
            return Furo(
                id=0,
                x=x_final,
                y=mpr_y,
                z=mpr_z,
                diametro=diametro,
                profundidade=22.0,
                tipo='horizontal',
                lado=lado
            )
        
        # FURO HORIZONTAL na direção da largura (YP ou YM)
        elif dir_larg == max_dir and dir_larg > tol_dir:
            # Verificar se Z está no meio da espessura
            z_meio = esp_total / 2
            if abs(mpr_z - z_meio) > esp_total * 0.4:
                return None
            
            # Furo entra pela face da largura (YP ou YM)
            if mpr_y <= tol_borda:
                lado = 'YP'
                y_final = 0
            elif mpr_y >= larg_total - tol_borda:
                lado = 'YM'
                y_final = larg_total
            else:
                return None  # Não está na borda
            
            return Furo(
                id=0,
                x=mpr_x,
                y=y_final,
                z=mpr_z,
                diametro=diametro,
                profundidade=22.0,
                tipo='horizontal',
                lado=lado
            )
        
        return None
    
    def _remove_duplicates(self, furos: List[Furo]) -> List[Furo]:
        """Remove furos duplicados (mesmo local e diâmetro)"""
        unique = []
        seen = set()
        
        for furo in furos:
            # Criar chave única baseada em posição arredondada e diâmetro
            key = (
                round(furo.x, 0),
                round(furo.y, 0),
                round(furo.diametro, 1),
                furo.tipo,
                furo.lado
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(furo)
        
        return unique
    
    def parse(self) -> List[Peca]:
        """Processa o STEP e extrai peças com furos"""
        
        if not self.shape:
            if not self.load():
                return []
        
        # Explorar sólidos
        explorer = TopExp_Explorer(self.shape, TopAbs_SOLID)
        solid_count = 0
        
        while explorer.More():
            solid = topods.Solid(explorer.Current())
            solid_count += 1
            
            # Calcular dimensões
            bbox = self._get_bounding_box(solid)
            dims = self._get_dimensions(solid)
            
            # Filtrar bordas e peças muito finas (espessura < 1mm)
            if dims[2] < 1.0:
                print(f"\n⏭️ Peca_{solid_count}: Ignorada (borda/fita - espessura {dims[2]:.2f}mm)")
                explorer.Next()
                continue
            
            # Nome da peça
            nome = f"Peca_{solid_count}"
            
            peca = Peca(
                nome=nome,
                comprimento=dims[0],
                largura=dims[1],
                espessura=dims[2]
            )
            
            print(f"\n📦 {nome}: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")
            
            # Encontrar cilindros (furos)
            cylinders = self._find_cylinders(solid)
            print(f"   🔍 Cilindros encontrados: {len(cylinders)}")
            
            # Classificar cada cilindro
            furos = []
            for cyl in cylinders:
                furo = self._classify_hole(cyl, dims, bbox)
                if furo:
                    furos.append(furo)
            
            # Remover duplicados
            furos = self._remove_duplicates(furos)
            
            # Atribuir IDs
            for i, furo in enumerate(furos, 1):
                furo.id = i
            
            peca.furos = furos
            
            v_count = len([f for f in furos if f.tipo == 'vertical'])
            h_count = len([f for f in furos if f.tipo == 'horizontal'])
            print(f"   ✅ Furos detectados: {v_count} verticais, {h_count} horizontais")
            
            self.pecas.append(peca)
            explorer.Next()
        
        print(f"\n📊 Total: {len(self.pecas)} peça(s) processada(s)")
        return self.pecas
    
    def to_dict(self) -> Dict[str, Any]:
        """Retorna resultado em formato JSON"""
        return {
            'pecas': [p.to_dict() for p in self.pecas],
            'resumo': {
                'total_pecas': len(self.pecas),
                'total_furos': sum(len(p.furos) for p in self.pecas)
            }
        }


def parse_step_occ(filepath: str = None, content: str = None) -> Dict[str, Any]:
    """
    Função principal para integração com FastAPI
    """
    parser = StepParserOCC(filepath=filepath, content=content)
    parser.parse()
    return parser.to_dict()


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) > 1:
        result = parse_step_occ(filepath=sys.argv[1])
        print("\n" + "=" * 60)
        print("RESULTADO JSON:")
        print("=" * 60)
        print(json.dumps(result, indent=2))
    else:
        print("Uso: python step_parser_occ.py <arquivo.step>")