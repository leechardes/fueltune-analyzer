"""
Validações para mapas de combustível 3D.
Verifica integridade dos dados, valores válidos e consistência.
"""

import logging
from typing import Any, Dict, List, Tuple

import numpy as np

from .models import Map3DData, MapConfig

logger = logging.getLogger(__name__)


class MapValidator:
    """Validador de mapas de combustível 3D."""

    # Limites de segurança por tipo de mapa
    SAFETY_LIMITS = {
        "main_fuel_3d_map": {"min": 0.1, "max": 100.0, "unit": "ms"},
        "lambda_target_3d_map": {"min": 0.6, "max": 1.5, "unit": "λ"},
        "ignition_3d_map": {"min": -20.0, "max": 50.0, "unit": "°"},
        "afr_target_3d_map": {"min": 8.0, "max": 20.0, "unit": "AFR"},
    }

    @staticmethod
    def validate_3d_map_values(
        values_matrix: np.ndarray, map_type: str, strict: bool = False
    ) -> Tuple[bool, List[str]]:
        """Valida valores da matriz 3D contra limites de segurança."""
        errors = []
        warnings = []

        try:
            # Verificar se matriz não está vazia
            if values_matrix is None or values_matrix.size == 0:
                errors.append("Matriz de valores está vazia")
                return False, errors

            # Verificar dimensões
            if len(values_matrix.shape) != 2:
                errors.append("Matriz deve ser bidimensional")
                return False, errors

            # Verificar se é quadrada
            if values_matrix.shape[0] != values_matrix.shape[1]:
                warnings.append(f"Matriz não é quadrada: {values_matrix.shape}")
                if strict:
                    errors.append("Matriz deve ser quadrada no modo estrito")

            # Verificar limites por tipo
            limits = MapValidator.SAFETY_LIMITS.get(map_type)
            if limits:
                min_val = limits["min"]
                max_val = limits["max"]
                unit = limits["unit"]

                # Valores abaixo do mínimo
                below_min = values_matrix < min_val
                if np.any(below_min):
                    count = np.sum(below_min)
                    errors.append(f"{count} valores abaixo do limite mínimo ({min_val} {unit})")

                # Valores acima do máximo
                above_max = values_matrix > max_val
                if np.any(above_max):
                    count = np.sum(above_max)
                    "errors" if strict else "warnings"
                    msg = f"{count} valores acima do limite máximo ({max_val} {unit})"

                    if strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)

            # Verificar valores NaN ou infinitos
            nan_count = np.sum(np.isnan(values_matrix))
            inf_count = np.sum(np.isinf(values_matrix))

            if nan_count > 0:
                errors.append(f"{nan_count} valores NaN encontrados")

            if inf_count > 0:
                errors.append(f"{inf_count} valores infinitos encontrados")

            # Verificar variação extrema (possível erro de dados)
            if values_matrix.size > 1:
                std_dev = np.std(values_matrix)
                mean_val = np.mean(values_matrix)
                coefficient_variation = std_dev / mean_val if mean_val != 0 else 0

                if coefficient_variation > 2.0:  # CV > 200%
                    warnings.append(
                        f"Variação muito alta nos dados (CV: {coefficient_variation:.1%})"
                    )

            # Log das validações
            if warnings:
                for warning in warnings:
                    logger.warning(f"Validação {map_type}: {warning}")

            if errors:
                for error in errors:
                    logger.error(f"Validação {map_type}: {error}")
                return False, errors

            return True, warnings

        except Exception as e:
            logger.error(f"Erro na validação: {e}")
            return False, [f"Erro interno na validação: {e}"]

    @staticmethod
    def validate_axis_values(
        axis_values: List[float], axis_type: str, expected_size: int
    ) -> Tuple[bool, List[str]]:
        """Valida valores de um eixo (RPM ou MAP)."""
        errors = []

        try:
            # Verificar tamanho
            if len(axis_values) != expected_size:
                errors.append(
                    f"Eixo {axis_type} tem {len(axis_values)} valores, esperado {expected_size}"
                )

            # Verificar se está em ordem crescente
            if not all(axis_values[i] <= axis_values[i + 1] for i in range(len(axis_values) - 1)):
                errors.append(f"Eixo {axis_type} não está em ordem crescente")

            # Verificar limites específicos do tipo
            if axis_type.upper() == "RPM":
                if any(v < 0 for v in axis_values):
                    errors.append("Valores de RPM não podem ser negativos")
                if any(v > 15000 for v in axis_values):
                    errors.append("Valores de RPM muito altos (>15000)")

            elif axis_type.upper() == "MAP":
                # MAP pode ser negativo (vácuo) até positivo (boost)
                if any(v < -1.0 for v in axis_values):
                    errors.append("Valores de MAP muito baixos (<-1.0 bar)")
                if any(v > 5.0 for v in axis_values):
                    errors.append("Valores de MAP muito altos (>5.0 bar)")

            # Verificar valores duplicados
            if len(set(axis_values)) != len(axis_values):
                errors.append(f"Eixo {axis_type} tem valores duplicados")

            return len(errors) == 0, errors

        except Exception as e:
            return False, [f"Erro na validação do eixo {axis_type}: {e}"]

    @staticmethod
    def validate_enabled_matrix(
        enabled_matrix: List[List[bool]], expected_size: int
    ) -> Tuple[bool, List[str]]:
        """Valida matriz de enable/disable."""
        errors = []

        try:
            # Verificar dimensões
            if len(enabled_matrix) != expected_size:
                errors.append(
                    f"Matriz enabled tem {len(enabled_matrix)} linhas, esperado {expected_size}"
                )

            for i, row in enumerate(enabled_matrix):
                if len(row) != expected_size:
                    errors.append(
                        f"Linha {i} da matriz enabled tem {len(row)} colunas, esperado {expected_size}"
                    )

            # Verificar se há pelo menos algumas células habilitadas
            total_enabled = sum(sum(row) for row in enabled_matrix)
            if total_enabled == 0:
                errors.append("Nenhuma célula está habilitada na matriz")

            # Aviso se muitas células estão desabilitadas
            total_cells = expected_size * expected_size
            if total_enabled < total_cells * 0.25:  # Menos de 25% habilitado
                logger.warning(
                    f"Apenas {total_enabled}/{total_cells} células habilitadas ({total_enabled/total_cells:.1%})"
                )

            return len(errors) == 0, errors

        except Exception as e:
            return False, [f"Erro na validação da matriz enabled: {e}"]

    @staticmethod
    def validate_map_config(config: MapConfig) -> Tuple[bool, List[str]]:
        """Valida configuração do mapa."""
        errors = []

        try:
            # Campos obrigatórios
            if not config.name:
                errors.append("Nome do mapa é obrigatório")

            if config.grid_size <= 0:
                errors.append("Tamanho do grid deve ser positivo")

            if config.grid_size > 64:
                errors.append("Tamanho do grid muito grande (máximo 64)")

            if not config.x_axis_type:
                errors.append("Tipo do eixo X é obrigatório")

            if not config.y_axis_type:
                errors.append("Tipo do eixo Y é obrigatório")

            # Verificar limites
            if config.min_value >= config.max_value:
                errors.append("Valor mínimo deve ser menor que valor máximo")

            # Verificar eixos padrão se fornecidos
            if config.default_rpm_values:
                valid, axis_errors = MapValidator.validate_axis_values(
                    config.default_rpm_values, "RPM", config.grid_size
                )
                errors.extend(axis_errors)

            if config.default_map_values:
                valid, axis_errors = MapValidator.validate_axis_values(
                    config.default_map_values, "MAP", config.grid_size
                )
                errors.extend(axis_errors)

            return len(errors) == 0, errors

        except Exception as e:
            return False, [f"Erro na validação da configuração: {e}"]

    @staticmethod
    def validate_complete_map(map_data: Map3DData) -> Tuple[bool, List[str]]:
        """Validação completa de um mapa 3D."""
        all_errors = []

        try:
            # Validar configuração
            config_valid, config_errors = MapValidator.validate_map_config(map_data.config)
            all_errors.extend(config_errors)

            # Validar eixos
            rpm_valid, rpm_errors = MapValidator.validate_axis_values(
                map_data.rpm_values, "RPM", map_data.grid_size
            )
            all_errors.extend(rpm_errors)

            map_valid, map_errors = MapValidator.validate_axis_values(
                map_data.map_values, "MAP", map_data.grid_size
            )
            all_errors.extend(map_errors)

            # Validar matriz de dados
            values_valid, values_errors = MapValidator.validate_3d_map_values(
                map_data.numpy_data_matrix, map_data.map_type
            )
            all_errors.extend(values_errors)

            # Validar matriz enabled
            enabled_valid, enabled_errors = MapValidator.validate_enabled_matrix(
                map_data.enabled_matrix, map_data.grid_size
            )
            all_errors.extend(enabled_errors)

            # Validar consistência entre matrizes
            if (
                len(map_data.data_matrix) != map_data.grid_size
                or len(map_data.enabled_matrix) != map_data.grid_size
            ):
                all_errors.append("Inconsistência no tamanho das matrizes")

            return len(all_errors) == 0, all_errors

        except Exception as e:
            return False, [f"Erro na validação completa: {e}"]

    @staticmethod
    def suggest_corrections(values_matrix: np.ndarray, map_type: str) -> Dict[str, Any]:
        """Sugere correções para problemas encontrados na matriz."""
        suggestions = {"auto_fix_available": False, "corrections": [], "warnings": []}

        try:
            limits = MapValidator.SAFETY_LIMITS.get(map_type)
            if not limits:
                return suggestions

            min_val = limits["min"]
            max_val = limits["max"]

            # Sugerir clipping de valores extremos
            below_min = np.sum(values_matrix < min_val)
            above_max = np.sum(values_matrix > max_val)

            if below_min > 0:
                suggestions["corrections"].append(
                    {
                        "type": "clip_minimum",
                        "description": f"Ajustar {below_min} valores para o mínimo ({min_val})",
                        "count": below_min,
                    }
                )
                suggestions["auto_fix_available"] = True

            if above_max > 0:
                suggestions["corrections"].append(
                    {
                        "type": "clip_maximum",
                        "description": f"Ajustar {above_max} valores para o máximo ({max_val})",
                        "count": above_max,
                    }
                )
                suggestions["auto_fix_available"] = True

            # Sugerir interpolação para valores NaN
            nan_count = np.sum(np.isnan(values_matrix))
            if nan_count > 0:
                suggestions["corrections"].append(
                    {
                        "type": "interpolate_nan",
                        "description": f"Interpolar {nan_count} valores NaN",
                        "count": nan_count,
                    }
                )
                suggestions["auto_fix_available"] = True

            return suggestions

        except Exception as e:
            logger.error(f"Erro ao gerar sugestões: {e}")
            return suggestions


# Funções de conveniência para manter compatibilidade
def validate_3d_map_values(*args, **kwargs) -> Tuple[bool, List[str]]:
    """Compatibilidade: valida valores da matriz 3D."""
    return MapValidator.validate_3d_map_values(*args, **kwargs)
