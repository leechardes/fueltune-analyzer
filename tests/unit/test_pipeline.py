"""
Testes para o módulo de pipeline de dados.

Author: FuelTune Development Team
Version: 1.0.0
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

from src.integration.pipeline import DataPipeline, PipelineStage


class TestDataPipeline:
    """Testes para DataPipeline."""

    @pytest.fixture
    def sample_data(self):
        """Dados de teste."""
        return pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=100, freq="100ms"),
                "vehicle_speed": np.random.uniform(0, 120, 100),
                "fuel_rate": np.random.uniform(0, 10, 100),
                "rpm": np.random.uniform(800, 6000, 100),
            }
        )

    @pytest.fixture
    def pipeline(self):
        """Pipeline de teste."""
        return DataPipeline()

    def test_pipeline_initialization(self, pipeline):
        """Testar inicialização do pipeline."""
        assert pipeline is not None
        assert hasattr(pipeline, "stages")
        assert hasattr(pipeline, "validations")
        assert len(pipeline.stages) == 0

    def test_add_stage(self, pipeline):
        """Testar adição de estágios."""

        def test_stage(data):
            data["processed"] = True
            return data

        pipeline.add_stage("test", test_stage)
        assert "test" in pipeline.stages
        assert pipeline.stages["test"] == test_stage

    def test_execute_single_stage(self, pipeline, sample_data):
        """Testar execução com um único estágio."""

        def add_column(data):
            data["new_col"] = 100
            return data

        pipeline.add_stage("add_col", add_column)
        result = pipeline.execute(sample_data)

        assert "new_col" in result.columns
        assert result["new_col"].iloc[0] == 100

    def test_execute_multiple_stages(self, pipeline, sample_data):
        """Testar execução com múltiplos estágios."""

        def stage1(data):
            data["stage1"] = 1
            return data

        def stage2(data):
            data["stage2"] = 2
            return data

        def stage3(data):
            data["stage3"] = data["stage1"] + data["stage2"]
            return data

        pipeline.add_stage("s1", stage1)
        pipeline.add_stage("s2", stage2)
        pipeline.add_stage("s3", stage3)

        result = pipeline.execute(sample_data)

        assert "stage1" in result.columns
        assert "stage2" in result.columns
        assert "stage3" in result.columns
        assert result["stage3"].iloc[0] == 3

    def test_validation(self, pipeline, sample_data):
        """Testar validação de dados."""

        def validate_speed(data):
            return (data["vehicle_speed"] >= 0).all()

        pipeline.add_validation("speed_check", validate_speed)

        # Dados válidos devem passar
        result = pipeline.execute(sample_data)
        assert result is not None

        # Dados inválidos devem falhar
        invalid_data = sample_data.copy()
        invalid_data["vehicle_speed"] = -100

        with pytest.raises(ValueError):
            pipeline.execute(invalid_data)

    def test_stage_with_parameters(self, pipeline, sample_data):
        """Testar estágio com parâmetros."""

        def filter_stage(data, threshold=50):
            return data[data["vehicle_speed"] > threshold]

        pipeline.add_stage("filter", lambda d: filter_stage(d, threshold=60))
        result = pipeline.execute(sample_data)

        assert len(result) <= len(sample_data)
        assert (result["vehicle_speed"] > 60).all()

    def test_pipeline_metrics(self, pipeline, sample_data):
        """Testar coleta de métricas."""

        def slow_stage(data):
            import time

            time.sleep(0.01)
            return data

        pipeline.add_stage("slow", slow_stage)
        pipeline.execute(sample_data)

        metrics = pipeline.get_metrics()
        assert "total_executions" in metrics
        assert "average_duration" in metrics
        assert metrics["total_executions"] == 1
        assert metrics["average_duration"] > 0

    def test_pipeline_error_handling(self, pipeline, sample_data):
        """Testar tratamento de erros."""

        def error_stage(data):
            raise ValueError("Test error")

        pipeline.add_stage("error", error_stage)

        with pytest.raises(ValueError):
            pipeline.execute(sample_data)

    def test_pipeline_data_transformation(self, pipeline, sample_data):
        """Testar transformação de dados."""

        def normalize_stage(data):
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col != "timestamp":
                    data[col] = (data[col] - data[col].mean()) / data[col].std()
            return data

        pipeline.add_stage("normalize", normalize_stage)
        result = pipeline.execute(sample_data.copy())

        # Verificar normalização
        for col in ["vehicle_speed", "fuel_rate", "rpm"]:
            assert abs(result[col].mean()) < 0.01  # Próximo de zero
            assert abs(result[col].std() - 1) < 0.01  # Próximo de 1

    def test_pipeline_clear(self, pipeline):
        """Testar limpeza do pipeline."""
        pipeline.add_stage("test1", lambda x: x)
        pipeline.add_stage("test2", lambda x: x)
        pipeline.add_validation("val1", lambda x: True)

        assert len(pipeline.stages) == 2
        assert len(pipeline.validations) == 1

        pipeline.clear()

        assert len(pipeline.stages) == 0
        assert len(pipeline.validations) == 0

    def test_pipeline_stage_order(self, pipeline):
        """Testar ordem de execução dos estágios."""
        execution_order = []

        def make_stage(name):
            def stage(data):
                execution_order.append(name)
                return data

            return stage

        pipeline.add_stage("first", make_stage("first"))
        pipeline.add_stage("second", make_stage("second"))
        pipeline.add_stage("third", make_stage("third"))

        sample_data = pd.DataFrame({"test": [1, 2, 3]})
        pipeline.execute(sample_data)

        assert execution_order == ["first", "second", "third"]

    def test_pipeline_with_quality_check(self, pipeline, sample_data):
        """Testar pipeline com verificação de qualidade."""

        def quality_check_stage(data):
            # Remover outliers
            for col in data.select_dtypes(include=[np.number]).columns:
                if col != "timestamp":
                    q1 = data[col].quantile(0.25)
                    q3 = data[col].quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    data = data[(data[col] >= lower) & (data[col] <= upper)]
            return data

        pipeline.add_stage("quality", quality_check_stage)
        original_len = len(sample_data)
        result = pipeline.execute(sample_data)

        assert len(result) <= original_len

    def test_pipeline_data_aggregation(self, pipeline, sample_data):
        """Testar agregação de dados no pipeline."""

        def aggregate_stage(data):
            # Agregar por segundos
            data["timestamp_sec"] = data["timestamp"].dt.floor("S")
            aggregated = (
                data.groupby("timestamp_sec")
                .agg({"vehicle_speed": "mean", "fuel_rate": "mean", "rpm": "mean"})
                .reset_index()
            )
            return aggregated

        pipeline.add_stage("aggregate", aggregate_stage)
        result = pipeline.execute(sample_data)

        assert len(result) <= len(sample_data)
        assert "timestamp_sec" in result.columns


class TestPipelineStage:
    """Testes para PipelineStage."""

    def test_stage_initialization(self):
        """Testar inicialização de estágio."""

        def test_handler(data):
            return data

        stage = PipelineStage(name="test", handler=test_handler, enabled=True)

        assert stage.name == "test"
        assert stage.handler == test_handler
        assert stage.enabled == True

    def test_stage_execution(self):
        """Testar execução de estágio."""

        def double_values(data):
            return data * 2

        stage = PipelineStage("double", double_values)
        test_data = pd.DataFrame({"value": [1, 2, 3]})

        result = stage.execute(test_data)
        assert result["value"].tolist() == [2, 4, 6]

    def test_stage_disabled(self):
        """Testar estágio desabilitado."""

        def test_handler(data):
            data["processed"] = True
            return data

        stage = PipelineStage("test", test_handler, enabled=False)
        test_data = pd.DataFrame({"value": [1, 2, 3]})

        result = stage.execute(test_data)
        assert "processed" not in result.columns
        assert result.equals(test_data)

    def test_stage_with_config(self):
        """Testar estágio com configuração."""

        def configurable_handler(data, config):
            multiplier = config.get("multiplier", 1)
            data["value"] = data["value"] * multiplier
            return data

        config = {"multiplier": 3}
        stage = PipelineStage("multiply", configurable_handler, config=config)
        test_data = pd.DataFrame({"value": [1, 2, 3]})

        result = stage.execute(test_data)
        assert result["value"].tolist() == [3, 6, 9]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
