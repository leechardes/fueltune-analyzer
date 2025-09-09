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

# Estratégias de compensação para mapas 2D
COMPENSATION_STRATEGIES = {
    "tps": {
        "conservative": {"economy": -2.0, "neutral": 0.0, "power": 8.0, "wot": 12.0},
        "balanced": {"economy": -5.0, "neutral": 0.0, "power": 10.0, "wot": 15.0},
        "aggressive": {"economy": -8.0, "neutral": 0.0, "power": 15.0, "wot": 20.0},
    },
    "temp": {
        "water": {"cold_max": 25.0, "hot_max": 8.0},
        "air": {"cold_max": 30.0, "hot_max": 12.0},
    },
    "rpm": {
        "conservative": {"max_compensation": 12.0, "start_rpm": 2600},
        "balanced": {"max_compensation": 15.0, "start_rpm": 2400},
        "aggressive": {"max_compensation": 18.0, "start_rpm": 2200},
    }
}

# Funções de compensação 2D
def calculate_tps_compensation(
    tps_values: List[float], 
    strategy: str = "balanced",
    safety_factor: float = 1.0
) -> List[float]:
    """
    Calcula compensação baseada na posição do acelerador (TPS).
    
    Args:
        tps_values: Lista de valores TPS (0-100%)
        strategy: Estratégia de compensação
        safety_factor: Fator de segurança adicional
        
    Returns:
        Lista de valores de compensação em %
    """
    compensations = []
    
    strategy_factors = COMPENSATION_STRATEGIES["tps"]
    factors = strategy_factors.get(strategy, strategy_factors["balanced"])
    
    for tps in tps_values:
        if tps <= 20:  # Zona de economia
            # Interpolação linear entre 0% e -X% baseado na estratégia
            compensation = factors["economy"] * (tps / 20.0)
        elif tps <= 70:  # Zona neutra
            # Transição suave da economia para neutro
            transition = (tps - 20) / 50.0  # 0 a 1
            compensation = factors["economy"] * (1 - transition)
        elif tps < 100:  # Zona de potência
            # Transição do neutro para potência
            transition = (tps - 70) / 30.0  # 0 a 1
            compensation = factors["power"] * transition
        else:  # WOT (Wide Open Throttle)
            compensation = factors["wot"]
        
        # Aplicar fator de segurança
        compensation *= safety_factor
        
        # Limitar valores para segurança
        compensation = max(-50.0, min(50.0, compensation))
        
        compensations.append(compensation)
    
    return compensations


def calculate_temp_compensation(
    temp_values: List[float], 
    cooling_type: str = "water", 
    climate: str = "temperate",
    strategy: str = "balanced"
) -> List[float]:
    """
    Calcula compensação baseada na temperatura do motor.
    
    Args:
        temp_values: Lista de temperaturas (-10 a 140°C)
        cooling_type: Tipo de refrigeração ("water"/"air")
        climate: Tipo de clima ("cold"/"temperate"/"hot")
        strategy: Estratégia de compensação
        
    Returns:
        Lista de valores de compensação em %
    """
    compensations = []
    
    # Fatores baseados no tipo de refrigeração e clima
    cooling_factors = COMPENSATION_STRATEGIES["temp"]
    climate_factors = {"cold": 0.8, "temperate": 1.0, "hot": 1.3}
    
    cool_factor = cooling_factors.get(cooling_type, cooling_factors["water"])
    climate_mult = climate_factors.get(climate, 1.0)
    
    for temp in temp_values:
        if temp < 40:  # Motor frio
            # Enriquecimento máximo no frio, reduzindo conforme esquenta
            cold_factor = (40 - temp) / 40.0  # 1.0 a 0°C, 0.0 a 40°C
            compensation = cool_factor["cold_max"] * cold_factor * climate_mult
        elif temp <= 80:  # Aquecendo
            # Transição do enriquecimento para neutro
            warm_factor = (80 - temp) / 40.0  # 1.0 a 40°C, 0.0 a 80°C
            compensation = cool_factor["cold_max"] * 0.3 * warm_factor * climate_mult
        elif temp <= 95:  # Temperatura ideal
            compensation = 0.0
        elif temp <= 105:  # Começando a esquentar demais
            # Pequeno enriquecimento para resfriamento
            hot_factor = (temp - 95) / 10.0  # 0.0 a 95°C, 1.0 a 105°C
            compensation = cool_factor["hot_max"] * 0.3 * hot_factor * climate_mult
        else:  # Motor muito quente
            # Enriquecimento para proteção térmica
            overheat_factor = min((temp - 105) / 20.0, 1.0)  # Max em 125°C
            compensation = (
                cool_factor["hot_max"] * (0.3 + 0.7 * overheat_factor) * climate_mult
            )
        
        # Limitar valores para segurança
        compensation = max(-10.0, min(50.0, compensation))
        
        compensations.append(compensation)
    
    return compensations


def calculate_air_temp_compensation(
    air_temp_values: List[float], 
    altitude: float = 0.0,
    humidity: float = 50.0
) -> List[float]:
    """
    Calcula compensação baseada na temperatura do ar de admissão.
    Usa lei dos gases ideais para correção de densidade.
    
    Args:
        air_temp_values: Lista de temperaturas do ar (-20 a 60°C)
        altitude: Altitude em metros (opcional)
        humidity: Umidade relativa % (opcional)
        
    Returns:
        Lista de valores de compensação em %
    """
    compensations = []
    
    # Temperatura de referência: 25°C (padrão para calibração)
    ref_temp = 25.0
    
    # Correção de altitude (pressão atmosférica diminui com altitude)
    altitude_factor = 1.0 - (altitude / 10000.0)  # Aproximação simples
    
    # Correção de umidade (ar úmido é menos denso)
    humidity_factor = 1.0 - (humidity - 50.0) / 500.0
    
    for air_temp in air_temp_values:
        # Calcular densidade relativa do ar
        # Densidade = P / (R * T) onde T é temperatura absoluta
        temp_absolute = air_temp + 273.15
        ref_temp_absolute = ref_temp + 273.15
        
        # Fator de densidade (relativo à temperatura de referência)
        density_ratio = ref_temp_absolute / temp_absolute
        
        # Aplicar correções ambientais
        density_ratio *= altitude_factor * humidity_factor
        
        # Conversão para percentual de compensação
        # Se densidade é maior (ar frio), precisamos reduzir combustível
        # Se densidade é menor (ar quente), precisamos aumentar combustível
        compensation = (density_ratio - 1.0) * 100.0
        
        # Limitar correção para valores práticos
        compensation = max(-20.0, min(20.0, compensation))
        
        compensations.append(compensation)
    
    return compensations


def calculate_voltage_compensation(
    voltage_values: List[float], 
    injector_impedance: str = "high",
    injector_flow: float = 440.0
) -> List[float]:
    """
    Calcula compensação de dead time dos injetores por voltagem.
    
    Args:
        voltage_values: Lista de voltagens (8.0 a 16.0V)
        injector_impedance: Impedância dos bicos ("high"/"low")
        injector_flow: Vazão dos bicos em cc/min
        
    Returns:
        Lista de valores de compensação em ms
    """
    compensations = []
    
    # Dead time característico por tipo de bico (em ms)
    dead_time_base = {
        "high": 1.0,  # Bicos de alta impedância (12-16Ω)
        "low": 0.6,  # Bicos de baixa impedância (2-3Ω)
    }
    
    # Correção por vazão do bico (bicos maiores têm mais dead time)
    flow_factor = injector_flow / 440.0  # Normalizado para 440cc/min
    
    base_voltage = 13.5  # Voltagem de referência
    base_dead_time = dead_time_base.get(injector_impedance, dead_time_base["high"]) * flow_factor
    
    for voltage in voltage_values:
        if voltage <= 8.0:  # Voltagem muito baixa
            # Dead time muito alto, precisa muita compensação
            dead_time = base_dead_time * 2.5
        elif voltage <= 10.0:  # Voltagem baixa
            # Interpolação entre 8V e 10V
            factor = 2.5 - (voltage - 8.0) * 0.75  # 2.5 a 1.0
            dead_time = base_dead_time * factor
        elif voltage <= 12.0:  # Voltagem um pouco baixa
            # Interpolação entre 10V e 12V
            factor = 1.75 - (voltage - 10.0) * 0.375  # 1.75 a 1.0
            dead_time = base_dead_time * factor
        elif voltage <= 16.0:  # Faixa normal
            # Dead time padrão com pequena variação
            factor = 1.0 - (voltage - 13.5) * 0.05  # Pequena redução com maior voltagem
            dead_time = base_dead_time * factor
        else:  # Voltagem alta
            # Dead time reduzido, mas limitado
            dead_time = base_dead_time * 0.7
        
        # Diferença em relação ao dead time base
        compensation = dead_time - base_dead_time
        
        # Limitar para valores práticos
        compensation = max(-2.0, min(3.0, compensation))
        
        compensations.append(compensation)
    
    return compensations


def calculate_rpm_compensation(
    rpm_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced"
) -> List[float]:
    """
    Calcula compensação baseada no RPM do motor.
    
    Args:
        rpm_values: Lista de valores de RPM (400-12000)
        vehicle_data: Dados do veículo (idle_rpm, redline, has_turbo)
        strategy: Estratégia de compensação
        
    Returns:
        Lista de valores de compensação em %
    """
    compensations = []
    
    # Obter dados do veículo
    has_turbo = vehicle_data.get("turbo", False)
    redline = vehicle_data.get("redline", 7000)
    idle_rpm = vehicle_data.get("idle_rpm", 800)
    
    # Estratégias de compensação
    rpm_strategies = COMPENSATION_STRATEGIES["rpm"]
    strategy_config = rpm_strategies.get(strategy, rpm_strategies["balanced"])
    
    # Pontos de referência do comportamento FTManager
    start_correction_rpm = strategy_config["start_rpm"]
    peak_rpm = 4200 if not has_turbo else 4500  # Pico de compensação
    max_compensation = strategy_config["max_compensation"] * (1.2 if has_turbo else 1.0)
    
    for rpm in rpm_values:
        if rpm <= start_correction_rpm:
            # Sem compensação em baixas rotações (idle até start_rpm)
            compensation = 0.0
        elif rpm <= peak_rpm:
            # Compensação crescente até o pico
            progress = (rpm - start_correction_rpm) / (peak_rpm - start_correction_rpm)
            compensation = progress * max_compensation  # 0% ao máximo
        elif rpm <= redline * 0.9:
            # Compensação decrescente após o pico
            progress = (rpm - peak_rpm) / (redline * 0.9 - peak_rpm)
            compensation = max_compensation * (
                1.0 - progress * 0.7
            )  # Cai para ~30% do máximo
        elif rpm <= redline:
            # Próximo ao limitador, compensação mínima mas ainda presente
            compensation = max_compensation * 0.3  # ~30% da compensação máxima
        else:  # Acima do limitador (não deveria acontecer normalmente)
            # Compensação mínima de segurança
            compensation = 2.0
        
        # Limitar valores para segurança
        compensation = max(-10.0, min(50.0, compensation))
        
        compensations.append(compensation)
    
    return compensations


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


def calculate_map_values_universal(
    map_type: str,
    axis_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
    safety_factor: float = 1.0,
    **kwargs
) -> List[float]:
    """
    Função universal para cálculo de valores de mapas 2D.
    
    Args:
        map_type: Tipo do mapa (ex: "tps_compensation_2d")
        axis_values: Valores do eixo
        vehicle_data: Dados do veículo
        strategy: Estratégia de cálculo
        safety_factor: Fator de segurança
        **kwargs: Parâmetros adicionais específicos
        
    Returns:
        Lista de valores calculados
    """
    try:
        # Mapeamento de funções específicas
        calculation_functions = {
            "main_fuel_2d_map": calculate_2d_map_values,
            "tps_compensation_2d": calculate_tps_compensation,
            "temp_compensation_2d": calculate_temp_compensation,
            "air_temp_compensation_2d": calculate_air_temp_compensation,
            "voltage_compensation_2d": calculate_voltage_compensation,
            "rpm_compensation_2d": calculate_rpm_compensation,
        }
        
        if map_type not in calculation_functions:
            logger.warning(f"Tipo de mapa 2D não suportado: {map_type}")
            return axis_values  # Retorna valores sem modificação
        
        # Chamar função específica
        calc_func = calculation_functions[map_type]
        
        # Preparar argumentos baseado no tipo
        if map_type == "main_fuel_2d_map":
            # Para compatibilidade com função existente
            map_config = {
                "unit": "ms",
                "min_value": 0.0,
                "max_value": 50.0,
                "name": "Mapa Principal de Injeção",
                "axis_type": "MAP"
            }
            return calc_func(axis_values, map_config, vehicle_data, strategy)
            
        elif map_type == "tps_compensation_2d":
            return calc_func(axis_values, strategy, safety_factor)
            
        elif map_type == "temp_compensation_2d":
            cooling_type = vehicle_data.get("cooling_type", "water")
            climate = kwargs.get("climate", "temperate")
            return calc_func(axis_values, cooling_type, climate, strategy)
            
        elif map_type == "air_temp_compensation_2d":
            altitude = kwargs.get("altitude", 0.0)
            humidity = kwargs.get("humidity", 50.0)
            return calc_func(axis_values, altitude, humidity)
            
        elif map_type == "voltage_compensation_2d":
            injector_impedance = vehicle_data.get("injector_impedance", "high")
            injector_flow = vehicle_data.get("injector_flow", 440.0)
            return calc_func(axis_values, injector_impedance, injector_flow)
            
        elif map_type == "rpm_compensation_2d":
            return calc_func(axis_values, vehicle_data, strategy)
            
        else:
            # Função padrão para tipos não específicos
            map_config = {
                "unit": "%",
                "min_value": -50.0,
                "max_value": 50.0,
                "name": map_type,
                "axis_type": "GENERIC"
            }
            return calculate_2d_map_values(axis_values, map_config, vehicle_data, strategy)
            
    except Exception as e:
        logger.error(f"Erro no cálculo universal de mapa 2D {map_type}: {e}")
        return [0.0] * len(axis_values)  # Retorna zeros em caso de erro