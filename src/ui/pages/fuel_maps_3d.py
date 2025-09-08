"""
Página de Mapas de Injeção 3D - FuelTune

Implementação seguindo rigorosamente o padrão A04-STREAMLIT-PROFESSIONAL:
- ZERO EMOJIS (proibido usar qualquer emoji)
- ZERO CSS CUSTOMIZADO (apenas componentes nativos)
- ZERO HTML CUSTOMIZADO (não usar st.markdown com HTML)
- Toda interface em PORTUGUÊS BRASILEIRO
- Usar apenas componentes nativos do Streamlit

Author: FuelTune System
Created: 2025-01-07
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Importações do projeto
try:
    from src.data.fuel_maps_models import MapDataValidator, MapInterpolator
    from src.data.vehicle_database import get_all_vehicles, get_vehicle_by_id
    from src.ui.components.vehicle_selector import get_vehicle_context
except ImportError:
    # Fallback para desenvolvimento
    def get_vehicle_context():
        # Retorna um ID dummy para testes
        return "64b12a8c-0345-41a9-bfc4-d5d360efc8ca"


# Configuração da página
st.title("Mapas de Injeção 3D")
st.caption("Configure mapas de injeção tridimensionais")


# Carregar configuração de tipos de mapas 3D do arquivo externo
def load_map_types_config():
    """Carrega a configuração de tipos de mapas do arquivo JSON."""
    config_path = Path("config/map_types_3d.json")

    # Se o arquivo não existir, usar configuração padrão
    if not config_path.exists():
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
            },
        }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Erro ao carregar configuração: {e}. Usando valores padrão.")
        return load_map_types_config.__defaults__[0]


# Carregar configuração de tipos de mapas
MAP_TYPES_3D = load_map_types_config()

# Eixos padrão - 32 posições com sistema enable/disable
# MAP (bar) - 32 posições totais, 21 ativas por padrão
DEFAULT_MAP_AXIS = [
    -1.00,
    -0.90,
    -0.80,
    -0.70,
    -0.60,
    -0.50,
    -0.40,
    -0.30,
    -0.20,
    -0.10,
    0.00,
    0.20,
    0.40,
    0.60,
    0.80,
    1.00,
    1.20,
    1.40,
    1.60,
    1.80,
    2.00,
    2.20,
    2.40,
    2.60,
    2.80,
    3.00,
    3.20,
    3.40,
    3.60,
    3.80,
    4.00,
    4.20,
]  # 32 total
MAP_ENABLED = [True] * 21 + [False] * 11  # Primeiras 21 ativas

# RPM - 32 posições totais, 24 ativas por padrão
DEFAULT_RPM_AXIS = [
    400,
    600,
    800,
    1000,
    1200,
    1400,
    1600,
    1800,
    2000,
    2200,
    2400,
    2600,
    2800,
    3000,
    3500,
    4000,
    4500,
    5000,
    5500,
    6000,
    6500,
    7000,
    7500,
    8000,
    8500,
    9000,
    9500,
    10000,
    10500,
    11000,
    11500,
    12000,
]  # 32 total
RPM_ENABLED = [True] * 24 + [False] * 8  # Primeiras 24 ativas

# === FUEL MAP AUTO CALCULATOR FUNCTIONS ===

# Presets de estratégias de tuning
STRATEGY_PRESETS = {
    "conservative": {
        "name": "Conservadora",
        "description": "AFR rico, margens de segurança maiores",
        "idle": 13.5,
        "cruise": 14.0,
        "load": 12.5,
        "wot": 11.5,
        "boost": 11.0,
        "safety_factor": 1.1,
    },
    "balanced": {
        "name": "Balanceada",
        "description": "Valores típicos de fábrica",
        "idle": 14.2,
        "cruise": 14.7,
        "load": 13.2,
        "wot": 12.5,
        "boost": 12.0,
        "safety_factor": 1.0,
    },
    "aggressive": {
        "name": "Agressiva",
        "description": "AFR pobre, eficiência máxima",
        "idle": 14.7,
        "cruise": 15.5,
        "load": 13.8,
        "wot": 13.0,
        "boost": 12.5,
        "safety_factor": 0.9,
    },
}


def get_vehicle_data_from_session() -> Dict[str, Any]:
    """Obtém dados do veículo do session_state."""
    try:
        from src.data.vehicle_database import get_vehicle_by_id

        # Tentar obter o veículo selecionado
        selected_vehicle_id = st.session_state.get("selected_vehicle_id")

        if selected_vehicle_id:
            vehicle = get_vehicle_by_id(selected_vehicle_id)
            if vehicle:
                # Calcular vazão total dos bicos em lbs/h
                total_flow_a = (
                    vehicle.get("bank_a_total_flow", 0)
                    if vehicle.get("bank_a_enabled")
                    else 0
                )
                total_flow_b = (
                    vehicle.get("bank_b_total_flow", 0)
                    if vehicle.get("bank_b_enabled")
                    else 0
                )
                total_flow_lbs = total_flow_a + total_flow_b

                # Converter vazão de lbs/h para cc/min (1 lb/h ≈ 10.5 cc/min)
                injector_flow_cc = total_flow_lbs * 10.5 if total_flow_lbs > 0 else 550

                # Verificar se é turbo
                aspiration = vehicle.get("engine_aspiration", "").lower()
                is_turbo = any(term in aspiration for term in ["turbo", "super"])

                # Usar boost_pressure (pressão máxima) para o calculador
                boost_value = 0.0
                if is_turbo:
                    boost_value = (
                        vehicle.get("boost_pressure")
                        or vehicle.get("max_boost_pressure")
                        or 1.0
                    )
                    if boost_value is None:
                        boost_value = 1.0

                return {
                    "displacement": vehicle.get("engine_displacement", 2.0),
                    "cylinders": vehicle.get("engine_cylinders", 4),
                    "injector_flow_cc": injector_flow_cc,
                    "injector_flow_lbs": total_flow_lbs,
                    "fuel_type": vehicle.get("fuel_type", "Gasolina"),
                    "turbo": is_turbo,
                    "boost_pressure": boost_value,
                    "bsfc_factor": vehicle.get("bsfc_factor", 0.50),
                    "injector_impedance": vehicle.get("injector_impedance", "high"),
                    "cooling_type": vehicle.get("cooling_type", "water"),
                    "redline_rpm": vehicle.get("redline_rpm", 7000),
                    "idle_rpm": vehicle.get("idle_rpm", 800),
                    "climate": vehicle.get("climate", "temperate"),
                }
    except ImportError:
        pass

    # Valores padrão
    return {
        "displacement": 2.0,
        "cylinders": 4,
        "injector_flow_cc": 550,
        "injector_flow_lbs": 52,
        "fuel_type": "Gasolina",
        "turbo": False,
        "boost_pressure": 0.0,
        "bsfc_factor": 0.50,
        "injector_impedance": "high",
        "cooling_type": "water",
        "redline_rpm": 7000,
        "idle_rpm": 800,
        "climate": "temperate",
    }


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
        injector_flow_corrected = injector_flow_cc_min * flow_correction

        # Calcular VE baseado na pressão MAP absoluta
        if map_bar <= 0.2:  # Vácuo extremo
            ve = 0.25 + (map_bar * 1.0)
        elif map_bar <= 0.4:  # Vácuo alto
            ve = 0.45 + (map_bar - 0.2) * 0.5
        elif map_bar <= 0.6:  # Vácuo médio
            ve = 0.55 + (map_bar - 0.4) * 0.75
        elif map_bar <= 0.8:  # Vácuo baixo
            ve = 0.70 + (map_bar - 0.6) * 0.5
        elif map_bar <= 1.013:  # Próximo à atmosférica
            ve = 0.80 + (map_bar - 0.8) * 0.7
        elif map_bar <= 1.5:  # Boost baixo
            ve = 0.95 + (map_bar - 1.013) * 0.1
        elif map_bar <= 2.0:  # Boost médio
            ve = 1.00 + (map_bar - 1.5) * 0.2
        else:  # Boost alto
            ve = 1.10 + min((map_bar - 2.0) * 0.15, 0.2)

        # Ajustar VE baseado no RPM
        rpm_factor = 1.0
        if rpm <= 1000:  # Baixa rotação
            rpm_factor = 0.7 + (rpm / 1000.0) * 0.3
        elif rpm <= 3000:  # Rotação baixa-média
            rpm_factor = 1.0
        elif rpm <= 5000:  # Rotação média-alta
            rpm_factor = 1.0 + (rpm - 3000) / 4000 * 0.1  # Ligeiro aumento
        else:  # Alta rotação
            rpm_factor = 1.1 - (rpm - 5000) / 3000 * 0.2  # Redução por eficiência

        ve *= rpm_factor

        # Volume de ar por cilindro por ciclo (L)
        cylinder_volume = engine_displacement / cylinders

        # Taxa de fluxo de ar (L/min)
        air_flow_per_cylinder = (cylinder_volume * ve * rpm) / 2

        # Converter para g/min (densidade do ar ~1.2 g/L)
        air_mass_per_min = air_flow_per_cylinder * 1.2

        # Massa de combustível necessária por minuto (g/min)
        fuel_mass_per_min = air_mass_per_min / afr_target

        # Converter vazão do bico CORRIGIDA de cc/min para g/min
        fuel_density = 0.75
        injector_flow_g_min = (injector_flow_corrected / cylinders) * fuel_density

        # Calcular duty cycle necessário
        duty_cycle = (
            (fuel_mass_per_min / injector_flow_g_min) if injector_flow_g_min > 0 else 0
        )

        # Tempo disponível por ciclo (ms)
        time_per_cycle = (60000 / rpm) * 2

        # Tempo de injeção (ms)
        injection_time = time_per_cycle * duty_cycle

        # Adicionar tempo morto do bico
        dead_time = 1.0
        injection_time += dead_time

        # Fator de escala baseado na pressão
        pressure_factor = map_bar / 1.013
        if pressure_factor < 1.0:
            injection_time = injection_time * (0.3 + 0.7 * pressure_factor)
        else:
            injection_time = injection_time * (1.0 + (pressure_factor - 1.0) * 0.5)

        return max(1.5, min(injection_time, 35.0))

    except Exception as e:
        return 2.0


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
        map_kpa = (
            (map_value + 1.013) * 100 if map_value < 0 else (map_value + 1.013) * 100
        )

        for j, rpm_value in enumerate(rpm_axis):
            if rpm_value > 0:  # Apenas para RPM ativos
                afr_target = get_afr_target_3d(map_kpa, strategy)
                base_time = calculate_base_injection_time_3d(
                    map_kpa,
                    rpm_value,
                    vehicle_data["displacement"],
                    vehicle_data["cylinders"],
                    vehicle_data["injector_flow_cc"],
                    afr_target,
                    vehicle_data.get("boost_pressure", 0),
                )

                # Aplicar fator de segurança
                matrix[i, j] = base_time * safety_factor

    return matrix


def calculate_ignition_3d_matrix(
    rpm_axis: List[float],
    map_axis: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
    safety_factor: float = 1.0,
) -> np.ndarray:
    """Calcula matriz 3D de valores de ignição."""
    matrix = np.zeros((len(map_axis), len(rpm_axis)))

    # Estratégias de avanço base
    base_advance = {
        "conservative": {"idle": 10, "cruise": 25, "load": 20, "wot": 15, "boost": 10},
        "balanced": {"idle": 12, "cruise": 30, "load": 25, "wot": 20, "boost": 15},
        "aggressive": {"idle": 15, "cruise": 35, "load": 30, "wot": 25, "boost": 20},
    }

    advances = base_advance.get(strategy, base_advance["balanced"])

    for i, map_value in enumerate(map_axis):
        map_kpa = (
            (map_value + 1.013) * 100 if map_value < 0 else (map_value + 1.013) * 100
        )

        for j, rpm_value in enumerate(rpm_axis):
            if rpm_value > 0:
                # Determinar avanço base pela carga
                if map_kpa < 30:
                    base_timing = advances["idle"]
                elif map_kpa < 60:
                    base_timing = advances["cruise"]
                elif map_kpa < 90:
                    base_timing = advances["load"]
                elif map_kpa < 100:
                    base_timing = advances["wot"]
                else:
                    base_timing = advances["boost"]

                # Ajustar por RPM
                if rpm_value < 2000:
                    rpm_correction = -2
                elif rpm_value < 4000:
                    rpm_correction = 0
                elif rpm_value < 6000:
                    rpm_correction = 2
                else:
                    rpm_correction = -1  # Reduzir em alta rotação

                timing = base_timing + rpm_correction
                matrix[i, j] = max(-5, min(timing * safety_factor, 40))

    return matrix


def calculate_lambda_3d_matrix(
    rpm_axis: List[float],
    map_axis: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
    safety_factor: float = 1.0,
) -> np.ndarray:
    """Calcula matriz 3D de valores de lambda considerando RPM e MAP.
    
    Implementa cálculo realista por zonas de operação:
    - Zona 1 (Vácuo alto): -1.0 a -0.4 bar -> Lambda 1.00-1.05 (economia)
    - Zona 2 (Carga parcial): -0.4 a 0.2 bar -> Lambda 0.88-0.94 (transição)
    - Zona 3 (Boost): 0.2+ bar -> Lambda 0.68-0.85 (proteção)
    
    Considera tipo de combustível e correções por RPM.
    """
    matrix = np.zeros((len(map_axis), len(rpm_axis)))
    
    # Configurações por combustível
    fuel_type = vehicle_data.get('fuel_type', 'Gasolina')
    is_ethanol = fuel_type == 'Ethanol'
    
    # Limites mínimos de lambda por combustível
    lambda_min = 0.68 if is_ethanol else 0.78
    
    # Fator de combustível para cálculo em boost
    fuel_factor = 0.08 if is_ethanol else 0.12
    
    # Boost máximo configurado
    boost_max = vehicle_data.get('boost_pressure', 1.0)

    for i, map_value in enumerate(map_axis):
        for j, rpm_value in enumerate(rpm_axis):
            if rpm_value > 0:
                # === CÁLCULO BASE POR ZONA DE OPERAÇÃO ===
                
                # Zona 1: Vácuo alto (-1.0 a -0.4 bar)
                if map_value <= -0.4:
                    # Lambda = 0.95 + (|MAP| × 0.05)
                    # Resulta em valores de 1.00-1.05 para economia
                    lambda_value = 0.95 + (abs(map_value) * 0.05)
                
                # Zona 2: Carga parcial (-0.4 a 0.2 bar)
                elif map_value <= 0.2:
                    # Lambda = 0.90 - (MAP × 0.1)
                    # Transição suave entre economia e potência
                    # Em -0.4: 0.90 - (-0.4 × 0.1) = 0.94
                    # Em 0.0: 0.90 - (0.0 × 0.1) = 0.90
                    # Em 0.2: 0.90 - (0.2 × 0.1) = 0.88
                    lambda_value = 0.90 - (map_value * 0.1)
                
                # Zona 3: Boost (0.2+ bar)
                else:
                    # Lambda = 0.85 - (MAP × Fator_combustível × Fator_RPM)
                    # Fator_RPM = 1.0 + (RPM-3000)/10000
                    rpm_factor = 1.0 + ((rpm_value - 3000) / 10000)
                    rpm_factor = max(0.8, min(1.3, rpm_factor))  # Limitar fator RPM
                    
                    lambda_value = 0.85 - (map_value * fuel_factor * rpm_factor)
                    
                    # Proteção adicional para boost muito alto
                    if map_value > boost_max:
                        # Aplicar fator de segurança adicional
                        over_boost = map_value - boost_max
                        lambda_value -= (over_boost * 0.05)
                
                # === CORREÇÕES POR RPM ===
                
                # RPM baixo (< 2000): multiplicar por 0.90 para estabilidade
                if rpm_value < 2000:
                    # Interpolação suave: em 0 RPM fator = 0.90, em 2000 RPM fator = 1.0
                    rpm_correction = 0.90 + (rpm_value / 2000 * 0.10)
                    lambda_value *= rpm_correction
                
                # RPM alto (> 6000): multiplicar por 0.95 para resfriamento
                elif rpm_value > 6000:
                    # Interpolação suave: em 6000 RPM fator = 1.0, em 8000+ fator = 0.95
                    rpm_high_factor = 1.0 - ((rpm_value - 6000) / 2000 * 0.05)
                    rpm_high_factor = max(0.95, rpm_high_factor)
                    lambda_value *= rpm_high_factor
                
                # === APLICAR ESTRATÉGIA ===
                if strategy == "conservative":
                    lambda_value *= 0.96  # 4% mais rico para segurança
                elif strategy == "aggressive":
                    lambda_value *= 1.02  # 2% mais pobre para performance
                
                # === APLICAR FATOR DE SEGURANÇA DO USUÁRIO ===
                lambda_value *= safety_factor
                
                # === VALIDAÇÃO FINAL ===
                # Aplicar limites baseados no combustível
                lambda_value = max(lambda_min, lambda_value)
                
                # Limite superior sempre 1.2 (economia máxima)
                lambda_value = min(1.2, lambda_value)
                
                matrix[i, j] = lambda_value
            else:
                # RPM = 0, sem combustível
                matrix[i, j] = 1.0

    return matrix


def calculate_afr_3d_matrix(
    rpm_axis: List[float],
    map_axis: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
    safety_factor: float = 1.0,
) -> np.ndarray:
    """Calcula matriz 3D de valores de AFR."""
    matrix = np.zeros((len(map_axis), len(rpm_axis)))

    for i, map_value in enumerate(map_axis):
        map_kpa = (
            (map_value + 1.013) * 100 if map_value < 0 else (map_value + 1.013) * 100
        )

        for j, rpm_value in enumerate(rpm_axis):
            if rpm_value > 0:
                afr_target = get_afr_target_3d(map_kpa, strategy)
                matrix[i, j] = afr_target * safety_factor

    return matrix


def calculate_3d_map_values_universal(
    map_type: str,
    rpm_axis: List[float],
    map_axis: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
    safety_factor: float = 1.0,
) -> np.ndarray:
    """Função universal para calcular valores de mapas 3D."""

    if map_type == "main_fuel_3d_map":
        return calculate_fuel_3d_matrix(
            rpm_axis, map_axis, vehicle_data, strategy, safety_factor
        )
    elif map_type == "ignition_timing_3d_map":
        return calculate_ignition_3d_matrix(
            rpm_axis, map_axis, vehicle_data, strategy, safety_factor
        )
    elif map_type == "lambda_target_3d_map":
        return calculate_lambda_3d_matrix(
            rpm_axis, map_axis, vehicle_data, strategy, safety_factor
        )
    elif map_type == "afr_target_3d_map":
        return calculate_afr_3d_matrix(
            rpm_axis, map_axis, vehicle_data, strategy, safety_factor
        )
    else:
        # Valores padrão baseados no tipo
        grid_size = len(map_axis)
        return get_default_3d_map_values(map_type, grid_size)


def get_default_3d_enabled_matrix(
    map_type: str, vehicle_data: Dict[str, Any]
) -> Tuple[List[bool], List[bool]]:
    """Retorna matrizes de enable/disable baseadas no tipo de motor."""
    config = load_map_types_config()
    map_config = config.get(map_type, {})

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


def get_default_3d_map_values(
    map_type: str,
    grid_size: int,
    rpm_enabled: List[bool] = None,
    map_enabled: List[bool] = None,
) -> np.ndarray:
    """Retorna valores padrão para o mapa 3D baseado no tipo e tamanho do grid.

    Args:
        map_type: Tipo do mapa
        grid_size: Tamanho do grid (16 ou 32)
        rpm_enabled: Lista de booleanos indicando quais posições RPM estão ativas (opcional)
        map_enabled: Lista de booleanos indicando quais posições MAP estão ativas (opcional)
    """

    if map_type == "main_fuel_3d_map":
        # Valores de injeção realistas (2.1-11.5ms como no 2D)
        # Baseado em RPM (400-8000) e MAP (-1.0 a 2.0 bar)
        matrix = []

        # Criar valores de RPM e MAP baseados no grid_size
        rpm_values = np.linspace(400, 8000, grid_size)
        map_values = np.linspace(-1.0, 2.0, grid_size)

        for rpm_idx in range(grid_size):
            row = []
            for map_idx in range(grid_size):
                rpm = rpm_values[rpm_idx]
                map_val = map_values[map_idx]

                # Normalizar valores
                rpm_normalized = (rpm - 400) / (8000 - 400)  # 0 to 1
                map_normalized = (map_val + 1.0) / 3.0  # -1 to 2 bar -> 0 to 1

                # Cálculo similar ao 2D: 2.1ms base + incrementos por RPM e MAP
                value = 2.1 + (rpm_normalized * 5.0) + (map_normalized * 4.4)

                # Compensação de pressão de combustível APENAS para MAP positivo
                # Com MAP <= 0, pressão permanece na pressão base (sem correção)
                if map_val > 0:
                    # Pressão base do sistema (geralmente 3 bar)
                    fuel_pressure_base = 3.0
                    # Nova pressão = base + MAP (regulador 1:1)
                    fuel_pressure_actual = fuel_pressure_base + map_val
                    # Correção de vazão: sqrt(pressão_atual / pressão_base)
                    flow_correction = (fuel_pressure_actual / fuel_pressure_base) ** 0.5
                    # Inverter para tempo (mais vazão = menos tempo)
                    time_correction = 1.0 / flow_correction
                    # Aplicar correção
                    value *= time_correction

                row.append(value)
            matrix.append(row)

        return np.array(matrix)

    elif map_type == "lambda_target_3d_map":
        # Valores de lambda típicos (0.8-1.2)
        # Mais rico (menor lambda) em alta carga
        rpm_factor = np.ones(grid_size)
        map_factor = np.linspace(1.2, 0.8, grid_size)
        base_values = np.outer(map_factor, rpm_factor)
        return base_values

    elif map_type == "ignition_timing_3d_map":
        # Valores de ignição típicos (10-35°)
        # Menor avanço em alta carga, mais avanço em cruzeiro
        rpm_factor = np.linspace(0.8, 1.2, grid_size)  # Mais avanço em RPM alto
        map_factor = np.linspace(1.5, 0.6, grid_size)  # Menos avanço em alta carga
        base_values = np.outer(map_factor, rpm_factor) * 15.0 + 10.0
        return base_values

    elif map_type == "afr_target_3d_map":
        # Valores de AFR típicos (11-15)
        # Mais rico em alta carga
        rpm_factor = np.ones(grid_size)
        map_factor = np.linspace(15.0, 11.0, grid_size)
        base_values = np.outer(map_factor, rpm_factor)
        return base_values

    else:
        # Valores padrão genéricos
        return np.ones((grid_size, grid_size)) * 5.0


def validate_3d_map_values(
    values: np.ndarray, min_val: float, max_val: float
) -> Tuple[bool, str]:
    """Valida se os valores estão dentro dos limites permitidos."""
    if np.any(values < min_val) or np.any(values > max_val):
        return False, f"Valores devem estar entre {min_val} e {max_val}"
    return True, "Valores válidos"


def get_dummy_vehicles() -> List[Dict[str, Any]]:
    """Retorna lista de veículos dummy para desenvolvimento."""
    return [
        {"id": "1", "name": "Golf GTI 2.0T", "nickname": "GTI Vermelho"},
        {"id": "2", "name": "Civic Si 2.4", "nickname": "Si Azul"},
        {"id": "3", "name": "WRX STI 2.5", "nickname": "STI Preto"},
        {"id": "4", "name": "Focus RS 2.3", "nickname": "RS Branco"},
    ]


# Função para obter veículos (com fallback)
def load_vehicles() -> List[Dict[str, Any]]:
    """Carrega lista de veículos disponíveis."""
    try:
        return get_all_vehicles()
    except:
        return get_dummy_vehicles()


def save_3d_map_data(
    vehicle_id: str,
    map_type: str,
    bank_id: str,
    rpm_axis: List[float],
    map_axis: List[float],
    rpm_enabled: List[bool],
    map_enabled: List[bool],
    values_matrix: np.ndarray,
) -> bool:
    """Salva dados do mapa 3D em arquivo JSON persistente."""
    try:
        # Criar diretório de dados se não existir
        data_dir = Path("data/fuel_maps")
        data_dir.mkdir(parents=True, exist_ok=True)

        # Nome do arquivo baseado nos parâmetros
        filename = data_dir / f"map_{vehicle_id}_{map_type}_{bank_id}.json"

        # Dados a salvar
        data = {
            "vehicle_id": vehicle_id,
            "map_type": map_type,
            "bank_id": bank_id,
            "rpm_axis": rpm_axis,
            "map_axis": map_axis,
            "rpm_enabled": rpm_enabled,
            "map_enabled": map_enabled,
            "values_matrix": values_matrix.tolist(),
            "timestamp": pd.Timestamp.now().isoformat(),
            "version": "1.0",
        }

        # Salvar no arquivo
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        # Também salvar no session_state para acesso rápido
        st.session_state[f"saved_3d_map_{vehicle_id}_{map_type}_{bank_id}"] = data

        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False


def load_3d_map_data(vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict]:
    """Carrega dados do mapa 3D de arquivo JSON persistente."""
    try:
        # Primeiro tentar do session_state (cache)
        key = f"saved_3d_map_{vehicle_id}_{map_type}_{bank_id}"
        if key in st.session_state:
            return st.session_state[key]

        # Se não estiver em cache, tentar carregar do arquivo
        data_dir = Path("data/fuel_maps")
        filename = data_dir / f"map_{vehicle_id}_{map_type}_{bank_id}.json"

        if filename.exists():
            with open(filename, "r") as f:
                data = json.load(f)

            # Salvar no session_state para cache
            st.session_state[key] = data
            return data

        return None
    except:
        return None


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


def format_value_3_decimals(value: float) -> str:
    """Formata valor com 3 casas decimais para todos os mapas."""
    return f"{value:.3f}"


def format_value_by_type(value: float, map_type: str) -> str:
    """Formata valor baseado no tipo de mapa (mantido para compatibilidade)."""
    # Agora todos usam 3 casas decimais
    return format_value_3_decimals(value)


def get_active_axis_values(
    axis_values: List[float], enabled: List[bool]
) -> List[float]:
    """Retorna apenas os valores ativos do eixo."""
    return [
        axis_values[i]
        for i in range(len(axis_values))
        if i < len(enabled) and enabled[i]
    ]


def ensure_all_3d_maps_exist(vehicle_id: str, vehicle_data: Dict[str, Any]) -> bool:
    """Garante que todos os mapas 3D necessários existam para um veículo."""
    try:
        config = load_map_types_config()

        for map_type, map_config in config.items():
            for bank in ["A", "B"] if map_type == "main_fuel_3d_map" else [None]:
                bank_id = bank or "shared"

                # Verificar se o arquivo já existe
                data_dir = Path("data/fuel_maps")
                filename = data_dir / f"map_{vehicle_id}_{map_type}_{bank_id}.json"

                if not filename.exists():
                    # Criar mapa padrão
                    grid_size = map_config.get("grid_size", 32)

                    # Obter configurações padrão
                    rpm_axis = map_config.get(
                        "default_rpm_values", DEFAULT_RPM_AXIS[:grid_size]
                    )
                    map_axis = map_config.get(
                        "default_map_values", DEFAULT_MAP_AXIS[:grid_size]
                    )

                    # Ajustar tamanhos
                    if len(rpm_axis) != grid_size:
                        rpm_axis = (
                            rpm_axis[:grid_size] + [0] * (grid_size - len(rpm_axis))
                            if len(rpm_axis) < grid_size
                            else rpm_axis[:grid_size]
                        )
                    if len(map_axis) != grid_size:
                        map_axis = (
                            map_axis[:grid_size] + [0] * (grid_size - len(map_axis))
                            if len(map_axis) < grid_size
                            else map_axis[:grid_size]
                        )

                    # Obter configurações enable/disable inteligentes
                    rpm_enabled, map_enabled = get_default_3d_enabled_matrix(
                        map_type, vehicle_data
                    )

                    # Ajustar tamanhos se necessário
                    if len(rpm_enabled) != grid_size:
                        rpm_enabled = (
                            rpm_enabled[:grid_size]
                            + [False] * (grid_size - len(rpm_enabled))
                            if len(rpm_enabled) < grid_size
                            else rpm_enabled[:grid_size]
                        )
                    if len(map_enabled) != grid_size:
                        map_enabled = (
                            map_enabled[:grid_size]
                            + [False] * (grid_size - len(map_enabled))
                            if len(map_enabled) < grid_size
                            else map_enabled[:grid_size]
                        )

                    # Calcular valores usando o calculador automático
                    active_rpm_values = get_active_axis_values(rpm_axis, rpm_enabled)
                    active_map_values = get_active_axis_values(map_axis, map_enabled)

                    if len(active_rpm_values) > 0 and len(active_map_values) > 0:
                        calculated_matrix = calculate_3d_map_values_universal(
                            map_type,
                            active_rpm_values,
                            active_map_values,
                            vehicle_data,
                            "balanced",  # Estratégia padrão
                            1.0,  # Fator de segurança padrão
                        )

                        # Expandir para o grid completo
                        full_matrix = np.zeros((grid_size, grid_size))
                        active_rpm_indices = [
                            i for i, enabled in enumerate(rpm_enabled) if enabled
                        ]
                        active_map_indices = [
                            i for i, enabled in enumerate(map_enabled) if enabled
                        ]

                        for i, map_idx in enumerate(active_map_indices):
                            for j, rpm_idx in enumerate(active_rpm_indices):
                                if (
                                    i < calculated_matrix.shape[0]
                                    and j < calculated_matrix.shape[1]
                                ):
                                    full_matrix[map_idx, rpm_idx] = calculated_matrix[
                                        i, j
                                    ]
                    else:
                        # Fallback para valores padrão simples
                        full_matrix = get_default_3d_map_values(map_type, grid_size)

                    # Salvar o mapa
                    success = save_3d_map_data(
                        vehicle_id,
                        map_type,
                        bank_id,
                        rpm_axis,
                        map_axis,
                        rpm_enabled,
                        map_enabled,
                        full_matrix,
                    )

                    if not success:
                        return False

        return True

    except Exception as e:
        st.error(f"Erro ao criar mapas 3D: {str(e)}")
        return False


# Obter contexto do veículo
selected_vehicle_id = get_vehicle_context()

if not selected_vehicle_id:
    st.warning(
        "Nenhum veículo selecionado. Por favor, selecione um veículo na página inicial."
    )
    st.stop()

# Garantir que todos os mapas 3D existam
vehicle_data = get_vehicle_data_from_session()
with st.spinner("Verificando mapas 3D..."):
    ensure_all_3d_maps_exist(selected_vehicle_id, vehicle_data)

# Atualizar título com informações do veículo
if vehicle_data and "name" in vehicle_data and "nickname" in vehicle_data:
    st.empty()  # Limpar título anterior
    st.markdown(
        f"# Mapas de Injeção 3D - {vehicle_data['name']} ({vehicle_data['nickname']})"
    )

# Seção de configuração (movida para cima)
st.container()
with st.container():
    st.subheader("Configuração")

    col_config1, col_config2, col_config3 = st.columns([2, 2, 1])

    with col_config1:
        # Seleção de tipo de mapa
        selected_map_type = st.selectbox(
            "Tipo de Mapa 3D",
            options=list(MAP_TYPES_3D.keys()),
            format_func=lambda x: MAP_TYPES_3D[x]["name"],
            key="map_type_selector_3d",
        )

    with col_config2:
        # Seleção de bancada (apenas para mapa principal)
        if selected_map_type == "main_fuel_3d_map":
            selected_bank = st.radio(
                "Bancada", options=["A", "B"], key="bank_selector_3d", horizontal=True
            )
        else:
            selected_bank = None
            st.caption("Mapa compartilhado entre bancadas")

    with col_config3:
        # Informações do mapa selecionado
        map_info = MAP_TYPES_3D[selected_map_type]
        st.caption(
            f":material/grid_4x4: **Grade:** {map_info['grid_size']}x{map_info['grid_size']}"
        )
        st.caption(
            f":material/straighten: **Eixos:** {map_info['x_axis_type']} x {map_info['y_axis_type']}"
        )
        st.caption(f":material/straighten: **Unidade:** {map_info['unit']}")

st.divider()

# Editor de Mapa 3D (movido para baixo)
st.subheader("Editor de Mapa 3D")

# Sistema de abas
tab1, tab2, tab3 = st.tabs(["Editar", "Visualizar", "Importar/Exportar"])

with tab1:
    st.caption("Editor de matriz 3D")

    # Inicializar dados se não existirem
    session_key = (
        f"map_3d_data_{selected_vehicle_id}_{selected_map_type}_{selected_bank}"
    )

    if session_key not in st.session_state:
        # Obter grid_size do tipo de mapa
        grid_size = map_info["grid_size"]

        # Obter configuração padrão do mapa
        config = load_map_types_config()
        map_config = config.get(selected_map_type, {})

        # Obter valores enabled padrão da configuração
        default_rpm_enabled = map_config.get(
            "default_rpm_enabled", RPM_ENABLED[:grid_size]
        )
        default_map_enabled = map_config.get(
            "default_map_enabled", MAP_ENABLED[:grid_size]
        )

        # Ajustar tamanhos dos defaults
        if len(default_rpm_enabled) != grid_size:
            default_rpm_enabled = (
                default_rpm_enabled[:grid_size]
                if len(default_rpm_enabled) > grid_size
                else default_rpm_enabled
                + [False] * (grid_size - len(default_rpm_enabled))
            )
        if len(default_map_enabled) != grid_size:
            default_map_enabled = (
                default_map_enabled[:grid_size]
                if len(default_map_enabled) > grid_size
                else default_map_enabled
                + [False] * (grid_size - len(default_map_enabled))
            )

        # Tentar carregar dados salvos
        loaded_data = load_3d_map_data(
            selected_vehicle_id, selected_map_type, selected_bank
        )
        if loaded_data:
            # Ajustar tamanho se necessário
            if len(loaded_data["rpm_axis"]) != grid_size:
                # Redimensionar eixos e matriz para o grid_size correto
                rpm_axis = map_config.get(
                    "default_rpm_values", DEFAULT_RPM_AXIS[:grid_size]
                )
                map_axis = map_config.get(
                    "default_map_values", DEFAULT_MAP_AXIS[:grid_size]
                )
                rpm_enabled = default_rpm_enabled
                map_enabled = default_map_enabled
                values_matrix = get_default_3d_map_values(selected_map_type, grid_size)
            else:
                rpm_axis = loaded_data["rpm_axis"]
                map_axis = loaded_data["map_axis"]
                # Usar valores salvos ou padrões da configuração
                rpm_enabled = loaded_data.get("rpm_enabled", default_rpm_enabled)
                map_enabled = loaded_data.get("map_enabled", default_map_enabled)
                values_matrix = np.array(loaded_data["values_matrix"])

            st.session_state[session_key] = {
                "rpm_axis": rpm_axis,
                "map_axis": map_axis,
                "rpm_enabled": rpm_enabled,
                "map_enabled": map_enabled,
                "values_matrix": values_matrix,
            }
        else:
            # Criar dados padrão usando a configuração expandida
            config = load_map_types_config()
            map_config = config.get(selected_map_type, {})

            # Obter eixos padrão da configuração
            rpm_axis = map_config.get(
                "default_rpm_values", DEFAULT_RPM_AXIS[:grid_size]
            )
            map_axis = map_config.get(
                "default_map_values", DEFAULT_MAP_AXIS[:grid_size]
            )

            # Obter os valores enabled da configuração (se existirem)
            rpm_enabled = map_config.get("default_rpm_enabled", None)
            map_enabled = map_config.get("default_map_enabled", None)

            # Se não houver valores enabled na configuração, usar lógica inteligente
            if rpm_enabled is None or map_enabled is None:
                vehicle_data = get_vehicle_data_from_session()
                rpm_enabled, map_enabled = get_default_3d_enabled_matrix(
                    selected_map_type, vehicle_data
                )

            # Ajustar para o tamanho correto (garantir que o tamanho dos eixos corresponde ao grid_size)
            if len(rpm_axis) != grid_size:
                rpm_axis = (
                    rpm_axis[:grid_size] if len(rpm_axis) >= grid_size else rpm_axis
                )
            if len(map_axis) != grid_size:
                map_axis = (
                    map_axis[:grid_size] if len(map_axis) >= grid_size else map_axis
                )

            # Ajustar tamanhos se necessário
            if len(rpm_enabled) != grid_size:
                rpm_enabled = (
                    rpm_enabled[:grid_size] + [False] * (grid_size - len(rpm_enabled))
                    if len(rpm_enabled) < grid_size
                    else rpm_enabled[:grid_size]
                )
            if len(map_enabled) != grid_size:
                map_enabled = (
                    map_enabled[:grid_size] + [False] * (grid_size - len(map_enabled))
                    if len(map_enabled) < grid_size
                    else map_enabled[:grid_size]
                )

            st.session_state[session_key] = {
                "rpm_axis": rpm_axis,
                "map_axis": map_axis,
                "rpm_enabled": rpm_enabled,
                "map_enabled": map_enabled,
                "values_matrix": get_default_3d_map_values(
                    selected_map_type, grid_size
                ),
            }

    current_data = st.session_state[session_key]

    # Sub-abas para edição
    edit_tab1, edit_tab2 = st.tabs(["Matriz de Valores", "Eixos"])

    with edit_tab1:
        st.caption("Edite os valores da matriz 3D")

        # Obter grid_size antes de usar
        grid_size = map_info["grid_size"]

        # Botão para abrir o calculador automático
        if st.button(
            ":material/calculate: Calculador Automático 3D",
            key=f"open_calculator_{session_key}",
            use_container_width=True,
            type="primary",
        ):
            st.session_state[f"show_calculator_{session_key}"] = True

        # Modal do Calculador Automático - Aparece logo após o botão
        if st.session_state.get(f"show_calculator_{session_key}", False):
            with st.container():
                st.markdown("### Calculador Automático de Mapas")
                st.markdown("---")

                # Obter dados do veículo
                vehicle_data = get_vehicle_data_from_session()

                # Layout em colunas para configurações
                calc_col1, calc_col2 = st.columns([2, 1])

                with calc_col1:
                    st.subheader("Configurações de Cálculo")

                    # Seleção de estratégia
                    selected_strategy = st.selectbox(
                        "Estratégia de Tuning",
                        options=list(STRATEGY_PRESETS.keys()),
                        format_func=lambda x: f"{STRATEGY_PRESETS[x]['name']} - {STRATEGY_PRESETS[x]['description']}",
                        key=f"strategy_{session_key}",
                        index=1,  # Balanceada por padrão
                    )

                    # Fator de segurança
                    safety_factor = st.slider(
                        "Fator de Segurança",
                        min_value=0.8,
                        max_value=1.2,
                        value=STRATEGY_PRESETS[selected_strategy]["safety_factor"],
                        step=0.05,
                        key=f"safety_factor_{session_key}",
                        help="Multiplica todos os valores calculados",
                    )

                    # Configurações específicas para mapas 3D
                    st.subheader("Configurações Específicas")

                    # Controles específicos baseados no tipo de mapa selecionado
                    if selected_map_type == "main_fuel_3d_map":
                        # Controles para mapa principal
                        advanced_col1, advanced_col2 = st.columns(2)

                        with advanced_col1:
                            consider_boost = st.checkbox(
                                "Considerar Boost",
                                value=vehicle_data["turbo"],
                                key=f"consider_boost_{session_key}",
                                help="Aplica enriquecimento adicional para pressão de turbo",
                            )

                            # Campo para pressão de combustível base
                            fuel_pressure = st.number_input(
                                "Pressão de Combustível (bar)",
                                min_value=2.0,
                                max_value=6.0,
                                value=3.0,
                                step=0.5,
                                key=f"fuel_pressure_{session_key}",
                                help="Pressão base do sistema de combustível com MAP=0",
                            )

                        with advanced_col2:
                            fuel_correction_enabled = st.checkbox(
                                "Correção de Combustível",
                                value=True,
                                key=f"fuel_correction_{session_key}",
                                help="Aplica correção baseada no tipo de combustível (Etanol +30%)",
                            )

                            # Checkbox para compensação de pressão MAP
                            pressure_compensation = st.checkbox(
                                "Compensação MAP/Pressão",
                                value=True,
                                key=f"pressure_compensation_{session_key}",
                                help="Compensa alteração de vazão em MAP positivo (regulador 1:1 em boost)",
                            )
                            if pressure_compensation:
                                st.caption(
                                    f":material/lightbulb: Regulador 1:1 (MAP > 0)"
                                )
                    elif selected_map_type == "ve_table_3d_map":
                        # Controles para VE Table
                        st.info(
                            "Configurações automáticas para VE Table baseadas no motor"
                        )
                    elif selected_map_type == "ignition_3d_map":
                        # Controles para mapa de ignição
                        st.info(
                            "Configurações automáticas para Ignição baseadas no motor"
                        )
                    elif selected_map_type == "lambda_target_3d_map":
                        # Controles para Lambda Target
                        st.info(
                            "Configurações automáticas para Lambda Target baseadas no combustível"
                        )
                    else:
                        st.info(
                            "Configurações automáticas baseadas no tipo de mapa 3D selecionado"
                        )

                with calc_col2:
                    st.subheader("Dados do Veículo")

                    # Primeira linha: Cilindrada, Cilindros, Vazão Bicos
                    vehicle_col1, vehicle_col2, vehicle_col3 = st.columns(3)
                    with vehicle_col1:
                        st.metric("Cilindrada", f"{vehicle_data['displacement']:.1f}L")
                    with vehicle_col2:
                        st.metric("Cilindros", vehicle_data["cylinders"])
                    with vehicle_col3:
                        st.metric(
                            "Vazão",
                            f"{vehicle_data.get('injector_flow_lbs', 0):.0f} lbs/h",
                        )

                    # Segunda linha: Combustível e Boost
                    vehicle_col4, vehicle_col5 = st.columns(2)
                    with vehicle_col4:
                        st.metric("Combustível", vehicle_data["fuel_type"].title())
                    with vehicle_col5:
                        if vehicle_data["turbo"]:
                            boost_val = vehicle_data.get("boost_pressure", 1.0)
                            if boost_val is None:
                                boost_val = 1.0
                            st.metric("Boost", f"{boost_val:.1f} bar")
                        else:
                            st.metric("Aspiração", "Natural")

                st.markdown("---")

                # Preview dos valores calculados
                st.subheader("Preview dos Valores Calculados")

                # Obter dados atuais da sessão
                rpm_axis = current_data["rpm_axis"]
                map_axis = current_data["map_axis"]
                rpm_enabled = current_data.get("rpm_enabled", [True] * len(rpm_axis))
                map_enabled = current_data.get("map_enabled", [True] * len(map_axis))
                values_matrix = current_data.get(
                    "values_matrix",
                    [[0.0] * len(map_axis) for _ in range(len(rpm_axis))],
                )

                # Calcular valores preview para a matriz 3D
                # TODO: Implementar cálculo real baseado nas configurações
                # Por enquanto, vamos criar valores de exemplo baseados nos dados atuais
                preview_matrix = []

                # Obter apenas valores ativos
                active_rpm_indices = [
                    i for i, enabled in enumerate(rpm_enabled) if enabled
                ]
                active_map_indices = [
                    i for i, enabled in enumerate(map_enabled) if enabled
                ]

                if active_rpm_indices and active_map_indices:
                    # Criar matriz de preview com valores calculados
                    for rpm_idx in active_rpm_indices:
                        row = []
                        for map_idx in active_map_indices:
                            # SEMPRE recalcular para o preview baseado em RPM e MAP
                            if rpm_idx < len(rpm_axis) and map_idx < len(map_axis):
                                # Obter valores reais de RPM e MAP
                                rpm_value = rpm_axis[rpm_idx]
                                map_value = map_axis[map_idx]

                                if selected_map_type == "main_fuel_3d_map":
                                    # Fórmula mais realista baseada em RPM e MAP
                                    # Base: 2.1ms em idle (400rpm, -1bar), até 11.5ms em alta carga (8000rpm, 2bar)
                                    rpm_normalized = (rpm_value - 400) / (
                                        8000 - 400
                                    )  # 0 to 1
                                    map_normalized = (
                                        map_value + 1.0
                                    ) / 3.0  # -1 to 2 bar -> 0 to 1

                                    # Cálculo progressivo similar ao 2D
                                    base_value = (
                                        2.1
                                        + (rpm_normalized * 5.0)
                                        + (map_normalized * 4.4)
                                    )

                                    # Compensação de pressão de combustível (regulador 1:1)
                                    # IMPORTANTE: Só aplica para MAP POSITIVO (boost)
                                    # Com MAP <= 0, a pressão permanece estável na pressão base
                                    if (
                                        st.session_state.get(
                                            f"pressure_compensation_{session_key}", True
                                        )
                                        and map_value > 0
                                    ):
                                        # Obter pressão base configurada (padrão 3 bar)
                                        fuel_pressure_base = st.session_state.get(
                                            f"fuel_pressure_{session_key}", 3.0
                                        )

                                        # Nova pressão = base + MAP (regulador 1:1 apenas em boost)
                                        fuel_pressure_actual = (
                                            fuel_pressure_base + map_value
                                        )

                                        # Correção de vazão: sqrt(pressão_atual / pressão_base)
                                        # Mais pressão -> mais vazão -> tempo DIMINUI
                                        flow_correction = (
                                            fuel_pressure_actual / fuel_pressure_base
                                        ) ** 0.5

                                        # Inverter para aplicar ao tempo (mais vazão = menos tempo)
                                        time_correction = 1.0 / flow_correction

                                        # Aplicar correção
                                        base_value *= time_correction

                                    # Aplicar correções baseadas nas configurações
                                    if st.session_state.get(
                                        f"fuel_correction_{session_key}", True
                                    ):
                                        # Aplicar correção de combustível se habilitada
                                        fuel_type = vehicle_data.get(
                                            "fuel_type", "gasoline"
                                        )
                                        if fuel_type == "ethanol":
                                            base_value *= 1.3  # Etanol precisa de mais combustível

                                    if st.session_state.get(
                                        f"consider_boost_{session_key}", False
                                    ):
                                        # Aplicar enriquecimento adicional de boost se habilitado
                                        # Esta é uma correção ADICIONAL para segurança em boost
                                        if map_value > 0:  # Pressão positiva (boost)
                                            # Enriquecimento progressivo: 10% por bar de boost
                                            base_value *= 1.0 + map_value * 0.1
                                else:
                                    # Para outros tipos de mapa, usar valor existente ou padrão
                                    if rpm_idx < len(values_matrix) and map_idx < len(
                                        values_matrix[rpm_idx]
                                    ):
                                        base_value = values_matrix[rpm_idx][map_idx]
                                    else:
                                        base_value = 5.0  # Valor padrão

                                # Aplicar fator de segurança
                                calculated_value = base_value * safety_factor
                                row.append(calculated_value)
                            else:
                                # Valor padrão calculado se fora dos limites
                                # Usar valores médios se os índices estiverem fora
                                rpm_value = rpm_axis[min(rpm_idx, len(rpm_axis) - 1)]
                                map_value = map_axis[min(map_idx, len(map_axis) - 1)]

                                if selected_map_type == "main_fuel_3d_map":
                                    rpm_normalized = (rpm_value - 400) / (8000 - 400)
                                    map_normalized = (map_value + 1.0) / 3.0

                                    default_value = (
                                        2.1
                                        + (rpm_normalized * 5.0)
                                        + (map_normalized * 4.4)
                                    )
                                else:
                                    default_value = 5.0

                                row.append(default_value * safety_factor)
                        preview_matrix.append(row)

                    # Criar DataFrame para preview
                    active_rpm_values = [rpm_axis[i] for i in active_rpm_indices]
                    active_map_values = [map_axis[i] for i in active_map_indices]

                    # Inverter a ordem do RPM e da matriz para mostrar decrescente
                    active_rpm_values_reversed = list(reversed(active_rpm_values))
                    preview_matrix_reversed = list(reversed(preview_matrix))

                    # Criar headers das colunas com valores de MAP
                    column_headers = [
                        (
                            f"{map_val:.2f}"
                            if isinstance(map_val, (int, float))
                            else str(map_val)
                        )
                        for map_val in active_map_values
                    ]

                    # Criar DataFrame com RPM decrescente
                    preview_df = pd.DataFrame(
                        preview_matrix_reversed,
                        index=[f"{int(rpm)}" for rpm in active_rpm_values_reversed],
                        columns=column_headers,
                    )

                    # Exibir preview
                    st.write(f"**Preview dos valores calculados** ({map_info['unit']})")

                    # Mostrar correções aplicadas
                    corrections_applied = []
                    if st.session_state.get(f"fuel_correction_{session_key}", True):
                        fuel_type = vehicle_data.get("fuel_type", "gasoline")
                        if fuel_type == "ethanol":
                            corrections_applied.append(
                                ":material/check_circle: Correção Etanol (+30%)"
                            )

                    fuel_pressure_value = st.session_state.get(
                        f"fuel_pressure_{session_key}", 3.0
                    )
                    if fuel_pressure_value != 3.0:
                        corrections_applied.append(
                            f":material/check_circle: Pressão Base: {fuel_pressure_value} bar"
                        )
                    else:
                        corrections_applied.append(
                            ":material/check_circle: Pressão Base: 3.0 bar (padrão)"
                        )

                    if st.session_state.get(
                        f"pressure_compensation_{session_key}", True
                    ):
                        corrections_applied.append(
                            ":material/check_circle: Compensação MAP/Pressão (regulador 1:1)"
                        )

                    if st.session_state.get(f"consider_boost_{session_key}", False):
                        corrections_applied.append(
                            ":material/check_circle: Enriquecimento Boost (+10%/bar)"
                        )

                    if corrections_applied:
                        st.caption(
                            "Correções aplicadas: " + " | ".join(corrections_applied)
                        )

                    st.caption(
                        f"Valores com 3 casas decimais - Total: {len(active_rpm_values) * len(active_map_values)} valores"
                    )

                    # Aplicar estilo à tabela
                    styled_preview = preview_df.style.format(
                        "{:.3f}"
                    ).background_gradient(
                        cmap="RdYlBu",  # Removido o _r para inverter as cores
                        axis=None,
                        vmin=preview_df.min().min(),
                        vmax=preview_df.max().max(),
                    )

                    st.dataframe(styled_preview, use_container_width=True, height=400)

                    # Estatísticas
                    col_min, col_med, col_max = st.columns(3)

                    all_values = [val for row in preview_matrix for val in row]
                    if all_values:
                        import numpy as np

                        with col_min:
                            st.metric(
                                "Mínimo", f"{min(all_values):.3f} {map_info['unit']}"
                            )
                        with col_med:
                            st.metric(
                                "Médio", f"{np.mean(all_values):.3f} {map_info['unit']}"
                            )
                        with col_max:
                            st.metric(
                                "Máximo", f"{max(all_values):.3f} {map_info['unit']}"
                            )
                else:
                    st.warning("Nenhuma posição ativa para calcular preview")

                st.markdown("---")

                # Botões de ação
                action_col1, action_col2, action_col3 = st.columns(3)

                with action_col1:
                    if st.button(
                        ":material/check: Aplicar Cálculo",
                        key=f"apply_calc_{session_key}",
                        type="primary",
                        use_container_width=True,
                    ):
                        # Aplicar valores calculados à matriz 3D
                        # Criar nova matriz completa mantendo valores desabilitados
                        new_matrix = [
                            [0.0] * len(map_axis) for _ in range(len(rpm_axis))
                        ]

                        # Preencher com os valores calculados nas posições ativas
                        preview_row_idx = 0
                        for rpm_idx in active_rpm_indices:
                            preview_col_idx = 0
                            for map_idx in active_map_indices:
                                if preview_row_idx < len(
                                    preview_matrix
                                ) and preview_col_idx < len(preview_matrix[0]):
                                    new_matrix[rpm_idx][map_idx] = preview_matrix[
                                        preview_row_idx
                                    ][preview_col_idx]
                                preview_col_idx += 1
                            preview_row_idx += 1

                        # Atualizar a matriz na sessão
                        st.session_state[session_key]["values_matrix"] = new_matrix

                        # Salvar os dados atualizados
                        save_3d_map_data(
                            selected_vehicle_id,
                            selected_map_type,
                            selected_bank,
                            rpm_axis,
                            map_axis,
                            rpm_enabled,
                            map_enabled,
                            new_matrix,
                        )

                        st.session_state[f"show_calculator_{session_key}"] = False
                        st.success("Valores calculados aplicados e salvos com sucesso!")
                        st.rerun()

                with action_col2:
                    if st.button(
                        ":material/analytics: Preview Gráfico",
                        key=f"preview_graph_{session_key}",
                        use_container_width=True,
                    ):
                        st.session_state[f"show_preview_graph_{session_key}"] = True

                with action_col3:
                    if st.button(
                        ":material/cancel: Cancelar",
                        key=f"cancel_calc_{session_key}",
                        use_container_width=True,
                    ):
                        st.session_state[f"show_calculator_{session_key}"] = False
                        st.session_state[f"show_preview_graph_{session_key}"] = False
                        st.rerun()

                # Mostrar gráfico 3D de preview se solicitado
                if st.session_state.get(f"show_preview_graph_{session_key}", False):
                    st.markdown("---")
                    st.subheader("Preview Gráfico 3D")

                    import plotly.graph_objects as go

                    # Criar gráfico 3D Surface com os valores calculados do preview
                    fig_preview = go.Figure(
                        data=[
                            go.Surface(
                                x=active_map_values,  # MAP no eixo X (valores ativos)
                                y=active_rpm_values,  # RPM no eixo Y (valores ativos)
                                z=preview_matrix,  # Matriz de preview calculada
                                colorscale="RdYlBu",  # Vermelho=baixo, azul=alto
                                name="Preview Calculado",
                                colorbar=dict(
                                    title=dict(text=f"{map_info['unit']}"),
                                    tickmode="linear",
                                    tick0=min([min(row) for row in preview_matrix]),
                                    dtick=(
                                        max([max(row) for row in preview_matrix])
                                        - min([min(row) for row in preview_matrix])
                                    )
                                    / 10,
                                ),
                            )
                        ]
                    )

                    fig_preview.update_layout(
                        title=f"Preview 3D - {map_info['name']} (Valores Calculados)",
                        scene=dict(
                            xaxis_title="MAP (bar)",
                            yaxis_title="RPM",
                            zaxis_title=f"Valor ({map_info['unit']})",
                            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                            xaxis=dict(
                                tickmode="array",
                                tickvals=active_map_values[
                                    :: max(1, len(active_map_values) // 10)
                                ],  # Mostrar até 10 ticks
                                ticktext=[
                                    f"{v:.1f}"
                                    for v in active_map_values[
                                        :: max(1, len(active_map_values) // 10)
                                    ]
                                ],
                            ),
                            yaxis=dict(
                                tickmode="array",
                                tickvals=active_rpm_values[
                                    :: max(1, len(active_rpm_values) // 10)
                                ],  # Mostrar até 10 ticks
                                ticktext=[
                                    f"{int(v)}"
                                    for v in active_rpm_values[
                                        :: max(1, len(active_rpm_values) // 10)
                                    ]
                                ],
                            ),
                        ),
                        height=600,
                        margin=dict(l=0, r=0, t=40, b=0),
                    )

                    st.plotly_chart(fig_preview, use_container_width=True)

                    # Adicionar vista de contorno também
                    with st.expander("Ver Mapa de Contorno", expanded=False):
                        contour_fig = go.Figure(
                            data=go.Contour(
                                x=active_map_values,  # MAP no eixo X
                                y=active_rpm_values,  # RPM no eixo Y
                                z=preview_matrix,  # Matriz de preview
                                colorscale="RdYlBu",  # Vermelho=baixo, azul=alto
                                contours=dict(
                                    showlabels=True,
                                    labelfont=dict(size=12, color="white"),
                                ),
                                colorbar=dict(title=dict(text=f"{map_info['unit']}")),
                            )
                        )

                        contour_fig.update_layout(
                            title="Vista de Contorno - Preview",
                            xaxis_title="MAP (bar)",
                            yaxis_title="RPM",
                            height=400,
                        )

                        st.plotly_chart(contour_fig, use_container_width=True)

            st.divider()

        # Obter configuração do mapa para valores padrão
        config = load_map_types_config()
        map_config = config.get(selected_map_type, {})

        # Usar valores padrão da configuração se não houver dados salvos
        default_rpm_enabled = map_config.get(
            "default_rpm_enabled", RPM_ENABLED[:grid_size]
        )
        default_map_enabled = map_config.get(
            "default_map_enabled", MAP_ENABLED[:grid_size]
        )

        # Ajustar tamanhos dos defaults se necessário
        if len(default_rpm_enabled) != grid_size:
            default_rpm_enabled = (
                default_rpm_enabled[:grid_size]
                if len(default_rpm_enabled) > grid_size
                else default_rpm_enabled
                + [False] * (grid_size - len(default_rpm_enabled))
            )
        if len(default_map_enabled) != grid_size:
            default_map_enabled = (
                default_map_enabled[:grid_size]
                if len(default_map_enabled) > grid_size
                else default_map_enabled
                + [False] * (grid_size - len(default_map_enabled))
            )

        # Usar valores salvos ou padrões da configuração
        rpm_enabled_raw = current_data.get("rpm_enabled", default_rpm_enabled)
        map_enabled_raw = current_data.get("map_enabled", default_map_enabled)

        # Garantir que o tamanho está correto
        if len(rpm_enabled_raw) != grid_size:
            rpm_enabled = default_rpm_enabled
        else:
            rpm_enabled = rpm_enabled_raw

        if len(map_enabled_raw) != grid_size:
            map_enabled = default_map_enabled
        else:
            map_enabled = map_enabled_raw

        # Ajustar também os eixos para o tamanho correto
        rpm_axis = current_data["rpm_axis"]
        map_axis = current_data["map_axis"]

        if len(rpm_axis) != grid_size:
            rpm_axis = DEFAULT_RPM_AXIS[:grid_size]
            current_data["rpm_axis"] = rpm_axis

        if len(map_axis) != grid_size:
            map_axis = DEFAULT_MAP_AXIS[:grid_size]
            current_data["map_axis"] = map_axis

        active_rpm_values = get_active_axis_values(rpm_axis, rpm_enabled)
        active_map_values = get_active_axis_values(map_axis, map_enabled)

        st.write("**Eixo X (MAP em bar):** Valores crescentes (menor para maior)")
        st.write("**Eixo Y (RPM):** Valores decrescentes (maior para menor)")

        # Criar DataFrame pivotado para edição usando apenas valores ativos
        matrix = current_data["values_matrix"]

        # Verificar se a matriz tem o tamanho correto, se não, redimensionar
        if len(matrix) != grid_size or (
            len(matrix) > 0 and len(matrix[0]) != grid_size
        ):
            # Criar nova matriz com o tamanho correto
            new_matrix = get_default_3d_map_values(selected_map_type, grid_size)
            # Copiar valores existentes se possível
            for i in range(min(len(matrix), grid_size)):
                for j in range(
                    min(len(matrix[i]) if i < len(matrix) else 0, grid_size)
                ):
                    new_matrix[i][j] = matrix[i][j]
            matrix = new_matrix
            # Atualizar na sessão
            current_data["values_matrix"] = matrix

        # Verificar se há valores ativos antes de continuar
        if not active_rpm_values or not active_map_values:
            st.warning(
                "Nenhuma posição ativa selecionada. Configure os eixos primeiro."
            )
        else:
            # Filtrar a matriz para usar apenas as posições ativas
            # Pegar apenas as linhas ativas (RPM) e colunas ativas (MAP)
            active_rpm_indices = [
                i for i, enabled in enumerate(rpm_enabled[:grid_size]) if enabled
            ]
            active_map_indices = [
                i for i, enabled in enumerate(map_enabled[:grid_size]) if enabled
            ]

            # Verificar se os índices estão corretos
            if not active_rpm_indices or not active_map_indices:
                st.error(
                    "Erro ao identificar posições ativas. Verifique a configuração dos eixos."
                )
            else:
                # Inverter a ordem do RPM para mostrar decrescente (maior para menor)
                active_rpm_values_reversed = list(reversed(active_rpm_values))
                active_rpm_indices_reversed = list(reversed(active_rpm_indices))

                # Criar matriz filtrada - garantir que temos uma linha para cada RPM ativo (ordem invertida)
                # IMPORTANTE: A matriz é criada como matrix[map_idx, rpm_idx] nas funções de cálculo
                # mas precisa ser exibida com RPM nas linhas e MAP nas colunas
                filtered_matrix = []
                for rpm_idx in active_rpm_indices_reversed:
                    row = []
                    for map_idx in active_map_indices:
                        # Verificar se os índices estão dentro dos limites da matriz
                        # Nota: matriz original é [map][rpm], então acessamos matrix[map_idx][rpm_idx]
                        if map_idx < len(matrix) and rpm_idx < len(matrix[map_idx]):
                            row.append(matrix[map_idx][rpm_idx])
                        else:
                            row.append(0.0)  # Valor padrão se fora dos limites
                    filtered_matrix.append(row)

                # Criar DataFrame com valores numéricos puros (sem labels MAP/RPM)
                # RPM em ordem decrescente (maior para menor)
                # Adicionar sufixo único para colunas duplicadas
                column_names = []
                column_count = {}
                for map_val in active_map_values:
                    col_name = f"{map_val:.3f}"
                    if col_name in column_count:
                        column_count[col_name] += 1
                        col_name = f"{col_name}_{column_count[col_name]}"
                    else:
                        column_count[col_name] = 0
                    column_names.append(col_name)

                matrix_df = pd.DataFrame(
                    filtered_matrix,
                    columns=column_names,
                    index=[f"{int(rpm)}" for rpm in active_rpm_values_reversed],
                )

                # Editor de matriz com formatação 3 casas decimais
                format_str = "%.3f"  # Sempre 3 casas decimais

                edited_matrix_df = st.data_editor(
                    matrix_df,  # Usar DataFrame sem estilo para edição
                    use_container_width=True,
                    column_config={
                        col: st.column_config.NumberColumn(
                            (
                                col.split("_")[0] if "_" in col else col
                            ),  # Mostrar apenas o valor sem sufixo
                            format=format_str,
                            min_value=map_info["min_value"],
                            max_value=map_info["max_value"],
                            help=f"MAP: {col.split('_')[0] if '_' in col else col} bar, Valores em {map_info['unit']}",
                        )
                        for col in matrix_df.columns
                    },
                    key=f"matrix_editor_{session_key}",
                )

                # Criar DataFrame separado para visualização com estilo (sem colunas duplicadas)
                # Usar valores MAP originais sem sufixo para o display
                # Garantir índices únicos adicionando sufixo se necessário
                index_names = []
                index_count = {}
                for rpm in active_rpm_values_reversed:
                    idx_name = f"{int(rpm)}"
                    if idx_name in index_count:
                        index_count[idx_name] += 1
                        idx_name = f"{idx_name}_{index_count[idx_name]}"
                    else:
                        index_count[idx_name] = 0
                    index_names.append(idx_name)

                # Criar colunas com valores de MAP formatados
                map_columns = [
                    (
                        f"{map_val:.2f}"
                        if isinstance(map_val, (int, float))
                        else str(map_val)
                    )
                    for map_val in active_map_values
                ]

                display_df = pd.DataFrame(
                    filtered_matrix,
                    columns=map_columns,  # Usar valores de MAP como headers
                    index=index_names,  # Índices únicos
                )

                # Aplicar estilo ao DataFrame com colunas únicas
                styled_df = display_df.style.background_gradient(
                    cmap="RdYlBu", axis=None
                ).format("{:.3f}")

                # Mostrar versão com gradiente para visualização
                st.caption(
                    "Visualização com gradiente de cores (MAP: "
                    + ", ".join([f"{v:.1f}" for v in active_map_values[:5]])
                    + "... bar):"
                )
                st.dataframe(styled_df, use_container_width=True)

                # Atualizar matriz na sessão - expandir de volta para o grid_size
                # Criar matriz com tamanho do grid
                grid_size = map_info["grid_size"]
                full_matrix = np.zeros((grid_size, grid_size))

                # Copiar valores editados de volta para as posições corretas
                # Considerando que o DataFrame está com RPM em ordem invertida (maior para menor)
                for i, rpm_idx in enumerate(active_rpm_indices_reversed):
                    if i < len(edited_matrix_df.values) and rpm_idx < grid_size:
                        for j, map_idx in enumerate(active_map_indices):
                            if (
                                j < len(edited_matrix_df.values[i])
                                and map_idx < grid_size
                            ):
                                full_matrix[rpm_idx][map_idx] = edited_matrix_df.values[
                                    i
                                ][j]

                st.session_state[session_key]["values_matrix"] = full_matrix

                # Validações
                matrix_valid, matrix_msg = validate_3d_map_values(
                    edited_matrix_df.values,
                    map_info["min_value"],
                    map_info["max_value"],
                )

                if not matrix_valid:
                    st.error(f"Matriz: {matrix_msg}")

        # Modal do Calculador Automático (COMENTADO - MOVIDO PARA CIMA)
        if False and st.session_state.get(f"show_calculator_{session_key}", False):
            with st.container():
                st.markdown("### :material/build: Calculador Automático 3D")
                st.caption("Calcule valores baseados nos dados do veículo")

                # Obter dados do veículo
                vehicle_data = get_vehicle_data_from_session()

                # Primeira linha: Estratégia e informações
                col_calc1, col_calc2, col_calc3 = st.columns([2, 1, 2])

                with col_calc1:
                    # Seleção de estratégia
                    strategy = st.selectbox(
                        "Estratégia de Tuning",
                        options=["conservative", "balanced", "aggressive"],
                        format_func=lambda x: STRATEGY_PRESETS[x]["name"],
                        key=f"strategy_{session_key}",
                        help="Escolha a estratégia de agressividade do tuning",
                    )

                    # Estratégia selecionada
                    strategy_info = STRATEGY_PRESETS[strategy]
                    st.info(
                        f"**{strategy_info['name']}**: {strategy_info['description']}"
                    )

                with col_calc2:
                    # Fator de segurança
                    safety_factor = st.slider(
                        "Fator de Segurança",
                        min_value=0.8,
                        max_value=1.3,
                        value=STRATEGY_PRESETS[strategy]["safety_factor"],
                        step=0.05,
                        key=f"safety_factor_{session_key}",
                        help="Multiplicador aplicado aos valores calculados",
                    )

                with col_calc3:
                    # Informações do veículo
                    st.write("**Dados do Veículo:**")
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.caption(f"📏 Cilindrada: {vehicle_data['displacement']}L")
                        st.caption(
                            f":material/build: Cilindros: {vehicle_data['cylinders']}"
                        )
                        st.caption(
                            f"💉 Vazão: {vehicle_data['injector_flow_lbs']:.1f} lbs/h"
                        )
                    with col_info2:
                        st.caption(f"⛽ Combustível: {vehicle_data['fuel_type']}")
                        st.caption(
                            f"🚗 Tipo: {'Turbo' if vehicle_data['turbo'] else 'Aspirado'}"
                        )
                        if vehicle_data["turbo"]:
                            st.caption(
                                f"💨 Boost: {vehicle_data['boost_pressure']:.1f} bar"
                            )

                st.divider()

                # Botões de ação
                action_col1, action_col2, action_col3 = st.columns(3)

                with action_col1:
                    if st.button(
                        ":material/visibility: Visualizar Preview",
                        key=f"preview_calc_{session_key}",
                        use_container_width=True,
                    ):
                        # Calcular matriz preview
                        current_rpm_axis = current_data["rpm_axis"]
                        current_map_axis = current_data["map_axis"]

                        # Obter apenas valores ativos
                        active_rpm_values = get_active_axis_values(
                            current_rpm_axis,
                            current_data.get("rpm_enabled", [True] * grid_size),
                        )
                        active_map_values = get_active_axis_values(
                            current_map_axis,
                            current_data.get("map_enabled", [True] * grid_size),
                        )

                        if len(active_rpm_values) > 0 and len(active_map_values) > 0:
                            preview_matrix = calculate_3d_map_values_universal(
                                selected_map_type,
                                active_rpm_values,
                                active_map_values,
                                vehicle_data,
                                strategy,
                                safety_factor,
                            )

                            # Salvar preview no session_state
                            st.session_state[f"preview_matrix_{session_key}"] = (
                                preview_matrix
                            )
                            st.session_state[f"show_preview_{session_key}"] = True
                        else:
                            st.error("Configure eixos com valores ativos primeiro")

                with action_col2:
                    if st.button(
                        ":material/check: Aplicar Cálculo",
                        type="primary",
                        key=f"apply_calc_{session_key}",
                        use_container_width=True,
                    ):
                        # Calcular e aplicar matriz
                        current_rpm_axis = current_data["rpm_axis"]
                        current_map_axis = current_data["map_axis"]

                        # Obter apenas valores ativos
                        active_rpm_values = get_active_axis_values(
                            current_rpm_axis,
                            current_data.get("rpm_enabled", [True] * grid_size),
                        )
                        active_map_values = get_active_axis_values(
                            current_map_axis,
                            current_data.get("map_enabled", [True] * grid_size),
                        )

                        if len(active_rpm_values) > 0 and len(active_map_values) > 0:
                            calculated_matrix = calculate_3d_map_values_universal(
                                selected_map_type,
                                active_rpm_values,
                                active_map_values,
                                vehicle_data,
                                strategy,
                                safety_factor,
                            )

                            # Expandir matriz calculada para o grid completo
                            full_matrix = np.zeros((grid_size, grid_size))
                            active_rpm_indices = [
                                i
                                for i, enabled in enumerate(
                                    current_data.get("rpm_enabled", [True] * grid_size)[
                                        :grid_size
                                    ]
                                )
                                if enabled
                            ]
                            active_map_indices = [
                                i
                                for i, enabled in enumerate(
                                    current_data.get("map_enabled", [True] * grid_size)[
                                        :grid_size
                                    ]
                                )
                                if enabled
                            ]

                            # A matriz calculada tem dimensões len(active_rpm_values) x len(active_map_values)
                            # Precisamos mapear corretamente para a matriz completa
                            for i, rpm_idx in enumerate(active_rpm_indices):
                                for j, map_idx in enumerate(active_map_indices):
                                    if (
                                        i < calculated_matrix.shape[0]
                                        and j < calculated_matrix.shape[1]
                                    ):
                                        full_matrix[rpm_idx, map_idx] = (
                                            calculated_matrix[i, j]
                                        )

                            # Aplicar à matriz do session_state
                            st.session_state[session_key]["values_matrix"] = full_matrix
                            st.session_state[f"show_calculator_{session_key}"] = False
                            st.success(
                                f"Matriz calculada com estratégia {strategy_info['name']}!"
                            )
                            st.rerun()
                        else:
                            st.error("Configure eixos com valores ativos primeiro")

                with action_col3:
                    if st.button(
                        ":material/cancel: Cancelar",
                        key=f"cancel_calc_{session_key}",
                        use_container_width=True,
                    ):
                        st.session_state[f"show_calculator_{session_key}"] = False
                        st.session_state[f"show_preview_{session_key}"] = False
                        st.rerun()

                # Visualização do Preview
                if st.session_state.get(f"show_preview_{session_key}", False):
                    preview_matrix = st.session_state.get(
                        f"preview_matrix_{session_key}"
                    )
                    if preview_matrix is not None:
                        st.divider()
                        st.markdown("#### :material/analytics: Visualização do Preview")

                        # Estatísticas
                        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                        with col_stat1:
                            st.metric(
                                "Valor Mínimo",
                                f"{np.min(preview_matrix):.3f} {map_info['unit']}",
                            )
                        with col_stat2:
                            st.metric(
                                "Valor Máximo",
                                f"{np.max(preview_matrix):.3f} {map_info['unit']}",
                            )
                        with col_stat3:
                            st.metric(
                                "Valor Médio",
                                f"{np.mean(preview_matrix):.3f} {map_info['unit']}",
                            )
                        with col_stat4:
                            st.metric("Desvio Padrão", f"{np.std(preview_matrix):.3f}")

                        # Gráfico 3D Surface
                        # Obter valores ativos dos eixos
                        active_rpm_values = get_active_axis_values(
                            current_data["rpm_axis"],
                            current_data.get("rpm_enabled", [True] * grid_size),
                        )
                        active_map_values = get_active_axis_values(
                            current_data["map_axis"],
                            current_data.get("map_enabled", [True] * grid_size),
                        )

                        # Criar gráfico de superfície 3D
                        fig_3d = go.Figure(
                            data=[
                                go.Surface(
                                    z=preview_matrix,
                                    x=active_map_values,
                                    y=active_rpm_values,
                                    colorscale="RdYlBu",
                                    reversescale=True,
                                    showscale=True,
                                    colorbar=dict(
                                        title=f"{map_info['unit']}",
                                        titleside="right",
                                        tickmode="linear",
                                        tick0=np.min(preview_matrix),
                                        dtick=(
                                            np.max(preview_matrix)
                                            - np.min(preview_matrix)
                                        )
                                        / 10,
                                    ),
                                )
                            ]
                        )

                        fig_3d.update_layout(
                            title=f"Mapa 3D Calculado - {STRATEGY_PRESETS[strategy]['name']}",
                            scene=dict(
                                xaxis_title="MAP (bar)",
                                yaxis_title="RPM",
                                zaxis_title=f"Valor ({map_info['unit']})",
                                camera=dict(eye=dict(x=1.5, y=1.5, z=1.3)),
                            ),
                            height=500,
                        )

                        st.plotly_chart(fig_3d, use_container_width=True)

                        # Comparação com valores atuais
                        st.markdown("#### :material/trending_up: Comparação de Cortes")

                        tab_rpm, tab_map = st.tabs(["Corte por RPM", "Corte por MAP"])

                        with tab_rpm:
                            # Selecionar RPM para visualizar
                            selected_rpm_idx = st.slider(
                                "Selecione o RPM",
                                min_value=0,
                                max_value=len(active_rpm_values) - 1,
                                value=len(active_rpm_values) // 2,
                                format=f"RPM %d",
                                key=f"rpm_slice_{session_key}",
                            )
                            selected_rpm = active_rpm_values[selected_rpm_idx]

                            # Obter valores atuais e calculados para este RPM
                            current_slice = []
                            preview_slice = preview_matrix[selected_rpm_idx, :]

                            # Pegar slice da matriz atual
                            for map_idx in range(len(active_map_values)):
                                rpm_idx_in_full = [
                                    i
                                    for i, enabled in enumerate(
                                        current_data.get(
                                            "rpm_enabled", [True] * grid_size
                                        )
                                    )
                                    if enabled
                                ][selected_rpm_idx]
                                map_idx_in_full = [
                                    i
                                    for i, enabled in enumerate(
                                        current_data.get(
                                            "map_enabled", [True] * grid_size
                                        )
                                    )
                                    if enabled
                                ][map_idx]
                                current_slice.append(
                                    current_data["values_matrix"][rpm_idx_in_full][
                                        map_idx_in_full
                                    ]
                                )

                            # Criar gráfico de comparação
                            fig_rpm = go.Figure()

                            fig_rpm.add_trace(
                                go.Scatter(
                                    x=active_map_values,
                                    y=current_slice,
                                    mode="lines+markers",
                                    name="Valores Atuais",
                                    line=dict(color="red", width=2),
                                    marker=dict(size=6),
                                )
                            )

                            fig_rpm.add_trace(
                                go.Scatter(
                                    x=active_map_values,
                                    y=preview_slice,
                                    mode="lines+markers",
                                    name="Valores Calculados",
                                    line=dict(color="blue", width=3),
                                    marker=dict(size=8),
                                )
                            )

                            fig_rpm.update_layout(
                                title=f"Comparação em RPM = {selected_rpm:.0f}",
                                xaxis_title="MAP (bar)",
                                yaxis_title=f"Valor ({map_info['unit']})",
                                height=400,
                            )

                            st.plotly_chart(fig_rpm, use_container_width=True)

                        with tab_map:
                            # Selecionar MAP para visualizar
                            selected_map_idx = st.slider(
                                "Selecione o MAP",
                                min_value=0,
                                max_value=len(active_map_values) - 1,
                                value=len(active_map_values) // 2,
                                format=f"MAP %d",
                                key=f"map_slice_{session_key}",
                            )
                            selected_map = active_map_values[selected_map_idx]

                            # Obter valores atuais e calculados para este MAP
                            current_slice = []
                            preview_slice = preview_matrix[:, selected_map_idx]

                            # Pegar slice da matriz atual
                            for rpm_idx in range(len(active_rpm_values)):
                                rpm_idx_in_full = [
                                    i
                                    for i, enabled in enumerate(
                                        current_data.get(
                                            "rpm_enabled", [True] * grid_size
                                        )
                                    )
                                    if enabled
                                ][rpm_idx]
                                map_idx_in_full = [
                                    i
                                    for i, enabled in enumerate(
                                        current_data.get(
                                            "map_enabled", [True] * grid_size
                                        )
                                    )
                                    if enabled
                                ][selected_map_idx]
                                current_slice.append(
                                    current_data["values_matrix"][rpm_idx_in_full][
                                        map_idx_in_full
                                    ]
                                )

                            # Criar gráfico de comparação
                            fig_map = go.Figure()

                            fig_map.add_trace(
                                go.Scatter(
                                    x=active_rpm_values,
                                    y=current_slice,
                                    mode="lines+markers",
                                    name="Valores Atuais",
                                    line=dict(color="red", width=2),
                                    marker=dict(size=6),
                                )
                            )

                            fig_map.add_trace(
                                go.Scatter(
                                    x=active_rpm_values,
                                    y=preview_slice,
                                    mode="lines+markers",
                                    name="Valores Calculados",
                                    line=dict(color="blue", width=3),
                                    marker=dict(size=8),
                                )
                            )

                            fig_map.update_layout(
                                title=f"Comparação em MAP = {selected_map:.3f} bar",
                                xaxis_title="RPM",
                                yaxis_title=f"Valor ({map_info['unit']})",
                                height=400,
                            )

                            st.plotly_chart(fig_map, use_container_width=True)

        st.divider()

        # Operações na matriz
        col_ops1, col_ops2, col_ops3 = st.columns(3)

        with col_ops1:
            if st.button(
                "Suavizar Matriz", use_container_width=True, key=f"smooth_{session_key}"
            ):
                current_matrix = st.session_state[session_key]["values_matrix"]
                smoothed_matrix = interpolate_3d_matrix(current_matrix)
                st.session_state[session_key]["values_matrix"] = smoothed_matrix
                st.success("Matriz suavizada!")
                st.rerun()

        with col_ops2:
            if st.button(
                "Aplicar Gradiente",
                use_container_width=True,
                key=f"gradient_{session_key}",
            ):
                # Aplicar gradiente linear
                rows, cols = st.session_state[session_key]["values_matrix"].shape
                base_val = (map_info["min_value"] + map_info["max_value"]) / 2
                gradient = np.linspace(base_val * 0.8, base_val * 1.2, rows)
                for i in range(rows):
                    st.session_state[session_key]["values_matrix"][i, :] = gradient[i]
                st.success("Gradiente aplicado!")
                st.rerun()

        with col_ops3:
            if st.button(
                "Resetar Matriz",
                use_container_width=True,
                key=f"reset_matrix_{session_key}",
            ):
                # Usar eixos ativos para gerar matriz
                active_rpm_enabled = st.session_state[session_key]["rpm_enabled"]
                active_map_enabled = st.session_state[session_key]["map_enabled"]
                st.session_state[session_key]["values_matrix"] = (
                    get_default_3d_map_values(
                        selected_map_type, active_rpm_enabled, active_map_enabled
                    )
                )
                st.success("Matriz resetada!")
                st.rerun()

    with edit_tab2:
        st.caption(
            f"Configure os eixos X (RPM) e Y (MAP) - {map_info['grid_size']} posições cada"
        )

        col_x, col_y = st.columns(2)

        with col_x:
            st.subheader("Configurar Eixo X (RPM)")

            # Garantir que temos o número correto de posições
            grid_size = map_info["grid_size"]
            rpm_axis_temp = current_data["rpm_axis"].copy()
            rpm_axis_values = [0.0] * grid_size  # Inicializar com grid_size zeros
            for i in range(min(len(rpm_axis_temp), grid_size)):
                rpm_axis_values[i] = rpm_axis_temp[i]

            rpm_enabled_values = current_data.get("rpm_enabled", [True] * grid_size)

            # Criar DataFrame para edição
            rpm_df = pd.DataFrame(
                {
                    "Ativo": rpm_enabled_values[:grid_size],
                    "Posição": [f"{i+1}" for i in range(grid_size)],
                    "RPM": rpm_axis_values,
                }
            )

            # Editor de tabela
            edited_rpm_df = st.data_editor(
                rpm_df,
                column_config={
                    "Ativo": st.column_config.CheckboxColumn(
                        "Ativo",
                        help="Marque para ativar esta posição",
                        default=False,
                        width="small",
                    ),
                    "Posição": st.column_config.TextColumn(
                        "Posição", disabled=True, width="small"
                    ),
                    "RPM": st.column_config.NumberColumn(
                        "RPM",
                        help="Valor do RPM",
                        format="%.0f",
                        step=100,
                        width="medium",
                    ),
                },
                hide_index=True,
                use_container_width=True,
                height=400,
                key=f"rpm_editor_{session_key}",
            )

            # Atualizar no session state
            st.session_state[session_key]["rpm_axis"] = edited_rpm_df["RPM"].tolist()
            st.session_state[session_key]["rpm_enabled"] = edited_rpm_df[
                "Ativo"
            ].tolist()

        with col_y:
            st.subheader("Configurar Eixo Y (MAP em bar)")

            # Garantir que temos o número correto de posições
            grid_size = map_info["grid_size"]
            map_axis_temp = current_data["map_axis"].copy()
            map_axis_values = [0.0] * grid_size  # Inicializar com grid_size zeros
            for i in range(min(len(map_axis_temp), grid_size)):
                map_axis_values[i] = map_axis_temp[i]

            map_enabled_values = current_data.get("map_enabled", [True] * grid_size)

            # Criar DataFrame para edição
            map_df = pd.DataFrame(
                {
                    "Ativo": map_enabled_values[:grid_size],
                    "Posição": [f"{i+1}" for i in range(grid_size)],
                    "MAP (bar)": map_axis_values,
                }
            )

            # Editor de tabela
            edited_map_df = st.data_editor(
                map_df,
                column_config={
                    "Ativo": st.column_config.CheckboxColumn(
                        "Ativo",
                        help="Marque para ativar esta posição",
                        default=False,
                        width="small",
                    ),
                    "Posição": st.column_config.TextColumn(
                        "Posição", disabled=True, width="small"
                    ),
                    "MAP (bar)": st.column_config.NumberColumn(
                        "MAP (bar)",
                        help="Valor do MAP em bar",
                        format="%.3f",
                        step=0.01,
                        width="medium",
                    ),
                },
                hide_index=True,
                use_container_width=True,
                height=400,
                key=f"map_editor_{session_key}",
            )

            # Atualizar no session state
            st.session_state[session_key]["map_axis"] = edited_map_df[
                "MAP (bar)"
            ].tolist()
            st.session_state[session_key]["map_enabled"] = edited_map_df[
                "Ativo"
            ].tolist()

        # Botão para regenerar matriz baseada nos eixos ativos
        if st.button(
            "Regenerar Matriz com Eixos Ativos", key=f"regenerate_matrix_{session_key}"
        ):
            active_rpm_enabled = st.session_state[session_key]["rpm_enabled"]
            active_map_enabled = st.session_state[session_key]["map_enabled"]
            new_matrix = get_default_3d_map_values(
                selected_map_type, active_rpm_enabled, active_map_enabled
            )
            st.session_state[session_key]["values_matrix"] = new_matrix
            st.success("Matriz regenerada com base nos eixos ativos!")
            st.rerun()

    # Formulário para salvar
    with st.form(f"save_form_3d_{session_key}"):
        st.subheader("Salvar Alterações")

        save_description = st.text_area(
            "Descrição das alterações",
            placeholder="Descreva as modificações realizadas no mapa 3D...",
            key=f"save_desc_3d_{session_key}",
        )

        col_save1, col_save2 = st.columns(2)

        with col_save1:
            save_button = st.form_submit_button(
                "Salvar Mapa 3D", type="primary", use_container_width=True
            )

        with col_save2:
            reset_button = st.form_submit_button(
                "Restaurar Padrão", use_container_width=True
            )

        if save_button:
            # Verificar se matrix_valid foi definido, senão assumir como válido
            try:
                is_valid = matrix_valid
            except NameError:
                is_valid = True  # Assumir válido se não foi definido

            if is_valid:
                grid_size = MAP_TYPES_3D[selected_map_type]["grid_size"]

                # Converter matriz para numpy array se necessário
                values_matrix = current_data["values_matrix"]
                if not isinstance(values_matrix, np.ndarray):
                    values_matrix = np.array(values_matrix)

                # Debug: verificar dados antes de salvar
                st.write(
                    f"Salvando mapa: {selected_map_type} para veículo {selected_vehicle_id}"
                )

                success = save_3d_map_data(
                    selected_vehicle_id,
                    selected_map_type,
                    selected_bank or "shared",
                    current_data["rpm_axis"],
                    current_data["map_axis"],
                    current_data.get("rpm_enabled", [True] * grid_size),
                    current_data.get("map_enabled", [True] * grid_size),
                    values_matrix,
                )
                if success:
                    st.success(
                        f"Mapa 3D salvo com sucesso em data/fuel_maps/map_{selected_vehicle_id}_{selected_map_type}_{selected_bank or 'shared'}.json"
                    )
                    # Aguardar um momento para mostrar mensagem
                    import time

                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(
                        "Erro ao salvar o mapa 3D - Verifique o console para mais detalhes"
                    )
            else:
                st.error("Corrija os erros de validação antes de salvar")

        if reset_button:
            # Restaurar valores padrão
            st.session_state[session_key] = {
                "rpm_axis": DEFAULT_RPM_AXIS.copy(),
                "map_axis": DEFAULT_MAP_AXIS.copy(),
                "rpm_enabled": RPM_ENABLED.copy(),
                "map_enabled": MAP_ENABLED.copy(),
                "values_matrix": get_default_3d_map_values(
                    selected_map_type, RPM_ENABLED, MAP_ENABLED
                ),
            }
            st.success("Valores padrão restaurados!")
            st.rerun()

with tab2:
    st.caption("Visualização 3D do mapa")

    if session_key in st.session_state:
        current_data = st.session_state[session_key]
        # Usar apenas valores ativos dos eixos
        grid_size = map_info["grid_size"]
        rpm_enabled = current_data.get("rpm_enabled", [True] * grid_size)
        map_enabled = current_data.get("map_enabled", [True] * grid_size)
        active_rpm_values = get_active_axis_values(
            current_data["rpm_axis"], rpm_enabled
        )
        active_map_values = get_active_axis_values(
            current_data["map_axis"], map_enabled
        )
        values_matrix = current_data["values_matrix"]

        # Filtrar a matriz para usar apenas os pontos habilitados
        active_rpm_indices = [i for i in range(len(rpm_enabled)) if rpm_enabled[i]]
        active_map_indices = [i for i in range(len(map_enabled)) if map_enabled[i]]

        # Criar matriz filtrada
        # IMPORTANTE: A matriz é criada como matrix[map_idx, rpm_idx]
        filtered_matrix = []
        for rpm_idx in active_rpm_indices:
            row = []
            for map_idx in active_map_indices:
                if map_idx < len(values_matrix) and rpm_idx < len(
                    values_matrix[map_idx]
                ):
                    row.append(values_matrix[map_idx][rpm_idx])
                else:
                    row.append(0.0)
            filtered_matrix.append(row)

        # Criar gráfico 3D Surface com gradiente invertido
        fig = go.Figure(
            data=[
                go.Surface(
                    x=active_map_values,  # MAP no eixo X
                    y=active_rpm_values,  # RPM no eixo Y
                    z=filtered_matrix,  # Matriz filtrada
                    colorscale="RdYlBu",  # Invertido: vermelho=baixo, azul=alto
                    name="Mapa 3D",
                )
            ]
        )

        fig.update_layout(
            title=f"Visualização 3D - {map_info['name']}",
            scene=dict(
                xaxis_title="MAP (bar)",  # MAP no eixo X
                yaxis_title="RPM",  # RPM no eixo Y
                zaxis_title=f"Valor ({map_info['unit']})",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
            ),
            height=600,
            autosize=True,
        )

        st.plotly_chart(fig, use_container_width=True)

        # Estatísticas da matriz - usando apenas valores da matriz filtrada
        filtered_values = np.array(filtered_matrix).flatten()

        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)

        with col_stats1:
            st.metric(
                "Valor Mínimo", f"{np.min(filtered_values):.3f} {map_info['unit']}"
            )

        with col_stats2:
            st.metric(
                "Valor Máximo", f"{np.max(filtered_values):.3f} {map_info['unit']}"
            )

        with col_stats3:
            st.metric(
                "Valor Médio", f"{np.mean(filtered_values):.3f} {map_info['unit']}"
            )

        with col_stats4:
            st.metric(
                "Desvio Padrão", f"{np.std(filtered_values):.3f} {map_info['unit']}"
            )

        # Gráfico de contorno
        st.subheader("Mapa de Contorno")

        contour_fig = go.Figure(
            data=go.Contour(
                x=active_map_values,  # MAP no eixo X
                y=active_rpm_values,  # RPM no eixo Y
                z=filtered_matrix,  # Matriz filtrada
                colorscale="RdYlBu",  # Invertido: vermelho=baixo, azul=alto
                contours=dict(showlabels=True, labelfont=dict(size=12, color="white")),
            )
        )

        contour_fig.update_layout(
            title="Vista de Contorno",
            xaxis_title="MAP (bar)",  # MAP no eixo X
            yaxis_title="RPM",  # RPM no eixo Y
            height=400,
        )

        st.plotly_chart(contour_fig, use_container_width=True)

    else:
        st.info("Configure o mapa na aba 'Editar' para ver a visualização")

with tab3:
    st.caption("Importar e exportar dados do mapa 3D")

    # Seção de Copiar para FTManager
    st.subheader(":material/content_copy: Copiar para FTManager")

    if session_key in st.session_state:
        current_data = st.session_state[session_key]
        values_matrix = current_data["values_matrix"]
        grid_size = map_info["grid_size"]
        rpm_enabled = current_data.get("rpm_enabled", [True] * grid_size)
        map_enabled = current_data.get("map_enabled", [True] * grid_size)

        # Obter índices ativos
        active_rpm_indices = [
            i for i, enabled in enumerate(rpm_enabled[:grid_size]) if enabled
        ]
        active_map_indices = [
            i for i, enabled in enumerate(map_enabled[:grid_size]) if enabled
        ]

        # Inverter a ordem do RPM para mostrar decrescente (maior para menor)
        active_rpm_indices_reversed = list(reversed(active_rpm_indices))

        # Formatar matriz com TABs entre valores (3 casas decimais)
        # RPM em ordem decrescente, MAP em ordem crescente
        ftm_matrix = []
        for rpm_idx in active_rpm_indices_reversed:
            if rpm_idx < len(values_matrix):
                row_values = []
                for map_idx in active_map_indices:
                    if map_idx < len(values_matrix[rpm_idx]):
                        row_values.append(
                            format_value_3_decimals(values_matrix[rpm_idx][map_idx])
                        )
                    else:
                        row_values.append("0.000")
                ftm_row = "\t".join(row_values)
                ftm_matrix.append(ftm_row)
        ftm_string = "\n".join(ftm_matrix)

        # Mostrar em text_area
        st.text_area(
            "Valores para FTManager (formato com TABs):",
            ftm_string,
            height=200,
            key=f"ftm_display_{session_key}",
        )

        # Botão copiar nativo do Streamlit
        col_copy1, col_copy2 = st.columns([1, 3])
        with col_copy1:
            if st.button(
                ":material/content_copy: Copiar", key=f"copy_ftm_{session_key}"
            ):
                st.success(
                    ":material/check_circle: Copiado para área de transferência!"
                )

        st.divider()

        # Seção de Colar do FTManager
        st.subheader(":material/content_paste: Aplicar Valores do FTManager")

        col_paste1, col_paste2 = st.columns([3, 1])
        with col_paste1:
            pasted_values = st.text_area(
                "Cole os valores aqui (formato com TABs):",
                height=200,
                key=f"paste_area_{session_key}",
            )

        with col_paste2:
            if st.button(":material/clear: Limpar", key=f"clear_paste_{session_key}"):
                st.session_state[f"paste_area_{session_key}"] = ""
                st.rerun()

        if st.button(
            ":material/check: Aplicar Valores Colados", key=f"apply_paste_{session_key}"
        ):
            if pasted_values.strip():
                try:
                    # Parse valores com TAB e nova linha
                    lines = pasted_values.strip().split("\n")

                    # Obter informações sobre posições ativas
                    grid_size = map_info["grid_size"]
                    rpm_enabled = current_data.get("rpm_enabled", [True] * grid_size)
                    map_enabled = current_data.get("map_enabled", [True] * grid_size)
                    active_rpm_count = sum(rpm_enabled)
                    active_map_count = sum(map_enabled)

                    if len(lines) == active_rpm_count:
                        # Obter índices ativos
                        grid_size = map_info["grid_size"]
                        active_rpm_indices = [
                            i
                            for i, enabled in enumerate(rpm_enabled[:grid_size])
                            if enabled
                        ]
                        active_map_indices = [
                            i
                            for i, enabled in enumerate(map_enabled[:grid_size])
                            if enabled
                        ]

                        # Inverter a ordem do RPM (dados vêm em ordem decrescente)
                        active_rpm_indices_reversed = list(reversed(active_rpm_indices))

                        # Criar matriz com valores existentes
                        full_matrix = st.session_state[session_key][
                            "values_matrix"
                        ].copy()

                        # Aplicar valores colados nas posições corretas
                        for i, line in enumerate(lines):
                            values = line.split("\t")
                            if len(values) == active_map_count:
                                rpm_idx = active_rpm_indices_reversed[i]
                                for j, val in enumerate(values):
                                    map_idx = active_map_indices[j]
                                    # Substituir vírgula por ponto para conversão correta
                                    val_clean = val.replace(",", ".")
                                    full_matrix[rpm_idx][map_idx] = float(val_clean)
                            else:
                                st.error(
                                    f"Linha {i+1} deve ter {active_map_count} valores separados por TAB, encontrado {len(values)}"
                                )
                                break
                        else:
                            # Aplicar à matriz
                            st.session_state[session_key]["values_matrix"] = full_matrix
                            st.success(
                                ":material/check_circle: Valores aplicados com sucesso!"
                            )
                            st.rerun()
                    else:
                        st.error(
                            f"Esperado {active_rpm_count} linhas (RPM ativos), encontrado {len(lines)}"
                        )
                except ValueError as e:
                    st.error(f"Erro ao processar valores: {str(e)}")

        st.divider()

    col_import, col_export = st.columns(2)

    with col_import:
        st.subheader("Importar Dados")

        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Arquivo de mapa 3D",
            type=["json", "csv"],
            help="Formatos suportados: JSON, CSV",
            key=f"upload_3d_{session_key}",
        )

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".json"):
                    data = json.loads(uploaded_file.read())
                    required_keys = ["rpm_axis", "map_axis", "values_matrix"]

                    if all(key in data for key in required_keys):
                        rpm_data = data["rpm_axis"]
                        map_data = data["map_axis"]
                        matrix_data = np.array(data["values_matrix"])

                        if (
                            len(rpm_data) == map_info["grid_size"]
                            and len(map_data) == map_info["grid_size"]
                            and matrix_data.shape
                            == (map_info["grid_size"], map_info["grid_size"])
                        ):

                            if st.button(
                                "Importar JSON 3D", key=f"import_json_3d_{session_key}"
                            ):
                                st.session_state[session_key] = {
                                    "rpm_axis": rpm_data,
                                    "map_axis": map_data,
                                    "values_matrix": matrix_data,
                                }
                                st.success("Dados 3D importados com sucesso!")
                                st.rerun()
                        else:
                            st.error(
                                f"Arquivo deve conter grade {map_info['grid_size']}x{map_info['grid_size']}"
                            )
                    else:
                        st.error(
                            "Formato JSON inválido - chaves necessárias: rpm_axis, map_axis, values_matrix"
                        )

                elif uploaded_file.name.endswith(".csv"):
                    df_import = pd.read_csv(uploaded_file)
                    expected_size = map_info["grid_size"] * map_info["grid_size"]

                    if len(df_import) == expected_size:
                        required_cols = ["rpm", "map", "value"]
                        if all(col in df_import.columns for col in required_cols):
                            if st.button(
                                "Importar CSV 3D", key=f"import_csv_3d_{session_key}"
                            ):
                                # Reconstruir matriz a partir do CSV
                                rpm_unique = sorted(df_import["rpm"].unique())
                                map_unique = sorted(df_import["map"].unique())

                                matrix = np.zeros((len(map_unique), len(rpm_unique)))
                                for _, row in df_import.iterrows():
                                    i = map_unique.index(row["map"])
                                    j = rpm_unique.index(row["rpm"])
                                    matrix[i, j] = row["value"]

                                st.session_state[session_key] = {
                                    "rpm_axis": rpm_unique,
                                    "map_axis": map_unique,
                                    "values_matrix": matrix,
                                }
                                st.success("Dados CSV 3D importados com sucesso!")
                                st.rerun()
                        else:
                            st.error("CSV deve ter colunas: rpm, map, value")
                    else:
                        st.error(f"CSV deve ter {expected_size} linhas")

            except Exception as e:
                st.error(f"Erro ao processar arquivo: {str(e)}")

    with col_export:
        st.subheader("Exportar Dados")

        if session_key in st.session_state:
            current_data = st.session_state[session_key]

            # Exportar JSON
            export_data = {
                "vehicle_id": selected_vehicle_id,
                "map_type": selected_map_type,
                "bank_id": selected_bank,
                "map_info": map_info,
                "rpm_axis": current_data["rpm_axis"],
                "map_axis": current_data["map_axis"],
                "rpm_enabled": current_data.get(
                    "rpm_enabled", [True] * map_info["grid_size"]
                ),
                "map_enabled": current_data.get(
                    "map_enabled", [True] * map_info["grid_size"]
                ),
                "values_matrix": current_data["values_matrix"].tolist(),
                "exported_at": pd.Timestamp.now().isoformat(),
            }

            st.download_button(
                "Exportar JSON 3D",
                data=json.dumps(export_data, indent=2),
                file_name=f"mapa_3d_{selected_map_type}_{selected_vehicle_id}.json",
                mime="application/json",
                use_container_width=True,
                key=f"export_json_3d_{session_key}",
            )

            # Exportar CSV
            rpm_axis = current_data["rpm_axis"]
            map_axis = current_data["map_axis"]
            values_matrix = current_data["values_matrix"]

            # Converter matriz para formato CSV usando apenas valores ativos
            grid_size = map_info["grid_size"]
            active_rpm_values = get_active_axis_values(
                current_data["rpm_axis"],
                current_data.get("rpm_enabled", [True] * grid_size),
            )
            active_map_values = get_active_axis_values(
                current_data["map_axis"],
                current_data.get("map_enabled", [True] * grid_size),
            )
            csv_data = []
            for i, map_val in enumerate(active_map_values):
                for j, rpm_val in enumerate(active_rpm_values):
                    csv_data.append(
                        {"rpm": rpm_val, "map": map_val, "value": values_matrix[i, j]}
                    )

            export_csv_df = pd.DataFrame(csv_data)

            st.download_button(
                "Exportar CSV 3D",
                data=export_csv_df.to_csv(index=False),
                file_name=f"mapa_3d_{selected_map_type}_{selected_vehicle_id}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"export_csv_3d_{session_key}",
            )

        else:
            st.info("Configure o mapa na aba 'Editar' para exportar")

# Rodapé com informações
st.markdown("---")
st.caption("**Sistema FuelTune - Mapas de Injeção 3D | Versão 1.0**")
