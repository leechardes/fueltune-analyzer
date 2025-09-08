"""
Cálculos para mapas de combustível 3D.
Contém toda a lógica de cálculo de injeção, ignição, lambda e AFR.
"""

import logging
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)

# Presets de estratégia para AFR
STRATEGY_PRESETS = {
    "conservative": {
        "idle": 14.5,
        "cruise": 14.7,
        "load": 13.5,
        "wot": 12.5,
        "boost": 11.5,
    },
    "balanced": {
        "idle": 14.2,
        "cruise": 14.5,
        "load": 13.2,
        "wot": 12.2,
        "boost": 11.2,
    },
    "aggressive": {
        "idle": 14.0,
        "cruise": 14.3,
        "load": 12.8,
        "wot": 11.8,
        "boost": 10.8,
    },
}

class Calculator:
    """Classe para cálculos de mapas de combustível 3D."""

    @staticmethod
    def calculate_base_injection_time_3d(
        map_kpa: float,
        rpm: float,
        engine_displacement: float,
        cylinders: int,
        injector_flow_cc_min: float,
        afr_target: float,
        boost_pressure: float = 0,
    ) -> float:
        """Calcula tempo base de injeção 3D baseado nos parâmetros do motor e RPM."""
        try:
            # MAP é pressão absoluta em kPa
            map_bar = map_kpa / 100.0

            # Calcular pressão de combustível real
            fuel_pressure_base = 3.0
            fuel_pressure_actual = fuel_pressure_base + boost_pressure

            # Ajustar vazão do bico baseado na pressão real
            flow_correction = (fuel_pressure_actual / fuel_pressure_base) ** 0.5
            effective_flow = injector_flow_cc_min * flow_correction

            # Densidade do ar corrigida pela temperatura e pressão
            air_density_correction = map_bar / 1.013
            temperature_correction = 1.0  # Assumir temperatura padrão

            # Volume de ar por ciclo
            volume_per_cycle = (engine_displacement / cylinders) * (rpm / 60 / 2)
            air_mass_per_cycle = volume_per_cycle * air_density_correction * temperature_correction

            # Massa de combustível necessária
            fuel_mass_needed = air_mass_per_cycle / afr_target

            # Converter para tempo de injeção (aproximação)
            # Densidade da gasolina ≈ 0.75 kg/L
            fuel_density = 0.75
            fuel_volume_ml = fuel_mass_needed / fuel_density * 1000

            # Tempo de injeção em ms
            injection_time = fuel_volume_ml / effective_flow * 60 * 1000

            return max(0.5, min(50.0, injection_time))  # Limitar entre 0.5ms e 50ms

        except Exception as e:
            logger.error(f"Erro no cálculo de tempo de injeção: {e}")
            return 2.0  # Valor padrão seguro

    @staticmethod
    def get_afr_target_3d(map_kpa: float, strategy: str) -> float:
        """Retorna AFR alvo baseado na pressão MAP e estratégia para mapas 3D."""
        preset = STRATEGY_PRESETS.get(strategy, STRATEGY_PRESETS["balanced"])

        if map_kpa < 30:  # Vácuo alto (idle)
            return preset["idle"]
        elif map_kpa < 60:  # Cruzeiro baixo
            return preset["cruise"]
        elif map_kpa < 90:  # Carga parcial
            return preset["load"]
        elif map_kpa < 100:  # Carga alta (atmosférico)
            return preset["wot"]
        else:  # Boost (turbo)
            return preset["boost"]

    @staticmethod
    def calculate_fuel_3d_matrix(
        rpm_axis: List[float],
        map_axis: List[float],
        vehicle_data: Dict[str, Any],
        strategy: str = "balanced",
        safety_factor: float = 1.0,
    ) -> np.ndarray:
        """Calcula matriz 3D de valores de combustível."""
        matrix = np.zeros((len(map_axis), len(rpm_axis)))

        for i, map_value in enumerate(map_axis):
            # Converter MAP de bar para kPa
            map_kpa = (map_value + 1.013) * 100 if map_value < 0 else (map_value + 1.013) * 100

            for j, rpm in enumerate(rpm_axis):
                afr_target = Calculator.get_afr_target_3d(map_kpa, strategy)

                injection_time = Calculator.calculate_base_injection_time_3d(
                    map_kpa=map_kpa,
                    rpm=rpm,
                    engine_displacement=vehicle_data.get("displacement", 2000) / 1000,  # L
                    cylinders=vehicle_data.get("cylinders", 4),
                    injector_flow_cc_min=vehicle_data.get("injector_flow", 440),
                    afr_target=afr_target,
                    boost_pressure=max(0, map_value * 100),  # Converter para kPa
                )

                matrix[i, j] = injection_time * safety_factor

        return matrix

    @staticmethod
    def calculate_ignition_3d_matrix(
        rpm_axis: List[float],
        map_axis: List[float],
        vehicle_data: Dict[str, Any],
        octane_rating: float = 91.0,
    ) -> np.ndarray:
        """Calcula matriz 3D de valores de ignição (avanço)."""
        matrix = np.zeros((len(map_axis), len(rpm_axis)))

        for i, map_value in enumerate(map_axis):
            map_kpa = (map_value + 1.013) * 100 if map_value < 0 else (map_value + 1.013) * 100

            for j, rpm in enumerate(rpm_axis):
                # Avanço base por RPM
                base_advance = 15.0 + (rpm - 1000) / 1000 * 5.0

                # Correção por carga (MAP)
                if map_kpa < 50:  # Vácuo - mais avanço
                    load_correction = 5.0
                elif map_kpa < 90:  # Carga parcial
                    load_correction = 2.0
                elif map_kpa < 100:  # WOT atmosférico
                    load_correction = 0.0
                else:  # Boost - menos avanço
                    boost_level = (map_kpa - 100) / 100
                    load_correction = -3.0 * boost_level

                # Correção por octanagem
                octane_correction = (octane_rating - 91) * 0.5

                total_advance = base_advance + load_correction + octane_correction
                matrix[i, j] = max(-10.0, min(45.0, total_advance))

        return matrix

    @staticmethod
    def calculate_lambda_3d_matrix(
        rpm_axis: List[float],
        map_axis: List[float],
        vehicle_data: Dict[str, Any],
        strategy: str = "balanced",
    ) -> np.ndarray:
        """Calcula matriz 3D de valores de lambda."""
        matrix = np.zeros((len(map_axis), len(rpm_axis)))

        for i, map_value in enumerate(map_axis):
            map_kpa = (map_value + 1.013) * 100 if map_value < 0 else (map_value + 1.013) * 100

            for j, rpm in enumerate(rpm_axis):
                afr_target = Calculator.get_afr_target_3d(map_kpa, strategy)
                # Lambda = AFR / AFR_stoich (14.7 para gasolina)
                lambda_value = afr_target / 14.7
                matrix[i, j] = max(0.7, min(1.3, lambda_value))

        return matrix

    @staticmethod
    def calculate_afr_3d_matrix(
        rpm_axis: List[float],
        map_axis: List[float],
        vehicle_data: Dict[str, Any],
        strategy: str = "balanced",
    ) -> np.ndarray:
        """Calcula matriz 3D de valores de AFR."""
        matrix = np.zeros((len(map_axis), len(rpm_axis)))

        for i, map_value in enumerate(map_axis):
            map_kpa = (map_value + 1.013) * 100 if map_value < 0 else (map_value + 1.013) * 100

            for j, rpm in enumerate(rpm_axis):
                afr_target = Calculator.get_afr_target_3d(map_kpa, strategy)
                matrix[i, j] = afr_target

        return matrix

    @staticmethod
    def calculate_3d_map_values_universal(
        map_type: str,
        rpm_axis: List[float],
        map_axis: List[float],
        vehicle_data: Dict[str, Any],
        **kwargs
    ) -> np.ndarray:
        """Função universal para calcular valores de qualquer tipo de mapa 3D."""
        try:
            if map_type == "main_fuel_3d_map":
                return Calculator.calculate_fuel_3d_matrix(
                    rpm_axis, map_axis, vehicle_data, 
                    kwargs.get("strategy", "balanced"),
                    kwargs.get("safety_factor", 1.0)
                )
            elif map_type == "ignition_3d_map":
                return Calculator.calculate_ignition_3d_matrix(
                    rpm_axis, map_axis, vehicle_data,
                    kwargs.get("octane_rating", 91.0)
                )
            elif map_type == "lambda_target_3d_map":
                return Calculator.calculate_lambda_3d_matrix(
                    rpm_axis, map_axis, vehicle_data,
                    kwargs.get("strategy", "balanced")
                )
            elif map_type == "afr_target_3d_map":
                return Calculator.calculate_afr_3d_matrix(
                    rpm_axis, map_axis, vehicle_data,
                    kwargs.get("strategy", "balanced")
                )
            else:
                logger.warning(f"Tipo de mapa desconhecido: {map_type}")
                return np.ones((len(map_axis), len(rpm_axis)))

        except Exception as e:
            logger.error(f"Erro no cálculo universal de mapa {map_type}: {e}")
            return np.ones((len(map_axis), len(rpm_axis)))

    @staticmethod
    def interpolate_3d_matrix(matrix: np.ndarray, method: str = "linear") -> np.ndarray:
        """Aplica interpolação suave na matriz 3D."""
        if method == "linear":
            # Interpolação linear simples - média dos vizinhos
            result = matrix.copy()
            rows, cols = matrix.shape

            for i in range(1, rows - 1):
                for j in range(1, cols - 1):
                    neighbors = [
                        matrix[i - 1, j],
                        matrix[i + 1, j],  # vertical
                        matrix[i, j - 1],
                        matrix[i, j + 1],  # horizontal
                    ]
                    result[i, j] = (matrix[i, j] * 2 + sum(neighbors)) / 6

            return result

        return matrix

    @staticmethod
    def apply_safety_corrections(
        matrix: np.ndarray,
        map_type: str,
        safety_factor: float = 1.0,
        temp_correction: float = 1.0,
        altitude_correction: float = 1.0
    ) -> np.ndarray:
        """Aplica correções de segurança na matriz."""
        corrected = matrix.copy()
        
        # Aplicar fator de segurança
        if map_type == "main_fuel_3d_map":
            corrected *= safety_factor
        elif map_type == "ignition_3d_map":
            # Para ignição, fator de segurança reduz avanço
            corrected *= (2.0 - safety_factor) if safety_factor > 1.0 else 1.0
        
        # Correções ambientais
        corrected *= temp_correction * altitude_correction
        
        return corrected

# Funções de conveniência para manter compatibilidade
def calculate_base_injection_time_3d(*args, **kwargs) -> float:
    """Compatibilidade: calcula tempo base de injeção."""
    return Calculator.calculate_base_injection_time_3d(*args, **kwargs)

def get_afr_target_3d(*args, **kwargs) -> float:
    """Compatibilidade: retorna AFR alvo."""
    return Calculator.get_afr_target_3d(*args, **kwargs)

def calculate_fuel_3d_matrix(*args, **kwargs) -> np.ndarray:
    """Compatibilidade: calcula matriz de combustível."""
    return Calculator.calculate_fuel_3d_matrix(*args, **kwargs)

def calculate_ignition_3d_matrix(*args, **kwargs) -> np.ndarray:
    """Compatibilidade: calcula matriz de ignição."""
    return Calculator.calculate_ignition_3d_matrix(*args, **kwargs)

def calculate_lambda_3d_matrix(*args, **kwargs) -> np.ndarray:
    """Compatibilidade: calcula matriz de lambda."""
    return Calculator.calculate_lambda_3d_matrix(*args, **kwargs)

def calculate_afr_3d_matrix(*args, **kwargs) -> np.ndarray:
    """Compatibilidade: calcula matriz de AFR."""
    return Calculator.calculate_afr_3d_matrix(*args, **kwargs)

def calculate_3d_map_values_universal(*args, **kwargs) -> np.ndarray:
    """Compatibilidade: função universal de cálculo."""
    return Calculator.calculate_3d_map_values_universal(*args, **kwargs)

def interpolate_3d_matrix(*args, **kwargs) -> np.ndarray:
    """Compatibilidade: interpola matriz."""
    return Calculator.interpolate_3d_matrix(*args, **kwargs)

# Funções para mapas 2D
def calculate_2d_map_values(axis_values: List[float], map_config: Dict[str, Any], 
                           vehicle_data: Dict[str, Any], strategy: str = "balanced") -> List[float]:
    """Calcula valores do mapa 2D baseado na estratégia e dados do veículo da sessão."""
    
    # Obter configuração do mapa
    unit = map_config.get("unit", "")
    min_val = map_config.get("min_value", 0)
    max_val = map_config.get("max_value", 100)
    map_type = map_config.get("name", "")
    
    # Obter dados do veículo da sessão
    engine_size = vehicle_data.get("displacement", 2000)  # cc
    num_cylinders = vehicle_data.get("cylinders", 4)
    fuel_type = vehicle_data.get("fuel_type", "Gasolina")
    turbo = vehicle_data.get("turbo", False)
    
    # Fatores de correção
    engine_factor = engine_size / 2000  # Normalizado para 2000cc
    
    # Fator de combustível
    fuel_factor = 1.0
    if fuel_type == "Etanol":
        fuel_factor = 1.3  # Etanol precisa de mais combustível
    elif fuel_type == "Flex":
        fuel_factor = 1.15
    
    # Fator turbo
    turbo_factor = 1.2 if turbo else 1.0
    
    # Estratégias
    strategy_factors = {
        "conservador": 0.85,
        "conservative": 0.85,
        "balanceado": 1.0,
        "balanced": 1.0,
        "agressivo": 1.15,
        "aggressive": 1.15
    }
    base_factor = strategy_factors.get(strategy.lower(), 1.0)
    
    calculated_values = []
    
    for i, axis_val in enumerate(axis_values):
        # Cálculo progressivo baseado no valor do eixo
        if map_config.get("axis_type") == "RPM":
            # Para RPM, aumenta progressivamente
            progress = axis_val / 8000  # Normalizado para 8000 RPM
        elif map_config.get("axis_type") == "TPS":
            # Para TPS, aumenta com a abertura
            progress = axis_val / 100  # TPS já em percentual
        else:  # MAP
            # Para MAP, considera vácuo vs pressão
            progress = (axis_val + 1.0) / 3.0  # Normalizado de -1 a 2 bar
        
        # Cálculo do valor baseado no tipo de mapa
        if "fuel" in map_type.lower() or "injeção" in map_type.lower():
            # Mapa de combustível - tempo de injeção
            base_time = 2.0  # ms base
            value = base_time * engine_factor * fuel_factor * turbo_factor * base_factor * (0.5 + progress)
            value = min(max(value, min_val), max_val)
            
        elif "ignition" in map_type.lower() or "ignição" in map_type.lower():
            # Mapa de ignição - avanço
            base_advance = 15  # graus base
            value = base_advance * base_factor * (0.5 + progress * 0.5)
            if turbo and progress > 0.5:
                value *= 0.9  # Reduz avanço em boost
            value = min(max(value, min_val), max_val)
            
        elif "lambda" in map_type.lower():
            # Mapa lambda
            if fuel_type == "Etanol":
                base_lambda = 0.85
            else:
                base_lambda = 1.0
            
            value = base_lambda * base_factor
            if progress > 0.7:  # Alta carga
                value *= 0.88  # Enriquece
            value = min(max(value, min_val), max_val)
            
        else:
            # Mapa genérico - escala linear
            value = min_val + (max_val - min_val) * progress * base_factor
            value = min(max(value, min_val), max_val)
        
        calculated_values.append(round(value, 2))
    
    return calculated_values