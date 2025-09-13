"""
Utilitários para interpolação de mapas de injeção.
Implementa as regras específicas da documentação de interpolação.

Padrão: A04-STREAMLIT-PROFESSIONAL (ZERO emojis, Material Icons)
"""

from typing import Dict, List, Tuple

import numpy as np
from scipy.interpolate import griddata, interp1d

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MapInterpolator:
    """Classe para interpolação de dados de mapas seguindo especificação."""

    def linear_interpolation_2d(
        self, x_values: List[float], y_values: List[float], target_x: float
    ) -> float:
        """
        Interpolação linear 2D seguindo regras da especificação.

        Regras:
        - Entre pontos existentes: Interpolação linear
        - Antes do primeiro ponto: Repete primeiro valor
        - Após o último ponto: Repete último valor

        Args:
            x_values: Valores do eixo X (ordenados)
            y_values: Valores correspondentes do eixo Y
            target_x: Valor X para interpolar

        Returns:
            Valor Y interpolado
        """
        if not x_values or not y_values or len(x_values) != len(y_values):
            raise ValueError("Listas de valores inválidas ou tamanhos diferentes")

        # Filtrar valores válidos (não None/NaN)
        valid_points = [
            (x, y)
            for x, y in zip(x_values, y_values)
            if x is not None and y is not None and not (np.isnan(x) or np.isnan(y))
        ]

        if not valid_points:
            logger.warning("Nenhum ponto válido para interpolação")
            return 0.0

        if len(valid_points) == 1:
            return valid_points[0][1]  # Retorna único valor válido

        # Ordenar por X
        valid_points.sort(key=lambda p: p[0])
        x_clean, y_clean = zip(*valid_points)

        # Antes do primeiro ponto - repete primeiro valor
        if target_x <= x_clean[0]:
            return y_clean[0]

        # Após o último ponto - repete último valor
        if target_x >= x_clean[-1]:
            return y_clean[-1]

        # Interpolação linear entre pontos
        return np.interp(target_x, x_clean, y_clean)

    def interpolate_missing_points(
        self, x_values: List[float], y_values: List[float]
    ) -> Tuple[List[float], List[float]]:
        """
        Interpola pontos faltantes em uma série 2D.

        Args:
            x_values: Valores do eixo X (podem conter None)
            y_values: Valores do eixo Y (podem conter None)

        Returns:
            Tupla com (x_values_filled, y_values_filled)
        """
        if len(x_values) != len(y_values):
            raise ValueError("Tamanhos diferentes entre x_values e y_values")

        # Encontrar índices com valores válidos
        valid_indices = [
            i
            for i, (x, y) in enumerate(zip(x_values, y_values))
            if x is not None and y is not None and not (np.isnan(float(x)) or np.isnan(float(y)))
        ]

        if len(valid_indices) < 2:
            logger.warning("Menos de 2 pontos válidos, não é possível interpolar")
            return x_values, y_values

        # Extrair valores válidos
        x_valid = [x_values[i] for i in valid_indices]
        y_valid = [y_values[i] for i in valid_indices]

        # Criar interpolador
        try:
            interpolator = interp1d(
                x_valid, y_valid, kind="linear", bounds_error=False, fill_value="extrapolate"
            )
        except Exception as e:
            logger.error(f"Erro ao criar interpolador: {str(e)}")
            return x_values, y_values

        # Preencher pontos faltantes
        x_result = x_values.copy()
        y_result = y_values.copy()

        for i in range(len(x_values)):
            # Se X é válido mas Y não
            if (
                x_values[i] is not None
                and not np.isnan(float(x_values[i]))
                and (y_values[i] is None or np.isnan(float(y_values[i])))
            ):
                try:
                    y_result[i] = float(interpolator(x_values[i]))
                except:
                    pass  # Manter valor original se interpolação falhar

        return x_result, y_result

    def smooth_2d_data(self, y_values: List[float], window_size: int = 3) -> List[float]:
        """
        Aplica suavização em dados 2D usando média móvel.

        Args:
            y_values: Valores a suavizar
            window_size: Tamanho da janela (deve ser ímpar)

        Returns:
            Lista de valores suavizados
        """
        if window_size < 3 or window_size % 2 == 0:
            window_size = 3

        # Filtrar valores válidos para análise
        valid_mask = [y is not None and not np.isnan(float(y)) for y in y_values]
        valid_count = sum(valid_mask)

        if valid_count < window_size:
            logger.warning("Poucos valores válidos para suavização")
            return y_values

        # Aplicar média móvel
        smoothed = []
        half_window = window_size // 2

        for i in range(len(y_values)):
            if not valid_mask[i]:
                smoothed.append(y_values[i])  # Manter valor original se inválido
                continue

            # Definir janela
            start_idx = max(0, i - half_window)
            end_idx = min(len(y_values), i + half_window + 1)

            # Coletar valores válidos na janela
            window_values = []
            for j in range(start_idx, end_idx):
                if valid_mask[j]:
                    window_values.append(float(y_values[j]))

            if window_values:
                smoothed.append(sum(window_values) / len(window_values))
            else:
                smoothed.append(y_values[i])  # Fallback para valor original

        return smoothed

    def interpolate_3d_matrix(self, matrix: np.ndarray, method: str = "linear") -> np.ndarray:
        """
        Interpola valores faltantes em matriz 3D.

        Args:
            matrix: Matriz numpy com dados (NaN para valores faltantes)
            method: Método de interpolação ('linear', 'cubic', 'nearest')

        Returns:
            Matriz interpolada
        """
        if matrix.size == 0:
            return matrix

        # Criar cópia para não modificar original
        result = matrix.copy()

        # Encontrar posições com dados válidos
        valid_mask = ~np.isnan(result)

        if not np.any(valid_mask):
            logger.warning("Nenhum valor válido na matriz para interpolação")
            return result

        if np.all(valid_mask):
            return result  # Todos os valores são válidos

        # Coordenadas de todos os pontos
        rows, cols = result.shape
        x_coords, y_coords = np.meshgrid(np.arange(cols), np.arange(rows))

        # Pontos com dados válidos
        valid_points = np.column_stack((x_coords[valid_mask].ravel(), y_coords[valid_mask].ravel()))
        valid_values = result[valid_mask]

        # Pontos a interpolar (apenas os inválidos)
        invalid_mask = np.isnan(result)
        if not np.any(invalid_mask):
            return result

        invalid_points = np.column_stack(
            (x_coords[invalid_mask].ravel(), y_coords[invalid_mask].ravel())
        )

        # Interpolação
        try:
            interpolated_values = griddata(
                valid_points, valid_values, invalid_points, method=method, fill_value=np.nan
            )

            # Preencher apenas os valores que foram interpolados com sucesso
            valid_interp_mask = ~np.isnan(interpolated_values)
            if np.any(valid_interp_mask):
                result[invalid_mask] = interpolated_values

        except Exception as e:
            logger.error(f"Erro na interpolação 3D com método {method}: {str(e)}")
            # Fallback para método nearest se linear falhar
            if method != "nearest":
                return self.interpolate_3d_matrix(matrix, "nearest")

        return result

    def convert_2d_maps_to_3d(
        self,
        map_2d_data: np.ndarray,
        rpm_2d_data: np.ndarray,
        map_axis: np.ndarray,
        rpm_axis: np.ndarray,
    ) -> np.ndarray:
        """
        Converte mapas 2D (MAP e RPM) em mapa 3D combinado.

        Args:
            map_2d_data: Valores do mapa MAP 2D
            rpm_2d_data: Valores do mapa RPM 2D
            map_axis: Eixo de pressão MAP
            rpm_axis: Eixo de RPM

        Returns:
            Matriz 3D combinada
        """
        try:
            # Validar entradas
            if len(map_2d_data) != len(map_axis) or len(rpm_2d_data) != len(rpm_axis):
                raise ValueError("Tamanhos inconsistentes entre dados e eixos")

            # Criar malha 3D
            map_grid, rpm_grid = np.meshgrid(map_axis, rpm_axis, indexing="ij")

            # Interpoladores para cada mapa 2D
            map_interpolator = interp1d(
                map_axis, map_2d_data, kind="linear", bounds_error=False, fill_value="extrapolate"
            )
            rpm_interpolator = interp1d(
                rpm_axis, rpm_2d_data, kind="linear", bounds_error=False, fill_value="extrapolate"
            )

            # Calcular valores base de cada mapa
            result = np.zeros_like(map_grid)

            for i in range(len(map_axis)):
                for j in range(len(rpm_axis)):
                    # Valor base do mapa MAP na pressão atual
                    map_base_value = map_interpolator(map_axis[i])

                    # Valor de compensação do mapa RPM no RPM atual
                    rpm_compensation = rpm_interpolator(rpm_axis[j])

                    # Combinar usando peso baseado na carga
                    # Maior peso para mapa MAP em alta carga (MAP positivo)
                    map_weight = max(0.3, min(0.9, (map_axis[i] + 1.5) / 3.5))
                    rpm_weight = 1.0 - map_weight

                    # Aplicar compensação como fator multiplicativo para RPM
                    rpm_factor = 1.0 + (rpm_compensation / 100.0)

                    # Resultado final
                    result[i, j] = map_base_value * (map_weight + rpm_weight * rpm_factor)

            return result

        except Exception as e:
            logger.error(f"Erro na conversão 2D para 3D: {str(e)}")
            # Retornar matriz baseada apenas no mapa MAP como fallback
            return np.outer(map_2d_data, np.ones(len(rpm_axis)))

    def calculate_interpolation_preview(
        self, x_values: List[float], y_values: List[float], resolution: int = 100
    ) -> Tuple[List[float], List[float]]:
        """
        Calcula preview da interpolação para visualização.

        Args:
            x_values: Valores do eixo X
            y_values: Valores correspondentes
            resolution: Número de pontos para o preview

        Returns:
            Tupla com (x_interpolated, y_interpolated)
        """
        try:
            # Filtrar valores válidos
            valid_points = [
                (x, y)
                for x, y in zip(x_values, y_values)
                if x is not None
                and y is not None
                and not (np.isnan(float(x)) or np.isnan(float(y)))
            ]

            if len(valid_points) < 2:
                return [], []

            # Ordenar e extrair
            valid_points.sort(key=lambda p: p[0])
            x_clean, y_clean = zip(*valid_points)

            # Criar eixo interpolado
            x_min, x_max = min(x_clean), max(x_clean)
            if x_min == x_max:
                return [x_min], [y_clean[0]]

            x_interp = np.linspace(x_min, x_max, resolution)

            # Interpolação
            y_interp = [
                self.linear_interpolation_2d(list(x_clean), list(y_clean), x) for x in x_interp
            ]

            return list(x_interp), y_interp

        except Exception as e:
            logger.error(f"Erro no preview de interpolação: {str(e)}")
            return [], []

    def validate_interpolation_quality(
        self, x_values: List[float], y_values: List[float]
    ) -> Dict[str, any]:
        """
        Valida qualidade dos dados para interpolação.

        Args:
            x_values: Valores do eixo X
            y_values: Valores do eixo Y

        Returns:
            Dict com métricas de qualidade
        """
        result = {
            "valid": False,
            "total_points": len(x_values),
            "valid_points": 0,
            "missing_points": 0,
            "x_range": 0.0,
            "y_range": 0.0,
            "monotonic_x": False,
            "quality_score": 0.0,
            "issues": [],
        }

        try:
            # Contar pontos válidos
            valid_mask = [
                x is not None and y is not None and not (np.isnan(float(x)) or np.isnan(float(y)))
                for x, y in zip(x_values, y_values)
            ]

            result["valid_points"] = sum(valid_mask)
            result["missing_points"] = len(x_values) - result["valid_points"]

            if result["valid_points"] < 2:
                result["issues"].append("Menos de 2 pontos válidos")
                return result

            # Extrair valores válidos
            valid_x = [float(x) for x, valid in zip(x_values, valid_mask) if valid]
            valid_y = [float(y) for y, valid in zip(y_values, valid_mask) if valid]

            # Calcular faixas
            result["x_range"] = max(valid_x) - min(valid_x)
            result["y_range"] = max(valid_y) - min(valid_y)

            # Verificar monotonicidade do eixo X
            sorted_x = sorted(valid_x)
            result["monotonic_x"] = valid_x == sorted_x

            if not result["monotonic_x"]:
                result["issues"].append("Valores X não estão em ordem crescente")

            # Calcular score de qualidade (0-100)
            quality_factors = []

            # Fator 1: Proporção de pontos válidos
            valid_ratio = result["valid_points"] / result["total_points"]
            quality_factors.append(valid_ratio * 30)  # Até 30 pontos

            # Fator 2: Monotonicidade
            if result["monotonic_x"]:
                quality_factors.append(20)  # 20 pontos

            # Fator 3: Distribuição dos pontos
            if result["valid_points"] >= 5:
                # Verificar se pontos estão bem distribuídos
                x_diffs = [sorted_x[i + 1] - sorted_x[i] for i in range(len(sorted_x) - 1)]
                max_gap = max(x_diffs)
                avg_gap = sum(x_diffs) / len(x_diffs)

                if max_gap <= 3 * avg_gap:  # Gap máximo não é muito maior que média
                    quality_factors.append(25)  # 25 pontos
                else:
                    quality_factors.append(15)  # Penalizar gaps grandes
                    result["issues"].append("Distribuição irregular dos pontos")

            # Fator 4: Quantidade de pontos
            if result["valid_points"] >= 10:
                quality_factors.append(25)  # 25 pontos para muitos pontos
            elif result["valid_points"] >= 5:
                quality_factors.append(15)
            else:
                quality_factors.append(5)
                result["issues"].append("Poucos pontos para interpolação robusta")

            result["quality_score"] = sum(quality_factors)
            result["valid"] = result["quality_score"] >= 50  # Mínimo 50/100

            if not result["valid"]:
                result["issues"].append(
                    f"Score de qualidade baixo: {result['quality_score']:.1f}/100"
                )

        except Exception as e:
            result["issues"].append(f"Erro na validação: {str(e)}")
            logger.error(f"Erro na validação de qualidade: {str(e)}")

        return result
