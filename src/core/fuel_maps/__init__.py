# Fuel Maps Core Module
"""
Módulo core para gerenciamento de mapas de combustível 3D.
Contém toda a lógica de negócio, persistência e utilitários.
"""

# Import principais classes e funções
from .models import MapConfig, Map3DData, VehicleData
from .defaults import ConfigManager, config_manager
from .calculations import Calculator
from .persistence import PersistenceManager, persistence_manager
from .validation import MapValidator
from .session_utils import SessionManager, session_manager
from .utils import format_value_3_decimals, format_value_by_type, get_active_axis_values
from .ui_components import UIComponents, ui_components

# Import funções de compatibilidade
from .defaults import (
    load_map_types_config,
    get_map_config_values,
    get_default_3d_enabled_matrix,
    get_default_3d_map_values,
    get_dummy_vehicles,
    get_all_maps,
    get_map_dimension,
    has_bank_selection,
    get_sorted_maps_for_display
)

from .calculations import (
    calculate_base_injection_time_3d,
    get_afr_target_3d,
    calculate_fuel_3d_matrix,
    calculate_ignition_3d_matrix,
    calculate_lambda_3d_matrix,
    calculate_afr_3d_matrix,
    calculate_3d_map_values_universal,
    interpolate_3d_matrix,
    calculate_2d_map_values
)

from .persistence import (
    save_3d_map_data,
    load_3d_map_data,
    ensure_all_3d_maps_exist,
    load_vehicles,
    save_2d_map_data,
    load_2d_map_data,
    create_default_2d_map,
    ensure_all_maps_exist
)

from .validation import (
    validate_3d_map_values
)

from .session_utils import (
    get_vehicle_data_from_session,
    get_selected_vehicle_id,
    cache_map_data,
    get_cached_map_data
)

__all__ = [
    # Modelos
    'MapConfig',
    'Map3DData', 
    'VehicleData',
    
    # Gerenciadores principais
    'ConfigManager',
    'Calculator',
    'PersistenceManager',
    'MapValidator',
    'SessionManager',
    'UIComponents',
    
    # Instâncias globais
    'config_manager',
    'persistence_manager',
    'session_manager',
    'ui_components',
    
    # Utilitários
    'format_value_3_decimals',
    'format_value_by_type',
    'get_active_axis_values',
    
    # Funções de compatibilidade - defaults
    'load_map_types_config',
    'get_map_config_values',
    'get_default_3d_enabled_matrix',
    'get_default_3d_map_values',
    'get_dummy_vehicles',
    'get_all_maps',
    'get_map_dimension',
    'has_bank_selection',
    'get_sorted_maps_for_display',
    
    # Funções de compatibilidade - calculations
    'calculate_base_injection_time_3d',
    'get_afr_target_3d',
    'calculate_fuel_3d_matrix',
    'calculate_ignition_3d_matrix',
    'calculate_lambda_3d_matrix',
    'calculate_afr_3d_matrix',
    'calculate_3d_map_values_universal',
    'interpolate_3d_matrix',
    'calculate_2d_map_values',
    
    # Funções de compatibilidade - persistence
    'save_3d_map_data',
    'load_3d_map_data',
    'ensure_all_3d_maps_exist',
    'load_vehicles',
    'save_2d_map_data',
    'load_2d_map_data',
    'create_default_2d_map',
    'ensure_all_maps_exist',
    
    # Funções de compatibilidade - validation
    'validate_3d_map_values',
    
    # Funções de compatibilidade - session
    'get_vehicle_data_from_session',
    'get_selected_vehicle_id',
    'cache_map_data',
    'get_cached_map_data'
]