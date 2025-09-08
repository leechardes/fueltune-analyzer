"""
Página de Mapas de Injeção 2D - FuelTune

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
import streamlit.components.v1 as components

# Importações do projeto
try:
    from src.data.fuel_maps_models import (
        MapDataValidator,
        MapInterpolator,
        create_default_main_fuel_2d_map,
        create_default_rpm_compensation_map,
        create_default_temp_compensation_map,
    )
    from src.data.vehicle_database import get_all_vehicles, get_vehicle_by_id
    from src.ui.components.vehicle_selector import get_vehicle_context
except ImportError:
    # Fallback para desenvolvimento
    def get_vehicle_context():
        # Retorna um ID dummy para testes
        return "64b12a8c-0345-41a9-bfc4-d5d360efc8ca"

    pass

# === FUEL MAP AUTO CALCULATOR FUNCTIONS ===

# Funções de cálculo específicas para cada tipo de mapa


def calculate_tps_correction(
    tps_values: List[float], strategy: str = "balanced"
) -> List[float]:
    """Calcula valores de correção baseados no TPS (Throttle Position Sensor).

    Comportamento baseado em física de motores:
    - 0-20%: zona de economia, correção negativa para melhor combustão
    - 20-70%: zona neutra, sem grandes correções
    - 70-100%: zona de potência, correção positiva para mais combustível
    - WOT (100%): correção máxima para potência
    """
    corrections = []

    strategy_factors = {
        "conservative": {"economy": -2.0, "neutral": 0.0, "power": 8.0, "wot": 12.0},
        "balanced": {"economy": -5.0, "neutral": 0.0, "power": 10.0, "wot": 15.0},
        "aggressive": {"economy": -8.0, "neutral": 0.0, "power": 15.0, "wot": 20.0},
    }

    factors = strategy_factors.get(strategy, strategy_factors["balanced"])

    for tps in tps_values:
        if tps <= 20:  # Zona de economia
            # Interpolação linear entre 0% e -X% baseado na estratégia
            correction = factors["economy"] * (tps / 20.0)
        elif tps <= 70:  # Zona neutra
            # Transição suave da economia para neutro
            transition = (tps - 20) / 50.0  # 0 a 1
            correction = factors["economy"] * (1 - transition)
        elif tps < 100:  # Zona de potência
            # Transição do neutro para potência
            transition = (tps - 70) / 30.0  # 0 a 1
            correction = factors["power"] * transition
        else:  # WOT (Wide Open Throttle)
            correction = factors["wot"]

        corrections.append(correction)

    return corrections


def calculate_temp_correction(
    temp_values: List[float], cooling_type: str = "water", climate: str = "temperate"
) -> List[float]:
    """Calcula correção por temperatura do motor.

    Baseado em física de combustão:
    - < 40°C: motor frio, precisa enriquecimento
    - 80-90°C: temperatura ideal, sem correção
    - > 100°C: motor quente, pode precisar enriquecimento para resfriamento
    """
    corrections = []

    # Fatores baseados no tipo de refrigeração e clima
    cooling_factors = {
        "water": {"cold_max": 25.0, "hot_max": 8.0},
        "air": {"cold_max": 30.0, "hot_max": 12.0},
    }

    climate_factors = {"cold": 0.8, "temperate": 1.0, "hot": 1.3}

    cool_factor = cooling_factors.get(cooling_type, cooling_factors["water"])
    climate_mult = climate_factors.get(climate, 1.0)

    for temp in temp_values:
        if temp < 40:  # Motor frio
            # Enriquecimento máximo no frio, reduzindo conforme esquenta
            cold_factor = (40 - temp) / 40.0  # 1.0 a 0°C, 0.0 a 40°C
            correction = cool_factor["cold_max"] * cold_factor * climate_mult
        elif temp <= 80:  # Aquecendo
            # Transição do enriquecimento para neutro
            warm_factor = (80 - temp) / 40.0  # 1.0 a 40°C, 0.0 a 80°C
            correction = cool_factor["cold_max"] * 0.3 * warm_factor * climate_mult
        elif temp <= 95:  # Temperatura ideal
            correction = 0.0
        elif temp <= 105:  # Começando a esquentar demais
            # Pequeno enriquecimento para resfriamento
            hot_factor = (temp - 95) / 10.0  # 0.0 a 95°C, 1.0 a 105°C
            correction = cool_factor["hot_max"] * 0.3 * hot_factor * climate_mult
        else:  # Motor muito quente
            # Enriquecimento para proteção térmica
            overheat_factor = min((temp - 105) / 20.0, 1.0)  # Max em 125°C
            correction = (
                cool_factor["hot_max"] * (0.3 + 0.7 * overheat_factor) * climate_mult
            )

        corrections.append(correction)

    return corrections


def calculate_air_temp_correction(air_temp_values: List[float]) -> List[float]:
    """Calcula correção por temperatura do ar de admissão.

    Baseado na lei dos gases ideais - densidade do ar varia com temperatura:
    - Ar frio (< 20°C): mais denso, precisa menos combustível
    - Ar quente (> 40°C): menos denso, precisa mais combustível
    """
    corrections = []

    # Temperatura de referência: 25°C (padrão para calibração)
    ref_temp = 25.0

    for air_temp in air_temp_values:
        # Calcular densidade relativa do ar
        # Densidade = P / (R * T) onde T é temperatura absoluta
        temp_absolute = air_temp + 273.15
        ref_temp_absolute = ref_temp + 273.15

        # Fator de densidade (relativo à temperatura de referência)
        density_ratio = ref_temp_absolute / temp_absolute

        # Conversão para percentual de correção
        # Se densidade é maior (ar frio), precisamos reduzir combustível
        # Se densidade é menor (ar quente), precisamos aumentar combustível
        correction = (density_ratio - 1.0) * 100.0

        # Limitar correção para valores práticos
        correction = max(-15.0, min(15.0, correction))

        corrections.append(correction)

    return corrections


def calculate_voltage_correction(
    voltage_values: List[float], injector_impedance: str = "high"
) -> List[float]:
    """Calcula correção por voltagem (dead time dos bicos).

    Dead time varia com voltagem - bicos precisam de tempo mínimo para abrir:
    - < 12V: dead time maior, precisa compensação
    - 13-14V: voltagem nominal
    - > 14V: dead time menor
    """
    corrections = []

    # Dead time característico por tipo de bico (em ms)
    dead_time_base = {
        "high": 1.0,  # Bicos de alta impedância (12-16Ω)
        "low": 0.6,  # Bicos de baixa impedância (2-3Ω)
    }

    base_voltage = 13.5  # Voltagem de referência
    base_dead_time = dead_time_base.get(injector_impedance, dead_time_base["high"])

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
        correction = dead_time - base_dead_time

        corrections.append(correction)

    return corrections


def calculate_rpm_compensation(
    rpm_values: List[float],
    has_turbo: bool = False,
    redline: int = 7000,
    idle_rpm: int = 800,
) -> List[float]:
    """Calcula compensação por RPM baseada na eficiência volumétrica.

    Padrão FTManager:
    - Baixa rotação (idle até ~2400): 0% (sem correção)
    - Média rotação (~2400-4500): correção positiva crescente
    - Pico (~4000-4500): máxima correção
    - Alta rotação (>4500): correção decrescente
    """
    corrections = []

    # Pontos de referência do comportamento FTManager
    start_correction_rpm = 2400  # Onde começa a correção
    peak_rpm = 4200 if not has_turbo else 4500  # Pico de correção

    for rpm in rpm_values:
        if rpm <= start_correction_rpm:
            # Sem correção em baixas rotações (idle até 2400)
            correction = 0.0
        elif rpm <= peak_rpm:
            # Correção crescente até o pico
            progress = (rpm - start_correction_rpm) / (peak_rpm - start_correction_rpm)
            max_correction = 12.0 if has_turbo else 10.0
            correction = progress * max_correction  # 0% a 10-12%
        elif rpm <= redline * 0.9:
            # Correção decrescente após o pico
            progress = (rpm - peak_rpm) / (redline * 0.9 - peak_rpm)
            max_correction = 12.0 if has_turbo else 10.0
            correction = max_correction * (
                1.0 - progress * 0.7
            )  # Cai para ~30% do máximo
        elif rpm <= redline:
            # Próximo ao limitador, correção mínima mas ainda presente
            max_correction = 12.0 if has_turbo else 10.0
            correction = max_correction * 0.3  # ~3-4% de correção
        else:  # Acima do limitador (não deveria acontecer normalmente)
            # Correção mínima de segurança
            correction = 2.0

        corrections.append(correction)

    return corrections


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
                # Garantir que não seja None
                if boost_value is None:
                    boost_value = 1.0

            return {
                "displacement": vehicle.get("engine_displacement", 2.0),  # Litros
                "cylinders": vehicle.get("engine_cylinders", 4),
                "injector_flow_cc": injector_flow_cc,  # cc/min
                "injector_flow_lbs": total_flow_lbs,  # lbs/h para exibição
                "fuel_type": vehicle.get("fuel_type", "Gasolina"),
                "turbo": is_turbo,
                "boost_pressure": boost_value,  # Usar pressão máxima salva
                "bsfc_factor": vehicle.get("bsfc_factor", 0.50),
                # Novos campos para cálculos específicos
                "injector_impedance": vehicle.get(
                    "injector_impedance", "high"
                ),  # high/low
                "cooling_type": vehicle.get("cooling_type", "water"),  # water/air
                "redline_rpm": vehicle.get("redline_rpm", 7000),
                "idle_rpm": vehicle.get("idle_rpm", 800),
                "climate": vehicle.get("climate", "temperate"),  # cold/temperate/hot
            }

    # Valores padrão se não houver veículo selecionado
    return {
        "displacement": 2.0,  # Litros
        "cylinders": 4,
        "injector_flow_cc": 550,  # cc/min
        "injector_flow_lbs": 52,  # lbs/h (550cc/min ≈ 52 lbs/h)
        "fuel_type": "Gasolina",
        "turbo": False,
        "boost_pressure": 0.0,  # bar
        "bsfc_factor": 0.50,
        # Valores padrão para novos campos
        "injector_impedance": "high",  # high/low
        "cooling_type": "water",  # water/air
        "redline_rpm": 7000,
        "idle_rpm": 800,
        "climate": "temperate",  # cold/temperate/hot
    }


def calculate_base_injection_time(
    map_kpa: float,
    engine_displacement: float,
    cylinders: int,
    injector_flow_cc_min: float,
    afr_target: float,
    boost_pressure: float = 0,
) -> float:
    """Calcula tempo base de injeção baseado nos parâmetros do motor.

    A vazão do bico varia com a pressão de combustível:
    - Vazão nominal é medida a 3 bar de pressão de combustível
    - Com boost, a pressão de combustível aumenta (regulador 1:1)
    - Nova vazão = Vazão nominal × √(Nova pressão / Pressão base)
    """
    try:
        # MAP é pressão absoluta em kPa
        map_bar = map_kpa / 100.0

        # Calcular pressão de combustível real
        # Pressão base = 3 bar (padrão para medição de vazão)
        # Com boost, pressão aumenta 1:1 (regulador de pressão referenciado)
        fuel_pressure_base = 3.0  # bar
        fuel_pressure_actual = fuel_pressure_base + boost_pressure

        # Ajustar vazão do bico baseado na pressão real
        # Fórmula: Q2 = Q1 × √(P2/P1)
        flow_correction = (fuel_pressure_actual / fuel_pressure_base) ** 0.5
        injector_flow_corrected = injector_flow_cc_min * flow_correction

        # Calcular VE baseado na pressão MAP absoluta
        # Agora usando valores corretos considerando 1.013 bar como atmosférico
        if map_bar <= 0.2:  # Vácuo extremo (< 20 kPa absoluto)
            ve = 0.25 + (map_bar * 1.0)  # 25-45% VE
        elif map_bar <= 0.4:  # Vácuo alto (20-40 kPa)
            ve = 0.45 + (map_bar - 0.2) * 0.5  # 45-55% VE
        elif map_bar <= 0.6:  # Vácuo médio (40-60 kPa)
            ve = 0.55 + (map_bar - 0.4) * 0.75  # 55-70% VE
        elif map_bar <= 0.8:  # Vácuo baixo (60-80 kPa)
            ve = 0.70 + (map_bar - 0.6) * 0.5  # 70-80% VE
        elif map_bar <= 1.013:  # Próximo à atmosférica (80-101.3 kPa)
            ve = 0.80 + (map_bar - 0.8) * 0.7  # 80-95% VE
        elif map_bar <= 1.5:  # Boost baixo (101.3-150 kPa)
            ve = 0.95 + (map_bar - 1.013) * 0.1  # 95-100% VE
        elif map_bar <= 2.0:  # Boost médio (150-200 kPa)
            ve = 1.00 + (map_bar - 1.5) * 0.2  # 100-110% VE
        else:  # Boost alto (>200 kPa)
            ve = 1.10 + min((map_bar - 2.0) * 0.15, 0.2)  # 110-130% VE

        # Assumindo RPM médio de 3000 para cálculo base
        rpm = 3000

        # Volume de ar por cilindro por ciclo (L)
        cylinder_volume = engine_displacement / cylinders

        # Taxa de fluxo de ar (L/min)
        air_flow_per_cylinder = (cylinder_volume * ve * rpm) / 2  # /2 porque 4 tempos

        # Converter para g/min (densidade do ar ~1.2 g/L)
        air_mass_per_min = air_flow_per_cylinder * 1.2

        # Massa de combustível necessária por minuto (g/min)
        fuel_mass_per_min = air_mass_per_min / afr_target

        # Converter para por ciclo
        fuel_per_cycle = fuel_mass_per_min / (
            rpm / 2
        )  # /2 porque injeta a cada 2 rotações

        # Converter vazão do bico CORRIGIDA de cc/min para g/min
        # Densidade da gasolina ~0.75 g/cc
        fuel_density = 0.75
        injector_flow_g_min = (
            injector_flow_corrected / cylinders
        ) * fuel_density  # Por bico, com correção de pressão

        # Calcular duty cycle necessário
        duty_cycle = (
            (fuel_mass_per_min / injector_flow_g_min) if injector_flow_g_min > 0 else 0
        )

        # Tempo disponível por ciclo (ms)
        time_per_cycle = (60000 / rpm) * 2  # *2 porque injeta a cada 2 rotações

        # Tempo de injeção (ms)
        injection_time = time_per_cycle * duty_cycle

        # Adicionar tempo morto do bico (dead time)
        dead_time = 1.0  # ms típico
        injection_time += dead_time

        # Adicionar fator de escala baseado na pressão para garantir progressão correta
        # Pressão atmosférica (1.013 bar) deve ter valores maiores que vácuo
        pressure_factor = map_bar / 1.013  # Normalizar pela pressão atmosférica
        if pressure_factor < 1.0:
            # Para vácuo, reduzir proporcionalmente
            injection_time = injection_time * (0.3 + 0.7 * pressure_factor)
        else:
            # Para boost, aumentar proporcionalmente
            injection_time = injection_time * (1.0 + (pressure_factor - 1.0) * 0.5)

        return max(1.5, min(injection_time, 35.0))  # Entre 1.5ms e 35ms

    except Exception as e:
        return 2.0  # Valor padrão seguro


def get_afr_target(map_kpa: float, strategy: str) -> float:
    """Retorna AFR alvo baseado na pressão MAP e estratégia."""
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


def apply_boost_correction(
    base_time: float, map_kpa: float, boost_pressure_bar: float, has_turbo: bool
) -> float:
    """Aplica correção para pressão de boost."""
    if not has_turbo or map_kpa <= 100:
        return base_time

    # Fator de correção baseado na pressão de boost
    boost_factor = 1.0 + (boost_pressure_bar * (map_kpa - 100) / 100)
    return base_time * boost_factor


def apply_fuel_correction(base_time: float, fuel_type: str) -> float:
    """Aplica correção baseada no tipo de combustível."""
    corrections = {
        "gasoline": 1.0,
        "gasolina": 1.0,
        "ethanol": 1.4,  # Etanol precisa ~40% mais combustível
        "etanol": 1.4,
        "e85": 1.3,  # E85 precisa ~30% mais
        "flex": 1.2,  # Flex pode variar
        "metanol": 1.5,  # Metanol precisa mais combustível
        "gnv": 0.9,  # GNV é mais eficiente
        "racing": 0.95,  # Combustível de corrida pode ser mais eficiente
    }
    return base_time * corrections.get(fuel_type.lower(), 1.0)


def calculate_map_values_universal(
    map_type: str,
    axis_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = "balanced",
    safety_factor: float = 1.0,
    **kwargs,
) -> List[float]:
    """Função universal para calcular valores de qualquer tipo de mapa 2D.

    Args:
        map_type: Tipo do mapa (ex: "main_fuel_2d_map", "tps_correction_2d")
        axis_values: Valores do eixo X
        vehicle_data: Dados do veículo
        strategy: Estratégia de tuning
        safety_factor: Fator de segurança
        **kwargs: Parâmetros específicos para cada tipo de mapa

    Returns:
        Lista com valores calculados
    """
    # Obter informações do tipo de mapa
    map_info = MAP_TYPES_2D.get(map_type, {})
    axis_type = map_info.get("axis_type", "")
    unit = map_info.get("unit", "%")

    # Calcular valores baseado no tipo de mapa
    if map_type == "main_fuel_2d_map":
        # Usar função existente para mapa principal
        return calculate_map_values(
            axis_values,
            vehicle_data,
            strategy,
            safety_factor,
            kwargs.get("apply_fuel_corr", True),
        )

    elif map_type == "tps_correction_2d":
        # Correção por TPS
        calculated_values = calculate_tps_correction(axis_values, strategy)
        return [val * safety_factor for val in calculated_values]

    elif map_type == "temp_correction_2d":
        # Correção por temperatura do motor
        cooling_type = kwargs.get(
            "cooling_type", vehicle_data.get("cooling_type", "water")
        )
        climate = kwargs.get("climate", vehicle_data.get("climate", "temperate"))
        calculated_values = calculate_temp_correction(
            axis_values, cooling_type, climate
        )
        return [val * safety_factor for val in calculated_values]

    elif map_type == "air_temp_correction_2d":
        # Correção por temperatura do ar
        calculated_values = calculate_air_temp_correction(axis_values)
        return [val * safety_factor for val in calculated_values]

    elif map_type == "voltage_correction_2d":
        # Correção por voltagem (dead time)
        injector_impedance = kwargs.get(
            "injector_impedance", vehicle_data.get("injector_impedance", "high")
        )
        calculated_values = calculate_voltage_correction(
            axis_values, injector_impedance
        )
        return [val * safety_factor for val in calculated_values]

    elif map_type == "rpm_compensation_2d":
        # Compensação por RPM
        has_turbo = vehicle_data.get("turbo", False)
        redline = kwargs.get("redline", vehicle_data.get("redline_rpm", 7000))
        idle_rpm = kwargs.get("idle_rpm", vehicle_data.get("idle_rpm", 800))
        calculated_values = calculate_rpm_compensation(
            axis_values, has_turbo, redline, idle_rpm
        )
        return [val * safety_factor for val in calculated_values]

    else:
        # Tipo de mapa não reconhecido, retornar valores padrão
        st.warning(
            f"Tipo de mapa '{map_type}' não suportado pelo calculador automático"
        )
        return [0.0] * len(axis_values)


def calculate_map_values(
    axis_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str,
    safety_factor: float,
    apply_fuel_corr: bool = True,
) -> List[float]:
    """Calcula valores do mapa para todos os pontos do eixo."""
    calculated_values = []

    for map_value in axis_values:
        # MAP pode ser negativo (vácuo) ou positivo (boost)
        # Valores típicos: -1.0 a 2.0 bar (relativo à atmosfera)
        if abs(map_value) < 10:  # Assumir que valores < 10 são em bar
            map_bar_relative = map_value  # Valor relativo à pressão atmosférica
        else:
            # Se estiver em kPa, converter para bar
            map_bar_relative = map_value / 100

        # Converter para pressão absoluta
        # Pressão atmosférica = 1.013 bar (101.3 kPa)
        # -1.0 bar relative = 0.013 bar absolute (vácuo quase total)
        # -0.5 bar relative = 0.513 bar absolute (vácuo médio)
        # 0.0 bar relative = 1.013 bar absolute (pressão atmosférica)
        # 1.0 bar relative = 2.013 bar absolute (1 bar de boost)
        map_bar_absolute = map_bar_relative + 1.013
        map_absolute_kpa = map_bar_absolute * 100  # Converter para kPa para a função

        # Obter AFR alvo para este ponto usando pressão absoluta
        afr_target = get_afr_target(map_absolute_kpa, strategy)

        # Determinar boost atual baseado no MAP
        # Se MAP relativo > 0, temos boost
        current_boost = max(0, map_bar_relative)  # Boost em bar

        # Calcular tempo base de injeção usando pressão absoluta
        base_time = calculate_base_injection_time(
            map_absolute_kpa,  # Usar pressão absoluta para cálculo
            vehicle_data.get("displacement", 2.0),
            vehicle_data.get("cylinders", 4),
            vehicle_data.get("injector_flow_cc", 550),  # Usar injector_flow_cc
            afr_target,
            current_boost,  # Passar boost atual para correção de vazão
        )

        # Nota: A correção de boost agora é aplicada dentro de calculate_base_injection_time
        # através do ajuste da vazão do bico com a pressão de combustível

        # Aplicar correção de combustível se habilitado
        if apply_fuel_corr:
            fuel_type = vehicle_data.get("fuel_type", "gasoline").lower()
            base_time = apply_fuel_correction(base_time, fuel_type)

        # Aplicar fator de segurança
        final_time = base_time * safety_factor

        calculated_values.append(final_time)

    return calculated_values


def validate_vehicle_data(vehicle_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Valida se os dados do veículo estão completos para cálculo."""
    required_fields = [
        ("displacement", "Cilindrada"),
        ("cylinders", "Cilindros"),
        ("injector_flow_cc", "Vazão dos Bicos"),
    ]
    missing_fields = []

    for field, display_name in required_fields:
        value = vehicle_data.get(field, 0)
        if value == 0 or value is None:
            missing_fields.append(display_name)

    if missing_fields:
        return False, f"Dados incompletos: {', '.join(missing_fields)}"

    return True, "Dados válidos"


def ensure_all_maps_exist(vehicle_id: str) -> None:
    """Verifica e cria arquivos de mapa padrão para todos os tipos se não existirem.

    Ao iniciar a tela, verifica se existem arquivos para todos os tipos de mapas 2D.
    Se não existir, cria com valores de eixo padrão e valores de mapa zerados.
    """
    # Carregar configuração de tipos de mapas
    config_file = (
        Path(__file__).parent.parent.parent.parent / "config" / "map_types_2d.json"
    )

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            map_types_config = json.load(f)
    except:
        # Se não conseguir carregar config, usar padrão mínimo
        return

    # Para cada tipo de mapa configurado
    for map_type_key, map_config in map_types_config.items():
        # Verificar para bancada A
        for bank_id in ["A", "B"]:
            # Verificar se já existe arquivo salvo
            existing_data = load_map_data(vehicle_id, map_type_key, bank_id)

            if not existing_data:
                # Criar dados padrão usando valores do config
                default_axis = map_config.get("default_axis_values", [])
                default_enabled = map_config.get("default_enabled", [])
                positions = map_config.get("positions", 32)

                # Se não tiver valores padrão no config, criar genéricos
                if not default_axis:
                    default_axis = [0.0] * positions
                    default_enabled = [True] * min(20, positions) + [False] * max(
                        0, positions - 20
                    )

                # Criar valores de mapa zerados para posições ativas
                active_count = sum(default_enabled)
                default_map_values = [0.0] * active_count

                # Ajustar para motor aspirado se necessário
                vehicle = get_vehicle_by_id(vehicle_id)
                if vehicle and map_type_key == "main_fuel_2d_map":
                    aspiration = vehicle.get("engine_aspiration", "")
                    is_turbo = any(
                        term in aspiration.lower() for term in ["turbo", "super"]
                    )

                    if not is_turbo:
                        # Para aspirado, desabilitar valores positivos de MAP
                        turbo_config = map_config.get("turbo_adjustment", {})
                        aspirated_max = turbo_config.get("aspirated_max_index", 10)

                        # Desabilitar valores após o índice máximo para aspirados
                        for i in range(aspirated_max + 1, len(default_enabled)):
                            default_enabled[i] = False

                        # Recalcular valores ativos
                        active_count = sum(default_enabled)
                        default_map_values = [0.0] * active_count

                # Salvar o mapa com valores padrão
                save_map_data(
                    vehicle_id,
                    map_type_key,
                    bank_id,
                    default_axis,
                    default_map_values,
                    default_enabled,
                )


# Configuração da página
st.title("Mapas de Injeção 2D")
st.caption("Configure mapas de injeção bidimensionais")


# Carregar configuração de tipos de mapas 2D do arquivo externo
def load_map_types_config():
    """Carrega a configuração de tipos de mapas do arquivo JSON."""
    config_path = Path("config/map_types_2d.json")

    # Se o arquivo não existir, usar configuração padrão
    if not config_path.exists():
        return {
            "main_fuel_2d_map": {
                "name": "Mapa Principal de Injeção (MAP)",
                "positions": 32,
                "axis_type": "MAP",
                "unit": "ms",
                "min_value": 0.0,
                "max_value": 50.0,
                "description": "Mapa principal de combustível baseado na pressão MAP",
                "default_enabled_count": 21,
            },
            "tps_correction_2d": {
                "name": "Correção por TPS",
                "positions": 32,
                "axis_type": "TPS",
                "unit": "%",
                "min_value": -50.0,
                "max_value": 50.0,
                "description": "Correção de combustível baseada no TPS",
                "default_enabled_count": 16,
            },
            "temp_correction_2d": {
                "name": "Correção por Temperatura",
                "positions": 32,
                "axis_type": "TEMP",
                "unit": "%",
                "min_value": -30.0,
                "max_value": 30.0,
                "description": "Correção baseada na temperatura do motor",
                "default_enabled_count": 12,
            },
        }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Erro ao carregar configuração: {e}. Usando valores padrão.")
        return load_map_types_config.__defaults__[0]


# Carregar configuração de tipos de mapas
MAP_TYPES_2D = load_map_types_config()


def get_default_axis_values(
    axis_type: str, positions: int, map_type_key: str = None
) -> List[float]:
    """Retorna valores padrão do eixo usando configuração do JSON quando disponível."""

    # Primeiro tentar usar valores do arquivo de configuração
    if map_type_key and map_type_key in MAP_TYPES_2D:
        map_config = MAP_TYPES_2D[map_type_key]
        default_values = map_config.get("default_axis_values", [])
        if default_values and len(default_values) == positions:
            return default_values

    # Fallback para valores anteriores se não houver no config
    if axis_type == "MAP":
        # Valores MAP para 32 posições: -1.00 a 2.00 bar (21 ativas) + zeros
        return [
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
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
    elif axis_type == "TPS":
        # TPS para posições variáveis: 0 a 100%
        if positions == 20:
            return [
                0,
                5,
                10,
                15,
                20,
                25,
                30,
                35,
                40,
                45,
                50,
                55,
                60,
                65,
                70,
                75,
                80,
                85,
                90,
                100,
            ]
        else:
            return list(np.linspace(0, 100, positions))
    elif axis_type == "RPM":
        # RPM para 32 posições: 400 a 8000 RPM (24 ativas) + zeros
        return [
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
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]
    elif axis_type == "TEMP":
        # Temperatura do motor
        if positions == 16:
            return [-20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130]
        else:
            return list(np.linspace(-20, 130, positions))
    elif axis_type == "AIR_TEMP":
        # Temperatura do ar
        if positions == 16:
            return [-10, 0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100]
        else:
            return list(np.linspace(-10, 100, positions))
    elif axis_type == "VOLTAGE":
        # Tensão do sistema
        if positions == 9:
            return [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]
        else:
            return list(np.linspace(8, 16, positions))
    else:
        return [0.0] * positions


def get_default_enabled_positions(
    axis_type: str, positions: int, map_type_key: str = None
) -> List[bool]:
    """Retorna posições habilitadas por padrão usando configuração do JSON quando disponível."""

    # Primeiro tentar usar valores do arquivo de configuração
    if map_type_key and map_type_key in MAP_TYPES_2D:
        map_config = MAP_TYPES_2D[map_type_key]
        default_enabled = map_config.get("default_enabled", [])
        if default_enabled and len(default_enabled) == positions:
            return default_enabled

        # Se não tiver array de enabled, usar default_enabled_count
        default_count = map_config.get("default_enabled_count", positions)
        return [True] * min(default_count, positions) + [False] * max(
            0, positions - default_count
        )

    # Fallback para lógica anterior
    if axis_type == "MAP" and positions == 32:
        return [True] * 21 + [False] * 11  # Primeiras 21 ativas
    elif axis_type == "RPM" and positions == 32:
        return [True] * 24 + [False] * 8  # Primeiras 24 ativas
    else:
        return [True] * positions  # Todas ativas para outros tipos


def get_active_values(values: List[float], enabled: List[bool]) -> List[float]:
    """Retorna apenas os valores ativos (onde enabled[i] é True)."""
    if not enabled:
        return values  # Se não houver lista de enabled, retorna todos

    active = []
    for i in range(min(len(values), len(enabled))):
        if enabled[i]:  # Incluir apenas se estiver habilitado
            active.append(values[i])
    return active


def get_default_map_values(
    map_type: str, axis_type: str, positions: int, vehicle_id: str = None
) -> List[float]:
    """Retorna valores padrão para o mapa baseado no tipo, posições ativas e características do veículo.

    Os valores padrão são específicos para cada veículo baseado em suas características:
    - Cilindrada do motor
    - Número de cilindros
    - Vazão dos bicos
    - Tipo de combustível
    - Presença de turbo
    """
    enabled = get_default_enabled_positions(axis_type, positions)
    active_count = sum(enabled)

    # Tentar obter dados do veículo para personalizar valores padrão
    vehicle_factor = 1.0
    if vehicle_id:
        try:
            vehicle = get_vehicle_by_id(vehicle_id)
            if vehicle:
                # Calcular fator baseado nas características do veículo
                displacement = vehicle.get("engine_displacement", 2.0)
                cylinders = vehicle.get("engine_cylinders", 4)

                # Fator baseado em cilindrada por cilindro
                cc_per_cylinder = (displacement * 1000) / cylinders
                # Motor padrão: 500cc por cilindro
                vehicle_factor = cc_per_cylinder / 500.0
        except:
            pass

    if "main_fuel" in map_type:
        # Valores de injeção personalizados para o veículo
        base_min = 3.0 * vehicle_factor
        base_max = 12.0 * vehicle_factor
        return list(np.linspace(base_min, base_max, active_count))
    elif "rpm_compensation" in map_type:
        # Compensação por RPM inicial varia com características do motor
        # Motores maiores precisam de mais compensação em altas rotações
        return list(np.linspace(0, 10.0 * vehicle_factor, active_count))
    elif "tps_correction" in map_type:
        # Correção TPS baseada no veículo
        return list(np.linspace(-5.0, 5.0, active_count))
    elif "temp_correction" in map_type:
        # Correção por temperatura
        return list(np.linspace(-10.0, 10.0, active_count))
    elif "compensation" in map_type or "correction" in map_type:
        # Outros mapas de compensação/correção começam em 0
        return [0.0] * active_count
    else:
        return [0.0] * active_count


def format_value_3_decimals(value: float) -> str:
    """Formata valor com 3 casas decimais."""
    return f"{value:.3f}"


def validate_map_values(
    values: List[float], min_val: float, max_val: float
) -> Tuple[bool, str]:
    """Valida se os valores estão dentro dos limites permitidos."""
    for i, val in enumerate(values):
        if val < min_val or val > max_val:
            return (
                False,
                f"Valor na posição {i+1} ({val}) está fora do limite ({min_val} a {max_val})",
            )
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


def copy_map_from_vehicle(
    source_vehicle_id: str, target_vehicle_id: str, map_type: str, bank_id: str
) -> bool:
    """Copia dados de mapa de um veículo para outro.

    Permite usar mapas de um veículo como template para outro,
    mantendo cada mapa exclusivo por veículo.
    """
    try:
        # Carregar dados do veículo origem
        source_data = load_map_data(source_vehicle_id, map_type, bank_id)
        if not source_data:
            return False

        # Salvar para o veículo destino
        return save_map_data(
            target_vehicle_id,
            map_type,
            bank_id,
            source_data["axis_values"],
            source_data["map_values"],
            source_data.get("axis_enabled"),
        )
    except Exception as e:
        logger.error(f"Erro ao copiar mapa: {e}")
        return False


def save_map_data(
    vehicle_id: str,
    map_type: str,
    bank_id: str,
    axis_values: List[float],
    map_values: List[float],
    axis_enabled: List[bool] = None,
) -> bool:
    """Salva dados do mapa em arquivo JSON persistente."""
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
            "axis_values": axis_values,
            "map_values": map_values,
            "axis_enabled": axis_enabled,
            "timestamp": pd.Timestamp.now().isoformat(),
            "version": "1.0",
        }

        # Salvar em arquivo JSON
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        # Também salvar no session_state para acesso rápido
        st.session_state[f"saved_map_{vehicle_id}_{map_type}_{bank_id}"] = data

        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False


def load_map_data(vehicle_id: str, map_type: str, bank_id: str) -> Optional[Dict]:
    """Carrega dados do mapa de arquivo JSON persistente."""
    try:
        # Primeiro tentar do session_state (cache)
        key = f"saved_map_{vehicle_id}_{map_type}_{bank_id}"
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
    except Exception as e:
        print(f"Erro ao carregar mapa: {e}")
        return None


# Obter veículo do contexto global (sidebar)
selected_vehicle_id = get_vehicle_context()

if not selected_vehicle_id:
    st.warning(
        "Selecione um veículo no menu lateral para configurar os mapas de injeção"
    )
    st.stop()

# Garantir que todos os mapas padrão existam para este veículo
ensure_all_maps_exist(selected_vehicle_id)

# Atualizar título com informações do veículo
vehicles = load_vehicles()

# Configurações no topo
st.subheader("Configuração do Mapa")

# Layout de configurações em colunas (agora com 3 colunas, sem seletor de veículo)
config_col1, config_col2, config_col3 = st.columns([3, 2, 2])

with config_col1:
    # Seleção de tipo de mapa
    selected_map_type = st.selectbox(
        "Tipo de Mapa 2D",
        options=list(MAP_TYPES_2D.keys()),
        format_func=lambda x: MAP_TYPES_2D[x]["name"],
        key="map_type_selector",
    )
    # Informações do mapa
    map_info = MAP_TYPES_2D[selected_map_type]

with config_col2:
    # Seleção de bancada (se aplicável)
    if "main_fuel" in selected_map_type:
        selected_bank = st.radio(
            "Bancada", options=["A", "B"], key="bank_selector", horizontal=True
        )
    else:
        selected_bank = None
        st.info("Mapa Compartilhado")

with config_col3:
    # Informações do mapa
    st.metric("Posições", map_info["positions"])
    st.caption(f"{map_info['axis_type']} / {map_info['unit']}")

# Linha divisória
st.divider()

# Editor de Mapa embaixo
st.subheader("Editor de Mapa")

# Sistema de abas
tab1, tab2, tab3 = st.tabs(["Editar", "Visualizar", "Importar/Exportar"])

with tab1:
    st.caption("Editor de dados do mapa")

    # Inicializar dados se não existirem
    session_key = f"map_data_{selected_vehicle_id}_{selected_map_type}_{selected_bank}"

    if session_key not in st.session_state:
        # Tentar carregar dados salvos
        loaded_data = load_map_data(
            selected_vehicle_id, selected_map_type, selected_bank
        )
        if loaded_data:
            # Verificar se tem dados enable/disable
            axis_enabled = loaded_data.get("axis_enabled")
            if axis_enabled is None:
                axis_enabled = get_default_enabled_positions(
                    map_info["axis_type"], map_info["positions"], selected_map_type
                )
            st.session_state[session_key] = {
                "axis_values": loaded_data["axis_values"],
                "map_values": loaded_data["map_values"],
                "axis_enabled": axis_enabled,
            }
        else:
            # Criar dados padrão específicos para o veículo
            axis_enabled = get_default_enabled_positions(
                map_info["axis_type"], map_info["positions"], selected_map_type
            )
            st.session_state[session_key] = {
                "axis_values": get_default_axis_values(
                    map_info["axis_type"],
                    map_info["positions"],
                    selected_map_type,  # Passar map_type_key para usar valores do config
                ),
                "map_values": get_default_map_values(
                    selected_map_type,
                    map_info["axis_type"],
                    map_info["positions"],
                    selected_vehicle_id,  # Passar ID do veículo para personalizar valores
                ),
                "axis_enabled": axis_enabled,
            }

    current_data = st.session_state[session_key]

    # Sub-abas para edição
    edit_tab1, edit_tab2 = st.tabs(["Valores", "Eixos"])

    with edit_tab1:
        st.caption("Edite os valores do mapa usando layout horizontal")

        # Botão para calcular valores automáticos
        if st.button(
            ":material/calculate: Calcular Valores Automáticos",
            key=f"auto_calc_btn_{session_key}",
            type="secondary",
            use_container_width=True,
        ):
            st.session_state[f"show_calculator_{session_key}"] = True
            st.rerun()

        # Modal/Dialog do calculador automático
        if st.session_state.get(f"show_calculator_{session_key}", False):
            with st.container():
                st.markdown("### Calculador Automático de Mapas")
                st.markdown("---")

                # Obter dados do veículo
                vehicle_data = get_vehicle_data_from_session()
                is_valid, validation_msg = validate_vehicle_data(vehicle_data)

                if not is_valid:
                    st.error(f"Dados do veículo incompletos: {validation_msg}")
                    st.info(
                        "Configure os dados do veículo no menu lateral para usar o calculador automático"
                    )
                    if st.button(
                        ":material/close: Fechar Calculador",
                        key=f"close_calc_{session_key}",
                    ):
                        st.session_state[f"show_calculator_{session_key}"] = False
                        st.rerun()
                else:
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

                        # Configurações específicas para cada tipo de mapa
                        st.subheader("Configurações Específicas")

                        # Inicializar variáveis padrão
                        fuel_correction_enabled = True  # Padrão para todos os mapas

                        # Controles específicos baseados no tipo de mapa selecionado
                        if selected_map_type == "main_fuel_2d_map":
                            # Controles para mapa principal
                            advanced_col1, advanced_col2 = st.columns(2)

                            with advanced_col1:
                                consider_boost = st.checkbox(
                                    "Considerar Boost",
                                    value=vehicle_data["turbo"],
                                    key=f"consider_boost_{session_key}",
                                    help="Aplica correção para pressão de turbo",
                                )

                            with advanced_col2:
                                fuel_correction_enabled = st.checkbox(
                                    "Correção de Combustível",
                                    value=True,
                                    key=f"fuel_correction_{session_key}",
                                    help="Aplica correção baseada no tipo de combustível",
                                )

                        elif selected_map_type == "tps_correction_2d":
                            # Controles para correção TPS
                            st.write("**Estratégia de Aceleração:**")
                            tps_strategy_help = {
                                "conservative": "Correções suaves, economia de combustível",
                                "balanced": "Correções padrão, equilíbrio entre economia e potência",
                                "aggressive": "Correções intensas, foco em potência",
                            }

                            st.radio(
                                "Sensibilidade do TPS",
                                options=["conservative", "balanced", "aggressive"],
                                format_func=lambda x: f"{STRATEGY_PRESETS[x]['name']} - {tps_strategy_help[x]}",
                                index=1,  # Balanceada por padrão
                                key=f"tps_sensitivity_{session_key}",
                                help="Define o comportamento da correção TPS",
                            )

                        elif selected_map_type == "temp_correction_2d":
                            # Controles para correção de temperatura
                            temp_col1, temp_col2 = st.columns(2)

                            with temp_col1:
                                cooling_type = st.radio(
                                    "Tipo de Refrigeração",
                                    options=["water", "air"],
                                    format_func=lambda x: (
                                        "Água" if x == "water" else "Ar"
                                    ),
                                    index=(
                                        0
                                        if vehicle_data.get("cooling_type", "water")
                                        == "water"
                                        else 1
                                    ),
                                    key=f"cooling_type_{session_key}",
                                    help="Tipo de sistema de refrigeração do motor",
                                )

                            with temp_col2:
                                climate = st.selectbox(
                                    "Clima Predominante",
                                    options=["cold", "temperate", "hot"],
                                    format_func=lambda x: {
                                        "cold": "Frio",
                                        "temperate": "Temperado",
                                        "hot": "Quente",
                                    }[x],
                                    index=["cold", "temperate", "hot"].index(
                                        vehicle_data.get("climate", "temperate")
                                    ),
                                    key=f"climate_{session_key}",
                                    help="Clima onde o veículo será usado predominantemente",
                                )

                        elif selected_map_type == "air_temp_correction_2d":
                            # Controles para temperatura do ar
                            st.info("Correção automática baseada na densidade do ar")
                            st.caption(
                                "Baseia-se na lei dos gases ideais para calcular a densidade relativa do ar"
                            )

                        elif selected_map_type == "voltage_correction_2d":
                            # Controles para correção de voltagem
                            voltage_col1, voltage_col2 = st.columns(2)

                            with voltage_col1:
                                injector_impedance = st.radio(
                                    "Tipo de Bico",
                                    options=["high", "low"],
                                    format_func=lambda x: (
                                        "Alta Impedância (12-16Ω)"
                                        if x == "high"
                                        else "Baixa Impedância (2-3Ω)"
                                    ),
                                    index=(
                                        0
                                        if vehicle_data.get(
                                            "injector_impedance", "high"
                                        )
                                        == "high"
                                        else 1
                                    ),
                                    key=f"injector_impedance_{session_key}",
                                    help="Tipo de impedância dos bicos injetores",
                                )

                            with voltage_col2:
                                st.metric("Voltagem de Referência", "13.5V")
                                st.caption("Dead time varia com a voltagem da bateria")

                        elif selected_map_type == "rpm_compensation_2d":
                            # Controles para compensação RPM
                            rpm_col1, rpm_col2 = st.columns(2)

                            with rpm_col1:
                                redline_rpm = st.number_input(
                                    "Limitador de RPM",
                                    min_value=4000,
                                    max_value=12000,
                                    value=vehicle_data.get("redline_rpm", 7000),
                                    step=250,
                                    key=f"redline_rpm_{session_key}",
                                    help="RPM máximo do motor",
                                )

                            with rpm_col2:
                                idle_rpm = st.number_input(
                                    "RPM de Marcha Lenta",
                                    min_value=500,
                                    max_value=1500,
                                    value=vehicle_data.get("idle_rpm", 800),
                                    step=50,
                                    key=f"idle_rpm_{session_key}",
                                    help="RPM de marcha lenta",
                                )

                        else:
                            # Para tipos não implementados
                            st.info(
                                f"Configurações específicas para '{map_info['name']}' não disponíveis"
                            )

                    with calc_col2:
                        st.subheader("Dados do Veículo")

                        # Primeira linha: Cilindrada, Cilindros, Vazão Bicos
                        vehicle_col1, vehicle_col2, vehicle_col3 = st.columns(3)
                        with vehicle_col1:
                            st.metric(
                                "Cilindrada", f"{vehicle_data['displacement']:.1f}L"
                            )
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

                    # Calcular valores preview usando função universal
                    axis_values = current_data["axis_values"]
                    enabled = current_data.get("enabled", [True] * len(axis_values))

                    # Preparar parâmetros específicos para cada tipo de mapa usando controles da interface
                    calc_kwargs = {}
                    if selected_map_type == "main_fuel_2d_map":
                        calc_kwargs["apply_fuel_corr"] = fuel_correction_enabled
                    elif selected_map_type == "tps_correction_2d":
                        # Usar estratégia específica do TPS se diferente
                        tps_strategy = st.session_state.get(
                            f"tps_sensitivity_{session_key}", selected_strategy
                        )
                        selected_strategy = tps_strategy  # Sobrescrever para este tipo
                    elif selected_map_type == "temp_correction_2d":
                        calc_kwargs["cooling_type"] = st.session_state.get(
                            f"cooling_type_{session_key}",
                            vehicle_data.get("cooling_type", "water"),
                        )
                        calc_kwargs["climate"] = st.session_state.get(
                            f"climate_{session_key}",
                            vehicle_data.get("climate", "temperate"),
                        )
                    elif selected_map_type == "voltage_correction_2d":
                        calc_kwargs["injector_impedance"] = st.session_state.get(
                            f"injector_impedance_{session_key}",
                            vehicle_data.get("injector_impedance", "high"),
                        )
                    elif selected_map_type == "rpm_compensation_2d":
                        calc_kwargs["redline"] = st.session_state.get(
                            f"redline_rpm_{session_key}",
                            vehicle_data.get("redline_rpm", 7000),
                        )
                        calc_kwargs["idle_rpm"] = st.session_state.get(
                            f"idle_rpm_{session_key}", vehicle_data.get("idle_rpm", 800)
                        )

                    preview_values = calculate_map_values_universal(
                        selected_map_type,
                        axis_values,
                        vehicle_data,
                        selected_strategy,
                        safety_factor,
                        **calc_kwargs,
                    )

                    # Criar DataFrame no mesmo formato do mapa principal (uma linha, múltiplas colunas)
                    # Primeiro criar os headers com o valor do eixo
                    column_headers = {}
                    for i, (axis_val, enabled_flag) in enumerate(
                        zip(axis_values, enabled)
                    ):
                        if enabled_flag:
                            # Para valores habilitados, mostrar o valor do eixo
                            header = f"{axis_val:.1f}"
                        else:
                            # Para desabilitados, mostrar com indicação
                            header = f"[{axis_val:.1f}]"
                        column_headers[header] = preview_values[i]

                    # Criar DataFrame com uma única linha de dados
                    # Usando lista com um único dicionário para garantir uma linha
                    preview_df = pd.DataFrame([column_headers])

                    # Aplicar formatação similar ao mapa principal
                    st.write(f"**Preview dos valores calculados** ({map_info['unit']})")
                    st.caption(
                        f"Valores com 3 casas decimais - Total: {len(preview_values)} valores"
                    )

                    # Aplicar formatação de 3 casas decimais
                    formatted_preview_df = preview_df.copy()
                    for col in formatted_preview_df.columns:
                        formatted_preview_df[col] = formatted_preview_df[col].apply(
                            lambda x: round(x, 3)
                        )

                    # Filtrar apenas valores habilitados para o gradiente
                    enabled_cols = [
                        col for i, col in enumerate(preview_df.columns) if enabled[i]
                    ]
                    if enabled_cols:
                        enabled_values = [
                            preview_df[col].iloc[0] for col in enabled_cols
                        ]
                        vmin = min(enabled_values)
                        vmax = max(enabled_values)
                    else:
                        vmin = min(formatted_preview_df.iloc[0].values)
                        vmax = max(formatted_preview_df.iloc[0].values)

                    # Aplicar estilo com gradiente de cores RdYlBu
                    styled_preview = formatted_preview_df.style.background_gradient(
                        cmap="RdYlBu",  # Red-Yellow-Blue (vermelho para baixo, azul para alto)
                        axis=1,  # Gradiente horizontal
                        vmin=vmin,
                        vmax=vmax,
                        subset=None,
                    )

                    # Adicionar formato de 3 casas decimais
                    styled_preview = styled_preview.format("{:.3f}")

                    # Exibir com dataframe estilizado
                    # Usar altura mínima para uma linha (35px para header + 35px para linha de dados)
                    st.dataframe(
                        styled_preview,
                        use_container_width=True,
                        hide_index=True,
                        height=70,  # Altura mínima para header + uma linha
                    )

                    # Estatísticas do preview
                    preview_stats_col1, preview_stats_col2, preview_stats_col3 = (
                        st.columns(3)
                    )

                    with preview_stats_col1:
                        st.metric(
                            "Mínimo", f"{min(preview_values):.3f} {map_info['unit']}"
                        )
                    with preview_stats_col2:
                        st.metric(
                            "Médio", f"{np.mean(preview_values):.3f} {map_info['unit']}"
                        )
                    with preview_stats_col3:
                        st.metric(
                            "Máximo", f"{max(preview_values):.3f} {map_info['unit']}"
                        )

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
                            # Aplicar valores calculados
                            st.session_state[session_key]["map_values"] = preview_values
                            st.session_state[f"show_calculator_{session_key}"] = False
                            st.success("Valores calculados aplicados com sucesso!")
                            st.rerun()

                    with action_col2:
                        if st.button(
                            ":material/analytics: Preview Gráfico",
                            key=f"preview_graph_{session_key}",
                            use_container_width=True,
                        ):
                            # Mostrar gráfico de preview
                            fig_preview = go.Figure()

                            # Valores atuais
                            fig_preview.add_trace(
                                go.Scatter(
                                    x=axis_values,
                                    y=current_data["map_values"],
                                    mode="lines+markers",
                                    name="Atual",
                                    line=dict(color="gray", width=2),
                                    marker=dict(size=6),
                                )
                            )

                            # Valores calculados
                            fig_preview.add_trace(
                                go.Scatter(
                                    x=axis_values,
                                    y=preview_values,
                                    mode="lines+markers",
                                    name="Calculado",
                                    line=dict(color="blue", width=3),
                                    marker=dict(size=8, color="blue"),
                                )
                            )

                            fig_preview.update_layout(
                                title=f"Comparação: Atual vs Calculado ({STRATEGY_PRESETS[selected_strategy]['name']})",
                                xaxis_title=f"Eixo X ({map_info['axis_type']})",
                                yaxis_title=f"Valor ({map_info['unit']})",
                                height=400,
                            )

                            st.plotly_chart(fig_preview, use_container_width=True)

                    with action_col3:
                        if st.button(
                            ":material/cancel: Cancelar",
                            key=f"cancel_calc_{session_key}",
                            use_container_width=True,
                        ):
                            st.session_state[f"show_calculator_{session_key}"] = False
                            st.rerun()

        st.divider()

        # Criar DataFrame horizontal usando apenas valores ativos
        # Filtrar baseado em axis_enabled
        axis_enabled = current_data.get(
            "axis_enabled", [True] * len(current_data["axis_values"])
        )
        active_axis_values = get_active_values(
            current_data["axis_values"], axis_enabled
        )
        active_map_values = get_active_values(current_data["map_values"], axis_enabled)

        st.write(f"**Eixo X ({map_info['axis_type']}):** Valores numéricos")
        st.caption(f"Total de {len(active_axis_values)} posições ativas")

        # Criar dicionário com os valores do eixo X como chaves (apenas valores numéricos)
        data_dict = {}
        col_name_to_index = {}  # Mapear nome da coluna para índice original

        for i, axis_val in enumerate(active_axis_values):
            # Usar formatação 3 casas decimais para colunas
            col_name = format_value_3_decimals(axis_val)

            # Se já existe uma coluna com esse nome (ex: múltiplos 0.000), adicionar sufixo
            if col_name in data_dict:
                col_name = f"{col_name}_{i}"

            data_dict[col_name] = [
                active_map_values[i] if i < len(active_map_values) else 0.0
            ]
            col_name_to_index[col_name] = i  # Guardar índice original

        # Criar DataFrame horizontal com uma única linha de valores
        df = pd.DataFrame(data_dict)

        # Configurar colunas dinamicamente com formatação 3 casas decimais
        column_config = {}
        value_format = "%.3f"  # Sempre 3 casas decimais

        for col in df.columns:
            column_config[col] = st.column_config.NumberColumn(
                col,  # Valor numérico puro
                format=value_format,
                min_value=map_info["min_value"],
                max_value=map_info["max_value"],
                help=f"{map_info['axis_type']}: {col}, Valor em {map_info['unit']}",
            )

        # Editor de tabela horizontal com gradiente de cores
        st.write(f"**Editar valores do mapa** ({map_info['unit']})")
        st.caption(f"Valores com 3 casas decimais - Total: {len(df.columns)} valores")

        # Aplicar formatação de 3 casas decimais ao DataFrame para exibição
        formatted_df = df.copy()
        for col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: round(x, 3))

        # Aplicar estilo com gradiente de cores na linha de valores
        styled_df = formatted_df.style.background_gradient(
            cmap="RdYlBu",  # Red-Yellow-Blue (vermelho para valores baixos, azul para altos)
            axis=1,  # Aplicar gradiente ao longo das colunas (horizontal)
            vmin=min(formatted_df.iloc[0].values),  # Usar valores reais do DataFrame
            vmax=max(formatted_df.iloc[0].values),  # Usar valores reais do DataFrame
            subset=None,  # Aplicar a todas as células
        )

        # Adicionar formato de exibição com 3 casas decimais
        styled_df = styled_df.format("{:.3f}")

        # Usar st.dataframe com estilo para mostrar cores
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        st.divider()

        # Editor de dados (sem cores mas funcional)
        st.caption("Clique nos valores abaixo para editar:")
        edited_df = st.data_editor(
            df,
            num_rows="fixed",
            use_container_width=True,
            column_config=column_config,
            key=f"data_editor_{session_key}",
            hide_index=True,
        )

        # Atualizar dados na sessão
        # Manter os valores do eixo X originais (não editáveis nesta versão)
        st.session_state[session_key]["axis_values"] = current_data["axis_values"]
        # Extrair os valores editados do mapa preservando a ordem original
        # IMPORTANTE: Manter a ordem original dos valores baseado em active_axis_values
        new_values = []

        # Recriar o mapeamento para garantir consistência
        for i, axis_val in enumerate(active_axis_values):
            col_name = format_value_3_decimals(axis_val)

            # Verificar se há duplicatas (múltiplos valores 0.000 por exemplo)
            if list(df.columns).count(col_name) > 1 or col_name not in df.columns:
                # Procurar com sufixo
                col_name_with_suffix = f"{col_name}_{i}"
                if col_name_with_suffix in edited_df.columns:
                    col_name = col_name_with_suffix

            try:
                if col_name in edited_df.columns:
                    value = edited_df[col_name].iloc[0]
                    # Garantir que não seja None ou NaN
                    if value is None or (isinstance(value, float) and pd.isna(value)):
                        # Usar o valor original
                        if i < len(active_map_values):
                            value = active_map_values[i]
                        else:
                            value = 0.0
                else:
                    # Coluna não encontrada, usar valor original
                    value = active_map_values[i] if i < len(active_map_values) else 0.0

                new_values.append(float(value))
            except Exception as e:
                # Em caso de erro, usar o valor original
                if i < len(active_map_values):
                    new_values.append(float(active_map_values[i]))
                else:
                    new_values.append(0.0)

        # Atualizar valores no session_state mantendo a estrutura completa
        # Os map_values salvos contêm apenas valores para posições ativas
        # então simplesmente atualizar com os novos valores editados
        st.session_state[session_key]["map_values"] = new_values

        # Validações
        axis_valid, axis_msg = validate_map_values(
            current_data["axis_values"], -1000, 10000  # Validação genérica ampla
        )
        values_valid, values_msg = validate_map_values(
            new_values, map_info["min_value"], map_info["max_value"]
        )

        if not axis_valid:
            st.error(f"Eixo X: {axis_msg}")
        if not values_valid:
            st.error(f"Valores: {values_msg}")

        # Formulário para salvar
        with st.form(f"save_form_{session_key}"):
            st.subheader("Salvar Alterações")

            save_description = st.text_area(
                "Descrição das alterações",
                placeholder="Descreva as modificações realizadas no mapa...",
                key=f"save_desc_{session_key}",
            )

            col_save1, col_save2 = st.columns(2)

            with col_save1:
                save_button = st.form_submit_button(
                    "Salvar Mapa", type="primary", use_container_width=True
                )

            with col_save2:
                reset_button = st.form_submit_button(
                    "Restaurar Padrão", use_container_width=True
                )

            if save_button:
                # Debug info (comentado para produção)
                # st.write(f"Debug - axis_valid: {axis_valid}, values_valid: {values_valid}")
                # st.write(f"Debug - Values to save: {new_values[:5]}...")  # Primeiros 5 valores

                if axis_valid and values_valid:
                    success = save_map_data(
                        selected_vehicle_id,
                        selected_map_type,
                        selected_bank or "shared",
                        current_data["axis_values"],
                        new_values,
                        current_data.get("axis_enabled"),
                    )
                    if success:
                        st.success("Mapa salvo com sucesso!")
                        st.balloons()  # Feedback visual
                        # Aguardar um pouco antes de rerun
                        import time

                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(
                            "Erro ao salvar o mapa - Verifique as permissões do diretório data/fuel_maps"
                        )
                else:
                    st.error(
                        f"Corrija os erros de validação antes de salvar\nAxis: {axis_msg}\nValues: {values_msg}"
                    )

            if reset_button:
                # Restaurar valores padrão
                axis_enabled = get_default_enabled_positions(
                    map_info["axis_type"], map_info["positions"], selected_map_type
                )
                st.session_state[session_key] = {
                    "axis_values": get_default_axis_values(
                        map_info["axis_type"], map_info["positions"]
                    ),
                    "map_values": get_default_map_values(
                        selected_map_type, map_info["axis_type"], map_info["positions"]
                    ),
                    "axis_enabled": axis_enabled,
                }
                st.success("Valores padrão restaurados!")
                st.rerun()

    with edit_tab2:
        st.caption("Configure os eixos com sistema enable/disable")

        # Configurar eixos com checkboxes
        st.write(
            f"**Configurar Eixo X ({map_info['axis_type']})** - {map_info['positions']} posições"
        )
        st.caption("Use os checkboxes para ativar/desativar cada posição")

        # Garantir que temos o número correto de posições
        axis_values_temp = current_data["axis_values"].copy()
        total_positions = map_info["positions"]
        axis_values = [0.0] * total_positions
        for i in range(min(len(axis_values_temp), total_positions)):
            axis_values[i] = axis_values_temp[i]

        axis_enabled_values = current_data.get("axis_enabled", [True] * total_positions)

        # Determinar formato baseado no tipo de eixo
        if map_info["axis_type"] == "MAP":
            step = 0.01
            format_str = "%.3f"
        elif map_info["axis_type"] in ["VOLTAGE"]:
            step = 0.1
            format_str = "%.3f"
        else:
            step = 1.0 if map_info["axis_type"] in ["RPM", "TPS"] else 5.0
            format_str = "%.3f"

        # Criar DataFrame para edição
        axis_df = pd.DataFrame(
            {
                "Ativo": axis_enabled_values[:total_positions],
                "Posição": [f"Pos {i+1}" for i in range(total_positions)],
                f"{map_info['axis_type']}": axis_values,
            }
        )

        # Editor de tabela
        edited_axis_df = st.data_editor(
            axis_df,
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
                f"{map_info['axis_type']}": st.column_config.NumberColumn(
                    f"{map_info['axis_type']}",
                    help=f"Valor do {map_info['axis_type']}",
                    format=format_str,
                    step=step,
                    width="medium",
                ),
            },
            hide_index=True,
            use_container_width=True,
            height=400,
            key=f"axis_editor_{session_key}",
        )

        # Extrair valores editados
        new_axis_values = edited_axis_df[f"{map_info['axis_type']}"].tolist()
        new_axis_enabled = edited_axis_df["Ativo"].tolist()

        # Atualizar dados na sessão
        st.session_state[session_key]["axis_values"] = new_axis_values
        st.session_state[session_key]["axis_enabled"] = new_axis_enabled

        # Botão para aplicar apenas valores ativos
        if st.button(
            ":material/done_all: Aplicar Valores Ativos",
            key=f"apply_active_{session_key}",
        ):
            # Filtrar apenas valores ativos
            active_axis = get_active_values(new_axis_values, new_axis_enabled)
            active_map = get_active_values(
                (
                    st.session_state[session_key]["map_values"]
                    if len(st.session_state[session_key]["map_values"])
                    >= len(active_axis)
                    else get_default_map_values(
                        selected_map_type, map_info["axis_type"], map_info["positions"]
                    )[: len(active_axis)]
                ),
                new_axis_enabled,
            )

            # Garantir que temos valores de mapa suficientes
            while len(active_map) < len(active_axis):
                active_map.append(0.0)

            st.session_state[session_key]["axis_values"] = active_axis
            st.session_state[session_key]["map_values"] = active_map[: len(active_axis)]
            st.success(f"Aplicados {len(active_axis)} valores ativos!")
            st.rerun()

with tab2:
    st.caption("Visualização gráfica do mapa")

    if session_key in st.session_state:
        current_data = st.session_state[session_key]
        axis_values = current_data["axis_values"]
        map_values = current_data["map_values"]

        # Criar gráfico com gradiente de cores
        fig = go.Figure()

        # Normalizar valores para escala de cores
        min_val = min(map_values)
        max_val = max(map_values)
        norm_values = [
            (v - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            for v in map_values
        ]

        fig.add_trace(
            go.Scatter(
                x=axis_values,
                y=map_values,
                mode="lines+markers",
                name="Mapa",
                line=dict(
                    width=3,
                    color="rgba(100, 100, 100, 0.7)",  # Linha cinza semi-transparente
                ),
                marker=dict(
                    size=10,
                    color=map_values,  # Usar valores para colorir
                    colorscale="RdYlBu",  # Red-Yellow-Blue (vermelho para baixo, azul para alto)
                    cmin=min(map_values),  # Usar valores reais
                    cmax=max(map_values),  # Usar valores reais
                    showscale=True,
                    colorbar=dict(
                        title=map_info["unit"],
                        tickmode="linear",
                        tick0=map_info["min_value"],
                        dtick=(map_info["max_value"] - map_info["min_value"]) / 10,
                    ),
                    line=dict(width=1, color="white"),
                ),
            )
        )

        fig.update_layout(
            title=f"Visualização - {map_info['name']}",
            xaxis_title=f"Eixo X ({map_info['axis_type']})",
            yaxis_title=f"Valor ({map_info['unit']})",
            height=500,
            showlegend=False,
            hovermode="closest",
        )

        # Configurar grid
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")

        st.plotly_chart(fig, use_container_width=True)

        # Estatísticas do mapa
        col_stats1, col_stats2, col_stats3 = st.columns(3)

        # Formatação sempre com 3 casas decimais
        decimal_places = 3

        with col_stats1:
            st.metric(
                "Valor Mínimo",
                f"{min(map_values):.{decimal_places}f} {map_info['unit']}",
            )

        with col_stats2:
            st.metric(
                "Valor Máximo",
                f"{max(map_values):.{decimal_places}f} {map_info['unit']}",
            )

        with col_stats3:
            st.metric(
                "Valor Médio",
                f"{np.mean(map_values):.{decimal_places}f} {map_info['unit']}",
            )

        # Adicionar linha com desvio padrão
        col_stats4, col_stats5, col_stats6 = st.columns(3)

        with col_stats4:
            st.metric(
                "Desvio Padrão",
                f"{np.std(map_values):.{decimal_places}f} {map_info['unit']}",
            )

        with col_stats5:
            st.metric(
                "Amplitude",
                f"{max(map_values) - min(map_values):.{decimal_places}f} {map_info['unit']}",
            )

        with col_stats6:
            st.metric("Total de Pontos", f"{len(map_values)}")

    else:
        st.info("Configure o mapa na aba 'Editar' para ver a visualização")

with tab3:
    st.caption("Importar e exportar dados do mapa")

    # Seções organizadas
    section_tabs = st.tabs(
        ["Copiar FTManager", "Colar FTManager", "Importar Dados", "Exportar Dados"]
    )

    with section_tabs[0]:  # Copiar para FTManager
        st.subheader("Copiar para FTManager")

        if session_key in st.session_state:
            current_data = st.session_state[session_key]

            st.caption("Copie os valores formatados para colar no FTManager")

            # Gerar string para copiar (formato FTManager com 3 casas decimais)
            ftm_values = []
            for val in current_data["map_values"]:
                # Formatar valor com vírgula como separador decimal (3 casas)
                formatted = f"{val:.3f}".replace(".", ",")
                ftm_values.append(formatted)

            # Criar string com TAB entre valores (formato FTManager)
            ftm_string = "\t".join(ftm_values)

            # Área de texto para copiar
            text_area_copy = st.text_area(
                "Valores formatados para FTManager",
                value=ftm_string,
                height=100,
                key=f"copy_ftm_{session_key}",
                help="Valores separados por TAB, prontos para FTManager",
            )

            # Botão para copiar para área de transferência
            if st.button(
                "Copiar para Área de Transferência",
                key=f"copy_clipboard_{session_key}",
                use_container_width=True,
            ):
                # Usar componente HTML com JavaScript para copiar
                # Escapar tabs para JavaScript
                ftm_string_js = (
                    ftm_string.replace("\\", "\\\\")
                    .replace("\t", "\\t")
                    .replace("`", "\\`")
                )
                components.html(
                    f"""
                    <script>
                    const text = "{ftm_string_js}";
                    navigator.clipboard.writeText(text).then(function() {{
                        console.log('Copiado para área de transferência');
                    }}, function(err) {{
                        console.error('Erro ao copiar: ', err);
                    }});
                    </script>
                    """,
                    height=0,
                )
                st.success("Valores copiados para a área de transferência!")
        else:
            st.info("Configure o mapa na aba 'Editar' para copiar valores")

    with section_tabs[1]:  # Colar do FTManager
        st.subheader("Colar do FTManager")

        st.caption("Cole os valores copiados do FTManager")

        # Área para colar valores do FTManager
        paste_text = st.text_area(
            "Cole os valores aqui",
            placeholder="Cole aqui os valores copiados do FTManager...",
            height=100,
            key=f"paste_ftm_{session_key}",
            help="Aceita valores separados por TAB, espaços ou ponto-e-vírgula",
        )

        # Botões em duas colunas
        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            if st.button(
                "Aplicar Valores",
                key=f"apply_paste_{session_key}",
                use_container_width=True,
            ):
                if paste_text:
                    try:
                        # Processar valores colados - aceitar TAB, espaços ou ponto-e-vírgula
                        # Substituir tabs e ponto-e-vírgula por espaços
                        normalized_text = paste_text.replace("\t", " ").replace(
                            ";", " "
                        )
                        # Remover espaços extras e dividir
                        values_str = normalized_text.strip().split()
                        # Converter vírgulas para pontos e para float
                        new_values = [float(v.replace(",", ".")) for v in values_str]

                        # Verificar quantidade de valores
                        if session_key in st.session_state:
                            current_positions = len(
                                st.session_state[session_key]["axis_values"]
                            )
                            if len(new_values) == current_positions:
                                # Aplicar valores
                                st.session_state[session_key]["map_values"] = new_values
                                st.success(
                                    f"Aplicados {len(new_values)} valores com sucesso!"
                                )
                                st.rerun()
                            else:
                                st.error(
                                    f"Esperados {current_positions} valores, mas foram colados {len(new_values)}"
                                )
                        else:
                            st.error("Configure o mapa primeiro na aba 'Editar'")
                    except Exception as e:
                        st.error(f"Erro ao processar valores: {e}")
                else:
                    st.warning("Cole os valores primeiro")

        with btn_col2:
            if st.button(
                "Limpar", key=f"clear_paste_{session_key}", use_container_width=True
            ):
                # Limpar a área de texto
                st.session_state[f"paste_ftm_{session_key}"] = ""
                st.rerun()

    with section_tabs[2]:  # Importar Dados
        st.subheader("Importar Dados")

        # Tabs para diferentes tipos de importação
        import_tabs = st.tabs(["De Arquivo", "De Outro Veículo"])

        with import_tabs[0]:
            # Upload de arquivo
            uploaded_file = st.file_uploader(
                "Arquivo de mapa",
                type=["json", "csv"],
                help="Formatos suportados: JSON, CSV",
                key=f"upload_{session_key}",
            )

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith(".json"):
                        data = json.loads(uploaded_file.read())
                        if "axis_values" in data and "map_values" in data:
                            if (
                                len(data["axis_values"]) == map_info["positions"]
                                and len(data["map_values"]) == map_info["positions"]
                            ):

                                if st.button(
                                    "Importar JSON", key=f"import_json_{session_key}"
                                ):
                                    st.session_state[session_key] = {
                                        "axis_values": data["axis_values"],
                                        "map_values": data["map_values"],
                                    }
                                    st.success("Dados importados com sucesso!")
                                    st.rerun()
                            else:
                                st.error(
                                    f"Arquivo deve conter {map_info['positions']} valores"
                                )
                        else:
                            st.error("Formato JSON inválido")

                    elif uploaded_file.name.endswith(".csv"):
                        df_import = pd.read_csv(uploaded_file)
                        if len(df_import) == map_info["positions"]:
                            required_cols = ["axis_x", "value"]
                            if all(col in df_import.columns for col in required_cols):
                                if st.button(
                                    "Importar CSV", key=f"import_csv_{session_key}"
                                ):
                                    st.session_state[session_key] = {
                                        "axis_values": df_import["axis_x"].tolist(),
                                        "map_values": df_import["value"].tolist(),
                                    }
                                    st.success("Dados importados com sucesso!")
                                    st.rerun()
                            else:
                                st.error("CSV deve ter colunas: axis_x, value")
                        else:
                            st.error(f"CSV deve ter {map_info['positions']} linhas")

                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {str(e)}")

        with import_tabs[1]:
            st.markdown("### Copiar Mapa de Outro Veículo")
            st.info(
                "Use esta opção para copiar configurações de mapa de outro veículo como template"
            )

            # Listar veículos disponíveis (exceto o atual)
            all_vehicles = load_vehicles()
            other_vehicles = [v for v in all_vehicles if v["id"] != selected_vehicle_id]

            if other_vehicles:
                source_vehicle = st.selectbox(
                    "Selecione o veículo de origem:",
                    options=other_vehicles,
                    format_func=lambda v: f"{v.get('nickname', v['name'])} ({v['name']})",
                    key=f"source_vehicle_{session_key}",
                )

                if source_vehicle:
                    # Verificar se existe mapa para este tipo no veículo origem
                    source_data = load_map_data(
                        source_vehicle["id"], selected_map_type, selected_bank
                    )

                    if source_data:
                        st.success(
                            f"Mapa encontrado no veículo {source_vehicle.get('nickname', source_vehicle['name'])}"
                        )

                        # Preview dos dados
                        with st.expander("Visualizar dados do mapa origem"):
                            preview_values = (
                                source_data["map_values"][:10]
                                if len(source_data["map_values"]) > 10
                                else source_data["map_values"]
                            )
                            st.json(
                                {
                                    "primeiros_valores": preview_values,
                                    "total_valores": len(source_data["map_values"]),
                                }
                            )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(
                                "Copiar Mapa",
                                type="primary",
                                key=f"copy_map_{session_key}",
                                use_container_width=True,
                            ):
                                if copy_map_from_vehicle(
                                    source_vehicle["id"],
                                    selected_vehicle_id,
                                    selected_map_type,
                                    selected_bank,
                                ):
                                    # Atualizar session state
                                    st.session_state[session_key] = {
                                        "axis_values": source_data["axis_values"],
                                        "map_values": source_data["map_values"],
                                        "axis_enabled": source_data.get("axis_enabled"),
                                    }
                                    st.success(f"Mapa copiado com sucesso!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Erro ao copiar mapa")

                        with col2:
                            st.warning("Esta ação irá substituir os valores atuais")
                    else:
                        st.warning(
                            f"Nenhum mapa '{map_info['name']}' encontrado neste veículo"
                        )
            else:
                st.info("Nenhum outro veículo disponível para copiar mapas")

    with section_tabs[3]:  # Exportar Dados
        st.subheader("Exportar Dados")

        if session_key in st.session_state:
            current_data = st.session_state[session_key]

            col_export1, col_export2 = st.columns(2)

            with col_export1:
                # Exportar JSON
                export_data = {
                    "vehicle_id": selected_vehicle_id,
                    "map_type": selected_map_type,
                    "bank_id": selected_bank,
                    "map_info": map_info,
                    "axis_values": current_data["axis_values"],
                    "map_values": current_data["map_values"],
                    "axis_enabled": current_data.get("axis_enabled"),
                    "exported_at": pd.Timestamp.now().isoformat(),
                }

                st.download_button(
                    "Exportar JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"mapa_2d_{selected_map_type}_{selected_vehicle_id}.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"export_json_{session_key}",
                )

            with col_export2:
                # Exportar CSV - usar apenas o tamanho real dos dados habilitados
                # Garantir que ambos os arrays tenham o mesmo tamanho
                axis_values = current_data.get("axis_values", [])
                map_values = current_data.get("map_values", [])

                # Usar o menor tamanho para evitar erro
                num_values = min(len(axis_values), len(map_values))

                if num_values > 0:
                    export_df = pd.DataFrame(
                        {
                            "posicao": range(1, num_values + 1),
                            "axis_x": axis_values[:num_values],
                            "value": map_values[:num_values],
                        }
                    )
                else:
                    # DataFrame vazio se não houver dados
                    export_df = pd.DataFrame({"posicao": [], "axis_x": [], "value": []})

                st.download_button(
                    "Exportar CSV",
                    data=export_df.to_csv(index=False),
                    file_name=f"mapa_2d_{selected_map_type}_{selected_vehicle_id}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key=f"export_csv_{session_key}",
                )

        else:
            st.info("Configure o mapa na aba 'Editar' para exportar")

# Rodapé com informações
st.markdown("---")
st.caption("Sistema FuelTune - Mapas de Injeção 2D | Versão 1.0")
