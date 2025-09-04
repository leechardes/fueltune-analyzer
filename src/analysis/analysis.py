"""
FuelTune Analysis Engine

Motor de análise principal que coordena todos os módulos de análise.

Author: FuelTune Development Team
Version: 1.0.0
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from ..utils.logger import get_logger

# Import all analysis modules
from .anomaly import AnomalyDetector
from .correlation import CorrelationAnalyzer
from .dynamics import VehicleDynamicsAnalyzer
from .fuel_efficiency import FuelEfficiencyAnalyzer
from .performance import PerformanceAnalyzer
from .predictive import PredictiveAnalyzer
from .statistics import StatisticalAnalyzer
from .time_series import TimeSeriesAnalyzer
from .reports import ReportGenerator

logger = get_logger(__name__)


class AnalysisEngine:
    """Motor de análise principal do FuelTune."""

    def __init__(self):
        """Inicializar o motor de análise."""
        self.anomaly_detector = AnomalyDetector()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.dynamics_analyzer = VehicleDynamicsAnalyzer()
        self.fuel_analyzer = FuelEfficiencyAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.predictive_analyzer = PredictiveAnalyzer()
        self.statistics_analyzer = StatisticalAnalyzer()
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.report_generator = ReportGenerator()

        logger.info("Analysis Engine initialized")

    def analyze(
        self, data: pd.DataFrame, analysis_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executar análises selecionadas nos dados.

        Args:
            data: DataFrame com dados de telemetria
            analysis_types: Lista de tipos de análise a executar
                           Se None, executa todas

        Returns:
            Dicionário com resultados de todas as análises
        """
        if analysis_types is None:
            analysis_types = [
                "statistics",
                "anomaly",
                "correlation",
                "dynamics",
                "fuel_efficiency",
                "performance",
                "predictive",
                "time_series",
            ]

        results = {}

        # Executar análises selecionadas
        if "statistics" in analysis_types:
            try:
                results["statistics"] = self.statistics_analyzer.analyze(data)
                logger.info("Statistics analysis completed")
            except Exception as e:
                logger.error(f"Statistics analysis failed: {e}")
                results["statistics"] = {"error": str(e)}

        if "anomaly" in analysis_types:
            try:
                results["anomaly"] = self.anomaly_detector.detect_anomalies(data)
                logger.info("Anomaly detection completed")
            except Exception as e:
                logger.error(f"Anomaly detection failed: {e}")
                results["anomaly"] = {"error": str(e)}

        if "correlation" in analysis_types:
            try:
                results["correlation"] = self.correlation_analyzer.analyze(data)
                logger.info("Correlation analysis completed")
            except Exception as e:
                logger.error(f"Correlation analysis failed: {e}")
                results["correlation"] = {"error": str(e)}

        if "dynamics" in analysis_types:
            try:
                results["dynamics"] = self.dynamics_analyzer.analyze(data)
                logger.info("Dynamics analysis completed")
            except Exception as e:
                logger.error(f"Dynamics analysis failed: {e}")
                results["dynamics"] = {"error": str(e)}

        if "fuel_efficiency" in analysis_types:
            try:
                results["fuel_efficiency"] = self.fuel_analyzer.analyze(data)
                logger.info("Fuel efficiency analysis completed")
            except Exception as e:
                logger.error(f"Fuel efficiency analysis failed: {e}")
                results["fuel_efficiency"] = {"error": str(e)}

        if "performance" in analysis_types:
            try:
                results["performance"] = self.performance_analyzer.analyze(data)
                logger.info("Performance analysis completed")
            except Exception as e:
                logger.error(f"Performance analysis failed: {e}")
                results["performance"] = {"error": str(e)}

        if "predictive" in analysis_types:
            try:
                results["predictive"] = self.predictive_analyzer.analyze(data)
                logger.info("Predictive analysis completed")
            except Exception as e:
                logger.error(f"Predictive analysis failed: {e}")
                results["predictive"] = {"error": str(e)}

        if "time_series" in analysis_types:
            try:
                results["time_series"] = self.time_series_analyzer.analyze(data)
                logger.info("Time series analysis completed")
            except Exception as e:
                logger.error(f"Time series analysis failed: {e}")
                results["time_series"] = {"error": str(e)}

        return results

    def generate_report(self, analysis_results: Dict[str, Any], format: str = "html") -> str:
        """
        Gerar relatório com os resultados das análises.

        Args:
            analysis_results: Resultados das análises
            format: Formato do relatório (html, pdf, markdown)

        Returns:
            Relatório formatado
        """
        return self.report_generator.generate(analysis_results, format=format)

    def quick_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Análise rápida com métricas essenciais.

        Args:
            data: DataFrame com dados

        Returns:
            Dicionário com métricas essenciais
        """
        # Get summary statistics
        stats_summary = {}
        try:
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols[:5]:  # Limit to first 5 columns for quick analysis
                stats_summary[col] = {
                    "mean": data[col].mean(),
                    "std": data[col].std(),
                    "min": data[col].min(),
                    "max": data[col].max(),
                }
        except Exception as e:
            logger.warning(f"Error in summary statistics: {e}")

        return {
            "statistics": stats_summary,
            "anomalies_count": len(
                self.anomaly_detector.detect_anomalies(data).get("anomalies", [])
            ),
            "correlation_matrix": (
                self.correlation_analyzer.get_correlation_matrix(data)
                if hasattr(self.correlation_analyzer, "get_correlation_matrix")
                else {}
            ),
            "fuel_metrics": (
                self.fuel_analyzer.calculate_basic_metrics(data)
                if hasattr(self.fuel_analyzer, "calculate_basic_metrics")
                else {}
            ),
        }

    def validate_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validar dados antes da análise.

        Args:
            data: DataFrame a validar

        Returns:
            Resultado da validação
        """
        validation = {"is_valid": True, "errors": [], "warnings": []}

        # Verificar se há dados
        if data.empty:
            validation["is_valid"] = False
            validation["errors"].append("DataFrame is empty")
            return validation

        # Verificar colunas mínimas necessárias
        required_columns = ["timestamp"]
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            validation["warnings"].append(f"Missing recommended columns: {missing}")

        # Verificar tipos de dados
        if "timestamp" in data.columns:
            try:
                pd.to_datetime(data["timestamp"])
            except:
                validation["warnings"].append("timestamp column is not datetime compatible")

        # Verificar valores nulos
        null_counts = data.isnull().sum()
        if null_counts.any():
            validation["warnings"].append(
                f"Found null values: {null_counts[null_counts > 0].to_dict()}"
            )

        return validation
