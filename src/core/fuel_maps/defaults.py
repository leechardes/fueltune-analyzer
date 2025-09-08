"""
Configurações padrão e valores default para mapas de combustível 3D.
Gerencia carregamento do arquivo config/map_types.json e fallbacks.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .models import MapConfig, VehicleData

logger = logging.getLogger(__name__)

class ConfigManager:
    """Gerenciador de configurações para mapas 3D."""
    
    _instance = None
    _config_cache = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._load_config()
    
    def _load_config(self):
        """Carrega configuração do arquivo JSON ou usa defaults."""
        self._config_cache = self.load_map_types_config()
    
    @staticmethod
    def load_map_types_config() -> Dict[str, Any]:
        """Carrega a configuração de tipos de mapas do arquivo JSON."""
        config_path = Path("config/map_types.json")

        # Se o arquivo não existir, usar configuração padrão
        if not config_path.exists():
            logger.warning(f"Arquivo {config_path} não encontrado. Usando configuração padrão.")
            return ConfigManager._get_default_config()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"Configuração carregada de {config_path}")
                return config
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}. Usando valores padrão.")
            return ConfigManager._get_default_config()
    
    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Retorna configuração padrão hardcoded."""
        return {
            "main_fuel_3d_map": {
                "name": "Mapa Principal de Injeção 3D - 32x32 (1024 posições)",
                "grid_size": 32,
                "x_axis_type": "RPM",
                "y_axis_type": "MAP",
                "unit": "ms",
                "min_value": 0.0,
                "max_value": 50.0,
                "description": "Mapa principal 3D",
                "default_rpm_values": [1000.0 + i * 300 for i in range(32)],
                "default_map_values": [20.0 + i * 5 for i in range(32)],
                "default_rpm_enabled": [True] * 32,
                "default_map_enabled": [True] * 32,
            },
            "lambda_target_3d_map": {
                "name": "Mapa de Lambda Alvo 3D - 32x32",
                "grid_size": 32,
                "x_axis_type": "RPM",
                "y_axis_type": "MAP",
                "unit": "λ",
                "min_value": 0.8,
                "max_value": 1.2,
                "description": "Mapa 3D de lambda alvo",
                "default_rpm_values": [1000.0 + i * 300 for i in range(32)],
                "default_map_values": [20.0 + i * 5 for i in range(32)],
                "default_rpm_enabled": [True] * 32,
                "default_map_enabled": [True] * 32,
            },
            "ignition_3d_map": {
                "name": "Mapa de Ignição 3D - 32x32",
                "grid_size": 32,
                "x_axis_type": "RPM", 
                "y_axis_type": "MAP",
                "unit": "°",
                "min_value": -10.0,
                "max_value": 45.0,
                "description": "Mapa 3D de avanço de ignição",
                "default_rpm_values": [1000.0 + i * 300 for i in range(32)],
                "default_map_values": [20.0 + i * 5 for i in range(32)],
                "default_rpm_enabled": [True] * 32,
                "default_map_enabled": [True] * 32,
            },
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna configuração atual."""
        if self._config_cache is None:
            self._load_config()
        return self._config_cache
    
    def get_map_config(self, map_type: str) -> Optional[Dict[str, Any]]:
        """Obtém configuração específica de um tipo de mapa."""
        return self.get_config().get(map_type)
    
    def get_map_config_object(self, map_type: str) -> Optional[MapConfig]:
        """Converte configuração em objeto MapConfig."""
        config_dict = self.get_map_config(map_type)
        if not config_dict:
            return None
        
        return MapConfig(
            name=config_dict.get("name", ""),
            unit=config_dict.get("unit", ""),
            min_value=config_dict.get("min_value", 0.0),
            max_value=config_dict.get("max_value", 100.0),
            description=config_dict.get("description", ""),
            dimension=config_dict.get("dimension"),
            display_name=config_dict.get("display_name"),
            
            # Campos específicos para mapas 3D
            grid_size=config_dict.get("grid_size"),
            x_axis_type=config_dict.get("x_axis_type"),
            y_axis_type=config_dict.get("y_axis_type"),
            default_rpm_values=config_dict.get("default_rpm_values"),
            default_map_values=config_dict.get("default_map_values"),
            default_values=config_dict.get("default_values"),
            
            # Campos específicos para mapas 2D
            positions=config_dict.get("positions"),
            axis_type=config_dict.get("axis_type"),
            default_enabled_count=config_dict.get("default_enabled_count"),
            default_axis_values=config_dict.get("default_axis_values"),
            default_enabled=config_dict.get("default_enabled")
        )
    
    def get_map_config_values(self, map_type: str, key: str, grid_size: int = 32) -> Optional[List]:
        """Obtém valores de configuração do mapa específico do arquivo JSON.
        
        Args:
            map_type: Tipo do mapa (ex: 'main_fuel_3d_map')
            key: Chave da configuração (ex: 'default_rpm_values')
            grid_size: Tamanho do grid
            
        Returns:
            Lista com os valores da configuração ou None se não encontrado
        """
        config = self.get_config()
        if map_type not in config:
            return None
        
        config_value = config[map_type].get(key)
        if config_value is None:
            return None
        
        # Ajustar tamanho se necessário
        if len(config_value) != grid_size:
            if len(config_value) > grid_size:
                return config_value[:grid_size]
            else:
                # Preencher com valores padrão se menor
                if 'enabled' in key:
                    return config_value + [False] * (grid_size - len(config_value))
                else:
                    # Para valores numéricos, repetir o último valor
                    if config_value:
                        last_value = config_value[-1]
                        return config_value + [last_value] * (grid_size - len(config_value))
        
        return config_value
    
    def get_default_3d_enabled_matrix(self, map_type: str, vehicle_data: Dict[str, Any]) -> Tuple[List[bool], List[bool]]:
        """Retorna matrizes de enable/disable baseadas no tipo de motor."""
        map_config = self.get_map_config(map_type) or {}

        # Obter configurações padrão
        rpm_enabled = map_config.get(
            "default_rpm_enabled", [True] * map_config.get("grid_size", 32)
        )
        map_enabled = map_config.get(
            "default_map_enabled", [True] * map_config.get("grid_size", 32)
        )

        # Ajustar para motores aspirados vs turbo
        turbo_config = map_config.get("turbo_adjustment", {})

        if not vehicle_data.get("turbo", False):
            # Motor aspirado - desabilitar valores de boost positivo
            if turbo_config.get("enable_positive_values", False):
                max_index = turbo_config.get("aspirated_max_map_index", 10)
                map_enabled = [i <= max_index for i in range(len(map_enabled))]

        return rpm_enabled, map_enabled
    
    def get_default_3d_map_values(self, map_type: str, grid_size: int, 
                                  rpm_enabled: Optional[List[bool]] = None,
                                  map_enabled: Optional[List[bool]] = None) -> np.ndarray:
        """Retorna valores padrão para o mapa 3D baseado no tipo e tamanho do grid."""
        config = self.get_map_config(map_type) or {}
        
        # Valores base padrão por tipo
        if map_type == "main_fuel_3d_map":
            base_value = 2.0  # ms
        elif map_type == "lambda_target_3d_map":
            base_value = 0.85  # lambda
        elif map_type == "ignition_3d_map":
            base_value = 15.0  # graus
        else:
            base_value = config.get("default_value", 1.0)
        
        # Criar matriz com valores padrão
        matrix = np.full((grid_size, grid_size), base_value)
        
        # Aplicar valores específicos se definidos na configuração
        default_values = config.get("default_values")
        if default_values and len(default_values) == grid_size:
            for i, row in enumerate(default_values):
                if len(row) == grid_size:
                    matrix[i] = row
        
        return matrix
    
    def get_dummy_vehicles(self) -> List[Dict[str, Any]]:
        """Retorna lista de veículos dummy para desenvolvimento."""
        return [
            {"id": "1", "name": "Golf GTI 2.0T", "nickname": "GTI Vermelho", "turbo": True},
            {"id": "2", "name": "Civic Si 2.4", "nickname": "Si Azul", "turbo": False},
            {"id": "3", "name": "WRX STI 2.5", "nickname": "STI Preto", "turbo": True},
            {"id": "4", "name": "Focus RS 2.3", "nickname": "RS Branco", "turbo": True},
        ]
    
    def get_maps_by_dimension(self, dimension: str) -> Dict[str, Any]:
        """Filtra mapas por dimensão (2D ou 3D)."""
        config = self.get_config()
        return {
            map_type: map_config 
            for map_type, map_config in config.items() 
            if map_config.get("dimension") == dimension
        }
    
    def get_display_name(self, map_type: str) -> Optional[str]:
        """Obtém nome de exibição do mapa."""
        config_dict = self.get_map_config(map_type)
        if not config_dict:
            return None
        return config_dict.get("display_name", config_dict.get("name"))
    
    def get_all_maps(self) -> Dict[str, Any]:
        """Retorna todos os mapas disponíveis (2D e 3D)."""
        return self.get_config()
    
    def get_map_dimension(self, map_type: str) -> Optional[str]:
        """Obtém a dimensão do mapa (2D ou 3D)."""
        config_dict = self.get_map_config(map_type)
        if not config_dict:
            return None
        return config_dict.get("dimension", "3D")  # Default para 3D (compatibilidade)
    
    def has_bank_selection(self, map_type: str) -> bool:
        """Verifica se o mapa requer seleção de banco."""
        # Apenas mapas principais de combustível têm bancos
        return map_type in ["main_fuel_3d_map", "main_fuel_2d_map"]
    
    def get_sorted_maps_for_display(self) -> List[tuple]:
        """Retorna lista de mapas ordenados para exibição no dropdown.
        
        Returns:
            Lista de tuplas (map_type, display_info) onde display_info contém
            display_name, dimension, requires_bank
        """
        all_maps = self.get_all_maps()
        map_list = []
        
        for map_type, config in all_maps.items():
            display_info = {
                'display_name': config.get('display_name', config.get('name', map_type)),
                'dimension': config.get('dimension', '3D'),
                'requires_bank': self.has_bank_selection(map_type),
                'name': config.get('name', map_type)
            }
            map_list.append((map_type, display_info))
        
        # Ordenar por nome para interface consistente
        map_list.sort(key=lambda x: x[1]['display_name'])
        return map_list
    
    def reload_config(self) -> bool:
        """Recarrega configuração do arquivo."""
        try:
            self._load_config()
            logger.info("Configuração recarregada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao recarregar configuração: {e}")
            return False

# Instância global do gerenciador de configuração
config_manager = ConfigManager()

# Funções de conveniência para manter compatibilidade
def load_map_types_config() -> Dict[str, Any]:
    """Compatibilidade: carrega configuração de tipos de mapas."""
    return config_manager.get_config()

def get_map_config_values(map_type: str, key: str, grid_size: int = 32) -> Optional[List]:
    """Compatibilidade: obtém valores de configuração específicos."""
    return config_manager.get_map_config_values(map_type, key, grid_size)

def get_default_3d_enabled_matrix(map_type: str, vehicle_data: Dict[str, Any]) -> Tuple[List[bool], List[bool]]:
    """Compatibilidade: retorna matrizes de enable/disable."""
    return config_manager.get_default_3d_enabled_matrix(map_type, vehicle_data)

def get_default_3d_map_values(map_type: str, grid_size: int, 
                              rpm_enabled: Optional[List[bool]] = None,
                              map_enabled: Optional[List[bool]] = None) -> np.ndarray:
    """Compatibilidade: retorna valores padrão para o mapa 3D."""
    return config_manager.get_default_3d_map_values(map_type, grid_size, rpm_enabled, map_enabled)

def get_dummy_vehicles() -> List[Dict[str, Any]]:
    """Compatibilidade: retorna lista de veículos dummy."""
    return config_manager.get_dummy_vehicles()

def get_maps_by_dimension(dimension: str) -> Dict[str, Any]:
    """Compatibilidade: filtra mapas por dimensão."""
    return config_manager.get_maps_by_dimension(dimension)

def get_display_name(map_type: str) -> Optional[str]:
    """Compatibilidade: obtém nome de exibição do mapa."""
    return config_manager.get_display_name(map_type)

def get_all_maps() -> Dict[str, Any]:
    """Compatibilidade: retorna todos os mapas disponíveis."""
    return config_manager.get_all_maps()

def get_map_dimension(map_type: str) -> Optional[str]:
    """Compatibilidade: obtém dimensão do mapa."""
    return config_manager.get_map_dimension(map_type)

def has_bank_selection(map_type: str) -> bool:
    """Compatibilidade: verifica se requer seleção de banco."""
    return config_manager.has_bank_selection(map_type)

def get_sorted_maps_for_display() -> List[tuple]:
    """Compatibilidade: retorna lista ordenada de mapas para interface."""
    return config_manager.get_sorted_maps_for_display()