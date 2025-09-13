"""
Utilitários para cálculos relacionados a bancadas de injeção.
Inclui cálculos de vazão, duty cycle, balanceamento e recomendações.

Padrão: A04-STREAMLIT-PROFESSIONAL (ZERO emojis, Material Icons)
"""

import math
from typing import Dict, List, Tuple

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


def calculate_total_flow(flow_per_injector: float, injector_count: int) -> float:
    """
    Calcula vazão total da bancada.

    Args:
        flow_per_injector: Vazão por bico em lb/h
        injector_count: Quantidade de bicos

    Returns:
        Vazão total em lb/h
    """
    if flow_per_injector < 0 or injector_count < 0:
        return 0.0

    return flow_per_injector * injector_count


def calculate_duty_cycle(
    injection_time_ms: float, rpm: int, cylinders: int = 4, injection_mode: str = "sequencial"
) -> float:
    """
    Calcula duty cycle dos injetores.

    Args:
        injection_time_ms: Tempo de injeção em ms
        rpm: RPM do motor
        cylinders: Número de cilindros
        injection_mode: Modo de injeção (sequencial, semissequencial, multiponto)

    Returns:
        Duty cycle em % (0-100)
    """
    if rpm <= 0 or injection_time_ms < 0:
        return 0.0

    # Tempo disponível por ciclo (4 tempos = 2 voltas do virabrequim)
    cycle_time_ms = (60.0 / rpm) * 1000.0 / 2.0

    # Ajustar tempo disponível baseado no modo de injeção
    if injection_mode == "sequencial":
        # Injeção sequencial: cada bico injeta uma vez por ciclo
        available_time_ms = cycle_time_ms
    elif injection_mode == "semissequencial":
        # Semissequencial: pares de bicos, então duas injeções por ciclo
        available_time_ms = cycle_time_ms / 2.0
    else:  # multiponto
        # Multiponto: todos os bicos injetam simultaneamente
        available_time_ms = cycle_time_ms / cylinders

    # Calcular duty cycle
    duty_cycle = (injection_time_ms / available_time_ms) * 100.0

    return min(duty_cycle, 100.0)  # Cap em 100%


def validate_injector_flow(flow_lb_h: float, max_duty: float = 85.0) -> Tuple[bool, str]:
    """
    Valida se a vazão do injetor é adequada.

    Args:
        flow_lb_h: Vazão em lb/h
        max_duty: Duty cycle máximo recomendado

    Returns:
        Tuple com (válido, mensagem)
    """
    if flow_lb_h < 10:
        return False, "Vazão muito baixa (< 10 lb/h)"

    if flow_lb_h > 2000:
        return False, "Vazão muito alta (> 2000 lb/h)"

    if 10 <= flow_lb_h <= 50:
        return True, "Vazão adequada para motores pequenos"
    elif 50 <= flow_lb_h <= 200:
        return True, "Vazão adequada para motores médios"
    elif 200 <= flow_lb_h <= 800:
        return True, "Vazão adequada para motores grandes/turbo"
    elif 800 <= flow_lb_h <= 2000:
        return True, "Vazão adequada para motores de alta performance"

    return True, "Vazão adequada"


def calculate_fuel_pressure_compensation(base_pressure: float, actual_pressure: float) -> float:
    """
    Calcula fator de compensação por pressão de combustível.

    Args:
        base_pressure: Pressão base de calibração (bar)
        actual_pressure: Pressão atual do sistema (bar)

    Returns:
        Fator de compensação (multiplicador)
    """
    if base_pressure <= 0 or actual_pressure <= 0:
        return 1.0

    # A vazão varia com a raiz quadrada da pressão
    compensation_factor = math.sqrt(actual_pressure / base_pressure)

    # Limitar fator entre 0.5 e 2.0 para segurança
    return max(0.5, min(2.0, compensation_factor))


def estimate_power_per_bank(
    total_flow_lb_h: float, bsfc: float = 0.5, efficiency: float = 0.85
) -> float:
    """
    Estima potência suportada por bancada.

    Args:
        total_flow_lb_h: Vazão total da bancada em lb/h
        bsfc: Consumo específico (lb/hp/h) - padrão 0.5 para motores turbo
        efficiency: Eficiência do sistema (0-1)

    Returns:
        Potência estimada em HP
    """
    if total_flow_lb_h <= 0 or bsfc <= 0:
        return 0.0

    # Potência = Vazão / BSFC * Eficiência
    estimated_power = (total_flow_lb_h / bsfc) * efficiency

    return max(0.0, estimated_power)


def check_bank_balance(
    bank_a_flow: float, bank_b_flow: float, tolerance: float = 0.15
) -> Tuple[bool, str]:
    """
    Verifica balanceamento entre bancadas.

    Args:
        bank_a_flow: Vazão bancada A
        bank_b_flow: Vazão bancada B
        tolerance: Tolerância aceita (0.15 = 15%)

    Returns:
        Tuple com (balanceado, mensagem)
    """
    if bank_b_flow == 0:
        return True, "Apenas bancada A ativa"

    if bank_a_flow == 0:
        return False, "Bancada A inativa mas B ativa"

    # Calcular diferença percentual
    max_flow = max(bank_a_flow, bank_b_flow)
    difference = abs(bank_a_flow - bank_b_flow) / max_flow

    if difference <= tolerance:
        return True, f"Bancadas balanceadas (diferença: {difference*100:.1f}%)"
    else:
        status = "maior" if bank_a_flow > bank_b_flow else "menor"
        return False, f"Bancada A {status} que B (diferença: {difference*100:.1f}%)"


def recommend_injector_size(
    target_power_hp: float,
    cylinders: int = 4,
    max_duty: float = 85.0,
    bsfc: float = 0.5,
    num_banks: int = 1,
) -> Dict[str, float]:
    """
    Recomenda tamanho de injetor para potência alvo.

    Args:
        target_power_hp: Potência desejada em HP
        cylinders: Número de cilindros
        max_duty: Duty cycle máximo permitido
        bsfc: Consumo específico (lb/hp/h)
        num_banks: Número de bancadas (1 ou 2)

    Returns:
        Dict com recomendações
    """
    if target_power_hp <= 0:
        return {"error": "Potência deve ser maior que zero"}

    # Fluxo necessário total
    total_flow_needed = target_power_hp * bsfc

    # Ajustar para duty cycle máximo (margem de segurança)
    total_flow_adjusted = total_flow_needed / (max_duty / 100.0)

    # Dividir entre bancadas
    flow_per_bank = total_flow_adjusted / num_banks

    # Fluxo por injetor (assumindo injetores iguais em cada bancada)
    injectors_per_bank = cylinders // num_banks
    if cylinders % num_banks != 0:
        injectors_per_bank = cylinders  # Bancada principal leva todos se não divide igual

    flow_per_injector = flow_per_bank / injectors_per_bank

    # Tamanhos comerciais comuns (lb/h)
    common_sizes = [
        19,
        24,
        30,
        36,
        42,
        47,
        55,
        60,
        72,
        80,
        96,
        110,
        120,
        160,
        200,
        250,
        300,
        370,
        440,
        550,
        650,
        750,
        850,
        1000,
        1200,
        1600,
        2000,
    ]

    # Encontrar tamanho mais próximo (maior que necessário para margem)
    recommended_size = min(
        [size for size in common_sizes if size >= flow_per_injector], default=common_sizes[-1]
    )

    # Calcular valores reais com o tamanho recomendado
    actual_flow_per_bank = recommended_size * injectors_per_bank
    actual_total_flow = actual_flow_per_bank * num_banks
    actual_max_power = (actual_total_flow * (max_duty / 100.0)) / bsfc

    return {
        "target_power_hp": target_power_hp,
        "total_flow_needed_lb_h": total_flow_needed,
        "total_flow_adjusted_lb_h": total_flow_adjusted,
        "flow_per_injector_needed_lb_h": flow_per_injector,
        "recommended_injector_size_lb_h": recommended_size,
        "injectors_per_bank": injectors_per_bank,
        "actual_flow_per_bank_lb_h": actual_flow_per_bank,
        "actual_total_flow_lb_h": actual_total_flow,
        "actual_max_power_hp": actual_max_power,
        "safety_margin_percent": ((actual_max_power - target_power_hp) / target_power_hp) * 100,
        "num_banks": num_banks,
        "max_duty_percent": max_duty,
    }


def calculate_injector_dead_time_compensation(
    voltage: float, injector_type: str = "standard"
) -> float:
    """
    Calcula compensação de dead time baseada na tensão.

    Args:
        voltage: Tensão da bateria em V
        injector_type: Tipo do injetor (standard, low_impedance, high_impedance)

    Returns:
        Compensação de dead time em ms
    """
    if voltage < 6.0 or voltage > 18.0:
        return 0.0

    # Valores base por tipo de injetor
    base_dead_times = {
        "standard": 1.0,  # ms a 12V
        "low_impedance": 0.8,  # ms a 12V - resposta mais rápida
        "high_impedance": 1.2,  # ms a 12V - resposta mais lenta
    }

    base_dead_time = base_dead_times.get(injector_type, 1.0)
    reference_voltage = 12.0

    # Compensação varia inversamente com a tensão
    # Mais tensão = abertura mais rápida = menos dead time
    voltage_factor = reference_voltage / voltage

    compensated_dead_time = base_dead_time * voltage_factor

    # Limitar entre 0.3ms e 3.0ms
    return max(0.3, min(3.0, compensated_dead_time))


def validate_bank_configuration(bank_config: Dict[str, any]) -> List[Dict[str, str]]:
    """
    Valida configuração de uma bancada.

    Args:
        bank_config: Dicionário com configuração da bancada

    Returns:
        Lista de validações com status e mensagens
    """
    validations = []

    # Validar se bancada está habilitada
    if not bank_config.get("enabled", False):
        return [{"status": "INFO", "message": "Bancada desabilitada"}]

    # Validar modo
    valid_modes = ["multiponto", "semissequencial", "sequencial"]
    mode = bank_config.get("mode", "")
    if mode not in valid_modes:
        validations.append(
            {
                "status": "ERROR",
                "message": f"Modo inválido: {mode}. Deve ser: {', '.join(valid_modes)}",
            }
        )
    else:
        validations.append({"status": "OK", "message": f"Modo válido: {mode}"})

    # Validar saídas
    outputs = bank_config.get("outputs", [])
    if not outputs:
        validations.append({"status": "ERROR", "message": "Nenhuma saída configurada"})
    elif not all(1 <= output <= 8 for output in outputs):
        validations.append({"status": "ERROR", "message": "Saídas devem estar entre 1 e 8"})
    else:
        validations.append({"status": "OK", "message": f"{len(outputs)} saídas configuradas"})

    # Validar vazão por injetor
    flow = bank_config.get("injector_flow", 0)
    valid, message = validate_injector_flow(flow)
    validations.append(
        {"status": "OK" if valid else "WARNING", "message": f"Vazão por bico: {message}"}
    )

    # Validar quantidade de injetores
    count = bank_config.get("injector_count", 0)
    if count <= 0:
        validations.append({"status": "ERROR", "message": "Quantidade de injetores inválida"})
    elif count > 8:
        validations.append({"status": "WARNING", "message": "Muitos injetores (>8)"})
    else:
        validations.append({"status": "OK", "message": f"{count} injetores configurados"})

    # Validar dead time
    dead_time = bank_config.get("dead_time", 0)
    if dead_time < 0.1 or dead_time > 5.0:
        validations.append(
            {"status": "WARNING", "message": f"Dead time fora da faixa normal: {dead_time}ms"}
        )
    else:
        validations.append({"status": "OK", "message": f"Dead time adequado: {dead_time}ms"})

    # Calcular e validar vazão total
    total_flow = calculate_total_flow(flow, count)
    if total_flow > 0:
        estimated_power = estimate_power_per_bank(total_flow)
        validations.append(
            {
                "status": "INFO",
                "message": f"Vazão total: {total_flow:.0f} lb/h (~{estimated_power:.0f} HP)",
            }
        )

    return validations


def compare_bank_configurations(
    bank_a: Dict[str, any], bank_b: Dict[str, any]
) -> List[Dict[str, str]]:
    """
    Compara configurações entre bancadas A e B.

    Args:
        bank_a: Configuração da bancada A
        bank_b: Configuração da bancada B

    Returns:
        Lista de comparações com status e mensagens
    """
    comparisons = []

    if not bank_a.get("enabled") and not bank_b.get("enabled"):
        return [{"status": "ERROR", "message": "Nenhuma bancada habilitada"}]

    if not bank_b.get("enabled"):
        return [{"status": "INFO", "message": "Apenas bancada A ativa"}]

    # Comparar vazões
    flow_a = calculate_total_flow(bank_a.get("injector_flow", 0), bank_a.get("injector_count", 0))
    flow_b = calculate_total_flow(bank_b.get("injector_flow", 0), bank_b.get("injector_count", 0))

    balanced, balance_msg = check_bank_balance(flow_a, flow_b)
    comparisons.append(
        {"status": "OK" if balanced else "WARNING", "message": f"Balanceamento: {balance_msg}"}
    )

    # Comparar modos
    if bank_a.get("mode") == bank_b.get("mode"):
        comparisons.append({"status": "OK", "message": f"Modos idênticos: {bank_a.get('mode')}"})
    else:
        comparisons.append(
            {
                "status": "INFO",
                "message": f"Modos diferentes: A={bank_a.get('mode')}, B={bank_b.get('mode')}",
            }
        )

    # Verificar conflitos de saídas
    outputs_a = set(bank_a.get("outputs", []))
    outputs_b = set(bank_b.get("outputs", []))
    conflicts = outputs_a.intersection(outputs_b)

    if conflicts:
        comparisons.append({"status": "ERROR", "message": f"Conflitos de saída: {list(conflicts)}"})
    else:
        comparisons.append({"status": "OK", "message": "Nenhum conflito de saída"})

    # Comparar dead times
    dead_time_diff = abs(bank_a.get("dead_time", 0) - bank_b.get("dead_time", 0))
    if dead_time_diff > 0.5:  # Diferença > 0.5ms
        comparisons.append(
            {"status": "WARNING", "message": f"Dead times muito diferentes: {dead_time_diff:.2f}ms"}
        )
    else:
        comparisons.append(
            {"status": "OK", "message": f"Dead times similares (diff: {dead_time_diff:.2f}ms)"}
        )

    # Potência total estimada
    total_power = estimate_power_per_bank(flow_a) + estimate_power_per_bank(flow_b)
    comparisons.append(
        {"status": "INFO", "message": f"Potência total estimada: {total_power:.0f} HP"}
    )

    return comparisons
