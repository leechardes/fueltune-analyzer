"""
Validators for vehicle data.
"""

import re
from typing import Any, Dict


def normalize_plate(plate: str) -> str:
    """Normalize license plate format."""
    if not plate:
        return ""

    # Remove spaces and convert to uppercase
    plate = plate.upper().replace(" ", "").replace("-", "")

    # Brazilian plate format: ABC-1234 or ABC1D23 (Mercosul)
    if len(plate) == 7:
        # Old format: 3 letters + 4 numbers
        if re.match(r"^[A-Z]{3}[0-9]{4}$", plate):
            return f"{plate[:3]}-{plate[3:]}"
        # Mercosul format: 3 letters + 1 number + 1 letter + 2 numbers
        elif re.match(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$", plate):
            return f"{plate[:3]}{plate[3]}{plate[4]}{plate[5:]}"

    return plate


def validate_vehicle_data(vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate vehicle data before saving."""
    errors = []
    warnings = []

    # Required fields
    required_fields = ["name", "brand", "model"]
    for field in required_fields:
        if not vehicle_data.get(field):
            errors.append(f"Campo obrigatório: {field}")

    # Validate year
    year = vehicle_data.get("year")
    if year:
        if year < 1900 or year > 2030:
            errors.append("Ano deve estar entre 1900 e 2030")

    # Validate engine displacement
    displacement = vehicle_data.get("engine_displacement")
    if displacement:
        if displacement <= 0 or displacement > 10:
            warnings.append("Cilindrada incomum (esperado entre 0.1 e 10.0L)")

    # Validate cylinders
    cylinders = vehicle_data.get("engine_cylinders")
    if cylinders:
        if cylinders < 1 or cylinders > 16:
            errors.append("Número de cilindros deve estar entre 1 e 16")

    # Validate power
    power = vehicle_data.get("estimated_power")
    if power:
        if power < 0 or power > 2000:
            warnings.append("Potência incomum (esperado entre 0 e 2000hp)")

    # Validate torque
    torque = vehicle_data.get("estimated_torque")
    if torque:
        if torque < 0 or torque > 2000:
            warnings.append("Torque incomum (esperado entre 0 e 2000Nm)")

    # Validate RPM
    rpm = vehicle_data.get("max_rpm")
    if rpm:
        if rpm < 1000 or rpm > 20000:
            warnings.append("RPM máximo incomum (esperado entre 1000 e 20000)")

    # Validate injector flow
    flow = vehicle_data.get("injector_flow_rate")
    if flow:
        if flow < 0 or flow > 3000:
            warnings.append("Vazão de bico incomum (esperado entre 0 e 3000cc/min)")

    # Validate boost pressure
    boost = vehicle_data.get("max_boost_pressure")
    if boost:
        if boost < 0 or boost > 5:
            warnings.append("Pressão de turbo incomum (esperado entre 0 e 5 bar)")

    # Validate weight
    weight = vehicle_data.get("curb_weight")
    if weight:
        if weight < 500 or weight > 5000:
            warnings.append("Peso incomum (esperado entre 500 e 5000kg)")

    # Calculate power/weight ratio if both values exist
    if power and weight:
        vehicle_data["power_weight_ratio"] = round(power / weight * 1000, 2)

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "data": vehicle_data,
    }
