"""
FuelTune Data Pipeline

Sistema de pipeline unificado para processamento ETL de dados de telemetria
automotiva com foco em performance e escalabilidade.

Classes:
    DataPipeline: Pipeline principal de dados
    PipelineStage: Estágio individual do pipeline
    DataTransformer: Transformadores de dados
    ValidationEngine: Motor de validação

Author: FuelTune Development Team
Version: 1.0.0
"""

import asyncio
import time
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ..utils.logger import get_logger

logger = get_logger(__name__)


class StageStatus(Enum):
    """Status de execução de estágio."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DataQuality(Enum):
    """Níveis de qualidade de dados."""

    EXCELLENT = 5
    GOOD = 4
    FAIR = 3
    POOR = 2
    CRITICAL = 1


class TransformationType(Enum):
    """Tipos de transformações disponíveis."""

    FILTER = "filter"
    MAP = "map"
    AGGREGATE = "aggregate"
    JOIN = "join"
    VALIDATE = "validate"
    NORMALIZE = "normalize"
    ENRICH = "enrich"
    CLEAN = "clean"


@dataclass
class PipelineContext:
    """Contexto compartilhado entre estágios do pipeline."""

    pipeline_id: str
    session_id: Optional[str] = None
    data_source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)

    def get_metric(self, key: str, default: Any = None) -> Any:
        """Obter métrica do contexto."""
        return self.metrics.get(key, default)

    def set_metric(self, key: str, value: Any) -> None:
        """Definir métrica no contexto."""
        self.metrics[key] = value

    def increment_metric(self, key: str, value: Union[int, float] = 1) -> None:
        """Incrementar métrica numérica."""
        current = self.metrics.get(key, 0)
        self.metrics[key] = current + value


@dataclass
class StageResult:
    """Resultado da execução de um estágio."""

    stage_name: str
    status: StageStatus
    duration: float
    input_records: int
    output_records: int
    data: Any = None
    error: Optional[Exception] = None
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Verificar se estágio foi executado com sucesso."""
        return self.status == StageStatus.COMPLETED

    @property
    def data_loss_ratio(self) -> float:
        """Calcular taxa de perda de dados."""
        if self.input_records == 0:
            return 0.0
        return 1.0 - (self.output_records / self.input_records)


@dataclass
class PipelineResult:
    """Resultado completo da execução do pipeline."""

    pipeline_id: str
    total_duration: float
    status: StageStatus
    stage_results: List[StageResult] = field(default_factory=list)
    final_data: Any = None
    context: Optional[PipelineContext] = None

    @property
    def success(self) -> bool:
        """Verificar se pipeline foi executado com sucesso."""
        return self.status == StageStatus.COMPLETED

    @property
    def total_input_records(self) -> int:
        """Total de registros de entrada."""
        return self.stage_results[0].input_records if self.stage_results else 0

    @property
    def total_output_records(self) -> int:
        """Total de registros de saída."""
        return self.stage_results[-1].output_records if self.stage_results else 0

    @property
    def failed_stages(self) -> List[StageResult]:
        """Estágios que falharam."""
        return [stage for stage in self.stage_results if not stage.success]


class DataTransformer(ABC):
    """Classe base para transformadores de dados."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def transform(self, data: Any, context: PipelineContext) -> Any:
        """Transformar dados."""

    def validate_input(self, data: Any) -> bool:
        """Validar dados de entrada."""
        return data is not None

    def get_metrics(self, input_data: Any, output_data: Any) -> Dict[str, Any]:
        """Obter métricas da transformação."""
        metrics = {}

        # Métricas básicas baseadas no tipo de dados
        if isinstance(input_data, pd.DataFrame):
            metrics["input_rows"] = len(input_data)
            metrics["input_cols"] = len(input_data.columns)

        if isinstance(output_data, pd.DataFrame):
            metrics["output_rows"] = len(output_data)
            metrics["output_cols"] = len(output_data.columns)

            if isinstance(input_data, pd.DataFrame):
                metrics["rows_changed"] = len(output_data) - len(input_data)
                metrics["cols_changed"] = len(output_data.columns) - len(input_data.columns)

        return metrics


class FilterTransformer(DataTransformer):
    """Transformador para filtrar dados."""

    def __init__(self, name: str, condition: Callable[[Any], bool]):
        super().__init__(name)
        self.condition = condition

    def transform(self, data: Any, context: PipelineContext) -> Any:
        """Aplicar filtro aos dados."""
        if isinstance(data, pd.DataFrame):
            # Aplicar filtro usando query ou condição
            if callable(self.condition):
                mask = data.apply(self.condition, axis=1)
                return data[mask]
            else:
                return data.query(str(self.condition))
        elif isinstance(data, list):
            return [item for item in data if self.condition(item)]
        else:
            return data if self.condition(data) else None


class MapTransformer(DataTransformer):
    """Transformador para mapear/modificar dados."""

    def __init__(self, name: str, mapping_func: Callable[[Any], Any]):
        super().__init__(name)
        self.mapping_func = mapping_func

    def transform(self, data: Any, context: PipelineContext) -> Any:
        """Aplicar função de mapeamento."""
        if isinstance(data, pd.DataFrame):
            return data.apply(self.mapping_func, axis=1)
        elif isinstance(data, list):
            return [self.mapping_func(item) for item in data]
        else:
            return self.mapping_func(data)


class AggregateTransformer(DataTransformer):
    """Transformador para agregação de dados."""

    def __init__(self, name: str, group_by: List[str], agg_funcs: Dict[str, Union[str, List[str]]]):
        super().__init__(name)
        self.group_by = group_by
        self.agg_funcs = agg_funcs

    def transform(self, data: Any, context: PipelineContext) -> Any:
        """Aplicar agregação."""
        if isinstance(data, pd.DataFrame):
            return data.groupby(self.group_by).agg(self.agg_funcs)
        else:
            raise ValueError("Agregação só suportada para DataFrames")


class ValidationTransformer(DataTransformer):
    """Transformador para validação de dados."""

    def __init__(self, name: str, validators: Dict[str, Callable[[Any], bool]]):
        super().__init__(name)
        self.validators = validators

    def transform(self, data: Any, context: PipelineContext) -> Any:
        """Validar dados e marcar problemas."""
        if isinstance(data, pd.DataFrame):
            validation_results = {}

            for column, validator in self.validators.items():
                if column in data.columns:
                    try:
                        validation_results[f"{column}_valid"] = data[column].apply(validator)
                    except Exception as e:
                        logger.warning(f"Erro na validação da coluna {column}: {e}")
                        validation_results[f"{column}_valid"] = False

            # Adicionar colunas de validação ao DataFrame
            for col, results in validation_results.items():
                data[col] = results

            return data
        else:
            # Para outros tipos, aplicar validações disponíveis
            for name, validator in self.validators.items():
                try:
                    if not validator(data):
                        context.set_metric(f"validation_failed_{name}", True)
                except:
                    pass

            return data


class CleaningTransformer(DataTransformer):
    """Transformador para limpeza de dados."""

    def __init__(self, name: str, clean_nulls: bool = True, remove_duplicates: bool = True):
        super().__init__(name)
        self.clean_nulls = clean_nulls
        self.remove_duplicates = remove_duplicates

    def transform(self, data: Any, context: PipelineContext) -> Any:
        """Limpar dados."""
        if isinstance(data, pd.DataFrame):
            cleaned = data.copy()

            if self.clean_nulls:
                null_count = cleaned.isnull().sum().sum()
                cleaned = cleaned.dropna()
                context.set_metric("nulls_removed", null_count)

            if self.remove_duplicates:
                original_count = len(cleaned)
                cleaned = cleaned.drop_duplicates()
                duplicates_removed = original_count - len(cleaned)
                context.set_metric("duplicates_removed", duplicates_removed)

            return cleaned
        else:
            return data


class NormalizationTransformer(DataTransformer):
    """Transformador para normalização de dados."""

    def __init__(self, name: str, numeric_columns: List[str] = None, method: str = "minmax"):
        super().__init__(name)
        self.numeric_columns = numeric_columns or []
        self.method = method

    def transform(self, data: Any, context: PipelineContext) -> Any:
        """Normalizar dados numéricos."""
        if isinstance(data, pd.DataFrame):
            normalized = data.copy()

            # Determinar colunas numéricas se não especificado
            if not self.numeric_columns:
                self.numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()

            for column in self.numeric_columns:
                if column in normalized.columns:
                    try:
                        if self.method == "minmax":
                            min_val = normalized[column].min()
                            max_val = normalized[column].max()
                            if max_val != min_val:
                                normalized[column] = (normalized[column] - min_val) / (
                                    max_val - min_val
                                )
                        elif self.method == "zscore":
                            mean_val = normalized[column].mean()
                            std_val = normalized[column].std()
                            if std_val != 0:
                                normalized[column] = (normalized[column] - mean_val) / std_val
                    except Exception as e:
                        logger.warning(f"Erro na normalização da coluna {column}: {e}")

            return normalized
        else:
            return data


class PipelineStage:
    """Estágio individual do pipeline de dados."""

    def __init__(
        self,
        name: str,
        transformer: DataTransformer,
        required: bool = True,
        parallel: bool = False,
        timeout: Optional[float] = None,
    ):
        self.name = name
        self.transformer = transformer
        self.required = required
        self.parallel = parallel
        self.timeout = timeout

    def execute(self, data: Any, context: PipelineContext) -> StageResult:
        """Executar o estágio."""
        start_time = time.time()
        input_count = self._count_records(data)

        try:
            logger.debug(f"Executando estágio: {self.name}")

            # Validar entrada
            if not self.transformer.validate_input(data):
                raise ValueError(f"Dados de entrada inválidos para estágio {self.name}")

            # Executar transformação
            result_data = self.transformer.transform(data, context)
            output_count = self._count_records(result_data)

            # Obter métricas da transformação
            transform_metrics = self.transformer.get_metrics(data, result_data)

            duration = time.time() - start_time

            return StageResult(
                stage_name=self.name,
                status=StageStatus.COMPLETED,
                duration=duration,
                input_records=input_count,
                output_records=output_count,
                data=result_data,
                metrics=transform_metrics,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Erro no estágio {self.name}: {e}")

            return StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                duration=duration,
                input_records=input_count,
                output_records=0,
                error=e,
            )

    def _count_records(self, data: Any) -> int:
        """Contar registros nos dados."""
        if data is None:
            return 0
        elif isinstance(data, pd.DataFrame):
            return len(data)
        elif isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return len(data)
        else:
            return 1


class DataPipeline:
    """Pipeline principal de processamento de dados."""

    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        self.stages: List[PipelineStage] = []
        self.context = PipelineContext(pipeline_id=pipeline_id)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Registrar transformadores comuns
        self._register_common_transformers()

        logger.info(f"DataPipeline criado: {pipeline_id}")

    def add_stage(self, stage: PipelineStage) -> "DataPipeline":
        """Adicionar estágio ao pipeline."""
        self.stages.append(stage)
        logger.debug(f"Estágio adicionado ao pipeline {self.pipeline_id}: {stage.name}")
        return self

    def add_filter(
        self, name: str, condition: Callable[[Any], bool], required: bool = True
    ) -> "DataPipeline":
        """Adicionar estágio de filtro."""
        transformer = FilterTransformer(name, condition)
        stage = PipelineStage(name, transformer, required)
        return self.add_stage(stage)

    def add_map(
        self, name: str, mapping_func: Callable[[Any], Any], required: bool = True
    ) -> "DataPipeline":
        """Adicionar estágio de mapeamento."""
        transformer = MapTransformer(name, mapping_func)
        stage = PipelineStage(name, transformer, required)
        return self.add_stage(stage)

    def add_validation(
        self, name: str, validators: Dict[str, Callable[[Any], bool]], required: bool = False
    ) -> "DataPipeline":
        """Adicionar estágio de validação."""
        transformer = ValidationTransformer(name, validators)
        stage = PipelineStage(name, transformer, required)
        return self.add_stage(stage)

    def add_cleaning(
        self,
        name: str = "data_cleaning",
        clean_nulls: bool = True,
        remove_duplicates: bool = True,
        required: bool = True,
    ) -> "DataPipeline":
        """Adicionar estágio de limpeza."""
        transformer = CleaningTransformer(name, clean_nulls, remove_duplicates)
        stage = PipelineStage(name, transformer, required)
        return self.add_stage(stage)

    def add_normalization(
        self,
        name: str = "data_normalization",
        numeric_columns: List[str] = None,
        method: str = "minmax",
        required: bool = False,
    ) -> "DataPipeline":
        """Adicionar estágio de normalização."""
        transformer = NormalizationTransformer(name, numeric_columns, method)
        stage = PipelineStage(name, transformer, required)
        return self.add_stage(stage)

    def execute(self, input_data: Any) -> PipelineResult:
        """Executar pipeline completo."""
        start_time = time.time()
        results = []
        current_data = input_data

        try:
            logger.info(f"Executando pipeline: {self.pipeline_id}")

            # Disparar evento de início
            self._emit_pipeline_start_event(input_data)

            for stage in self.stages:
                # Executar estágio
                stage_result = stage.execute(current_data, self.context)
                results.append(stage_result)

                # Verificar se estágio foi bem-sucedido
                if not stage_result.success:
                    if stage.required:
                        logger.error(f"Estágio obrigatório falhou: {stage.name}")
                        break
                    else:
                        logger.warning(f"Estágio opcional falhou: {stage.name}")
                        continue

                # Atualizar dados para próximo estágio
                current_data = stage_result.data

                # Atualizar contexto com métricas
                for key, value in stage_result.metrics.items():
                    self.context.set_metric(f"{stage.name}_{key}", value)

            # Determinar status final
            failed_required = [
                r
                for r in results
                if not r.success and any(s.name == r.stage_name and s.required for s in self.stages)
            ]

            final_status = StageStatus.FAILED if failed_required else StageStatus.COMPLETED
            total_duration = time.time() - start_time

            pipeline_result = PipelineResult(
                pipeline_id=self.pipeline_id,
                total_duration=total_duration,
                status=final_status,
                stage_results=results,
                final_data=current_data,
                context=self.context,
            )

            # Disparar evento de conclusão
            self._emit_pipeline_end_event(pipeline_result)

            logger.info(
                f"Pipeline {self.pipeline_id} concluído: {final_status.value} ({total_duration:.2f}s)"
            )

            return pipeline_result

        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(f"Erro no pipeline {self.pipeline_id}: {e}")

            pipeline_result = PipelineResult(
                pipeline_id=self.pipeline_id,
                total_duration=total_duration,
                status=StageStatus.FAILED,
                stage_results=results,
                final_data=None,
                context=self.context,
            )

            # Disparar evento de erro
            self._emit_pipeline_error_event(e)

            return pipeline_result

    def execute_async(self, input_data: Any) -> "PipelineResult":
        """Executar pipeline de forma assíncrona."""
        return asyncio.run(self._execute_async(input_data))

    async def _execute_async(self, input_data: Any) -> PipelineResult:
        """Implementação assíncrona do pipeline."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.execute, input_data)

    def _register_common_transformers(self) -> None:
        """Registrar transformadores comuns."""
        # Pipelines pré-configurados para dados de telemetria

    def _emit_pipeline_start_event(self, input_data: Any) -> None:
        """Disparar evento de início do pipeline."""
        try:
            from .events import DataEvent, event_bus

            event = DataEvent(
                source=f"pipeline_{self.pipeline_id}",
                metadata={
                    "action": "pipeline_start",
                    "input_type": type(input_data).__name__,
                    "stages_count": len(self.stages),
                },
            )

            event_bus.publish_sync(event)
        except Exception as e:
            logger.debug(f"Erro ao disparar evento de início: {e}")

    def _emit_pipeline_end_event(self, result: PipelineResult) -> None:
        """Disparar evento de fim do pipeline."""
        try:
            from .events import DataEvent, event_bus

            event = DataEvent(
                source=f"pipeline_{self.pipeline_id}",
                metadata={
                    "action": "pipeline_completed",
                    "success": result.success,
                    "duration": result.total_duration,
                    "input_records": result.total_input_records,
                    "output_records": result.total_output_records,
                },
            )

            event_bus.publish_sync(event)
        except Exception as e:
            logger.debug(f"Erro ao disparar evento de fim: {e}")

    def _emit_pipeline_error_event(self, error: Exception) -> None:
        """Disparar evento de erro do pipeline."""
        try:
            from .events import ErrorEvent, event_bus

            event = ErrorEvent(
                component=f"pipeline_{self.pipeline_id}",
                error=error,
                error_message=str(error),
                stack_trace=traceback.format_exc(),
            )

            event_bus.publish_sync(event)
        except Exception as e:
            logger.debug(f"Erro ao disparar evento de erro: {e}")


class PipelineBuilder:
    """Builder para construção fluente de pipelines."""

    @staticmethod
    def create(pipeline_id: str) -> DataPipeline:
        """Criar novo pipeline."""
        return DataPipeline(pipeline_id)

    @staticmethod
    def for_csv_import(session_id: str) -> DataPipeline:
        """Criar pipeline para importação CSV."""
        pipeline = DataPipeline(f"csv_import_{session_id}")

        # Estágios padrão para importação CSV
        pipeline.add_validation(
            "validate_required_fields",
            {"TIME": lambda x: pd.notnull(x), "RPM": lambda x: pd.notnull(x) and x >= 0},
        ).add_cleaning("clean_data", clean_nulls=True, remove_duplicates=True).add_filter(
            "filter_valid_rpm", lambda row: 0 <= row["RPM"] <= 20000 if "RPM" in row else True
        ).add_normalization(
            "normalize_sensors", method="minmax", required=False
        )

        return pipeline

    @staticmethod
    def for_analysis(session_id: str) -> DataPipeline:
        """Criar pipeline para análise de dados."""
        pipeline = DataPipeline(f"analysis_{session_id}")

        # Estágios para análise
        pipeline.add_validation(
            "validate_analysis_data",
            {
                "rpm": lambda x: isinstance(x, (int, float)) and x >= 0,
                "timestamp": lambda x: isinstance(x, (int, float)),
            },
        ).add_map(
            "calculate_derived_metrics",
            lambda row: {**row, "power_estimate": row.get("rpm", 0) * row.get("torque", 0) / 5252},
        )

        return pipeline


# Instância global de pipelines
pipeline_registry: Dict[str, DataPipeline] = {}
