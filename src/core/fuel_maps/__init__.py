# Fuel Maps Core Module
"""
Módulo core para gerenciamento de mapas de combustível 3D.
Contém toda a lógica de negócio, persistência e utilitários.
"""

from .calculations import (
    Calculator,
    calculate_2d_map_values,
    calculate_3d_map_values_universal,
    calculate_afr_3d_matrix,
    calculate_base_injection_time_3d,
    calculate_fuel_3d_matrix,
    calculate_ignition_3d_matrix,
    calculate_lambda_3d_matrix,
    get_afr_target_3d,
    interpolate_3d_matrix,
)

# Import funções de compatibilidade
from .defaults import (
    ConfigManager,
    config_manager,
    get_all_maps,
    get_default_3d_enabled_matrix,
    get_default_3d_map_values,
    get_dummy_vehicles,
    get_map_config_values,
    get_map_dimension,
    get_sorted_maps_for_display,
    has_bank_selection,
    load_map_types_config,
)

# Import principais classes e funções
from .models import Map3DData, MapConfig, VehicleData
from .persistence import (
    PersistenceManager,
    create_default_2d_map,
    ensure_all_3d_maps_exist,
    ensure_all_maps_exist,
    load_2d_map_data,
    load_3d_map_data,
    load_vehicles,
    persistence_manager,
    save_2d_map_data,
    save_3d_map_data,
)
from .session_utils import (
    SessionManager,
    cache_map_data,
    get_cached_map_data,
    get_selected_vehicle_id,
    get_vehicle_data_from_session,
    session_manager,
)
from .ui_components import UIComponents, ui_components
from .utils import format_value_3_decimals, format_value_by_type, get_active_axis_values
from .validation import MapValidator, validate_3d_map_values

__all__ = [
    # Modelos
    "MapConfig",
    "Map3DData",
    "VehicleData",
    # Gerenciadores principais
    "ConfigManager",
    "Calculator",
    "PersistenceManager",
    "MapValidator",
    "SessionManager",
    "UIComponents",
    # Instâncias globais
    "config_manager",
    "persistence_manager",
    "session_manager",
    "ui_components",
    # Utilitários
    "format_value_3_decimals",
    "format_value_by_type",
    "get_active_axis_values",
    # Funções de compatibilidade - defaults
    "load_map_types_config",
    "get_map_config_values",
    "get_default_3d_enabled_matrix",
    "get_default_3d_map_values",
    "get_dummy_vehicles",
    "get_all_maps",
    "get_map_dimension",
    "has_bank_selection",
    "get_sorted_maps_for_display",
    # Funções de compatibilidade - calculations
    "calculate_base_injection_time_3d",
    "get_afr_target_3d",
    "calculate_fuel_3d_matrix",
    "calculate_ignition_3d_matrix",
    "calculate_lambda_3d_matrix",
    "calculate_afr_3d_matrix",
    "calculate_3d_map_values_universal",
    "interpolate_3d_matrix",
    "calculate_2d_map_values",
    # Funções de compatibilidade - persistence
    "save_3d_map_data",
    "load_3d_map_data",
    "ensure_all_3d_maps_exist",
    "load_vehicles",
    "save_2d_map_data",
    "load_2d_map_data",
    "create_default_2d_map",
    "ensure_all_maps_exist",
    # Funções de compatibilidade - validation
    "validate_3d_map_values",
    # Funções de compatibilidade - session
    "get_vehicle_data_from_session",
    "get_selected_vehicle_id",
    "cache_map_data",
    "get_cached_map_data",
]
