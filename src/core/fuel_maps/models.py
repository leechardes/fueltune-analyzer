"""
Modelos de dados para mapas de combustível 3D.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class MapConfig:
    """Configuração de um tipo de mapa 2D ou 3D."""

    name: str
    unit: str
    min_value: float
    max_value: float
    description: str
    dimension: Optional[str] = None
    display_name: Optional[str] = None

    # Campos específicos para mapas 3D
    grid_size: Optional[int] = None
    x_axis_type: Optional[str] = None
    y_axis_type: Optional[str] = None
    default_rpm_values: Optional[List[float]] = None
    default_map_values: Optional[List[float]] = None
    default_values: Optional[List[List[float]]] = None

    # Campos específicos para mapas 2D
    positions: Optional[int] = None
    axis_type: Optional[str] = None
    default_enabled_count: Optional[int] = None
    default_axis_values: Optional[List[float]] = None
    default_enabled: Optional[List[bool]] = None

    def __post_init__(self):
        """Valida e configura valores padrão após inicialização."""
        if self.default_rpm_values is None:
            self.default_rpm_values = []
        if self.default_map_values is None:
            self.default_map_values = []
        if self.default_values is None:
            self.default_values = []


@dataclass
class Map3DData:
    """Dados completos de um mapa 3D."""

    vehicle_id: str
    map_type: str
    map_id: str
    config: MapConfig

    # Dados dos eixos
    rpm_values: List[float] = field(default_factory=list)
    map_values: List[float] = field(default_factory=list)

    # Matriz principal do mapa
    data_matrix: List[List[float]] = field(default_factory=list)

    # Matrizes auxiliares
    enabled_matrix: List[List[bool]] = field(default_factory=list)

    # Metadados
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: str = "1.0"

    def __post_init__(self):
        """Valida e inicializa dados após criação."""
        grid_size = self.config.grid_size

        # Inicializar eixos se vazios
        if not self.rpm_values:
            self.rpm_values = [1000.0 + i * 300 for i in range(grid_size)]
        if not self.map_values:
            self.map_values = [20.0 + i * 5 for i in range(grid_size)]

        # Inicializar matrizes se vazias
        if not self.data_matrix:
            self.data_matrix = [[0.0 for _ in range(grid_size)] for _ in range(grid_size)]
        if not self.enabled_matrix:
            self.enabled_matrix = [[True for _ in range(grid_size)] for _ in range(grid_size)]

    @property
    def grid_size(self) -> int:
        """Tamanho do grid do mapa."""
        return self.config.grid_size

    @property
    def numpy_data_matrix(self) -> np.ndarray:
        """Retorna a matriz de dados como numpy array."""
        return np.array(self.data_matrix)

    @property
    def numpy_enabled_matrix(self) -> np.ndarray:
        """Retorna a matriz enabled como numpy array."""
        return np.array(self.enabled_matrix, dtype=bool)

    def get_value_at(self, rpm_idx: int, map_idx: int) -> Optional[float]:
        """Obtém valor em posição específica."""
        if (
            0 <= rpm_idx < self.grid_size
            and 0 <= map_idx < self.grid_size
            and self.enabled_matrix[rpm_idx][map_idx]
        ):
            return self.data_matrix[rpm_idx][map_idx]
        return None

    def set_value_at(self, rpm_idx: int, map_idx: int, value: float) -> bool:
        """Define valor em posição específica."""
        if 0 <= rpm_idx < self.grid_size and 0 <= map_idx < self.grid_size:
            self.data_matrix[rpm_idx][map_idx] = value
            return True
        return False

    def is_enabled_at(self, rpm_idx: int, map_idx: int) -> bool:
        """Verifica se posição está habilitada."""
        if 0 <= rpm_idx < self.grid_size and 0 <= map_idx < self.grid_size:
            return self.enabled_matrix[rpm_idx][map_idx]
        return False

    def set_enabled_at(self, rpm_idx: int, map_idx: int, enabled: bool) -> bool:
        """Define se posição está habilitada."""
        if 0 <= rpm_idx < self.grid_size and 0 <= map_idx < self.grid_size:
            self.enabled_matrix[rpm_idx][map_idx] = enabled
            return True
        return False


@dataclass
class VehicleData:
    """Dados básicos do veículo para contexto."""

    vehicle_id: str
    name: str
    engine_type: str = "Unknown"
    fuel_type: str = "Gasoline"
    displacement: Optional[float] = None
    cylinders: Optional[int] = None

    def __post_init__(self):
        """Valida dados do veículo."""
        if not self.vehicle_id:
            raise ValueError("vehicle_id é obrigatório")
        if not self.name:
            raise ValueError("name é obrigatório")


# Tipos auxiliares
MapMatrix = List[List[float]]
EnabledMatrix = List[List[bool]]
AxisValues = List[float]
MapConfigDict = Dict[str, Any]
