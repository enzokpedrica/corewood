"""
Modelos de dados para peças e furações
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Dimensoes:
    """Dimensões da peça"""
    largura: float  # X
    comprimento: float  # Y
    espessura: float  # Z


@dataclass
class FuroVertical:
    """Furo vertical (de cima/baixo)"""
    x: float
    y: float
    diametro: float
    profundidade: float
    lado: str = "LS"  # LS = lado superior


@dataclass
class FuroHorizontal:
    """Furo horizontal (lateral)"""
    x: float  # pode ser número ou "x" (lado oposto)
    y: float
    z: float
    diametro: float
    profundidade: float
    lado: str  # XP, XM, YP, YM


@dataclass
class Peca:
    """Representação completa de uma peça"""
    nome: str
    dimensoes: Dimensoes
    furos_verticais: List[FuroVertical]
    furos_horizontais: List[FuroHorizontal]
    comentarios: List[str]