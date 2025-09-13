"""
Utilitários gerais para mapas de combustível 3D.
Funções auxiliares para formatação, conversão e manipulação de dados.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def format_value_3_decimals(value: float) -> str:
    """Formata valor com 3 casas decimais para todos os mapas."""
    try:
        return f"{value:.3f}"
    except (ValueError, TypeError):
        return "0.000"


def format_value_by_type(value: float, map_type: str) -> str:
    """Formata valor baseado no tipo de mapa (mantido para compatibilidade)."""
    # Agora todos usam 3 casas decimais por padronização
    return format_value_3_decimals(value)


def get_active_axis_values(axis_values: List[float], enabled: List[bool]) -> List[float]:
    """Retorna apenas os valores ativos do eixo."""
    try:
        return [axis_values[i] for i in range(len(axis_values)) if i < len(enabled) and enabled[i]]
    except (IndexError, TypeError):
        logger.warning("Erro ao filtrar valores ativos do eixo")
        return axis_values


def convert_matrix_to_numpy(matrix: List[List[float]]) -> np.ndarray:
    """Converte matriz Python para numpy array com validação."""
    try:
        return np.array(matrix, dtype=float)
    except (ValueError, TypeError) as e:
        logger.error(f"Erro na conversão para numpy: {e}")
        # Retornar matriz vazia com dimensões padrão
        return np.zeros((32, 32))


def convert_numpy_to_matrix(array: np.ndarray) -> List[List[float]]:
    """Converte numpy array para matriz Python."""
    try:
        return array.tolist()
    except (ValueError, AttributeError) as e:
        logger.error(f"Erro na conversão de numpy: {e}")
        return [[0.0] * 32 for _ in range(32)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divisão segura com fallback."""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return default


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Limita valor entre mínimo e máximo."""
    try:
        return max(min_val, min(max_val, value))
    except (TypeError, ValueError):
        return min_val


def interpolate_value(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Interpolação linear entre dois pontos."""
    try:
        if x2 == x1:
            return y1
        return y1 + (x - x1) * (y2 - y1) / (x2 - x1)
    except (ZeroDivisionError, TypeError):
        return y1


def calculate_matrix_statistics(matrix: np.ndarray) -> Dict[str, float]:
    """Calcula estatísticas básicas da matriz."""
    try:
        if matrix.size == 0:
            return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}

        return {
            "min": float(np.min(matrix)),
            "max": float(np.max(matrix)),
            "mean": float(np.mean(matrix)),
            "std": float(np.std(matrix)),
            "median": float(np.median(matrix)),
            "non_zero_count": int(np.count_nonzero(matrix)),
            "total_cells": int(matrix.size),
        }
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}


def find_matrix_peaks(
    matrix: np.ndarray, threshold_percentile: int = 90
) -> List[Tuple[int, int, float]]:
    """Encontra picos na matriz (valores acima do percentil especificado)."""
    try:
        if matrix.size == 0:
            return []

        threshold = np.percentile(matrix, threshold_percentile)
        peaks = []

        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if matrix[i, j] >= threshold:
                    peaks.append((i, j, float(matrix[i, j])))

        # Ordenar por valor decrescente
        return sorted(peaks, key=lambda x: x[2], reverse=True)

    except Exception as e:
        logger.error(f"Erro ao encontrar picos: {e}")
        return []


def smooth_matrix(matrix: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Aplica suavização na matriz usando kernel de média móvel."""
    try:
        if kernel_size < 3 or kernel_size % 2 == 0:
            kernel_size = 3  # Garantir que é ímpar e >= 3

        rows, cols = matrix.shape
        result = matrix.copy()
        half_kernel = kernel_size // 2

        for i in range(half_kernel, rows - half_kernel):
            for j in range(half_kernel, cols - half_kernel):
                # Extrair janela
                window = matrix[
                    i - half_kernel : i + half_kernel + 1, j - half_kernel : j + half_kernel + 1
                ]
                result[i, j] = np.mean(window)

        return result

    except Exception as e:
        logger.error(f"Erro na suavização: {e}")
        return matrix


def validate_axis_consistency(axis1: List[float], axis2: List[float]) -> Tuple[bool, str]:
    """Valida consistência entre dois eixos."""
    try:
        if len(axis1) != len(axis2):
            return False, f"Tamanhos diferentes: {len(axis1)} vs {len(axis2)}"

        # Verificar se ambos estão em ordem crescente
        axis1_sorted = all(axis1[i] <= axis1[i + 1] for i in range(len(axis1) - 1))
        axis2_sorted = all(axis2[i] <= axis2[i + 1] for i in range(len(axis2) - 1))

        if not axis1_sorted:
            return False, "Primeiro eixo não está ordenado"
        if not axis2_sorted:
            return False, "Segundo eixo não está ordenado"

        return True, "Eixos consistentes"

    except Exception as e:
        return False, f"Erro na validação: {e}"


def generate_linear_axis(start: float, end: float, steps: int) -> List[float]:
    """Gera eixo linear com espaçamento uniforme."""
    try:
        if steps <= 1:
            return [start]

        step_size = (end - start) / (steps - 1)
        return [start + i * step_size for i in range(steps)]

    except Exception as e:
        logger.error(f"Erro ao gerar eixo linear: {e}")
        return [0.0] * max(1, steps)


def generate_logarithmic_axis(start: float, end: float, steps: int) -> List[float]:
    """Gera eixo logarítmico."""
    try:
        if start <= 0 or end <= 0 or steps <= 1:
            return generate_linear_axis(start, end, steps)

        log_start = np.log(start)
        log_end = np.log(end)
        log_step = (log_end - log_start) / (steps - 1)

        return [np.exp(log_start + i * log_step) for i in range(steps)]

    except Exception as e:
        logger.error(f"Erro ao gerar eixo logarítmico: {e}")
        return generate_linear_axis(start, end, steps)


def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """Converte entre diferentes unidades."""
    try:
        # Conversões de pressão
        if from_unit == "bar" and to_unit == "kPa":
            return value * 100.0
        elif from_unit == "kPa" and to_unit == "bar":
            return value / 100.0
        elif from_unit == "psi" and to_unit == "bar":
            return value * 0.0689476
        elif from_unit == "bar" and to_unit == "psi":
            return value / 0.0689476

        # Conversões de vazão
        elif from_unit == "lbs/h" and to_unit == "cc/min":
            return value * 10.5  # Aproximação para gasolina
        elif from_unit == "cc/min" and to_unit == "lbs/h":
            return value / 10.5

        # Se não houver conversão, retornar valor original
        else:
            return value

    except Exception as e:
        logger.error(f"Erro na conversão de unidades: {e}")
        return value


def create_color_scale(values: np.ndarray, colormap: str = "viridis") -> List[str]:
    """Cria escala de cores para visualização."""
    try:
        import matplotlib.cm as cm
        import matplotlib.colors as colors

        # Normalizar valores para 0-1
        norm = colors.Normalize(vmin=np.min(values), vmax=np.max(values))
        cmap = cm.get_cmap(colormap)

        # Gerar cores
        color_scale = []
        flat_values = values.flatten()

        for value in flat_values:
            rgba = cmap(norm(value))
            # Converter para hex
            hex_color = colors.rgb2hex(rgba[:3])
            color_scale.append(hex_color)

        return color_scale

    except ImportError:
        # Fallback sem matplotlib - usar cores básicas
        flat_values = values.flatten()
        min_val, max_val = np.min(flat_values), np.max(flat_values)

        color_scale = []
        for value in flat_values:
            # Normalizar para 0-1
            normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0

            # Mapear para cor (azul -> vermelho)
            red = int(255 * normalized)
            blue = int(255 * (1 - normalized))
            green = 128

            hex_color = f"#{red:02x}{green:02x}{blue:02x}"
            color_scale.append(hex_color)

        return color_scale

    except Exception as e:
        logger.error(f"Erro ao criar escala de cores: {e}")
        return ["#808080"] * values.size


def calculate_fuel_efficiency_rating(matrix: np.ndarray, reference_matrix: np.ndarray) -> float:
    """Calcula rating de eficiência de combustível comparando com referência."""
    try:
        if matrix.shape != reference_matrix.shape:
            return 0.0

        # Calcular diferença percentual média
        diff_percent = np.abs((matrix - reference_matrix) / reference_matrix) * 100

        # Rating baseado na proximidade da referência (0-100)
        avg_diff = np.mean(diff_percent)
        rating = max(0.0, 100.0 - avg_diff)

        return float(rating)

    except Exception as e:
        logger.error(f"Erro ao calcular rating: {e}")
        return 0.0


def export_matrix_to_csv(
    matrix: np.ndarray,
    filename: str,
    row_labels: Optional[List[str]] = None,
    col_labels: Optional[List[str]] = None,
) -> bool:
    """Exporta matriz para arquivo CSV."""
    try:
        import pandas as pd

        # Criar DataFrame
        df = pd.DataFrame(matrix)

        if row_labels:
            df.index = row_labels[: len(df)]
        if col_labels:
            df.columns = col_labels[: len(df.columns)]

        # Salvar CSV
        df.to_csv(filename, float_format="%.3f")
        logger.info(f"Matriz exportada para {filename}")
        return True

    except ImportError:
        # Fallback sem pandas
        with open(filename, "w") as f:
            for i, row in enumerate(matrix):
                row_str = ",".join(f"{val:.3f}" for val in row)
                f.write(row_str + "\n")
        return True

    except Exception as e:
        logger.error(f"Erro ao exportar CSV: {e}")
        return False
