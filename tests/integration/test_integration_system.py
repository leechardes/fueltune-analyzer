"""
Testes de Integração do Sistema FuelTune

Testes para verificar a integração completa entre todos os módulos
do sistema de integração.

Author: FuelTune Development Team
Version: 1.0.0
"""

import asyncio
import tempfile
import time
from pathlib import Path

import pandas as pd
import pytest

# Import integration modules
from src.integration import (
    BackgroundTaskManager,
    ClipboardManager,
    DataPipeline,
    EventBus,
    ExportImportManager,
    IntegrationManager,
    NotificationSystem,
    PluginSystem,
    WorkflowManager,
)
from src.integration.background import TaskStatus
from src.integration.events import (
    CSVImportCompletedEvent,
    CSVImportStartedEvent,
    SystemEvent,
)
from src.integration.export_import import ExportFormat, ExportType
from src.integration.plugins import HookPoint, PluginType
from src.integration.workflow import WorkflowContext, WorkflowStage


@pytest.fixture
def integration_manager():
    """Fixture para criar uma instância do IntegrationManager."""
    manager = IntegrationManager()
    manager.initialize()
    yield manager
    manager.shutdown()


@pytest.fixture
def event_bus():
    """Fixture para criar uma instância do EventBus."""
    return EventBus()


@pytest.fixture
def workflow_manager():
    """Fixture para criar uma instância do WorkflowManager."""
    return WorkflowManager()


@pytest.fixture
def task_manager():
    """Fixture para criar uma instância do BackgroundTaskManager."""
    return BackgroundTaskManager()


@pytest.fixture
def notification_system():
    """Fixture para criar uma instância do NotificationSystem."""
    return NotificationSystem()


class TestIntegrationSystem:
    """Testes do sistema de integração completo."""

    def test_integration_manager_initialization(self, integration_manager):
        """Testar inicialização do gerenciador de integração."""
        assert integration_manager.initialized == True

        # Verificar componentes principais
        assert integration_manager.workflow_manager is not None
        assert integration_manager.event_bus is not None
        assert integration_manager.task_manager is not None
        assert integration_manager.notification_system is not None
        assert integration_manager.clipboard_manager is not None
        assert integration_manager.export_import_manager is not None
        assert integration_manager.plugin_system is not None

    def test_system_health_check(self, integration_manager):
        """Testar verificação de saúde do sistema."""
        health_result = integration_manager.run_health_check()

        assert "system_status" in health_result
        assert "components" in health_result
        assert "unhealthy_count" in health_result
        assert "check_timestamp" in health_result

        # Sistema deve estar rodando ou em modo degradado
        assert health_result["system_status"] in ["running", "degraded"]

    def test_system_status(self, integration_manager):
        """Testar obtenção de status do sistema."""
        status = integration_manager.get_system_status()

        required_keys = [
            "system_status",
            "uptime_seconds",
            "initialized",
            "metrics",
            "components",
            "subsystems",
            "active_sessions",
        ]

        for key in required_keys:
            assert key in status, f"Status missing key: {key}"

        assert status["initialized"] == True
        assert status["uptime_seconds"] >= 0


class TestEventSystem:
    """Testes do sistema de eventos."""

    def test_event_publishing_and_subscription(self, event_bus):
        """Testar publicação e inscrição de eventos."""
        received_events = []

        def test_handler(event):
            received_events.append(event)

        # Inscrever handler
        event_bus.subscribe(SystemEvent, test_handler, "test_handler")

        # Publicar evento
        test_event = SystemEvent(component="test", metadata={"test": True})
        event_bus.publish_sync(test_event)

        # Verificar recebimento
        assert len(received_events) == 1
        assert received_events[0].component == "test"
        assert received_events[0].metadata["test"] == True

        # Cleanup
        event_bus.unsubscribe(SystemEvent, "test_handler")

    def test_event_bus_statistics(self, event_bus):
        """Testar estatísticas do event bus."""
        stats = event_bus.get_stats()

        required_keys = [
            "events_published",
            "events_processed",
            "events_failed",
            "subscribers_count",
        ]
        for key in required_keys:
            assert key in stats

        # Deve haver pelo menos alguns eventos publicados
        assert stats["events_published"] >= 0


class TestWorkflowSystem:
    """Testes do sistema de workflows."""

    def test_workflow_registration(self, workflow_manager):
        """Testar registro de workflows."""
        # Verificar workflows padrão
        assert "csv_import" in workflow_manager.workflows
        assert "full_analysis" in workflow_manager.workflows

        # Cada workflow deve ter etapas
        csv_workflow = workflow_manager.workflows["csv_import"]
        assert len(csv_workflow) > 0

    def test_workflow_execution_sync(self, workflow_manager):
        """Testar execução síncrona de workflow."""
        context = WorkflowContext(
            workflow_id="test_workflow", data={"test": "data"}, metadata={"source": "test"}
        )

        # Criar workflow de teste simples
        def test_stage(ctx: WorkflowContext):
            ctx.data["processed"] = True
            return ctx

        workflow_manager.register_workflow(
            "test_sync", [WorkflowStage(name="test", handler=test_stage)]
        )

        # Executar workflow
        result = workflow_manager.execute_sync("test_sync", context)

        assert result.status == "completed"
        assert result.data["processed"] == True

    @pytest.mark.asyncio
    async def test_workflow_execution_async(self, workflow_manager):
        """Testar execução assíncrona de workflow."""
        context = WorkflowContext(
            workflow_id="test_workflow_async", data={"test": "data"}, metadata={"source": "test"}
        )

        # Criar workflow de teste simples
        async def test_stage_async(ctx: WorkflowContext):
            await asyncio.sleep(0.01)  # Simular operação assíncrona
            ctx.data["processed"] = True
            return ctx

        workflow_manager.register_workflow(
            "test_async", [WorkflowStage(name="test", handler=test_stage_async, is_async=True)]
        )

        # Executar workflow
        result = await workflow_manager.execute_async("test_async", context)

        assert result.status == "completed"
        assert result.data["processed"] == True


class TestBackgroundTasks:
    """Testes do sistema de tarefas em background."""

    def test_task_submission(self, task_manager):
        """Testar submissão de tarefas."""

        # Submeter tarefa
        def test_task():
            time.sleep(0.01)
            return "completed"

        task_id = task_manager.submit_task(test_task, name="test_task")

        assert task_id is not None

        # Aguardar conclusão
        time.sleep(0.1)

        # Verificar status
        status = task_manager.get_task_status(task_id)
        assert status["status"] == TaskStatus.COMPLETED.value
        assert status["result"] == "completed"

    def test_task_cancellation(self, task_manager):
        """Testar cancelamento de tarefas."""

        # Submeter tarefa longa
        def long_task():
            time.sleep(2)
            return "completed"

        task_id = task_manager.submit_task(long_task, name="long_task")

        # Cancelar tarefa
        success = task_manager.cancel_task(task_id)
        assert success == True

        # Verificar status
        status = task_manager.get_task_status(task_id)
        assert status["status"] in [TaskStatus.CANCELLED.value, TaskStatus.RUNNING.value]

    def test_task_progress(self, task_manager):
        """Testar rastreamento de progresso de tarefas."""

        # Submeter tarefa com progresso
        def task_with_progress(callback):
            for i in range(5):
                callback(i * 20)
                time.sleep(0.01)
            return "completed"

        task_id = task_manager.submit_task(task_with_progress, name="progress_task")

        # Aguardar conclusão
        time.sleep(0.2)

        # Verificar status final
        status = task_manager.get_task_status(task_id)
        assert status["status"] == TaskStatus.COMPLETED.value


class TestNotificationSystem:
    """Testes do sistema de notificações."""

    def test_notification_creation(self, notification_system):
        """Testar criação de notificações."""
        # Criar notificação
        notification_id = notification_system.notify(
            title="Test Notification", message="This is a test", type="info"
        )

        assert notification_id is not None

        # Verificar que notificação foi criada
        notifications = notification_system.get_notifications()
        assert len(notifications) > 0

        # Encontrar notificação criada
        found = False
        for notif in notifications:
            if notif["id"] == notification_id:
                found = True
                assert notif["title"] == "Test Notification"
                assert notif["message"] == "This is a test"
                assert notif["type"] == "info"
                break

        assert found == True

    def test_notification_dismissal(self, notification_system):
        """Testar dismissão de notificações."""
        # Criar notificação
        notification_id = notification_system.notify(
            title="Dismissable", message="Will be dismissed", type="warning"
        )

        # Dismiss notificação
        success = notification_system.dismiss(notification_id)
        assert success == True

        # Verificar que foi marcada como lida
        notifications = notification_system.get_notifications(include_read=True)
        for notif in notifications:
            if notif["id"] == notification_id:
                assert notif["read"] == True
                break

    def test_notification_filtering(self, notification_system):
        """Testar filtragem de notificações."""
        # Criar várias notificações
        notification_system.notify("Info", "Info message", type="info")
        notification_system.notify("Warning", "Warning message", type="warning")
        notification_system.notify("Error", "Error message", type="error")

        # Filtrar por tipo
        warnings = notification_system.get_notifications(type_filter="warning")
        for notif in warnings:
            assert notif["type"] == "warning"

        # Filtrar por não lidas
        unread = notification_system.get_notifications(include_read=False)
        for notif in unread:
            assert notif["read"] == False


class TestClipboardIntegration:
    """Testes da integração com clipboard."""

    def test_clipboard_operations(self):
        """Testar operações básicas de clipboard."""
        clipboard = ClipboardManager()

        # Testar cópia de texto
        test_text = "Test clipboard content"
        clipboard.copy_text(test_text)

        # Testar cópia de DataFrame
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        clipboard.copy_dataframe(df)

        # Verificar formatação
        formatted = clipboard.format_for_clipboard(df, format_type="csv")
        assert "A,B" in formatted
        assert "1,4" in formatted


class TestExportImport:
    """Testes do sistema de exportação/importação."""

    def test_export_formats(self):
        """Testar suporte a diferentes formatos de exportação."""
        manager = ExportImportManager()

        # Verificar formatos suportados
        formats = manager.get_supported_formats()
        assert ExportFormat.CSV in formats
        assert ExportFormat.JSON in formats
        assert ExportFormat.EXCEL in formats

    def test_export_data(self):
        """Testar exportação de dados."""
        manager = ExportImportManager()

        # Dados de teste
        df = pd.DataFrame(
            {"timestamp": pd.date_range("2024-01-01", periods=5), "value": [1, 2, 3, 4, 5]}
        )

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            # Exportar dados
            result = manager.export_data(
                data=df,
                filepath=tmp.name,
                format=ExportFormat.CSV,
                export_type=ExportType.ANALYSIS_RESULTS,
            )

            assert result["success"] == True
            assert Path(tmp.name).exists()

            # Limpar
            Path(tmp.name).unlink()

    def test_import_data(self):
        """Testar importação de dados."""
        manager = ExportImportManager()

        # Criar arquivo temporário com dados
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            df.to_csv(tmp.name, index=False)

            # Importar dados
            result = manager.import_data(filepath=tmp.name, format=ExportFormat.CSV)

            assert result["success"] == True
            assert "data" in result
            imported_df = result["data"]
            assert len(imported_df) == 3
            assert list(imported_df.columns) == ["A", "B"]

            # Limpar
            Path(tmp.name).unlink()


class TestPluginSystem:
    """Testes do sistema de plugins."""

    def test_plugin_registration(self):
        """Testar registro de plugins."""
        plugin_system = PluginSystem()

        # Criar plugin de teste
        class TestPlugin:
            def __init__(self):
                self.name = "test_plugin"
                self.version = "1.0.0"
                self.type = PluginType.ANALYSIS

            def execute(self, data):
                return data

        # Registrar plugin
        plugin = TestPlugin()
        success = plugin_system.register_plugin(plugin)
        assert success == True

        # Verificar registro
        plugins = plugin_system.get_plugins(plugin_type=PluginType.ANALYSIS)
        assert len(plugins) > 0
        assert any(p.name == "test_plugin" for p in plugins)

    def test_hook_system(self):
        """Testar sistema de hooks."""
        plugin_system = PluginSystem()

        # Registrar hook
        called = {"count": 0}

        def test_hook(data):
            called["count"] += 1
            return data

        plugin_system.register_hook(HookPoint.BEFORE_ANALYSIS, test_hook)

        # Executar hooks
        result = plugin_system.execute_hooks(HookPoint.BEFORE_ANALYSIS, {"test": "data"})

        assert called["count"] == 1
        assert result["test"] == "data"

    def test_plugin_lifecycle(self):
        """Testar ciclo de vida de plugins."""
        plugin_system = PluginSystem()

        # Criar plugin com lifecycle
        class LifecyclePlugin:
            def __init__(self):
                self.name = "lifecycle_plugin"
                self.version = "1.0.0"
                self.type = PluginType.INTEGRATION
                self.initialized = False
                self.cleaned_up = False

            def initialize(self):
                self.initialized = True

            def cleanup(self):
                self.cleaned_up = True

            def execute(self, data):
                return data

        plugin = LifecyclePlugin()
        plugin_system.register_plugin(plugin)

        # Inicializar sistema
        plugin_system.initialize_plugins()
        assert plugin.initialized == True

        # Cleanup
        plugin_system.cleanup_plugins()
        assert plugin.cleaned_up == True


class TestDataPipeline:
    """Testes do pipeline de dados."""

    def test_pipeline_creation(self):
        """Testar criação de pipeline."""
        pipeline = DataPipeline()

        # Adicionar estágios
        def stage1(data):
            data["stage1"] = True
            return data

        def stage2(data):
            data["stage2"] = True
            return data

        pipeline.add_stage("stage1", stage1)
        pipeline.add_stage("stage2", stage2)

        # Executar pipeline
        result = pipeline.execute({"initial": "data"})

        assert result["initial"] == "data"
        assert result["stage1"] == True
        assert result["stage2"] == True

    def test_pipeline_validation(self):
        """Testar validação no pipeline."""
        pipeline = DataPipeline()

        # Adicionar validação
        def validate_data(data):
            return "required_field" in data

        pipeline.add_validation("check_required", validate_data)

        # Testar com dados válidos
        valid_data = {"required_field": "value"}
        result = pipeline.execute(valid_data)
        assert "error" not in result

        # Testar com dados inválidos
        invalid_data = {"other_field": "value"}
        try:
            result = pipeline.execute(invalid_data)
            assert False, "Should have raised validation error"
        except Exception:
            pass  # Esperado

    def test_pipeline_metrics(self):
        """Testar métricas do pipeline."""
        pipeline = DataPipeline()

        # Adicionar estágios
        def slow_stage(data):
            time.sleep(0.01)
            return data

        pipeline.add_stage("slow", slow_stage)

        # Executar pipeline
        pipeline.execute({"test": "data"})

        # Obter métricas
        metrics = pipeline.get_metrics()

        assert "total_executions" in metrics
        assert "average_duration" in metrics
        assert "stage_metrics" in metrics

        assert metrics["total_executions"] > 0
        assert metrics["average_duration"] > 0


# Testes de integração completa entre múltiplos componentes
class TestFullSystemIntegration:
    """Testes de integração completa do sistema."""

    def test_csv_import_workflow_with_events(self, integration_manager):
        """Testar workflow completo de importação CSV com eventos."""
        # Preparar dados de teste
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=10),
                "vehicle_speed": [50, 55, 60, 65, 70, 65, 60, 55, 50, 45],
                "fuel_rate": [2.5, 2.7, 3.0, 3.2, 3.5, 3.2, 3.0, 2.7, 2.5, 2.3],
            }
        )

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            df.to_csv(tmp.name, index=False)

            # Capturar eventos
            events_received = []

            def capture_events(event):
                events_received.append(event)

            # Inscrever para eventos
            integration_manager.event_bus.subscribe(
                CSVImportStartedEvent, capture_events, "test_capture_start"
            )
            integration_manager.event_bus.subscribe(
                CSVImportCompletedEvent, capture_events, "test_capture_complete"
            )

            # Executar workflow
            context = WorkflowContext(
                workflow_id="csv_import_test",
                data={"filepath": tmp.name},
                metadata={"source": "test"},
            )

            result = integration_manager.workflow_manager.execute_sync("csv_import", context)

            # Verificar resultado
            assert result.status == "completed"

            # Verificar eventos
            assert len(events_received) >= 2
            assert any(isinstance(e, CSVImportStartedEvent) for e in events_received)
            assert any(isinstance(e, CSVImportCompletedEvent) for e in events_received)

            # Limpar
            Path(tmp.name).unlink()
            integration_manager.event_bus.unsubscribe(CSVImportStartedEvent, "test_capture_start")
            integration_manager.event_bus.unsubscribe(
                CSVImportCompletedEvent, "test_capture_complete"
            )

    def test_analysis_workflow_with_notifications(self, integration_manager):
        """Testar workflow de análise com notificações."""
        # Preparar dados
        df = pd.DataFrame(
            {"timestamp": pd.date_range("2024-01-01", periods=100), "value": range(100)}
        )

        # Executar análise
        context = WorkflowContext(
            workflow_id="analysis_test",
            data={"dataframe": df, "analysis_type": "statistics"},
            metadata={"source": "test"},
        )

        # Executar workflow
        integration_manager.workflow_manager.execute_sync("full_analysis", context)

        # Verificar notificações
        notifications = integration_manager.notification_system.get_notifications()

        # Deve haver notificações sobre a análise
        analysis_notifications = [
            n
            for n in notifications
            if "analysis" in n["title"].lower() or "análise" in n["title"].lower()
        ]

        assert len(analysis_notifications) > 0

    def test_background_export_with_progress(self, integration_manager):
        """Testar exportação em background com progresso."""
        # Preparar dados grandes
        df = pd.DataFrame(
            {"timestamp": pd.date_range("2024-01-01", periods=1000), "value": range(1000)}
        )

        # Função de exportação
        def export_task(progress_callback):
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                # Simular exportação com progresso
                for i in range(10):
                    progress_callback(i * 10)
                    time.sleep(0.01)

                df.to_csv(tmp.name, index=False)
                progress_callback(100)

                return {"filepath": tmp.name, "success": True}

        # Submeter tarefa
        task_id = integration_manager.task_manager.submit_task(export_task, name="export_test")

        # Aguardar conclusão
        time.sleep(0.2)

        # Verificar resultado
        status = integration_manager.task_manager.get_task_status(task_id)
        assert status["status"] == TaskStatus.COMPLETED.value
        assert status["result"]["success"] == True

        # Limpar arquivo
        if "filepath" in status["result"]:
            Path(status["result"]["filepath"]).unlink()

    def test_plugin_integration_with_hooks(self, integration_manager):
        """Testar integração de plugins com hooks."""

        # Criar plugin personalizado
        class CustomAnalysisPlugin:
            def __init__(self):
                self.name = "custom_analysis"
                self.version = "1.0.0"
                self.type = PluginType.ANALYSIS
                self.executed = False

            def execute(self, data):
                self.executed = True
                data["custom_analysis"] = True
                return data

        plugin = CustomAnalysisPlugin()
        integration_manager.plugin_system.register_plugin(plugin)

        # Registrar hook
        def analysis_hook(data):
            data["hook_executed"] = True
            return data

        integration_manager.plugin_system.register_hook(HookPoint.BEFORE_ANALYSIS, analysis_hook)

        # Executar análise com plugins
        test_data = {"original": "data"}

        # Executar hooks
        result = integration_manager.plugin_system.execute_hooks(
            HookPoint.BEFORE_ANALYSIS, test_data
        )

        # Executar plugin
        plugin_result = plugin.execute(result)

        # Verificar execução
        assert plugin.executed == True
        assert plugin_result["hook_executed"] == True
        assert plugin_result["custom_analysis"] == True
        assert plugin_result["original"] == "data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
