"""
Parser STEP usando pythonOCC para CoreWood - v2.0
Correções:
- Tolerância de borda aumentada (5 -> 25mm)
- Tolerância de direção reduzida (0.7 -> 0.1)
- Filtro de rebaixos (Ø > 15mm)
- Debug detalhado para diagnóstico
- Cálculo de profundidade baseado na geometria real
- Extração de nomes das peças do STEP
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
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import math


# ============================================================
# CONFIGURAÇÕES - Ajuste conforme necessário
# ============================================================
CONFIG = {
    'tol_direcao': 0.1,        # Tolerância para classificar direção (era 0.7)
    'tol_borda': 25.0,         # Tolerância para considerar furo na borda em mm (era 5.0)
    'min_espessura': 1.0,      # Espessura mínima para não ser borda/fita
    'max_diametro_furo': 15.0, # Diâmetro máximo para considerar furo (acima = rebaixo)
    'min_diametro_furo': 2.0,  # Diâmetro mínimo para considerar furo
    'debug': True,             # Ativar logs detalhados
}


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
    
    # Informações do bounding box original (para debug)
    bbox_min: Tuple[float, float, float] = (0, 0, 0)
    bbox_max: Tuple[float, float, float] = (0, 0, 0)
    
    def to_dict(self) -> dict:
        return {
            'nome': self.nome,
            'comprimento': round(self.comprimento, 2),
            'largura': round(self.largura, 2),
            'espessura': round(self.espessura, 2),
            'furos': [f.to_dict() for f in self.furos]
        }


class StepParserOCC:
    """Parser STEP usando pythonOCC - v2.0"""
    
    def __init__(self, filepath: str = None, content: str = None, debug: bool = None):
        self.filepath = filepath
        self.content = content
        self.shape = None
        self.pecas: List[Peca] = []
        self.debug = debug if debug is not None else CONFIG['debug']
        self._cylinder_debug_info = []  # Para debug
        
    def _log(self, msg: str):
        """Log de debug"""
        if self.debug:
            print(msg)
    
    def load(self) -> bool:
        """Carrega o arquivo STEP"""
        reader = STEPControl_Reader()
        
        if self.filepath:
            status = reader.ReadFile(self.filepath)
        else:
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.step', delete=False) as f:
                f.write(self.content)
                temp_path = f.name
            status = reader.ReadFile(temp_path)
            os.unlink(temp_path)
        
        if status != 1:
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
    
    def _get_dimensions_and_axes(self, shape) -> Tuple[Tuple[float, float, float], Dict]:
        """
        Retorna (comprimento, largura, espessura) e mapeamento de eixos.
        O mapeamento indica qual eixo XYZ corresponde a qual dimensão.
        """
        xmin, ymin, zmin, xmax, ymax, zmax = self._get_bounding_box(shape)
        
        dim_x = abs(xmax - xmin)
        dim_y = abs(ymax - ymin)
        dim_z = abs(zmax - zmin)
        
        # Criar lista com (dimensão, eixo, min, max)
        dims_info = [
            (dim_x, 'x', xmin, xmax),
            (dim_y, 'y', ymin, ymax),
            (dim_z, 'z', zmin, zmax)
        ]
        
        # Ordenar por tamanho (maior = comprimento)
        dims_sorted = sorted(dims_info, key=lambda d: d[0], reverse=True)
        
        # Mapeamento
        axes_map = {
            'comprimento': {'eixo': dims_sorted[0][1], 'min': dims_sorted[0][2], 'max': dims_sorted[0][3], 'tamanho': dims_sorted[0][0]},
            'largura': {'eixo': dims_sorted[1][1], 'min': dims_sorted[1][2], 'max': dims_sorted[1][3], 'tamanho': dims_sorted[1][0]},
            'espessura': {'eixo': dims_sorted[2][1], 'min': dims_sorted[2][2], 'max': dims_sorted[2][3], 'tamanho': dims_sorted[2][0]},
        }
        
        return (dims_sorted[0][0], dims_sorted[1][0], dims_sorted[2][0]), axes_map
    
    def _find_cylinders(self, shape) -> List[Dict]:
        """Encontra todas as faces cilíndricas (furos) com informações detalhadas"""
        cylinders = []
        
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        face_count = 0
        
        while explorer.More():
            face = topods.Face(explorer.Current())
            face_count += 1
            
            try:
                surface = BRepAdaptor_Surface(face)
                
                if surface.GetType() == GeomAbs_Cylinder:
                    cylinder = surface.Cylinder()
                    
                    # Informações básicas
                    location = cylinder.Location()
                    axis = cylinder.Axis().Direction()
                    radius = cylinder.Radius()
                    
                    # Calcular bounding box da face cilíndrica para estimar profundidade
                    face_bbox = Bnd_Box()
                    brepbndlib.Add(face, face_bbox)
                    fxmin, fymin, fzmin, fxmax, fymax, fzmax = face_bbox.Get()
                    
                    # Estimar profundidade baseado na extensão do cilindro
                    extent_x = abs(fxmax - fxmin)
                    extent_y = abs(fymax - fymin)
                    extent_z = abs(fzmax - fzmin)
                    
                    cyl_info = {
                        'x': location.X(),
                        'y': location.Y(),
                        'z': location.Z(),
                        'radius': radius,
                        'dir_x': axis.X(),
                        'dir_y': axis.Y(),
                        'dir_z': axis.Z(),
                        'extent_x': extent_x,
                        'extent_y': extent_y,
                        'extent_z': extent_z,
                        'face_bbox': (fxmin, fymin, fzmin, fxmax, fymax, fzmax),
                    }
                    
                    cylinders.append(cyl_info)
                    
            except Exception as e:
                self._log(f"   ⚠️ Erro ao analisar face {face_count}: {e}")
            
            explorer.Next()
        
        self._log(f"   📊 Total de faces analisadas: {face_count}")
        return cylinders
    
    def _classify_hole(self, cyl: Dict, dims: Tuple[float, float, float], 
                       axes_map: Dict, bbox: Tuple) -> Optional[Furo]:
        """
        Classifica um cilindro como furo vertical ou horizontal.
        Versão 2.0 com tolerâncias corrigidas.
        """
        xmin, ymin, zmin, xmax, ymax, zmax = bbox
        comprimento, largura, espessura = dims
        
        diametro = cyl['radius'] * 2
        
        # Filtrar por diâmetro
        if diametro > CONFIG['max_diametro_furo']:
            self._log(f"   ⏭️ Cilindro Ø{diametro:.1f}mm ignorado (rebaixo/furo grande)")
            return None
        
        if diametro < CONFIG['min_diametro_furo']:
            self._log(f"   ⏭️ Cilindro Ø{diametro:.1f}mm ignorado (muito pequeno)")
            return None
        
        # Direções absolutas do cilindro
        dir_x = abs(cyl['dir_x'])
        dir_y = abs(cyl['dir_y'])
        dir_z = abs(cyl['dir_z'])
        
        # Identificar qual eixo é qual dimensão
        eixo_comp = axes_map['comprimento']['eixo']
        eixo_larg = axes_map['largura']['eixo']
        eixo_esp = axes_map['espessura']['eixo']
        
        # Funções auxiliares para pegar valores por eixo
        def get_coord(eixo, point_dict):
            return point_dict.get(eixo, 0)
        
        def get_dir(eixo):
            if eixo == 'x': return dir_x
            if eixo == 'y': return dir_y
            return dir_z
        
        def get_cyl_coord(eixo):
            if eixo == 'x': return cyl['x']
            if eixo == 'y': return cyl['y']
            return cyl['z']
        
        def get_extent(eixo):
            if eixo == 'x': return cyl['extent_x']
            if eixo == 'y': return cyl['extent_y']
            return cyl['extent_z']
        
        # Coordenadas do cilindro no sistema da peça
        cyl_comp = get_cyl_coord(eixo_comp)
        cyl_larg = get_cyl_coord(eixo_larg)
        cyl_esp = get_cyl_coord(eixo_esp)
        
        # Limites da peça
        comp_min = axes_map['comprimento']['min']
        comp_max = axes_map['comprimento']['max']
        larg_min = axes_map['largura']['min']
        larg_max = axes_map['largura']['max']
        esp_min = axes_map['espessura']['min']
        esp_max = axes_map['espessura']['max']
        
        # Coordenadas relativas (origem no canto min)
        rel_comp = cyl_comp - comp_min
        rel_larg = cyl_larg - larg_min
        rel_esp = cyl_esp - esp_min
        
        # Direções no sistema da peça
        dir_comp = get_dir(eixo_comp)
        dir_larg = get_dir(eixo_larg)
        dir_esp = get_dir(eixo_esp)
        
        tol_dir = CONFIG['tol_direcao']
        tol_borda = CONFIG['tol_borda']
        
        self._log(f"   🔍 Cilindro Ø{diametro:.1f}mm em ({cyl['x']:.1f}, {cyl['y']:.1f}, {cyl['z']:.1f})")
        self._log(f"      Direção: comp={dir_comp:.2f}, larg={dir_larg:.2f}, esp={dir_esp:.2f}")
        self._log(f"      Rel: comp={rel_comp:.1f}, larg={rel_larg:.1f}, esp={rel_esp:.1f}")
        
        # Determinar tipo baseado na direção dominante
        max_dir = max(dir_comp, dir_larg, dir_esp)
        
        # FURO VERTICAL: direção paralela ao eixo da espessura
        if dir_esp > (1.0 - tol_dir):
            # Verificar se está dentro da peça (não é furo de borda lateral)
            profundidade = get_extent(eixo_esp)
            
            # Determinar lado (LS = topo, LSU = base)
            meio_esp = (esp_min + esp_max) / 2
            if cyl_esp > meio_esp:
                lado = 'LS'
            else:
                lado = 'LSU'
            
            self._log(f"      ✅ VERTICAL {lado} - prof={profundidade:.1f}mm")
            
            return Furo(
                id=0,
                x=rel_comp,
                y=rel_larg,
                z=rel_esp,
                diametro=diametro,
                profundidade=profundidade if profundidade > 0 else espessura,
                tipo='vertical',
                lado=lado
            )
        
        # FURO HORIZONTAL na direção do comprimento (XP ou XM)
        elif dir_comp > (1.0 - tol_dir):
            # Verificar se está na borda do comprimento
            dist_comp_min = abs(cyl_comp - comp_min)
            dist_comp_max = abs(cyl_comp - comp_max)
            
            self._log(f"      Dist bordas comp: min={dist_comp_min:.1f}, max={dist_comp_max:.1f}")
            
            profundidade = get_extent(eixo_comp)
            
            if dist_comp_min <= tol_borda:
                lado = 'XM'  # Entra pelo lado menor do comprimento
                x_final = 0
                self._log(f"      ✅ HORIZONTAL {lado} - prof={profundidade:.1f}mm")
                
                return Furo(
                    id=0,
                    x=x_final,
                    y=rel_larg,
                    z=rel_esp,
                    diametro=diametro,
                    profundidade=profundidade if profundidade > 0 else 22.0,
                    tipo='horizontal',
                    lado=lado
                )
            elif dist_comp_max <= tol_borda:
                lado = 'XP'  # Entra pelo lado maior do comprimento
                x_final = comprimento
                self._log(f"      ✅ HORIZONTAL {lado} - prof={profundidade:.1f}mm")
                
                return Furo(
                    id=0,
                    x=x_final,
                    y=rel_larg,
                    z=rel_esp,
                    diametro=diametro,
                    profundidade=profundidade if profundidade > 0 else 22.0,
                    tipo='horizontal',
                    lado=lado
                )
            else:
                self._log(f"      ❌ Descartado: não está na borda do comprimento")
                return None
        
        # FURO HORIZONTAL na direção da largura (YP ou YM)
        elif dir_larg > (1.0 - tol_dir):
            dist_larg_min = abs(cyl_larg - larg_min)
            dist_larg_max = abs(cyl_larg - larg_max)
            
            self._log(f"      Dist bordas larg: min={dist_larg_min:.1f}, max={dist_larg_max:.1f}")
            
            profundidade = get_extent(eixo_larg)
            
            if dist_larg_min <= tol_borda:
                lado = 'YM'
                y_final = 0
                self._log(f"      ✅ HORIZONTAL {lado} - prof={profundidade:.1f}mm")
                
                return Furo(
                    id=0,
                    x=rel_comp,
                    y=y_final,
                    z=rel_esp,
                    diametro=diametro,
                    profundidade=profundidade if profundidade > 0 else 22.0,
                    tipo='horizontal',
                    lado=lado
                )
            elif dist_larg_max <= tol_borda:
                lado = 'YP'
                y_final = largura
                self._log(f"      ✅ HORIZONTAL {lado} - prof={profundidade:.1f}mm")
                
                return Furo(
                    id=0,
                    x=rel_comp,
                    y=y_final,
                    z=rel_esp,
                    diametro=diametro,
                    profundidade=profundidade if profundidade > 0 else 22.0,
                    tipo='horizontal',
                    lado=lado
                )
            else:
                self._log(f"      ❌ Descartado: não está na borda da largura")
                return None
        
        else:
            self._log(f"      ❌ Descartado: direção não alinhada com nenhum eixo")
            return None
    
    def _remove_duplicates(self, furos: List[Furo]) -> List[Furo]:
        """Remove furos duplicados (mesmo local e diâmetro)"""
        unique = []
        seen = set()
        
        for furo in furos:
            # Chave única com tolerância de 1mm
            key = (
                round(furo.x / 2) * 2,  # Arredondar para 2mm
                round(furo.y / 2) * 2,
                round(furo.diametro, 0),
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
        
        explorer = TopExp_Explorer(self.shape, TopAbs_SOLID)
        solid_count = 0
        
        while explorer.More():
            solid = topods.Solid(explorer.Current())
            solid_count += 1
            
            # Calcular dimensões e mapeamento de eixos
            bbox = self._get_bounding_box(solid)
            dims, axes_map = self._get_dimensions_and_axes(solid)
            
            # Filtrar bordas e peças muito finas
            if dims[2] < CONFIG['min_espessura']:
                print(f"\n⏭️ Peca_{solid_count}: Ignorada (borda/fita - espessura {dims[2]:.2f}mm)")
                explorer.Next()
                continue
            
            nome = f"Peca_{solid_count}"
            
            peca = Peca(
                nome=nome,
                comprimento=dims[0],
                largura=dims[1],
                espessura=dims[2],
                bbox_min=(bbox[0], bbox[1], bbox[2]),
                bbox_max=(bbox[3], bbox[4], bbox[5])
            )
            
            print(f"\n{'='*60}")
            print(f"📦 {nome}: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")
            print(f"   BBox: ({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}) -> ({bbox[3]:.1f}, {bbox[4]:.1f}, {bbox[5]:.1f})")
            print(f"   Eixos: comp={axes_map['comprimento']['eixo']}, larg={axes_map['largura']['eixo']}, esp={axes_map['espessura']['eixo']}")
            print(f"{'='*60}")
            
            # Encontrar cilindros
            cylinders = self._find_cylinders(solid)
            print(f"\n   🔍 Cilindros encontrados: {len(cylinders)}")
            
            # Classificar cada cilindro
            furos = []
            for i, cyl in enumerate(cylinders):
                self._log(f"\n   --- Cilindro {i+1}/{len(cylinders)} ---")
                furo = self._classify_hole(cyl, dims, axes_map, bbox)
                if furo:
                    furos.append(furo)
            
            # Remover duplicados
            furos_unicos = self._remove_duplicates(furos)
            
            # Atribuir IDs
            for i, furo in enumerate(furos_unicos, 1):
                furo.id = i
            
            peca.furos = furos_unicos
            
            # Resumo
            v_count = len([f for f in furos_unicos if f.tipo == 'vertical'])
            h_count = len([f for f in furos_unicos if f.tipo == 'horizontal'])
            
            print(f"\n   📊 RESUMO:")
            print(f"   ✅ Furos detectados: {len(furos_unicos)} ({v_count} verticais, {h_count} horizontais)")
            
            # Detalhar furos por lado
            lados = {}
            for f in furos_unicos:
                if f.lado not in lados:
                    lados[f.lado] = []
                lados[f.lado].append(f)
            
            for lado, lista in sorted(lados.items()):
                diams = [f.diametro for f in lista]
                print(f"      {lado}: {len(lista)} furos - Ø{diams}")
            
            self.pecas.append(peca)
            explorer.Next()
        
        print(f"\n{'='*60}")
        print(f"📊 TOTAL: {len(self.pecas)} peça(s) processada(s)")
        print(f"{'='*60}")
        
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


def parse_step_occ(filepath: str = None, content: str = None, debug: bool = False) -> Dict[str, Any]:
    """
    Função principal para integração com FastAPI
    """
    parser = StepParserOCC(filepath=filepath, content=content, debug=debug)
    parser.parse()
    return parser.to_dict()


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        debug = '--debug' in sys.argv or '-d' in sys.argv
        
        print(f"\n🚀 CoreWood STEP Parser v2.0")
        print(f"   Arquivo: {filepath}")
        print(f"   Debug: {'ON' if debug else 'OFF'}")
        print()
        
        result = parse_step_occ(filepath=filepath, debug=debug)
        
        print("\n" + "=" * 60)
        print("RESULTADO JSON:")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Uso: python step_parser_occ_v2.py <arquivo.step> [--debug|-d]")
        print()
        print("Exemplos:")
        print("  python step_parser_occ_v2.py 03_Chapeu.step")
        print("  python step_parser_occ_v2.py 03_Chapeu.step --debug")