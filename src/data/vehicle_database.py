"""
Database operations for vehicle management - wrapper for database.py functions.
Converts SQLAlchemy objects to dictionaries for use in Streamlit UI.
"""

from typing import Optional, List, Dict, Any
from src.data.database import (
    get_database,
    create_vehicle as db_create_vehicle,
    get_vehicle_by_id as db_get_vehicle_by_id,
    get_all_vehicles as db_get_all_vehicles,
    update_vehicle as db_update_vehicle,
    delete_vehicle as db_delete_vehicle,
    search_vehicles as db_search_vehicles,
    get_vehicle_statistics as db_get_vehicle_statistics
)

def vehicle_to_dict(vehicle) -> Dict[str, Any]:
    """Convert Vehicle SQLAlchemy model to dictionary."""
    if not vehicle:
        return None
    
    return {
        "id": vehicle.id,
        "name": vehicle.name,
        "nickname": vehicle.nickname,
        "plate": vehicle.plate,
        "year": vehicle.year,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "engine_displacement": vehicle.engine_displacement,
        "engine_cylinders": vehicle.engine_cylinders,
        "engine_configuration": vehicle.engine_configuration,
        "engine_aspiration": vehicle.engine_aspiration,
        "injector_type": vehicle.injector_type,
        "injector_count": vehicle.injector_count,
        "injector_flow_rate": vehicle.injector_flow_rate,
        "fuel_rail_pressure": vehicle.fuel_rail_pressure,
        "turbo_brand": vehicle.turbo_brand,
        "turbo_model": vehicle.turbo_model,
        "max_boost_pressure": vehicle.max_boost_pressure,
        "wastegate_type": vehicle.wastegate_type,
        "transmission_type": vehicle.transmission_type,
        "gear_count": vehicle.gear_count,
        "final_drive_ratio": vehicle.final_drive_ratio,
        "curb_weight": vehicle.curb_weight,
        "power_weight_ratio": vehicle.power_weight_ratio,
        "drivetrain": vehicle.drivetrain,
        "tire_size": vehicle.tire_size,
        "fuel_type": vehicle.fuel_type,
        "octane_rating": vehicle.octane_rating,
        "fuel_system": vehicle.fuel_system,
        "estimated_power": vehicle.estimated_power,
        "estimated_torque": vehicle.estimated_torque,
        "max_rpm": vehicle.max_rpm,
        "bank_a_enabled": vehicle.bank_a_enabled,
        "bank_a_mode": vehicle.bank_a_mode,
        "bank_a_outputs": vehicle.bank_a_outputs,
        "bank_a_injector_flow": vehicle.bank_a_injector_flow,
        "bank_a_injector_count": vehicle.bank_a_injector_count,
        "bank_a_total_flow": vehicle.bank_a_total_flow,
        "bank_a_dead_time": vehicle.bank_a_dead_time,
        "bank_b_enabled": vehicle.bank_b_enabled,
        "bank_b_mode": vehicle.bank_b_mode,
        "bank_b_outputs": vehicle.bank_b_outputs,
        "bank_b_injector_flow": vehicle.bank_b_injector_flow,
        "bank_b_injector_count": vehicle.bank_b_injector_count,
        "bank_b_total_flow": vehicle.bank_b_total_flow,
        "bank_b_dead_time": vehicle.bank_b_dead_time,
        "max_map_pressure": vehicle.max_map_pressure,
        "min_map_pressure": vehicle.min_map_pressure,
        "created_at": vehicle.created_at,
        "updated_at": vehicle.updated_at,
        "is_active": vehicle.is_active,
        "notes": vehicle.notes
    }

def get_all_vehicles(active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all vehicles from database as dictionaries."""
    vehicles = db_get_all_vehicles(active_only=active_only)
    return [vehicle_to_dict(v) for v in vehicles]

def get_vehicle_by_id(vehicle_id: str) -> Optional[Dict[str, Any]]:
    """Get vehicle by ID as dictionary."""
    vehicle = db_get_vehicle_by_id(vehicle_id)
    return vehicle_to_dict(vehicle) if vehicle else None

def create_vehicle(vehicle_data: Dict[str, Any]) -> str:
    """Create a new vehicle."""
    return db_create_vehicle(vehicle_data)

def update_vehicle(vehicle_id: str, vehicle_data: Dict[str, Any]) -> bool:
    """Update existing vehicle."""
    return db_update_vehicle(vehicle_id, vehicle_data)

def delete_vehicle(vehicle_id: str) -> bool:
    """Delete a vehicle."""
    return db_delete_vehicle(vehicle_id)

def search_vehicles(search_term: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """Search vehicles by name, brand, model or nickname."""
    vehicles = db_search_vehicles(search_term, active_only=active_only)
    return [vehicle_to_dict(v) for v in vehicles]

def get_vehicle_statistics() -> Dict[str, Any]:
    """Get statistics about vehicles in database."""
    # Get basic statistics about all vehicles
    db = get_database()
    all_vehicles = db_get_all_vehicles(active_only=False)
    active_vehicles = db_get_all_vehicles(active_only=True)
    
    turbo_vehicles = [v for v in all_vehicles if v.engine_aspiration and "Turbo" in v.engine_aspiration]
    
    return {
        "total": len(all_vehicles),
        "active": len(active_vehicles),
        "inactive": len(all_vehicles) - len(active_vehicles),
        "turbo": len(turbo_vehicles),
        "naturally_aspirated": len(all_vehicles) - len(turbo_vehicles)
    }