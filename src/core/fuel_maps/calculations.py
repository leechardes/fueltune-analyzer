"""
Cálculos para mapas de combustível 3D.
Contém toda a lógica de cálculo de injeção, ignição, lambda e AFR.
"""

import logging
from typing import Any, Dict, List, Sequence, Tuple, Optional

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


# ======================
# VE 3D (geração padrão)
# ======================
def _interp1d(x: float, xs: Sequence[float], ys: Sequence[float]) -> float:
    """Interpolação linear 1D com extrapolação por clamp nos extremos.

    Args:
        x: ponto alvo
        xs: pontos do eixo (ordenados crescente)
        ys: valores correspondentes (mesmo tamanho de xs)
    Returns:
        valor interpolado (float)
    """
    if not xs or not ys or len(xs) != len(ys):
        return float('nan')
    if x <= xs[0]:
        return float(ys[0])
    if x >= xs[-1]:
        return float(ys[-1])
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x0 <= x <= x1 and x1 != x0:
            t = (x - x0) / (x1 - x0)
            return float(ys[i] + t * (ys[i + 1] - ys[i]))
    return float(ys[-1])


def generate_ve_3d_matrix(
    rpm_axis: Sequence[float],
    map_axis: Sequence[float],
    *,
    rpm_points: Sequence[float] = (1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000),
    ve_points: Sequence[float] = (0.70, 0.78, 0.86, 0.90, 0.88, 0.86, 0.84, 0.82),
    map_points: Sequence[float] = (-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0),
    gain_points: Sequence[float] = (0.80, 0.90, 1.00, 1.05, 1.08, 1.10, 1.12),
    ve_min: float = 0.65,
    ve_max: float = 1.10,
) -> np.ndarray:
    """Gera uma matriz VE 3D (MAP×RPM) com base em curvas simples (como no mapa.html).

    Lógica:
      - VE_base(rpm) obtido por interp1d(rpm_points, ve_points)
      - ganho(map) obtido por interp1d(map_points, gain_points)
      - VE(m,r) = clamp(VE_base(r) * ganho(m), [ve_min, ve_max])

    Args:
        rpm_axis: eixo de RPM (tamanho N)
        map_axis: eixo de MAP RELATIVO em bar (tamanho M)
        rpm_points, ve_points: curva base de VE por RPM
        map_points, gain_points: ganho por MAP relativo
        ve_min, ve_max: limites de clamp
    Returns:
        np.ndarray de shape (len(rpm_axis), len(map_axis)) com VE(m,r)
    """
    if not rpm_axis or not map_axis:
        return np.zeros((0, 0), dtype=float)
    # IMPORTANTE: O restante da aplicação usa convenção [map_idx][rpm_idx]
    # Portanto, geramos a matriz com linhas = MAP e colunas = RPM.
    matrix: List[List[float]] = []
    for m in map_axis:
        row: List[float] = []
        gain = _interp1d(float(m), map_points, gain_points)
        for r in rpm_axis:
            ve_base = _interp1d(float(r), rpm_points, ve_points)
            ve = ve_base * gain
            ve = max(ve_min, min(ve_max, ve))
            row.append(ve)
        matrix.append(row)
    return np.array(matrix, dtype=float)


# ===============================
# Malha Fechada (λ alvo) dedicada
# ===============================
def _lambda_base_from_strategy(map_rel: float, strategy: str) -> float:
    """Lambda base em função de MAP relativo (bar) por estratégia.

    Curvas alinhadas ao painel de referência (tests/mapa.html):
      CONS: -1.0:1.02, -0.3:1.00, 0.0:0.88, 0.5:0.84, 1.0:0.82, 2.0:0.80
      BAL:  -1.0:1.02, -0.3:1.01, 0.0:0.87, 0.5:0.83, 1.0:0.81, 2.0:0.79
      AGR:  -1.0:1.04, -0.3:1.02, 0.0:0.89, 0.5:0.85, 1.0:0.83, 2.0:0.81
    """
    xs = (-1.0, -0.3, 0.0, 0.5, 1.0, 2.0)
    if strategy == "conservadora":
        ys = (1.02, 1.00, 0.88, 0.84, 0.82, 0.80)
    elif strategy == "agressiva":
        ys = (1.04, 1.02, 0.89, 0.85, 0.83, 0.81)
    else:  # balanceada default
        ys = (1.02, 1.01, 0.87, 0.83, 0.81, 0.79)
    return _interp1d(map_rel, xs, ys)


def _rpm_shape_for_fuel(fuel_type: str, rpm: float, rpm_min: float, rpm_max: float) -> float:
    """Fator de forma por RPM (reduz levemente λ em alta), por tipo de combustível.
    Curvas inspiradas no painel de referência.
    """
    if rpm_max <= rpm_min:
        return 1.0
    t = min(1.0, max(0.0, (rpm - rpm_min) / (rpm_max - rpm_min)))
    ft = (fuel_type or "").lower()
    if "methanol" in ft:
        k = 0.07
    elif "ethanol" in ft:
        k = 0.06
    elif "e85" in ft:
        k = 0.05
    elif "diesel" in ft:
        k = 0.03
    elif "nitromethane" in ft or "nitro" in ft:
        k = 0.08
    else:
        k = 0.04
    return 1.0 - k * t


def calculate_lambda_target_closed_loop(
    rpm_axis: Sequence[float],
    map_axis: Sequence[float],
    *,
    strategy: str = "balanceada",
    cl_factor: float = 1.0,
    rpm_user_pairs: Optional[Sequence[Tuple[float, float]]] = None,
    fuel_type: str = "ethanol",
    lam_min: float = 0.6,
    lam_max: float = 1.5,
) -> np.ndarray:
    """Calcula a malha fechada (λ alvo) 3D no padrão do painel HTML.

    lam(m,r) = lambda_base(map_rel, strategy) * cl_factor * f_rpm_user(r) * rpm_shape(r, fuel_type)

    - lambda_base(map_rel, strategy) conforme curvas acima
    - f_rpm_user(r) = interp(rpm_user_pairs, r) ou 1.0
    - rpm_shape conforme combustível (redução leve em alta)
    - Clamp em [lam_min, lam_max]
    Retorna matriz com shape (len(map_axis), len(rpm_axis)).
    """
    if not rpm_axis or not map_axis:
        return np.zeros((0, 0), dtype=float)

    rpm_min = float(min(rpm_axis))
    rpm_max = float(max(rpm_axis))

    def f_user(r: float) -> float:
        if not rpm_user_pairs:
            return 1.0
        xs = [float(x) for x, _ in rpm_user_pairs]
        ys = [float(y) for _, y in rpm_user_pairs]
        return _interp1d(float(r), xs, ys)

    matrix: List[List[float]] = []
    eff_factor = 1.0 / max(float(cl_factor), 1e-6)
    for m in map_axis:
        lam_base = _lambda_base_from_strategy(float(m), strategy)
        row: List[float] = []
        for r in rpm_axis:
            lam = lam_base * eff_factor * f_user(float(r)) * _rpm_shape_for_fuel(fuel_type, float(r), rpm_min, rpm_max)
            lam = max(lam_min, min(lam_max, lam))
            row.append(lam)
        matrix.append(row)
    return np.array(matrix, dtype=float)


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
        fuel_pressure_base_bar: float = 3.0,
    ) -> float:
        """Calcula tempo base de injeção 3D baseado nos parâmetros do motor e RPM."""
        try:
            # MAP é pressão absoluta em kPa
            map_bar = map_kpa / 100.0

            # Calcular pressão de combustível real (1:1; vácuo não reduz abaixo da base)
            fuel_pressure_actual = fuel_pressure_base_bar + max(0.0, boost_pressure)

            # Ajustar vazão do bico baseado na pressão real
            flow_correction = (fuel_pressure_actual / fuel_pressure_base_bar) ** 0.5
            effective_flow = injector_flow_cc_min * flow_correction

            # Densidade do ar corrigida pela temperatura e pressão
            air_density_correction = map_bar / 1.013
            temperature_correction = 1.0  # Assumir temperatura padrão

            # Cálculo simplificado e corrigido
            # Volume de ar por admissão (L)
            cylinder_volume_L = engine_displacement / cylinders / 1000.0  # cc para L
            
            # Eficiência volumétrica base (varia com RPM e MAP)
            ve_base = 0.85  # 85% para motor naturalmente aspirado
            
            # Ajuste de VE por RPM
            if rpm < 1500:
                ve_rpm_factor = 0.7
            elif rpm < 3000:
                ve_rpm_factor = 0.85
            elif rpm < 5000:
                ve_rpm_factor = 0.95
            else:
                ve_rpm_factor = 0.85  # Cai em altos RPMs
            
            # VE final com correção de pressão
            ve_final = ve_base * ve_rpm_factor * air_density_correction
            
            # Volume real de ar admitido (L)
            air_volume = cylinder_volume_L * ve_final
            
            # Massa de ar (g) - densidade do ar ~1.2 g/L a 1 bar
            air_mass_g = air_volume * 1.2 * air_density_correction
            
            # Massa de combustível necessária (g)
            fuel_mass_g = air_mass_g / afr_target
            
            # Volume de combustível (ml) - densidade gasolina ~0.75 g/ml
            fuel_volume_ml = fuel_mass_g / 0.75
            
            # Tempo de injeção (ms)
            # Vazão do bico em cc/min = ml/min
            # Converter para ml/ms: effective_flow / 60000
            flow_ml_per_ms = effective_flow / 60000.0
            injection_time = fuel_volume_ml / flow_ml_per_ms

            # Sem teto/piso para não mascarar erros
            return injection_time

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
        consider_boost: bool = True,
        apply_fuel_corr: bool = False,
        ve_matrix: Optional[np.ndarray] = None,
        lambda_matrix: Optional[np.ndarray] = None,
        afr_stoich: Optional[float] = None,
    ) -> np.ndarray:
        """Calcula matriz 3D de PW (ms) usando VE, λ e parâmetros físicos.

        Fórmula por célula (m,r):
          - P_abs_bar = 1 + MAP_rel
          - m_ar_kg = (P_abs_Pa * V_cyl_m3) / (R * T) * VE(m,r)
          - AFR_target = (afr_stoich * λ(m,r)) se λ disponível; senão AFR da estratégia ajustado por FS (1/FS)
          - m_fuel_mg = (m_ar_kg * 1e6) / AFR_target
          - flow_mg_ms = (cc/min por bico) → ml/ms × densidade × 1000, corrigido por sqrt(ΔP/base)
          - PW_ms = m_fuel_mg / flow_mg_ms (com DT/PW_min opcionais)
        """
        rows = len(map_axis)
        cols = len(rpm_axis)
        matrix = np.zeros((rows, cols), dtype=float)

        # Parâmetros do motor
        raw_disp = float(vehicle_data.get("displacement", 2.0))
        engine_cc = raw_disp * 1000.0 if raw_disp < 50 else raw_disp  # aceita L ou cc
        cylinders = max(1, int(vehicle_data.get("cylinders", 4)))
        v_cyl_m3 = (engine_cc / cylinders) / 1e6  # cc → m^3

        # Temperatura do ar (IAT) – se não houver, usar 40°C (mais próximo do painel)
        iat_c = float(vehicle_data.get("iat_c", vehicle_data.get("air_temp_c", 40.0)))
        T = 273.15 + iat_c
        R = 287.0

        # VE matrix (fração). Se não fornecida, usar gerador padrão
        if ve_matrix is None or ve_matrix.shape != (rows, cols):
            from .calculations import generate_ve_3d_matrix
            ve_matrix = generate_ve_3d_matrix(rpm_axis, map_axis)

        # AFR estequiométrico por combustível, se não fornecido
        if afr_stoich is None:
            fuel = str(vehicle_data.get("fuel_type", "")).lower()
            if "ethanol" in fuel or "etanol" in fuel:
                afr_stoich = 9.0
            elif "e85" in fuel:
                afr_stoich = 9.8
            elif "diesel" in fuel:
                afr_stoich = 14.5
            elif "gnv" in fuel or "cng" in fuel:
                afr_stoich = 17.2
            elif "methanol" in fuel or "metanol" in fuel:
                afr_stoich = 6.4
            else:
                afr_stoich = 14.7  # Gasolina default
        # Se não quiser aplicar correção por combustível, padronizar em gasolina
        if not apply_fuel_corr:
            afr_stoich = 14.7

        # Fluxo por bico (cc/min) resolvido
        inj_cc_min = vehicle_data.get("injector_flow")
        if inj_cc_min is None:
            inj_cc_min = vehicle_data.get("injector_flow_cc")
        if inj_cc_min is None and vehicle_data.get("injector_flow_lbs") is not None:
            inj_cc_min = float(vehicle_data.get("injector_flow_lbs")) * 10.5
        inj_cc_min = float(inj_cc_min or 440.0)
        # Se parecer total, dividir por cilindros
        if inj_cc_min > 1500.0:
            inj_cc_min = inj_cc_min / cylinders

        # Densidade do combustível (gasolina aprox.)
        fuel_density_g_per_ml = 0.75
        # Fluxo nominal por bico em mg/ms a 3 bar
        flow_ml_ms_nom = inj_cc_min / 60000.0
        flow_mg_ms_nom = flow_ml_ms_nom * fuel_density_g_per_ml * 1000.0

        # Pressões
        base_bar = float(vehicle_data.get("fuel_pressure_base_bar", 3.0))
        regulator_11 = bool(vehicle_data.get("regulator_1_1", True))

        # Fator de segurança como riqueza (FS>1 => mais rico)
        eff_fs = 1.0 / max(float(safety_factor), 1e-6)

        # Parâmetros de tempo mínimos (defaults alinhados ao painel HTML)
        dead_time_ms = float(vehicle_data.get("dead_time_ms", 1.0))
        pw_min = float(vehicle_data.get("pw_min_ms", 1.6))

        for i, map_rel in enumerate(map_axis):
            p_abs_bar = 1.0 + float(map_rel)
            if not consider_boost and p_abs_bar > 1.0:
                p_abs_bar = 1.0
            p_abs_pa = p_abs_bar * 1e5
            # ΔP em bar
            if regulator_11:
                delta_p_bar = base_bar
            else:
                delta_p_bar = base_bar - float(map_rel)
            delta_p_bar = max(0.0, delta_p_bar)
            # Correção de fluxo pela raiz
            flow_mg_ms = flow_mg_ms_nom * (delta_p_bar / base_bar) ** 0.5 if base_bar > 0 else 0.0

            for j, rpm in enumerate(rpm_axis):
                ve = float(ve_matrix[i, j])
                # Massa de ar por admissão (mg)
                m_air_mg = (p_abs_pa * v_cyl_m3) / (R * T) * ve * 1e6

                # AFR alvo (aplicar fator de segurança como riqueza em ambos os casos)
                if lambda_matrix is not None and lambda_matrix.shape == (rows, cols):
                    lam = float(lambda_matrix[i, j])
                    afr_target = afr_stoich * lam
                else:
                    # AFR por estratégia (kPa) → converter para λ (dividir por 14.7)
                    map_kpa = p_abs_bar * 100.0
                    afr_gas = Calculator.get_afr_target_3d(map_kpa, strategy)
                    lam_strategy = afr_gas / 14.7
                    afr_target = afr_stoich * lam_strategy
                # Fator de segurança: FS>1 ⇒ mistura mais rica (AFR menor)
                afr_target *= eff_fs

                # Massa de combustível (mg)
                afr_target = max(0.1, float(afr_target))
                m_fuel_mg = m_air_mg / afr_target

                # Tempo de injeção (ms)
                if flow_mg_ms > 0:
                    pw = m_fuel_mg / flow_mg_ms
                else:
                    pw = 0.0
                pw = max(pw + dead_time_ms, pw_min)
                matrix[i, j] = pw

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
            # VE 3D (fração) e Tabela de VE 3D (percentual)
            if map_type in ("ve_3d_map", "ve_table_3d_map"):
                from .calculations import generate_ve_3d_matrix
                ve = generate_ve_3d_matrix(rpm_axis, map_axis)
                if map_type == "ve_table_3d_map":
                    return ve * 100.0  # tabela em %
                return ve
            if map_type == "main_fuel_3d_map":
                return Calculator.calculate_fuel_3d_matrix(
                    rpm_axis,
                    map_axis,
                    vehicle_data,
                    strategy=kwargs.get("strategy", "balanced"),
                    safety_factor=kwargs.get("safety_factor", 1.0),
                    consider_boost=kwargs.get("consider_boost", True),
                    apply_fuel_corr=kwargs.get("apply_fuel_corr", False),
                    ve_matrix=kwargs.get("ve_matrix"),
                    lambda_matrix=kwargs.get("lambda_matrix"),
                    afr_stoich=kwargs.get("afr_stoich"),
                )
            elif map_type in ("ignition_timing_3d_map", "ignition_3d_map"):
                return Calculator.calculate_ignition_3d_matrix(
                    rpm_axis, map_axis, vehicle_data,
                    kwargs.get("octane_rating", 91.0)
                )
            elif map_type == "lambda_target_3d_map":
                # Nova malha fechada dedicada
                cl_factor = kwargs.get("cl_factor", 1.0)
                rpm_user_pairs = kwargs.get("rpm_user_pairs")  # Optional[List[Tuple[rpm, fator]]]
                fuel_type = str(vehicle_data.get("fuel_type", "ethanol"))
                from .calculations import calculate_lambda_target_closed_loop
                return calculate_lambda_target_closed_loop(
                    rpm_axis, map_axis,
                    strategy=kwargs.get("strategy", "balanceada"),
                    cl_factor=cl_factor,
                    rpm_user_pairs=rpm_user_pairs,
                    fuel_type=fuel_type,
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
def _legacy_base_injection_time_2d(
    map_kpa: float,
    engine_displacement_l: float,
    cylinders: int,
    injector_flow_cc_total: float,
    afr_target: float,
    boost_pressure_bar: float,
    fuel_pressure_base_bar: float = 3.0,
) -> float:
    """Reprodução do cálculo base do backup para mapas 2D (por ciclo, por cilindro)."""
    try:
        map_bar_abs = map_kpa / 100.0

        # Pressão de combustível real (1:1; sem redução em vácuo)
        fuel_pressure_actual = fuel_pressure_base_bar + max(0.0, boost_pressure_bar)
        flow_correction = (fuel_pressure_actual / fuel_pressure_base_bar) ** 0.5
        injector_flow_corrected = injector_flow_cc_total * flow_correction

        # VE por faixas (backup)
        if map_bar_abs <= 0.2:
            ve = 0.25 + (map_bar_abs * 1.0)
        elif map_bar_abs <= 0.4:
            ve = 0.45 + (map_bar_abs - 0.2) * 0.5
        elif map_bar_abs <= 0.6:
            ve = 0.55 + (map_bar_abs - 0.4) * 0.75
        elif map_bar_abs <= 0.8:
            ve = 0.70 + (map_bar_abs - 0.6) * 0.5
        elif map_bar_abs <= 1.013:
            ve = 0.80 + (map_bar_abs - 0.8) * 0.7
        elif map_bar_abs <= 1.5:
            ve = 0.95 + (map_bar_abs - 1.013) * 0.1
        elif map_bar_abs <= 2.0:
            ve = 1.00 + (map_bar_abs - 1.5) * 0.2
        else:
            ve = 1.10 + min((map_bar_abs - 2.0) * 0.15, 0.2)

        rpm = 3000.0
        cylinder_volume_l = engine_displacement_l / cylinders

        # Fluxo de ar por cilindro (L/min), 4 tempos: /2
        air_flow_per_cyl_l_min = (cylinder_volume_l * ve * rpm) / 2.0
        air_mass_g_min = air_flow_per_cyl_l_min * 1.2
        fuel_mass_g_min = air_mass_g_min / afr_target

        # Converter vazão de bico para g/min por cilindro (densidade gasolina ~0.75 g/ml)
        fuel_density_g_per_cc = 0.75
        injector_flow_g_min_per_cyl = (injector_flow_corrected / cylinders) * fuel_density_g_per_cc

        duty_cycle = (fuel_mass_g_min / injector_flow_g_min_per_cyl) if injector_flow_g_min_per_cyl > 0 else 0.0
        time_per_cycle_ms = (60000.0 / rpm) * 2.0  # injeta a cada 2 rotações
        injection_time_ms = time_per_cycle_ms * duty_cycle

        # Dead time típico do backup
        injection_time_ms += 1.0

        # Ajuste suave por pressão absoluta (backup)
        pressure_factor = map_bar_abs / 1.013
        if pressure_factor < 1.0:
            injection_time_ms *= (0.3 + 0.7 * pressure_factor)
        else:
            injection_time_ms *= (1.0 + (pressure_factor - 1.0) * 0.5)

        return injection_time_ms
    except Exception:
        return 2.0

def calculate_main_fuel_2d_legacy(
    axis_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
) -> List[float]:
    """Calcula o mapa principal 2D reproduzindo a lógica de maps_2d (backup)."""
    # Displacement em litros (backup usava L; se vier em cc, converter)
    raw_disp = vehicle_data.get("displacement", 2.0)
    try:
        disp_val = float(raw_disp)
    except (TypeError, ValueError):
        disp_val = 2.0
    engine_l = disp_val / 1000.0 if disp_val > 50 else disp_val

    cylinders = int(vehicle_data.get("cylinders", 4))

    # Vazão TOTAL do conjunto (cc/min); se vier em lb/h total, converter
    injector_flow_total = vehicle_data.get("injector_flow_cc")
    if injector_flow_total is None and vehicle_data.get("injector_flow_lbs") is not None:
        try:
            injector_flow_total = float(vehicle_data.get("injector_flow_lbs")) * 10.5
        except (TypeError, ValueError):
            injector_flow_total = None
    if injector_flow_total is None:
        injector_flow_total = 550.0  # padrão compatível com backup
    else:
        injector_flow_total = float(injector_flow_total)

    fuel_pressure_base_bar = float(vehicle_data.get("fuel_pressure_base_bar", 3.0))

    values: List[float] = []
    for axis_val in axis_values:
        try:
            map_rel = float(axis_val)
        except (TypeError, ValueError):
            map_rel = 0.0

        map_abs_bar = map_rel + 1.013
        map_kpa = map_abs_bar * 100.0
        boost_rel = max(0.0, map_rel)

        afr_target = Calculator.get_afr_target_3d(map_kpa, strategy)

        base_time = _legacy_base_injection_time_2d(
            map_kpa=map_kpa,
            engine_displacement_l=engine_l,
            cylinders=cylinders,
            injector_flow_cc_total=injector_flow_total,
            afr_target=afr_target,
            boost_pressure_bar=boost_rel,
            fuel_pressure_base_bar=fuel_pressure_base_bar,
        )

        # Correção por combustível (backup via apply_fuel_correction)
        fuel_type = str(vehicle_data.get("fuel_type", "gasoline")).lower()
        if "e85" in fuel_type:
            base_time *= 1.3
        elif "ethanol" in fuel_type or "etanol" in fuel_type:
            base_time *= 1.4
        elif "flex" in fuel_type:
            base_time *= 1.2

        values.append(round(base_time, 2))

    return values

def calculate_main_fuel_2d_realistic(
    axis_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
    safety_factor: float = 1.0,
    *,
    consider_boost: bool = True,
    apply_fuel_corr: bool = True,
    regulator_11: bool = True,
    ref_rpm: Optional[float] = None,
    cl_factor: float = 1.0,
) -> List[float]:
    """Calcula o mapa principal 2D (MAP→PW ms) usando o mesmo modelo físico 3D.

    Colapsa o cálculo 3D em uma linha de RPM de referência (ref_rpm).
    Usa VE por célula (gerada) e opcionalmente λ alvo por célula.
    """
    try:
        rrpm = float(ref_rpm) if ref_rpm and ref_rpm > 0 else 3000.0
        rpm_axis = [rrpm]
        map_axis = [float(m) for m in axis_values]

        ve_matrix = generate_ve_3d_matrix(rpm_axis, map_axis)  # [map][rpm=1]
        lam_matrix = calculate_lambda_target_closed_loop(
            rpm_axis, map_axis, strategy=strategy, cl_factor=cl_factor,
            fuel_type=str(vehicle_data.get('fuel_type', 'ethanol'))
        )

        vcalc = dict(vehicle_data)
        vcalc["regulator_1_1"] = bool(regulator_11)

        mat = Calculator.calculate_fuel_3d_matrix(
            rpm_axis=rpm_axis,
            map_axis=map_axis,
            vehicle_data=vcalc,
            strategy=strategy,
            safety_factor=safety_factor,
            consider_boost=consider_boost,
            apply_fuel_corr=apply_fuel_corr,
            ve_matrix=ve_matrix,
            lambda_matrix=lam_matrix,
        )

        return [float(row[0]) for row in mat]
    except Exception as e:
        logger.error(f"Erro cálculo 2D realista: {e}")
        return [2.0 for _ in axis_values]

def calculate_main_fuel_rpm_2d_realistic(
    axis_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
    safety_factor: float = 1.0,
    *,
    consider_boost: bool = True,
    apply_fuel_corr: bool = True,
    regulator_11: bool = True,
    map_ref: Optional[float] = None,
    cl_factor: float = 1.0,
) -> List[float]:
    """Calcula PW 2D em função do RPM, usando um MAP de referência.

    Colapsa o cálculo 3D em uma coluna de MAP de referência (map_ref).
    Usa VE por célula e λ alvo por célula.
    """
    try:
        mref = float(map_ref) if map_ref is not None else 0.0
        rpm_axis = [float(r) for r in axis_values]
        map_axis = [mref]

        ve_matrix = generate_ve_3d_matrix(rpm_axis, map_axis)  # shape [map=1][rpm=N] pois nossa função gera [map][rpm]
        # Nossa generate_ve_3d_matrix espera (rpm_axis, map_axis) mas gera shape (len(map), len(rpm))
        # Acima passamos (rpm_axis, [map_ref]) então ve_matrix tem shape (1, N).

        lam_matrix = calculate_lambda_target_closed_loop(
            rpm_axis, map_axis, strategy=strategy, cl_factor=cl_factor,
            fuel_type=str(vehicle_data.get('fuel_type', 'ethanol'))
        )  # shape (1, N)

        vcalc = dict(vehicle_data)
        vcalc["regulator_1_1"] = bool(regulator_11)

        # A função 3D espera axes como listas: usamos rpm_axis=N, map_axis=1
        mat = Calculator.calculate_fuel_3d_matrix(
            rpm_axis=rpm_axis,
            map_axis=map_axis,
            vehicle_data=vcalc,
            strategy=strategy,
            safety_factor=safety_factor,
            consider_boost=consider_boost,
            apply_fuel_corr=apply_fuel_corr,
            ve_matrix=ve_matrix,
            lambda_matrix=lam_matrix,
        )  # shape (len(map)=1, len(rpm)=N)

        # Extrair a única linha (map_ref)
        row = mat[0]
        return [float(v) for v in row]
    except Exception as e:
        logger.error(f"Erro cálculo RPM 2D realista: {e}")
        return [2.0 for _ in axis_values]
def calculate_2d_map_values(axis_values: List[float], map_config: Dict[str, Any], 
                           vehicle_data: Dict[str, Any], strategy: str = "balanced") -> List[float]:
    """Calcula valores do mapa 2D baseado na estratégia e dados do veículo da sessão."""
    
    # Obter configuração do mapa
    unit = map_config.get("unit", "")
    min_val = map_config.get("min_value", 0)
    max_val = map_config.get("max_value", 100)
    map_type = map_config.get("name", "")
    
    # Obter dados do veículo da sessão
    # Displacement pode vir em litros (ex.: 1.9) ou cc (ex.: 1900)
    raw_displacement = vehicle_data.get("displacement", 2000)
    try:
        disp_val = float(raw_displacement)
    except (TypeError, ValueError):
        disp_val = 2000.0
    displacement_cc = disp_val * 1000.0 if disp_val < 50 else disp_val

    num_cylinders = vehicle_data.get("cylinders", 4)
    fuel_type_raw = vehicle_data.get("fuel_type", "Gasolina")
    fuel_type = str(fuel_type_raw).lower()
    turbo = vehicle_data.get("turbo", False)
    
    # Fatores de correção
    engine_factor = displacement_cc / 2000.0  # Normalizado para 2000cc
    
    # Fator de combustível
    fuel_factor = 1.0
    if "e85" in fuel_type:
        fuel_factor = 1.35
    elif "etanol" in fuel_type or "ethanol" in fuel_type:
        fuel_factor = 1.3  # Etanol precisa de mais combustível
    elif "flex" in fuel_type:
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

    # Resolver vazão por bico (cc/min)
    cylinders = int(num_cylinders) if num_cylinders else 4
    flow_per_injector = vehicle_data.get("injector_flow")
    if flow_per_injector is None:
        flow_cc = vehicle_data.get("injector_flow_cc")
        if flow_cc is not None:
            try:
                flow_cc = float(flow_cc)
                # Heurística: valores muito altos sugerem vazão total → dividir pelos cilindros
                flow_per_injector = flow_cc / cylinders if flow_cc > 900 else flow_cc
            except (TypeError, ValueError):
                flow_per_injector = None
    if flow_per_injector is None and vehicle_data.get("injector_flow_lbs") is not None:
        try:
            lbs_total = float(vehicle_data.get("injector_flow_lbs"))
            # Conversão aproximada: 1 lb/h ≈ 10.5 cc/min
            flow_cc_total = lbs_total * 10.5
            flow_per_injector = flow_cc_total / cylinders if cylinders else flow_cc_total
        except (TypeError, ValueError):
            flow_per_injector = None
    if flow_per_injector is None:
        flow_per_injector = 440.0  # padrão seguro

    for i, axis_val in enumerate(axis_values):
        # Para mapas principais 2D (eixo = MAP), usar modelo físico simplificado
        if ("fuel" in map_type.lower() or "injeção" in map_type.lower()) and map_config.get("axis_type") == "MAP":
            # MAP relativo (bar): -1.0 .. 2.0
            try:
                map_rel = float(axis_val)
            except (TypeError, ValueError):
                map_rel = 0.0
            map_abs_bar = map_rel + 1.013
            map_kpa = map_abs_bar * 100.0

            # AFR alvo por ponto (usa mesma curva do 3D)
            afr_point = Calculator.get_afr_target_3d(map_kpa, strategy)

            # Boost relativo em bar
            boost_rel_bar = max(0.0, map_rel)

            # Calcular tempo base a 3000 RPM usando rotina 3D (espera fluxo por bico)
            inj_time = Calculator.calculate_base_injection_time_3d(
                map_kpa=map_kpa,
                rpm=3000.0,
                engine_displacement=displacement_cc,
                cylinders=cylinders,
                injector_flow_cc_min=float(flow_per_injector),
                afr_target=afr_point,
                boost_pressure=boost_rel_bar,
                fuel_pressure_base_bar=float(vehicle_data.get("fuel_pressure_base_bar", 3.0)),
            )

            # Correção por combustível
            if "e85" in fuel_type:
                inj_time *= 1.35
            elif "etanol" in fuel_type or "ethanol" in fuel_type:
                inj_time *= 1.30
            elif "flex" in fuel_type:
                inj_time *= 1.15

            # Dead time típico
            inj_time += 1.0

            # Aplicar estratégia e BSFC (ajuste fino); sem multiplicar engine/turbo novamente
            inj_time *= base_factor
            inj_time *= float(vehicle_data.get("bsfc_factor", 1.0))

            # Sem teto/piso para não mascarar erros
            value = inj_time

        elif "ignition" in map_type.lower() or "ignição" in map_type.lower():
            # Mapa de ignição - avanço
            base_advance = 15  # graus base
            # Para eixos não-MAP, manter progressão simples
            if map_config.get("axis_type") == "RPM":
                progress = axis_val / 8000
            elif map_config.get("axis_type") == "TPS":
                progress = axis_val / 100
            else:
                progress = (axis_val + 1.0) / 3.0
            value = base_advance * base_factor * (0.5 + progress * 0.5)
            if turbo and progress > 0.5:
                value *= 0.9  # Reduz avanço em boost
            value = min(max(value, min_val), max_val)
            
        elif "lambda" in map_type.lower():
            # Mapa lambda
            if "etanol" in fuel_type or "ethanol" in fuel_type:
                base_lambda = 0.85
            else:
                base_lambda = 1.0
            
            value = base_lambda * base_factor
            if progress > 0.7:  # Alta carga
                value *= 0.88  # Enriquece
            value = min(max(value, min_val), max_val)
            
        else:
            # Mapa genérico - escala linear
            if map_config.get("axis_type") == "RPM":
                progress = axis_val / 8000
            elif map_config.get("axis_type") == "TPS":
                progress = axis_val / 100
            else:
                progress = (axis_val + 1.0) / 3.0
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
            return calculate_main_fuel_2d_realistic(
                axis_values,
                vehicle_data,
                strategy,
                safety_factor,
                consider_boost=kwargs.get("consider_boost", True),
                apply_fuel_corr=kwargs.get("apply_fuel_corr", True),
                regulator_11=kwargs.get("regulator_11", True),
                ref_rpm=kwargs.get("ref_rpm"),
                cl_factor=kwargs.get("cl_factor", 1.0),
            )
        if map_type == "main_fuel_rpm_2d_map":
            return calculate_main_fuel_rpm_2d_realistic(
                axis_values,
                vehicle_data,
                strategy,
                safety_factor,
                consider_boost=kwargs.get("consider_boost", True),
                apply_fuel_corr=kwargs.get("apply_fuel_corr", True),
                regulator_11=kwargs.get("regulator_11", True),
                map_ref=kwargs.get("map_ref", 0.0),
                cl_factor=kwargs.get("cl_factor", 1.0),
            )
            
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
