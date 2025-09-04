"""
Unit tests for CSV parser module.

Tests CSV parsing, format detection, field mapping,
and error handling for FuelTech data files.

Author: A02-DATA-PANDAS Agent
Created: 2025-01-02
"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.data.csv_parser import CSVParser, CSVParsingError, FieldMappingError, parse_fueltech_csv


class TestCSVParser:
    """Test cases for CSVParser class."""

    def setup_method(self):
        """Setup for each test method."""
        self.parser = CSVParser()

        # Sample data for testing
        self.sample_37_headers = [
            "TIME",
            "RPM",
            "TPS",
            "MAP",
            "Temp._do_motor",
            "Sonda_Geral",
            "Posição_do_acelerador",
            "Ponto_de_ignição",
            "Alvo_do_malha_fechada",
            "Sonda_Malha_Fechada",
            "Correção_do_malha_fechada",
            "2-step",
            "Conteúdo_de_Etanol",
            "Largada_validada",
            "Temperatura_do_combustível",
            "Marcha",
            "Vazão_da_bancada_A",
            "Ângulo_da_Fase_de_Injeção",
            "Abertura_bicos_A",
            "Tempo_de_Injeção_Banco_A",
            "Temp._do_Ar",
            "Pressão_de_Óleo",
            "Pressão_de_Combustível",
            "Tensão_da_Bateria",
            "Dwell_de_ignição",
            "Eletroventilador_1_-_Enriquecimento",
            "Nível_de_combustível",
            "Sinal_de_sincronia_do_motor",
            "Corte_na_desaceleração_(cutoff)",
            "Partida_do_motor",
            "Lenta",
            "Primeiro_pulso_de_partida",
            "Injeção_rápida_e_de_decaimento",
            "Ajuste_ativo",
            "Eletroventilador_1",
            "Eletroventilador_2",
            "Bomba_Combustível",
        ]

        self.sample_64_headers = self.sample_37_headers + [
            "Consumo_total",
            "Consumo_medio",
            "Consumo_instantâneo",
            "Potência_estimada",
            "Torque_estimado",
            "Distância_total",
            "Autonomia",
            "Velocidade_de_tração",
            "Velocidade_em_aceleração",
            "Controle_de_tração_-_Slip",
            "Controle_de_tração_-_Slip_rate",
            "Delta_TPS",
            "Força_G_aceleração",
            "Força_G_lateral",
            "Inclinação_frontal",
            "Taxa_de_inclinação_frontal",
            "Direção_(Heading)",
            "Inclinação_lateral",
            "Distancia_em_aceleração",
            "Taxa_de_inclinação_lateral",
            "Força_G_aceleração_(Raw)",
            "Força_G_lateral_(Raw)",
            "Injeção_rápida",
            "Injeção_de_decaimento",
            "Cutoff_de_injeção",
            "Injeção_pós_partida",
            "Botão_de_partida_-_Alternar",
        ]

        self.sample_data_37 = [
            [0.0, 1000, 0.0, -0.5, 85.0, 0.95] + [0] * 31,
            [0.04, 1100, 10.0, -0.4, 85.5, 0.94] + [0] * 31,
            [0.08, 1200, 20.0, -0.3, 86.0, 0.93] + [0] * 31,
        ]

        self.sample_data_64 = [
            [0.0, 1000, 0.0, -0.5, 85.0, 0.95] + [0] * 58,
            [0.04, 1100, 10.0, -0.4, 85.5, 0.94] + [0] * 58,
            [0.08, 1200, 20.0, -0.3, 86.0, 0.93] + [0] * 58,
        ]

    def create_test_csv(self, headers, data, filename="test.csv"):
        """Create a test CSV file."""
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        )

        writer = csv.writer(temp_file)
        writer.writerow(headers)
        writer.writerows(data)
        temp_file.close()

        return Path(temp_file.name)

    def test_detect_csv_format_37_fields(self):
        """Test detection of 37-field format."""
        csv_file = self.create_test_csv(self.sample_37_headers, self.sample_data_37)

        try:
            version, field_count = self.parser.detect_csv_format(csv_file)

            assert version == "v1.0"
            assert field_count == 37
            assert self.parser.detected_version == "v1.0"
            assert self.parser.field_mappings == self.parser.FIELD_MAPPINGS_37

        finally:
            csv_file.unlink()

    def test_detect_csv_format_64_fields(self):
        """Test detection of 64-field format."""
        csv_file = self.create_test_csv(self.sample_64_headers, self.sample_data_64)

        try:
            version, field_count = self.parser.detect_csv_format(csv_file)

            assert version == "v2.0"
            assert field_count == 64
            assert self.parser.detected_version == "v2.0"
            assert self.parser.field_mappings == self.parser.FIELD_MAPPINGS_64

        finally:
            csv_file.unlink()

    def test_detect_csv_format_invalid_field_count(self):
        """Test detection with invalid field count."""
        invalid_headers = ["TIME", "RPM", "TPS"]  # Only 3 fields
        invalid_data = [[0.0, 1000, 0.0], [0.04, 1100, 10.0]]

        csv_file = self.create_test_csv(invalid_headers, invalid_data)

        try:
            with pytest.raises(CSVParsingError) as exc_info:
                self.parser.detect_csv_format(csv_file)

            assert "Formato não suportado" in str(exc_info.value)
            assert "3 campos" in str(exc_info.value)

        finally:
            csv_file.unlink()

    def test_normalize_headers_37_fields(self):
        """Test header normalization for 37-field format."""
        self.parser.field_mappings = self.parser.FIELD_MAPPINGS_37

        normalized = self.parser.normalize_headers(self.sample_37_headers)

        # Check specific mappings
        assert normalized[0] == "time"  # TIME -> time
        assert normalized[1] == "rpm"  # RPM -> rpm
        assert normalized[2] == "tps"  # TPS -> tps
        assert normalized[4] == "engine_temp"  # Temp._do_motor -> engine_temp

        # Check length
        assert len(normalized) == 37

    def test_normalize_headers_64_fields(self):
        """Test header normalization for 64-field format."""
        self.parser.field_mappings = self.parser.FIELD_MAPPINGS_64

        normalized = self.parser.normalize_headers(self.sample_64_headers)

        # Check specific mappings including extended fields
        assert normalized[0] == "time"
        assert "total_consumption" in normalized  # Extended field
        assert "g_force_accel" in normalized  # Extended field

        # Check length
        assert len(normalized) == 64

    def test_normalize_headers_without_mappings(self):
        """Test header normalization without field mappings initialized."""
        with pytest.raises(FieldMappingError) as exc_info:
            self.parser.normalize_headers(self.sample_37_headers)

        assert "Field mappings not initialized" in str(exc_info.value)

    def test_parse_csv_37_fields(self):
        """Test parsing 37-field CSV."""
        csv_file = self.create_test_csv(self.sample_37_headers, self.sample_data_37)

        try:
            df = self.parser.parse_csv(csv_file)

            # Check shape
            assert df.shape == (3, 37)

            # Check columns are normalized
            assert "time" in df.columns
            assert "rpm" in df.columns
            assert "engine_temp" in df.columns

            # Check data types
            assert df["time"].dtype == "float64"
            assert df["rpm"].dtype == "int64"

            # Check values
            assert df.loc[0, "time"] == 0.0
            assert df.loc[1, "rpm"] == 1100

        finally:
            csv_file.unlink()

    def test_parse_csv_64_fields(self):
        """Test parsing 64-field CSV."""
        csv_file = self.create_test_csv(self.sample_64_headers, self.sample_data_64)

        try:
            df = self.parser.parse_csv(csv_file)

            # Check shape
            assert df.shape == (3, 64)

            # Check extended fields are present
            assert "total_consumption" in df.columns
            assert "g_force_accel" in df.columns

        finally:
            csv_file.unlink()

    def test_parse_csv_chunk_processing(self):
        """Test parsing with chunk processing."""
        csv_file = self.create_test_csv(self.sample_37_headers, self.sample_data_37)

        try:
            # Force chunk processing
            df = self.parser.parse_csv(csv_file, chunk_processing=True)

            # Should produce same result as direct processing
            assert df.shape == (3, 37)
            assert "time" in df.columns

        finally:
            csv_file.unlink()

    def test_get_file_info(self):
        """Test file information extraction."""
        csv_file = self.create_test_csv(self.sample_37_headers, self.sample_data_37)

        try:
            info = self.parser.get_file_info(csv_file)

            # Check info structure
            assert "filename" in info
            assert "file_size_mb" in info
            assert "format_version" in info
            assert "field_count" in info
            assert "estimated_rows" in info
            assert "encoding" in info

            # Check values
            assert info["format_version"] == "v1.0"
            assert info["field_count"] == 37
            assert info["estimated_rows"] == 3
            assert info["encoding"] == "utf-8"

        finally:
            csv_file.unlink()

    def test_validate_csv_structure_valid(self):
        """Test CSV structure validation with valid file."""
        csv_file = self.create_test_csv(self.sample_37_headers, self.sample_data_37)

        try:
            results = self.parser.validate_csv_structure(csv_file)

            assert results["is_valid"] is True
            assert len(results["errors"]) == 0
            assert "file_info" in results

        finally:
            csv_file.unlink()

    def test_validate_csv_structure_missing_fields(self):
        """Test CSV structure validation with missing required fields."""
        # Headers without required fields
        incomplete_headers = ["TIME", "SOME_FIELD", "ANOTHER_FIELD"]
        incomplete_data = [[0.0, 1, 2], [0.04, 3, 4]]

        csv_file = self.create_test_csv(incomplete_headers, incomplete_data)

        try:
            with pytest.raises(CSVParsingError):
                # This should fail during format detection
                self.parser.validate_csv_structure(csv_file)
        finally:
            csv_file.unlink()

    def test_parse_fueltech_csv_convenience_function(self):
        """Test convenience function for parsing."""
        csv_file = self.create_test_csv(self.sample_37_headers, self.sample_data_37)

        try:
            df = parse_fueltech_csv(csv_file)

            assert isinstance(df, pd.DataFrame)
            assert df.shape == (3, 37)
            assert "time" in df.columns

        finally:
            csv_file.unlink()

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file."""
        with pytest.raises(CSVParsingError):
            self.parser.parse_csv("nonexistent_file.csv")

    @patch("src.data.csv_parser.pd.read_csv")
    def test_parse_csv_pandas_error(self, mock_read_csv):
        """Test handling of pandas read_csv errors."""
        mock_read_csv.side_effect = Exception("Pandas error")

        csv_file = self.create_test_csv(self.sample_37_headers, self.sample_data_37)

        try:
            with pytest.raises(CSVParsingError) as exc_info:
                self.parser.parse_csv(csv_file)

            assert "Erro no parse do CSV" in str(exc_info.value)

        finally:
            csv_file.unlink()

    def test_data_type_application(self):
        """Test data type application during parsing."""
        # Create data with mixed types
        mixed_data = [
            [0.0, 1000, 0.0, -0.5, 85.0, 0.95, "ON"] + [0] * 30,
            [0.04, "1100", "10.0", -0.4, 85.5, 0.94, "OFF"] + [0] * 30,
        ]

        csv_file = self.create_test_csv(self.sample_37_headers, mixed_data)

        try:
            df = self.parser.parse_csv(csv_file, validate_types=True)

            # Check that string "1100" was converted to int
            assert df.loc[1, "rpm"] == 1100
            assert df["rpm"].dtype == "int64"

            # Check that string "10.0" was converted to float
            assert df.loc[1, "tps"] == 10.0
            assert df["tps"].dtype == "float64"

            # Check that string fields remain as string
            assert df["two_step"].dtype == "string"

        finally:
            csv_file.unlink()

    def test_field_mappings_completeness(self):
        """Test that field mappings cover all expected fields."""
        # Test 37-field mappings
        assert len(self.parser.FIELD_MAPPINGS_37) == 37

        # Test 64-field mappings
        assert len(self.parser.FIELD_MAPPINGS_64) == 64

        # Test that all 37-field mappings are included in 64-field mappings
        for key, value in self.parser.FIELD_MAPPINGS_37.items():
            assert key in self.parser.FIELD_MAPPINGS_64
            assert self.parser.FIELD_MAPPINGS_64[key] == value

    def test_data_types_mapping_completeness(self):
        """Test that data types are defined for all mapped fields."""
        # All normalized field names should have data types
        all_normalized_fields = set(self.parser.FIELD_MAPPINGS_64.values())
        defined_types = set(self.parser.DATA_TYPES.keys())

        # Check that all mapped fields have data types
        missing_types = all_normalized_fields - defined_types
        assert len(missing_types) == 0, f"Missing data types for fields: {missing_types}"

    def teardown_method(self):
        """Cleanup after each test method."""


class TestCSVParserIntegration:
    """Integration tests for CSV parser with real-world scenarios."""

    def test_large_file_simulation(self):
        """Test handling of large file simulation."""
        # Create larger dataset
        headers = ["TIME", "RPM", "TPS", "MAP", "Temp._do_motor", "Sonda_Geral"] + [
            "Field_" + str(i) for i in range(31)
        ]  # Total 37 fields

        # Generate 1000 rows
        data = []
        for i in range(1000):
            row = [
                i * 0.04,
                1000 + i,
                i % 100,
                -0.5 + (i % 10) * 0.1,
                85 + i * 0.01,
                0.95,
            ]
            row.extend([0] * 31)
            data.append(row)

        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        )

        writer = csv.writer(temp_file)
        writer.writerow(headers)
        writer.writerows(data)
        temp_file.close()

        try:
            parser = CSVParser(chunk_size=100)
            df = parser.parse_csv(temp_file.name, chunk_processing=True)

            assert df.shape == (1000, 37)
            assert df["time"].iloc[-1] == 999 * 0.04

        finally:
            Path(temp_file.name).unlink()

    def test_encoding_handling(self):
        """Test handling of different encodings."""
        # This test would require creating files with different encodings
        # For now, just test that the encoding parameter is used
        parser = CSVParser(encoding="latin-1")
        assert parser.encoding == "latin-1"

    def test_memory_usage_tracking(self):
        """Test that parser doesn't use excessive memory."""
        # This is more of a smoke test - real memory testing would require memory_profiler
        parser = CSVParser()

        # Create medium-sized dataset
        headers = ["TIME", "RPM"] + ["Field_" + str(i) for i in range(35)]
        data = [[i * 0.04, 1000 + i] + [0] * 35 for i in range(100)]

        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        )

        writer = csv.writer(temp_file)
        writer.writerow(headers)
        writer.writerows(data)
        temp_file.close()

        try:
            # Should not raise memory errors
            df = parser.parse_csv(temp_file.name)
            assert isinstance(df, pd.DataFrame)

        finally:
            Path(temp_file.name).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
