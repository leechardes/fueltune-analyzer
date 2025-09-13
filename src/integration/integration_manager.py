"""
FuelTune Integration Manager

Gerenciador principal que coordena todos os sistemas de integração,
orquestrando workflows, eventos, notifications e outros componentes.

Classes:
    IntegrationManager: Gerenciador central
    SystemHealth: Monitor de saúde do sistema
    PerformanceMonitor: Monitor de performance
    SessionManager: Gerenciamento de sessões integradas

Author: FuelTune Development Team
Version: 1.0.0
"""

import atexit
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from .background import task_manager
from .clipboard import clipboard_manager
from .events import event_bus
from .export_import import export_import_manager
from .notifications import (
    notification_system,
    notify_error,
    notify_info,
    notify_warning,
)
from .pipeline import PipelineBuilder
from .plugins import HookPoint, plugin_system
from .workflow import WorkflowContext, workflow_manager

logger = get_logger(__name__)


class SystemStatus(Enum):
    """Status do sistema de integração."""

    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


class ComponentStatus(Enum):
    """Status dos componentes individuais."""

    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class SystemMetrics:
    """Métricas do sistema."""

    uptime_seconds: float = 0.0
    total_workflows: int = 0
    active_workflows: int = 0
    total_events: int = 0
    events_per_minute: float = 0.0
    total_notifications: int = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
        return {
            "uptime_seconds": self.uptime_seconds,
            "uptime_formatted": self._format_uptime(),
            "total_workflows": self.total_workflows,
            "active_workflows": self.active_workflows,
            "total_events": self.total_events,
            "events_per_minute": round(self.events_per_minute, 2),
            "total_notifications": self.total_notifications,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "cpu_usage_percent": round(self.cpu_usage_percent, 2),
        }

    def _format_uptime(self) -> str:
        """Formatar uptime em string legível."""
        delta = timedelta(seconds=int(self.uptime_seconds))
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


@dataclass
class ComponentHealth:
    """Saúde de um componente."""

    name: str
    status: ComponentStatus
    last_check: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    warning_count: int = 0
    uptime_seconds: float = 0.0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "uptime_seconds": self.uptime_seconds,
            "last_error": self.last_error,
            "metadata": self.metadata,
        }


class PerformanceMonitor:
    """Monitor de performance do sistema."""

    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
        self.start_time = time.time()
        self.last_event_count = 0
        self.event_timestamps: List[float] = []
        self._lock = threading.Lock()

        # Thread de coleta de métricas
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self, interval: float = 30.0) -> None:
        """Iniciar monitoramento de performance."""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval,), daemon=True
        )
        self.monitor_thread.start()

        logger.info("Monitor de performance iniciado")

    def stop_monitoring(self) -> None:
        """Parar monitoramento."""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        logger.info("Monitor de performance parado")

    def _monitoring_loop(self, interval: float) -> None:
        """Loop de monitoramento."""
        while self.monitoring:
            try:
                metrics = self.collect_metrics()

                with self._lock:
                    self.metrics_history.append(metrics)
                    if len(self.metrics_history) > self.max_history_size:
                        self.metrics_history = self.metrics_history[-self.max_history_size :]

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Erro no monitoramento de performance: {e}")
                time.sleep(interval)

    def collect_metrics(self) -> SystemMetrics:
        """Coletar métricas atuais do sistema."""
        try:
            current_time = time.time()

            # Métricas básicas
            uptime = current_time - self.start_time

            # Métricas de workflow
            workflow_stats = (
                workflow_manager.get_stats() if hasattr(workflow_manager, "get_stats") else {}
            )

            # Métricas de eventos
            event_stats = event_bus.get_stats()
            current_event_count = event_stats.get("events_published", 0)

            # Calcular eventos por minuto
            self.event_timestamps = [ts for ts in self.event_timestamps if current_time - ts < 60]
            self.event_timestamps.append(current_time)
            events_per_minute = len(self.event_timestamps)

            # Métricas de notificações
            notification_stats = notification_system.get_stats()

            # Métricas de tarefas
            task_stats = task_manager.get_statistics()

            # Métricas de sistema (básicas)
            memory_usage = self._get_memory_usage()
            cpu_usage = self._get_cpu_usage()

            return SystemMetrics(
                uptime_seconds=uptime,
                total_workflows=workflow_stats.get("total_workflows", 0),
                active_workflows=workflow_stats.get("active_workflows", 0),
                total_events=current_event_count,
                events_per_minute=events_per_minute,
                total_notifications=notification_stats.get("total_notifications", 0),
                active_tasks=task_stats.get("active_tasks", 0),
                completed_tasks=task_stats.get("completed_tasks", 0),
                failed_tasks=task_stats.get("failed_tasks", 0),
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
            )

        except Exception as e:
            logger.error(f"Erro ao coletar métricas: {e}")
            return SystemMetrics()

    def _get_memory_usage(self) -> float:
        """Obter uso de memória."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
        except Exception:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Obter uso de CPU."""
        try:
            import psutil

            return psutil.cpu_percent(interval=None)
        except ImportError:
            return 0.0
        except Exception:
            return 0.0

    def get_latest_metrics(self) -> Optional[SystemMetrics]:
        """Obter métricas mais recentes."""
        with self._lock:
            return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_history(self, limit: int = 100) -> List[SystemMetrics]:
        """Obter histórico de métricas."""
        with self._lock:
            return self.metrics_history[-limit:]


class SystemHealth:
    """Monitor de saúde do sistema."""

    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self.system_status = SystemStatus.INITIALIZING
        self.health_checks: Dict[str, callable] = {}
        self._lock = threading.Lock()

        # Registrar verificações de saúde padrão
        self._register_default_health_checks()

    def register_component(self, name: str, health_check: callable = None) -> None:
        """Registrar componente para monitoramento."""
        with self._lock:
            self.components[name] = ComponentHealth(name=name, status=ComponentStatus.HEALTHY)

            if health_check:
                self.health_checks[name] = health_check

        logger.debug(f"Componente registrado para saúde: {name}")

    def update_component_status(
        self,
        name: str,
        status: ComponentStatus,
        error_message: str = None,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Atualizar status de um componente."""
        with self._lock:
            if name not in self.components:
                self.register_component(name)

            component = self.components[name]
            component.status = status
            component.last_check = datetime.now()

            if status == ComponentStatus.ERROR:
                component.error_count += 1
                component.last_error = error_message
            elif status == ComponentStatus.WARNING:
                component.warning_count += 1

            if metadata:
                component.metadata.update(metadata)

        # Atualizar status geral do sistema
        self._update_system_status()

    def check_all_components(self) -> Dict[str, ComponentHealth]:
        """Verificar saúde de todos os componentes."""
        results = {}

        with self._lock:
            components_copy = self.components.copy()
            health_checks_copy = self.health_checks.copy()

        for name, component in components_copy.items():
            try:
                # Executar verificação de saúde se disponível
                if name in health_checks_copy:
                    health_check = health_checks_copy[name]
                    is_healthy = health_check()

                    if is_healthy:
                        self.update_component_status(name, ComponentStatus.HEALTHY)
                    else:
                        self.update_component_status(name, ComponentStatus.ERROR)

                results[name] = self.components[name]

            except Exception as e:
                logger.error(f"Erro na verificação de saúde do componente {name}: {e}")
                self.update_component_status(name, ComponentStatus.ERROR, str(e))
                results[name] = self.components[name]

        return results

    def get_system_status(self) -> SystemStatus:
        """Obter status geral do sistema."""
        return self.system_status

    def get_component_health(self, name: str) -> Optional[ComponentHealth]:
        """Obter saúde de um componente específico."""
        with self._lock:
            return self.components.get(name)

    def get_unhealthy_components(self) -> List[ComponentHealth]:
        """Obter componentes não saudáveis."""
        with self._lock:
            return [
                component
                for component in self.components.values()
                if component.status in [ComponentStatus.ERROR, ComponentStatus.WARNING]
            ]

    def _update_system_status(self) -> None:
        """Atualizar status geral baseado nos componentes."""
        with self._lock:
            error_count = sum(
                1 for comp in self.components.values() if comp.status == ComponentStatus.ERROR
            )
            warning_count = sum(
                1 for comp in self.components.values() if comp.status == ComponentStatus.WARNING
            )

            if error_count > 0:
                if error_count >= len(self.components) // 2:
                    self.system_status = SystemStatus.ERROR
                else:
                    self.system_status = SystemStatus.DEGRADED
            elif warning_count > 0:
                self.system_status = SystemStatus.DEGRADED
            else:
                if self.system_status not in [SystemStatus.SHUTTING_DOWN, SystemStatus.STOPPED]:
                    self.system_status = SystemStatus.RUNNING

    def _register_default_health_checks(self) -> None:
        """Registrar verificações de saúde padrão."""

        def check_event_bus():
            try:
                return hasattr(event_bus, "_subscribers")
            except:
                return False

        def check_notification_system():
            try:
                return notification_system.processing
            except:
                return False

        def check_task_manager():
            try:
                return task_manager.running
            except:
                return False

        def check_workflow_manager():
            try:
                return hasattr(workflow_manager, "workflows")
            except:
                return False

        def check_clipboard_manager():
            try:
                return clipboard_manager.is_available()
            except:
                return False

        # Registrar verificações
        self.health_checks.update(
            {
                "event_bus": check_event_bus,
                "notification_system": check_notification_system,
                "task_manager": check_task_manager,
                "workflow_manager": check_workflow_manager,
                "clipboard_manager": check_clipboard_manager,
            }
        )


class SessionManager:
    """Gerenciador de sessões integrado."""

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_workflows: Dict[str, List[str]] = {}
        self.session_tasks: Dict[str, List[str]] = {}
        self._lock = threading.Lock()

    def create_session(self, session_id: str, metadata: Dict[str, Any] = None) -> bool:
        """Criar nova sessão integrada."""
        with self._lock:
            if session_id in self.active_sessions:
                return False

            self.active_sessions[session_id] = {
                "id": session_id,
                "created_at": datetime.now(),
                "metadata": metadata or {},
                "status": "active",
            }

            self.session_workflows[session_id] = []
            self.session_tasks[session_id] = []

        # Disparar evento
        plugin_system.execute_hook(HookPoint.SESSION_START, session_id=session_id)

        logger.info(f"Sessão criada: {session_id}")
        return True

    def end_session(self, session_id: str) -> bool:
        """Finalizar sessão."""
        with self._lock:
            if session_id not in self.active_sessions:
                return False

            # Cancelar tarefas ativas da sessão
            for task_id in self.session_tasks.get(session_id, []):
                task_manager.cancel_task(task_id)

            # Atualizar status
            self.active_sessions[session_id]["status"] = "completed"
            self.active_sessions[session_id]["ended_at"] = datetime.now()

        # Disparar evento
        plugin_system.execute_hook(HookPoint.SESSION_END, session_id=session_id)

        logger.info(f"Sessão finalizada: {session_id}")
        return True

    def add_workflow_to_session(self, session_id: str, workflow_id: str) -> None:
        """Adicionar workflow à sessão."""
        with self._lock:
            if session_id in self.session_workflows:
                self.session_workflows[session_id].append(workflow_id)

    def add_task_to_session(self, session_id: str, task_id: str) -> None:
        """Adicionar tarefa à sessão."""
        with self._lock:
            if session_id in self.session_tasks:
                self.session_tasks[session_id].append(task_id)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obter informações da sessão."""
        with self._lock:
            session = self.active_sessions.get(session_id)
            if session:
                return {
                    **session,
                    "workflows": self.session_workflows.get(session_id, []),
                    "tasks": self.session_tasks.get(session_id, []),
                }
            return None


class IntegrationManager:
    """Gerenciador central de integração."""

    def __init__(self):
        self.initialized = False
        self.start_time = time.time()

        # Componentes principais
        self.workflow_manager = workflow_manager
        self.event_bus = event_bus
        self.clipboard_manager = clipboard_manager
        self.notification_system = notification_system
        self.export_import_manager = export_import_manager
        self.task_manager = task_manager
        self.plugin_system = plugin_system

        # Sistemas de monitoramento
        self.health_monitor = SystemHealth()
        self.performance_monitor = PerformanceMonitor()
        self.session_manager = SessionManager()

        # Estado
        self._shutdown_hooks: List[callable] = []
        self._lock = threading.Lock()

        logger.info("IntegrationManager instanciado")

    def initialize(self) -> bool:
        """Inicializar todos os sistemas de integração."""
        if self.initialized:
            return True

        try:
            logger.info("Inicializando IntegrationManager...")

            # Registrar componentes no monitor de saúde
            self._register_components()

            # Inicializar plugin system
            self.plugin_system.initialize()

            # Iniciar monitoramento
            self.performance_monitor.start_monitoring()

            # Registrar hooks de finalização
            self._register_shutdown_hooks()

            # Executar hook de inicialização
            self.plugin_system.execute_hook(HookPoint.APPLICATION_STARTUP)

            # Marcar como inicializado
            self.initialized = True
            self.health_monitor.system_status = SystemStatus.RUNNING

            # Verificar saúde inicial
            self.health_monitor.check_all_components()

            # Notificar inicialização
            notify_info("Sistema de integração inicializado com sucesso")

            logger.info("IntegrationManager inicializado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar IntegrationManager: {e}")
            self.health_monitor.system_status = SystemStatus.ERROR
            notify_error(f"Erro na inicialização: {str(e)}")
            return False

    def shutdown(self) -> None:
        """Finalizar todos os sistemas."""
        if not self.initialized:
            return

        logger.info("Finalizando IntegrationManager...")

        # Atualizar status
        self.health_monitor.system_status = SystemStatus.SHUTTING_DOWN

        try:
            # Executar hook de finalização
            self.plugin_system.execute_hook(HookPoint.APPLICATION_SHUTDOWN)

            # Executar hooks personalizados
            for hook in self._shutdown_hooks:
                try:
                    hook()
                except Exception as e:
                    logger.error(f"Erro em shutdown hook: {e}")

            # Finalizar componentes em ordem
            self.performance_monitor.stop_monitoring()
            self.task_manager.stop(timeout=10.0)
            self.plugin_system.shutdown()
            self.notification_system.shutdown()

            # Finalizar event bus por último
            self.event_bus.shutdown()

            self.initialized = False
            self.health_monitor.system_status = SystemStatus.STOPPED

            logger.info("IntegrationManager finalizado")

        except Exception as e:
            logger.error(f"Erro ao finalizar IntegrationManager: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Obter status completo do sistema."""
        metrics = self.performance_monitor.get_latest_metrics()
        health_status = self.health_monitor.get_system_status()
        components = {name: comp.to_dict() for name, comp in self.health_monitor.components.items()}

        # Estatísticas dos subsistemas
        plugin_stats = self.plugin_system.get_system_stats()
        task_stats = self.task_manager.get_statistics()
        notification_stats = self.notification_system.get_stats()
        event_stats = self.event_bus.get_stats()

        return {
            "system_status": health_status.value,
            "uptime_seconds": time.time() - self.start_time,
            "initialized": self.initialized,
            "metrics": metrics.to_dict() if metrics else {},
            "components": components,
            "subsystems": {
                "plugins": plugin_stats,
                "tasks": task_stats,
                "notifications": notification_stats,
                "events": event_stats,
            },
            "active_sessions": len(self.session_manager.active_sessions),
        }

    def run_health_check(self) -> Dict[str, Any]:
        """Executar verificação completa de saúde."""
        logger.info("Executando verificação de saúde...")

        component_health = self.health_monitor.check_all_components()
        unhealthy = self.health_monitor.get_unhealthy_components()

        result = {
            "system_status": self.health_monitor.get_system_status().value,
            "components": {name: comp.to_dict() for name, comp in component_health.items()},
            "unhealthy_count": len(unhealthy),
            "unhealthy_components": [comp.name for comp in unhealthy],
            "check_timestamp": datetime.now().isoformat(),
        }

        # Notificar se há problemas
        if unhealthy:
            notify_warning(
                f"Encontrados {len(unhealthy)} componentes não saudáveis: {', '.join(comp.name for comp in unhealthy)}"
            )
        else:
            notify_info("Verificação de saúde: todos os componentes estão saudáveis")

        return result

    def create_integrated_workflow(
        self, workflow_name: str, session_id: str = None, **context_data
    ) -> str:
        """Criar workflow integrado com todos os sistemas."""

        # Criar contexto do workflow
        workflow_context = WorkflowContext(
            workflow_id=f"integrated_{int(time.time())}", session_id=session_id, **context_data
        )

        # Adicionar à sessão se especificado
        if session_id:
            self.session_manager.add_workflow_to_session(session_id, workflow_context.workflow_id)

        # Executar workflow de forma assíncrona
        def execute_workflow():
            return self.workflow_manager.execute_workflow_sync(workflow_name, workflow_context)

        task_id = self.task_manager.submit_task(
            func=execute_workflow,
            name=f"Workflow: {workflow_name}",
            task_type=task_manager.TaskType.USER_TASK,  # Usar o enum do módulo task_manager
        )

        # Adicionar à sessão
        if session_id:
            self.session_manager.add_task_to_session(session_id, task_id)

        return task_id

    def process_csv_with_pipeline(
        self, file_path: str, vehicle_id: int, session_id: str = None
    ) -> str:
        """Processar CSV usando pipeline integrado."""

        # Criar pipeline para CSV
        pipeline = PipelineBuilder.for_csv_import(session_id or "default")

        # Executar como tarefa em background
        def process_csv():
            # Simular processamento
            import pandas as pd

            # Ler arquivo CSV
            data = pd.read_csv(file_path)

            # Executar pipeline
            result = pipeline.execute(data)

            if result.success:
                # Notificar sucesso
                notify_info(f"CSV processado com sucesso: {result.total_output_records} registros")

                # Disparar evento
                from .events import CSVImportCompletedEvent

                event = CSVImportCompletedEvent(
                    file_path=file_path,
                    session_id=session_id or "default",
                    rows_imported=result.total_output_records,
                )
                self.event_bus.publish_sync(event)

                return {
                    "success": True,
                    "session_id": session_id,
                    "rows_processed": result.total_output_records,
                    "file_path": file_path,
                }
            else:
                notify_error(
                    f"Erro no processamento CSV: {', '.join(r.error for r in result.failed_stages if r.error)}"
                )
                raise Exception("Falha no pipeline de processamento")

        task_id = self.task_manager.submit_task(
            func=process_csv,
            name=f"Processar CSV: {Path(file_path).name}",
            task_type=task_manager.TaskType.CSV_IMPORT,  # Usar o enum do módulo task_manager
        )

        if session_id:
            self.session_manager.add_task_to_session(session_id, task_id)

        return task_id

    def add_shutdown_hook(self, hook: callable) -> None:
        """Adicionar hook de finalização."""
        with self._lock:
            self._shutdown_hooks.append(hook)

    def _register_components(self) -> None:
        """Registrar componentes no monitor de saúde."""
        components = [
            "workflow_manager",
            "event_bus",
            "clipboard_manager",
            "notification_system",
            "export_import_manager",
            "task_manager",
            "plugin_system",
        ]

        for component in components:
            self.health_monitor.register_component(component)

    def _register_shutdown_hooks(self) -> None:
        """Registrar hooks de finalização."""
        # Hook para atexit
        atexit.register(self.shutdown)

        # Comentado: signal handlers não funcionam em threads do Streamlit
        # if hasattr(signal, "SIGTERM"):
        #     signal.signal(signal.SIGTERM, lambda signum, frame: self.shutdown())
        # if hasattr(signal, "SIGINT"):
        #     signal.signal(signal.SIGINT, lambda signum, frame: self.shutdown())


# Instância global do gerenciador de integração
integration_manager = IntegrationManager()


# Função de conveniência para inicialização
def initialize_integration_system() -> bool:
    """Inicializar sistema de integração."""
    return integration_manager.initialize()


# Função de conveniência para finalização
def shutdown_integration_system() -> None:
    """Finalizar sistema de integração."""
    integration_manager.shutdown()
