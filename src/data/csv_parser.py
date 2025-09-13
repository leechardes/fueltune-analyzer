"""
CSV Parser for FuelTech data files.

Handles both 37-field and 64-field CSV formats with automatic detection.
Provides robust parsing, validation, and error handling.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class CSVParsingError(Exception):
    """Exception raised when CSV parsing fails."""


class FieldMappingError(Exception):
    """Exception raised when field mapping fails."""


class CSVParser:
    """
    Robust CSV parser for FuelTech data files.

    Features:
    - Auto-detection of CSV format (37 vs 64 fields)
    - Field name normalization (PT-BR to EN)
    - Data type inference and validation
    - Memory-efficient batch processing
    - Comprehensive error handling
    """

    # Field mappings from Portuguese to English
    FIELD_MAPPINGS_37 = {
        "TIME": "time",
        "RPM": "rpm",
        "TPS": "tps",
        "Posição_do_acelerador": "throttle_position",
        "Ponto_de_ignição": "ignition_timing",
        "MAP": "map",
        "Alvo_do_malha_fechada": "closed_loop_target",
        "Sonda_Malha_Fechada": "closed_loop_o2",
        "Correção_do_malha_fechada": "closed_loop_correction",
        "Sonda_Geral": "o2_general",
        "2-step": "two_step",
        "Conteúdo_de_Etanol": "ethanol_content",
        "Largada_validada": "launch_validated",
        "Temperatura_do_combustível": "fuel_temp",
        "Marcha": "gear",
        "Vazão_da_bancada_A": "flow_bank_a",
        "Ângulo_da_Fase_de_Injeção": "injection_phase_angle",
        "Abertura_bicos_A": "injector_duty_a",
        "Tempo_de_Injeção_Banco_A": "injection_time_a",
        "Temp._do_motor": "engine_temp",
        "Temp._do_Ar": "air_temp",
        "Pressão_de_Óleo": "oil_pressure",
        "Pressão_de_Combustível": "fuel_pressure",
        "Tensão_da_Bateria": "battery_voltage",
        "Dwell_de_ignição": "ignition_dwell",
        "Eletroventilador_1_-_Enriquecimento": "fan1_enrichment",
        "Nível_de_combustível": "fuel_level",
        "Sinal_de_sincronia_do_motor": "engine_sync",
        "Corte_na_desaceleração_(cutoff)": "decel_cutoff",
        "Partida_do_motor": "engine_cranking",
        "Lenta": "idle",
        "Primeiro_pulso_de_partida": "first_pulse_cranking",
        "Injeção_rápida_e_de_decaimento": "accel_decel_injection",
        "Ajuste_ativo": "active_adjustment",
        "Eletroventilador_1": "fan1",
        "Eletroventilador_2": "fan2",
        "Bomba_Combustível": "fuel_pump",
    }

    FIELD_MAPPINGS_64 = {
        **FIELD_MAPPINGS_37,
        # Additional 27 fields for 64-field format
        "Consumo_total": "total_consumption",
        "Consumo_medio": "average_consumption",
        "Consumo_instantâneo": "instant_consumption",
        "Potência_estimada": "estimated_power",
        "Torque_estimado": "estimated_torque",
        "Distância_total": "total_distance",
        "Autonomia": "range",
        "Velocidade_de_tração": "traction_speed",
        "Velocidade_em_aceleração": "acceleration_speed",
        "Controle_de_tração_-_Slip": "traction_control_slip",
        "Controle_de_tração_-_Slip_rate": "traction_control_slip_rate",
        "Delta_TPS": "delta_tps",
        "Força_G_aceleração": "g_force_accel",
        "Força_G_lateral": "g_force_lateral",
        "Inclinação_frontal": "pitch_angle",
        "Taxa_de_inclinação_frontal": "pitch_rate",
        "Direção_(Heading)": "heading",
        "Inclinação_lateral": "roll_angle",
        "Distancia_em_aceleração": "acceleration_distance",
        "Taxa_de_inclinação_lateral": "roll_rate",
        "Força_G_aceleração_(Raw)": "g_force_accel_raw",
        "Força_G_lateral_(Raw)": "g_force_lateral_raw",
        "Injeção_rápida": "accel_enrichment",
        "Injeção_de_decaimento": "decel_enrichment",
        "Cutoff_de_injeção": "injection_cutoff",
        "Injeção_pós_partida": "after_start_injection",
        "Botão_de_partida_-_Alternar": "start_button_toggle",
    }

    # Data type mappings
    DATA_TYPES = {
        # Core fields
        "time": "float64",
        "rpm": "int64",
        "tps": "float64",
        "throttle_position": "float64",
        "ignition_timing": "float64",
        "map": "float64",
        "closed_loop_target": "float64",
        "closed_loop_o2": "float64",
        "closed_loop_correction": "float64",
        "o2_general": "float64",
        "two_step": "string",
        "ethanol_content": "int64",
        "launch_validated": "string",
        "fuel_temp": "float64",
        "gear": "int64",
        "flow_bank_a": "float64",
        "injection_phase_angle": "float64",
        "injector_duty_a": "float64",
        "injection_time_a": "float64",
        "engine_temp": "float64",
        "air_temp": "float64",
        "oil_pressure": "float64",
        "fuel_pressure": "float64",
        "battery_voltage": "float64",
        "ignition_dwell": "float64",
        "fan1_enrichment": "float64",
        "fuel_level": "float64",
        "engine_sync": "string",
        "decel_cutoff": "string",
        "engine_cranking": "string",
        "idle": "string",
        "first_pulse_cranking": "string",
        "accel_decel_injection": "string",
        "active_adjustment": "int64",
        "fan1": "string",
        "fan2": "string",
        "fuel_pump": "string",
        # Extended 64-field format
        "total_consumption": "float64",
        "average_consumption": "float64",
        "instant_consumption": "float64",
        "estimated_power": "int64",
        "estimated_torque": "int64",
        "total_distance": "float64",
        "range": "float64",
        "traction_speed": "float64",
        "acceleration_speed": "float64",
        "traction_control_slip": "float64",
        "traction_control_slip_rate": "int64",
        "delta_tps": "float64",
        "g_force_accel": "float64",
        "g_force_lateral": "float64",
        "pitch_angle": "float64",
        "pitch_rate": "float64",
        "heading": "float64",
        "roll_angle": "float64",
        "acceleration_distance": "float64",
        "roll_rate": "float64",
        "g_force_accel_raw": "float64",
        "g_force_lateral_raw": "float64",
        "accel_enrichment": "string",
        "decel_enrichment": "string",
        "injection_cutoff": "string",
        "after_start_injection": "string",
        "start_button_toggle": "string",
    }

    def __init__(self, encoding: str = "utf-8", chunk_size: int = 10000):
        """
        Initialize CSV parser.

        Args:
            encoding: File encoding (default: utf-8)
            chunk_size: Chunk size for batch processing (default: 10000)
        """
        self.encoding = encoding
        self.chunk_size = chunk_size
        self.detected_version: Optional[str] = None
        self.field_mappings: Optional[Dict[str, str]] = None

    def detect_csv_format(self, file_path: Union[str, Path]) -> Tuple[str, int]:
        """
        Detect CSV format by analyzing header row.

        Args:
            file_path: Path to CSV file

        Returns:
            Tuple of (format_version, field_count)

        Raises:
            CSVParsingError: If format detection fails
        """
        try:
            file_path = Path(file_path)

            with open(file_path, "r", encoding=self.encoding) as file:
                # Read first line (header)
                first_line = file.readline().strip()

                # Count fields
                reader = csv.reader([first_line])
                headers = next(reader)
                field_count = len(headers)

                logger.info(f"Detectado {field_count} campos no arquivo {file_path.name}")

                # Flexible field count detection
                # v1.0: Accept 35-37 fields (allows for variations)
                # v2.0: Accept 62-66 fields (allows for variations)
                if 35 <= field_count <= 37:
                    version = "v1.0"
                    self.field_mappings = self.FIELD_MAPPINGS_37
                    logger.info(
                        f"Detectado formato v1.0 com {field_count} campos (variação aceita: 35-37)"
                    )
                elif 62 <= field_count <= 66:
                    version = "v2.0"
                    self.field_mappings = self.FIELD_MAPPINGS_64
                    logger.info(
                        f"Detectado formato v2.0 com {field_count} campos (variação aceita: 62-66)"
                    )
                else:
                    # Lenient handling for intermediate field counts: assume v2.0 (parcial)
                    if 38 <= field_count <= 61:
                        version = "v2.0"
                        self.field_mappings = self.FIELD_MAPPINGS_64
                        logger.warning(
                            "Contagem intermediária de campos detectada (%d). "
                            "Assumindo formato v2.0 parcial e prosseguindo com os campos disponíveis.",
                            field_count,
                        )
                    else:
                        # Provide helpful error message for clearly invalid counts
                        if field_count < 35:
                            suggestion = "Arquivo pode estar truncado ou corrompido. Mínimo esperado: 35 campos."
                        else:
                            suggestion = "Arquivo pode conter campos extras ou estar corrompido. Máximo suportado: 66 campos."

                        raise CSVParsingError(
                            f"Formato não suportado: {field_count} campos. {suggestion}"
                        )

                self.detected_version = version
                return version, field_count

        except Exception as e:
            raise CSVParsingError(f"Erro na detecção de formato: {str(e)}")

    def normalize_headers(self, headers: List[str]) -> List[str]:
        """
        Normalize Portuguese headers to English field names.

        Args:
            headers: Original Portuguese headers

        Returns:
            List of normalized English headers

        Raises:
            FieldMappingError: If header mapping fails
        """
        if not self.field_mappings:
            raise FieldMappingError("Field mappings not initialized. Call detect_csv_format first.")

        normalized = []
        unmapped = []
        mapped_count = 0

        for header in headers:
            # Clean header (remove extra whitespace, special characters)
            cleaned_header = header.strip()

            # Try exact match first
            normalized_name = self.field_mappings.get(cleaned_header)

            if normalized_name:
                normalized.append(normalized_name)
                mapped_count += 1
            else:
                # Try fuzzy matching for common variations
                fuzzy_match = self._find_fuzzy_header_match(cleaned_header)

                if fuzzy_match:
                    normalized.append(fuzzy_match)
                    mapped_count += 1
                    logger.info(f"Mapeamento fuzzy: '{cleaned_header}' -> '{fuzzy_match}'")
                else:
                    unmapped.append(cleaned_header)
                    # Create normalized version as fallback
                    fallback_name = self._create_fallback_header_name(cleaned_header)
                    normalized.append(fallback_name)

        # Log mapping statistics
        total_headers = len(headers)
        mapping_rate = (mapped_count / total_headers) * 100 if total_headers > 0 else 0
        logger.info(
            f"Taxa de mapeamento de campos: {mapping_rate:.1f}% ({mapped_count}/{total_headers})"
        )

        if unmapped:
            logger.warning(
                f"Campos não mapeados ({len(unmapped)}): {unmapped[:5]}{'...' if len(unmapped) > 5 else ''}"
            )

            # If too many fields are unmapped, suggest possible issues
            if len(unmapped) > len(headers) * 0.3:  # More than 30% unmapped
                logger.warning(
                    "Muitos campos não mapeados. Verifique se o formato do arquivo está correto."
                )

        return normalized

    def _find_fuzzy_header_match(self, header: str) -> Optional[str]:
        """
        Find fuzzy match for header using common variations and typos.

        Args:
            header: Header to match

        Returns:
            Matched field name or None
        """
        # Common variations and typos
        header_variations = {
            # Common typos and variations
            "RPMs": "rpm",
            "Rotações": "rpm",
            "TPS%": "tps",
            "Acelerador": "throttle_position",
            "Ponto": "ignition_timing",
            "Temperatura_motor": "engine_temp",
            "Temp_motor": "engine_temp",
            "Temperatura_ar": "air_temp",
            "Temp_ar": "air_temp",
            "Pressao_oleo": "oil_pressure",
            "Pressão_óleo": "oil_pressure",
            "Pressao_combustivel": "fuel_pressure",
            "Pressão_combustível": "fuel_pressure",
            "Bateria": "battery_voltage",
            "Tensão": "battery_voltage",
            # Extended fields variations
            "Potencia": "estimated_power",
            "Potência": "estimated_power",
            "Torque": "estimated_torque",
            "Consumo": "instant_consumption",
            "G_accel": "g_force_accel",
            "G_lateral": "g_force_lateral",
            "Força_G": "g_force_accel",
        }

        # Direct lookup
        if header in header_variations:
            return header_variations[header]

        # Case-insensitive partial matching
        header_lower = header.lower()
        for variation, field_name in header_variations.items():
            if variation.lower() in header_lower or header_lower in variation.lower():
                return field_name

        return None

    def _create_fallback_header_name(self, header: str) -> str:
        """
        Create a normalized fallback header name.

        Args:
            header: Original header

        Returns:
            Normalized header name
        """
        # Remove special characters and normalize
        import re

        # Convert to lowercase and replace special chars
        normalized = header.lower()

        # Replace Portuguese characters
        char_map = {
            "ã": "a",
            "á": "a",
            "à": "a",
            "â": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ì": "i",
            "î": "i",
            "õ": "o",
            "ó": "o",
            "ô": "o",
            "ú": "u",
            "ù": "u",
            "û": "u",
            "ç": "c",
            "ñ": "n",
        }

        for pt_char, en_char in char_map.items():
            normalized = normalized.replace(pt_char, en_char)

        # Replace spaces and special characters with underscores
        normalized = re.sub(r"[^a-z0-9]+", "_", normalized)

        # Remove leading/trailing underscores
        normalized = normalized.strip("_")

        # Ensure it's not empty
        if not normalized:
            normalized = f"unknown_field_{hash(header) % 1000}"

        return normalized

    def parse_csv(
        self,
        file_path: Union[str, Path],
        validate_types: bool = True,
        chunk_processing: bool = False,
    ) -> pd.DataFrame:
        """
        Parse CSV file into pandas DataFrame.

        Args:
            file_path: Path to CSV file
            validate_types: Apply data type validation
            chunk_processing: Use chunk processing for large files

        Returns:
            Parsed DataFrame with normalized columns

        Raises:
            CSVParsingError: If parsing fails
        """
        try:
            file_path = Path(file_path)

            # Detect format if not already done
            if not self.detected_version:
                self.detect_csv_format(file_path)

            logger.info(
                f"Iniciando parse do arquivo {file_path.name} (formato {self.detected_version})"
            )

            if chunk_processing:
                return self._parse_csv_chunks(file_path, validate_types)
            else:
                return self._parse_csv_direct(file_path, validate_types)

        except Exception as e:
            raise CSVParsingError(f"Erro no parse do CSV: {str(e)}")

    def _parse_csv_direct(self, file_path: Path, validate_types: bool) -> pd.DataFrame:
        """Parse CSV directly into memory."""
        # Read CSV
        df = pd.read_csv(file_path, encoding=self.encoding, sep=",", low_memory=False)

        # Normalize headers
        df.columns = self.normalize_headers(df.columns.tolist())

        # Clean invalid data (infinities and extreme values)
        df = self._clean_invalid_data(df)

        # Apply data types if requested
        if validate_types:
            df = self._apply_data_types(df)

        logger.info(f"CSV parseado com sucesso: {len(df)} linhas, {len(df.columns)} colunas")
        return df

    def _parse_csv_chunks(self, file_path: Path, validate_types: bool) -> pd.DataFrame:
        """Parse CSV in chunks for memory efficiency."""
        chunks = []

        chunk_reader = pd.read_csv(
            file_path,
            encoding=self.encoding,
            sep=",",
            chunksize=self.chunk_size,
            low_memory=False,
        )

        normalized_headers = None
        for i, chunk in enumerate(chunk_reader):
            # Normalize headers on first chunk and store them
            if i == 0:
                normalized_headers = self.normalize_headers(chunk.columns.tolist())
                chunk.columns = normalized_headers
            else:
                # Use the same normalized headers for all chunks
                chunk.columns = normalized_headers

            # Clean invalid data
            chunk = self._clean_invalid_data(chunk)

            # Apply data types if requested
            if validate_types:
                chunk = self._apply_data_types(chunk)

            chunks.append(chunk)
            logger.debug(f"Processado chunk {i+1}: {len(chunk)} linhas")

        # Combine chunks
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"CSV parseado em chunks: {len(df)} linhas, {len(df.columns)} colunas")
        return df

    def _clean_invalid_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove linhas com dados inválidos (infinitos ou valores extremos).

        Args:
            df: DataFrame para limpar

        Returns:
            DataFrame limpo sem linhas com valores inválidos
        """
        import numpy as np

        initial_rows = len(df)

        # Remover linhas com valores infinitos
        df = df.replace([np.inf, -np.inf], np.nan)

        # Para colunas numéricas, verificar valores extremos
        numeric_columns = df.select_dtypes(include=[np.number]).columns

        # Definir limites razoáveis para RPM e outros valores
        limits = {
            "rpm": (0, 20000),  # RPM entre 0 e 20000
            "throttle_position": (-5, 105),  # TPS entre -5 e 105%
            "map": (-1, 5),  # MAP entre -1 e 5 bar
            "engine_temp": (-50, 200),  # Temperatura entre -50 e 200°C
            "o2_general": (0, 2),  # Lambda entre 0 e 2
        }

        # Marcar linhas para remoção
        rows_to_remove = pd.Series([False] * len(df))

        for col in df.columns:
            # Normalizar nome da coluna para comparação
            col_lower = col.lower()

            # Verificar se a coluna tem limites definidos
            for key, (min_val, max_val) in limits.items():
                if key in col_lower and col in numeric_columns:
                    # Marcar linhas com valores fora do limite
                    mask = (df[col] < min_val) | (df[col] > max_val) | df[col].isna()
                    rows_to_remove = rows_to_remove | mask

                    # Log de valores inválidos encontrados
                    invalid_count = mask.sum()
                    if invalid_count > 0:
                        logger.warning(
                            f"Encontrados {invalid_count} valores inválidos em '{col}' "
                            f"(fora do intervalo [{min_val}, {max_val}])"
                        )

        # Remover linhas marcadas
        df_clean = df[~rows_to_remove].copy()

        rows_removed = initial_rows - len(df_clean)
        if rows_removed > 0:
            logger.info(
                f"Removidas {rows_removed} linhas com dados inválidos "
                f"({rows_removed/initial_rows*100:.1f}% do total)"
            )

        return df_clean

    def _apply_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply appropriate data types to DataFrame columns."""
        conversion_stats = {"converted": 0, "failed": 0, "skipped": 0}

        for col in df.columns:
            if col in self.DATA_TYPES:
                expected_type = self.DATA_TYPES[col]
                try:
                    # Check if column has any non-null values
                    if df[col].isna().all():
                        logger.warning(
                            f"Coluna '{col}' está completamente vazia, pulando conversão de tipo"
                        )
                        conversion_stats["skipped"] += 1
                        continue

                    original_type = str(df[col].dtype)

                    if expected_type == "string":
                        df[col] = df[col].astype("string")
                    elif expected_type in ["int64", "Int64"]:
                        # Convert to int64, handle missing values by filling with 0
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
                    elif expected_type == "float64":
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                    conversion_stats["converted"] += 1
                    logger.debug(f"Convertido '{col}': {original_type} -> {expected_type}")

                except Exception as e:
                    conversion_stats["failed"] += 1
                    logger.warning(f"Erro ao converter tipo da coluna '{col}': {str(e)}")
                    # Keep original data type on conversion failure

            else:
                # Column not in known types, try to infer appropriate type
                self._infer_and_apply_type(df, col)

        # Log conversion statistics
        total_cols = len([col for col in df.columns if col in self.DATA_TYPES])
        if total_cols > 0:
            success_rate = (conversion_stats["converted"] / total_cols) * 100
            logger.info(
                f"Conversão de tipos: {success_rate:.1f}% sucesso ({conversion_stats['converted']}/{total_cols})"
            )

            if conversion_stats["failed"] > 0:
                logger.warning(f"Falhas na conversão: {conversion_stats['failed']} colunas")

        return df

    def _infer_and_apply_type(self, df: pd.DataFrame, col: str) -> None:
        """
        Infer and apply appropriate data type for unknown columns.

        Args:
            df: DataFrame to modify
            col: Column name to infer type for
        """
        try:
            # Skip if column is empty
            if df[col].isna().all():
                return

            # Get sample of non-null values
            sample_values = df[col].dropna().head(100)

            if len(sample_values) == 0:
                return

            # Try to identify data type based on content
            str(sample_values.iloc[0]).strip()

            # Check if it looks like boolean/status (ON/OFF)
            unique_vals = set(str(val).strip().upper() for val in sample_values.unique())
            if unique_vals.issubset({"ON", "OFF", "TRUE", "FALSE", "1", "0", "SIM", "NÃO"}):
                logger.debug(f"Inferido tipo string para coluna '{col}' (valores booleanos/status)")
                df[col] = df[col].astype("string")
                return

            # Try numeric conversion
            numeric_sample = pd.to_numeric(sample_values, errors="coerce")
            non_null_numeric = numeric_sample.dropna()

            if len(non_null_numeric) > len(sample_values) * 0.8:  # 80% are numeric
                # Check if values are integers
                if all(val == int(val) for val in non_null_numeric):
                    logger.debug(f"Inferido tipo Int64 para coluna '{col}'")
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                else:
                    logger.debug(f"Inferido tipo float64 para coluna '{col}'")
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                # Default to string for non-numeric data
                logger.debug(f"Inferido tipo string para coluna '{col}' (não numérico)")
                df[col] = df[col].astype("string")

        except Exception as e:
            logger.debug(f"Erro na inferência de tipo para coluna '{col}': {str(e)}")
            # Keep original type on error

    def get_file_info(self, file_path: Union[str, Path]) -> Dict:
        """
        Get comprehensive information about CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with file information
        """
        file_path = Path(file_path)

        # Detect format
        version, field_count = self.detect_csv_format(file_path)

        # Get file stats
        file_stats = file_path.stat()

        # Count lines
        with open(file_path, "r", encoding=self.encoding) as f:
            line_count = sum(1 for _ in f) - 1  # Subtract header row

        return {
            "filename": file_path.name,
            "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
            "format_version": version,
            "field_count": field_count,
            "estimated_rows": line_count,
            "encoding": self.encoding,
            "last_modified": file_stats.st_mtime,
        }

    def validate_csv_structure(self, file_path: Union[str, Path]) -> Dict:
        """
        Validate CSV structure and content.

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with validation results
        """
        results = {"is_valid": True, "errors": [], "warnings": [], "file_info": {}}

        try:
            # Get file info
            results["file_info"] = self.get_file_info(file_path)

            # Read small sample for validation
            df_sample = pd.read_csv(file_path, encoding=self.encoding, nrows=100)

            # Normalize headers
            df_sample.columns = self.normalize_headers(df_sample.columns.tolist())

            # Check for required fields
            required_fields = ["time", "rpm", "map", "tps"]
            missing_fields = [f for f in required_fields if f not in df_sample.columns]

            if missing_fields:
                results["errors"].append(f"Campos obrigatórios faltando: {missing_fields}")
                results["is_valid"] = False

            # Check for data quality issues
            if df_sample["time"].isna().any():
                results["warnings"].append("Valores TIME em falta detectados")

            if (df_sample["rpm"] < 0).any():
                results["warnings"].append("Valores RPM negativos detectados")

        except Exception as e:
            results["is_valid"] = False
            results["errors"].append(f"Erro na validação: {str(e)}")

        # Raise exception if validation failed
        if not results["is_valid"]:
            error_msg = "; ".join(results["errors"])
            raise CSVParsingError(f"Validação do CSV falhou: {error_msg}")

        return results


def parse_fueltech_csv(
    file_path: Union[str, Path], chunk_size: int = 10000, validate: bool = True
) -> pd.DataFrame:
    """
    Convenience function to parse FuelTech CSV files.

    Args:
        file_path: Path to CSV file
        chunk_size: Chunk size for large files
        validate: Apply validation and type conversion

    Returns:
        Parsed DataFrame
    """
    parser = CSVParser(chunk_size=chunk_size)

    # Use chunk processing for large files (>10MB)
    file_size = Path(file_path).stat().st_size
    use_chunks = file_size > (10 * 1024 * 1024)

    return parser.parse_csv(
        file_path=file_path, validate_types=validate, chunk_processing=use_chunks
    )


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        parser = CSVParser()

        # Validate file
        validation = parser.validate_csv_structure(csv_file)
        print(f"Validation: {validation}")

        if validation["is_valid"]:
            # Parse file
            df = parser.parse_csv(csv_file)
            print(f"Parsed DataFrame: {df.shape}")
            print(f"Columns: {list(df.columns)}")
