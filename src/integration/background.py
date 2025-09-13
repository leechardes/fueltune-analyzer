"""
FuelTune Background Tasks

Sistema de tarefas em background com threading, fila de prioridades e
cancelamento para operações longas sem bloquear a interface.

Classes:
    BackgroundTaskManager: Gerenciador principal de tarefas
    Task: Representação de uma tarefa
    TaskQueue: Fila prioritária de tarefas
    WorkerThread: Thread de execução

Author: FuelTune Development Team
Version: 1.0.0
"""

import queue
import threading
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..utils.logger import get_logger
from .events import SystemEvent, event_bus
from .notifications import notify_error, notify_info, notify_progress, notify_success

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Status da execução de tarefas."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Prioridade das tarefas."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskType(Enum):
    """Tipos de tarefas do sistema."""

    CSV_IMPORT = "csv_import"
    DATA_ANALYSIS = "data_analysis"
    EXPORT_DATA = "export_data"
    DATABASE_CLEANUP = "database_cleanup"
    FILE_PROCESSING = "file_processing"
    SYSTEM_MAINTENANCE = "system_maintenance"
    USER_TASK = "user_task"


@dataclass
class TaskResult:
    """Resultado da execução de tarefa."""

    task_id: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    error_message: str = ""
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskProgress:
    """Progresso de execução da tarefa."""

    task_id: str
    progress: float = 0.0  # 0-100
    message: str = ""
    stage: str = ""
    estimated_remaining: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


class Task:
    """Representação de uma tarefa em background."""

    def __init__(
        self,
        task_id: str = None,
        name: str = "",
        func: Callable = None,
        args: tuple = None,
        kwargs: dict = None,
        task_type: TaskType = TaskType.USER_TASK,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        retries: int = 0,
        retry_delay: float = 1.0,
        progress_callback: Optional[Callable[[TaskProgress], None]] = None,
        completion_callback: Optional[Callable[[TaskResult], None]] = None,
        description: str = "",
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name or f"Task_{self.task_id[:8]}"
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.task_type = task_type
        self.priority = priority
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.description = description

        # Estado da execução
        self.status = TaskStatus.PENDING
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.result: Optional[TaskResult] = None
        self.current_retry = 0
        self.cancelled = False

        # Threading
        self._cancel_event = threading.Event()
        self._progress_lock = threading.Lock()
        self.current_progress = TaskProgress(self.task_id)

    def __lt__(self, other: "Task") -> bool:
        """Comparação para fila de prioridade."""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value  # Maior prioridade primeiro
        return self.created_at < other.created_at  # FIFO para mesma prioridade

    def cancel(self) -> bool:
        """Cancelar tarefa."""
        if self.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            self.status = TaskStatus.CANCELLED
            self.cancelled = True
            self._cancel_event.set()
            return True
        elif self.status == TaskStatus.RUNNING:
            self.cancelled = True
            self._cancel_event.set()
            return True
        return False

    def is_cancelled(self) -> bool:
        """Verificar se tarefa foi cancelada."""
        return self.cancelled or self._cancel_event.is_set()

    def update_progress(self, progress: float, message: str = "", stage: str = "") -> None:
        """Atualizar progresso da tarefa."""
        with self._progress_lock:
            self.current_progress.progress = max(0, min(100, progress))
            self.current_progress.message = message
            self.current_progress.stage = stage
            self.current_progress.timestamp = time.time()

        # Chamar callback de progresso
        if self.progress_callback:
            try:
                self.progress_callback(self.current_progress)
            except Exception as e:
                logger.warning(f"Erro no callback de progresso: {e}")

        # Notificar progresso via sistema de notificações
        try:
            notify_progress(
                f"{self.name}: {message}" if message else f"{self.name}: {progress:.1f}%",
                progress,
                title="Progresso da Tarefa",
            )
        except Exception as e:
            logger.debug(f"Erro ao notificar progresso: {e}")

    def get_progress(self) -> TaskProgress:
        """Obter progresso atual."""
        with self._progress_lock:
            return TaskProgress(
                task_id=self.current_progress.task_id,
                progress=self.current_progress.progress,
                message=self.current_progress.message,
                stage=self.current_progress.stage,
                estimated_remaining=self.current_progress.estimated_remaining,
                timestamp=self.current_progress.timestamp,
            )

    @property
    def duration(self) -> float:
        """Duração da execução."""
        if self.started_at is None:
            return 0.0
        end_time = self.completed_at or time.time()
        return end_time - self.started_at

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "description": self.description,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "retries": self.retries,
            "current_retry": self.current_retry,
            "cancelled": self.cancelled,
            "progress": self.current_progress.progress,
        }


class TaskExecutor(ABC):
    """Classe base para executores de tarefas específicas."""

    @abstractmethod
    def execute(self, task: Task) -> TaskResult:
        """Executar tarefa específica."""


class FunctionTaskExecutor(TaskExecutor):
    """Executor para tarefas baseadas em funções."""

    def execute(self, task: Task) -> TaskResult:
        """Executar função da tarefa."""
        try:
            # Verificar cancelamento antes de iniciar
            if task.is_cancelled():
                return TaskResult(
                    task_id=task.task_id, success=False, error_message="Tarefa foi cancelada"
                )

            start_time = time.time()

            # Executar função com timeout se especificado
            if task.timeout:
                # Usar ThreadPoolExecutor para timeout
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(task.func, *task.args, **task.kwargs)

                    try:
                        result = future.result(timeout=task.timeout)
                    except TimeoutError:
                        future.cancel()
                        raise TimeoutError(f"Tarefa excedeu timeout de {task.timeout}s")
            else:
                # Execução normal
                result = task.func(*task.args, **task.kwargs)

            duration = time.time() - start_time

            return TaskResult(task_id=task.task_id, success=True, result=result, duration=duration)

        except Exception as e:
            duration = time.time() - start_time

            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=e,
                error_message=str(e),
                duration=duration,
            )


class WorkerThread:
    """Thread de execução de tarefas."""

    def __init__(self, worker_id: str, task_queue: queue.PriorityQueue):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.current_task: Optional[Task] = None
        self.executor = FunctionTaskExecutor()

        # Estatísticas
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_execution_time = 0.0

    def start(self) -> None:
        """Iniciar worker thread."""
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.debug(f"Worker {self.worker_id} iniciado")

    def stop(self, timeout: float = 5.0) -> None:
        """Parar worker thread."""
        self.running = False

        # Cancelar tarefa atual se existir
        if self.current_task:
            self.current_task.cancel()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
            if self.thread.is_alive():
                logger.warning(f"Worker {self.worker_id} não parou dentro do timeout")

        logger.debug(f"Worker {self.worker_id} parado")

    def _run(self) -> None:
        """Loop principal do worker."""
        while self.running:
            try:
                # Obter próxima tarefa da fila
                try:
                    priority, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                self.current_task = task

                # Verificar se tarefa foi cancelada
                if task.is_cancelled():
                    task.status = TaskStatus.CANCELLED
                    self.task_queue.task_done()
                    continue

                # Executar tarefa
                self._execute_task(task)

                # Marcar tarefa como concluída na fila
                self.task_queue.task_done()
                self.current_task = None

            except Exception as e:
                logger.error(f"Erro no worker {self.worker_id}: {e}")
                if self.current_task:
                    self._handle_task_error(self.current_task, e)
                    self.task_queue.task_done()

    def _execute_task(self, task: Task) -> None:
        """Executar uma tarefa específica."""
        try:
            # Marcar tarefa como executando
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            logger.info(f"Executando tarefa {task.name} ({task.task_id})")

            # Loop de tentativas
            for attempt in range(task.retries + 1):
                task.current_retry = attempt

                if task.is_cancelled():
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = time.time()
                    return

                try:
                    # Executar tarefa
                    result = self.executor.execute(task)
                    task.result = result

                    if result.success:
                        # Sucesso
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = time.time()
                        self.tasks_completed += 1
                        self.total_execution_time += result.duration

                        # Callback de conclusão
                        if task.completion_callback:
                            try:
                                task.completion_callback(result)
                            except Exception as e:
                                logger.warning(f"Erro no callback de conclusão: {e}")

                        # Notificar sucesso
                        notify_success(
                            f"Tarefa concluída: {task.name}", duration=f"{result.duration:.2f}s"
                        )

                        logger.info(
                            f"Tarefa {task.name} concluída com sucesso ({result.duration:.2f}s)"
                        )
                        break

                    else:
                        # Falha - tentar novamente se possível
                        if attempt < task.retries:
                            logger.warning(
                                f"Tarefa {task.name} falhou (tentativa {attempt + 1}/{task.retries + 1}): "
                                f"{result.error_message}"
                            )
                            time.sleep(task.retry_delay)
                            continue
                        else:
                            # Esgotadas todas as tentativas
                            task.status = TaskStatus.FAILED
                            task.completed_at = time.time()
                            self.tasks_failed += 1

                            notify_error(f"Tarefa falhada: {task.name}", error=result.error_message)

                            logger.error(
                                f"Tarefa {task.name} falhada após {task.retries + 1} tentativas"
                            )
                            break

                except Exception as e:
                    if attempt < task.retries:
                        logger.warning(
                            f"Erro na execução da tarefa {task.name} (tentativa {attempt + 1}): {e}"
                        )
                        time.sleep(task.retry_delay)
                        continue
                    else:
                        # Erro final
                        task.status = TaskStatus.FAILED
                        task.completed_at = time.time()
                        task.result = TaskResult(
                            task_id=task.task_id,
                            success=False,
                            error=e,
                            error_message=str(e),
                            duration=time.time() - task.started_at,
                        )
                        self.tasks_failed += 1

                        notify_error(f"Erro na tarefa: {task.name}", error=str(e))
                        logger.error(f"Erro na tarefa {task.name}: {e}")
                        break

        except Exception as e:
            logger.error(f"Erro crítico na execução da tarefa {task.task_id}: {e}")
            self._handle_task_error(task, e)

    def _handle_task_error(self, task: Task, error: Exception) -> None:
        """Tratar erro na tarefa."""
        task.status = TaskStatus.FAILED
        task.completed_at = time.time()
        task.result = TaskResult(
            task_id=task.task_id,
            success=False,
            error=error,
            error_message=str(error),
            duration=task.duration,
        )
        self.tasks_failed += 1

    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do worker."""
        return {
            "worker_id": self.worker_id,
            "running": self.running,
            "current_task": self.current_task.name if self.current_task else None,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_execution_time": self.total_execution_time,
            "avg_execution_time": (
                self.total_execution_time / self.tasks_completed
                if self.tasks_completed > 0
                else 0.0
            ),
        }


class BackgroundTaskManager:
    """Gerenciador principal de tarefas em background."""

    def __init__(self, max_workers: int = 4, max_queue_size: int = 1000):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size

        # Fila de tarefas (prioridade)
        self.task_queue = queue.PriorityQueue(maxsize=max_queue_size)

        # Workers
        self.workers: List[WorkerThread] = []
        self.running = False

        # Registro de tarefas
        self.tasks: Dict[str, Task] = {}
        self.task_history: List[Task] = []
        self.max_history = 1000

        # Estatísticas
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
        }

        logger.info(f"BackgroundTaskManager inicializado com {max_workers} workers")

    def start(self) -> None:
        """Iniciar o gerenciador de tarefas."""
        if self.running:
            return

        self.running = True

        # Criar e iniciar workers
        for i in range(self.max_workers):
            worker = WorkerThread(f"worker_{i}", self.task_queue)
            worker.start()
            self.workers.append(worker)

        logger.info(f"TaskManager iniciado com {len(self.workers)} workers")

    def stop(self, timeout: float = 10.0) -> None:
        """Parar o gerenciador de tarefas."""
        if not self.running:
            return

        logger.info("Parando BackgroundTaskManager...")

        self.running = False

        # Cancelar todas as tarefas pendentes
        pending_tasks = [
            task
            for task in self.tasks.values()
            if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]
        ]
        for task in pending_tasks:
            task.cancel()

        # Parar workers
        for worker in self.workers:
            worker.stop(timeout=timeout / len(self.workers))

        self.workers.clear()

        logger.info("BackgroundTaskManager parado")

    def submit_task(
        self,
        func: Callable,
        args: tuple = None,
        kwargs: dict = None,
        name: str = "",
        task_type: TaskType = TaskType.USER_TASK,
        priority: TaskPriority = TaskPriority.NORMAL,
        **task_options,
    ) -> str:
        """Submeter nova tarefa."""

        if not self.running:
            raise RuntimeError("TaskManager não está executando")

        # Criar tarefa
        task = Task(
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            task_type=task_type,
            priority=priority,
            **task_options,
        )

        # Verificar se fila não está cheia
        if self.task_queue.qsize() >= self.max_queue_size:
            raise RuntimeError("Fila de tarefas está cheia")

        # Adicionar à fila
        task.status = TaskStatus.QUEUED
        self.task_queue.put((priority.value, task))

        # Registrar tarefa
        self.tasks[task.task_id] = task
        self.stats["total_tasks"] += 1

        logger.info(f"Tarefa submetida: {task.name} ({task.task_id})")

        # Notificar
        notify_info(f"Tarefa adicionada à fila: {task.name}")

        # Disparar evento
        self._emit_task_event(task, "task_submitted")

        return task.task_id

    def submit_csv_import(
        self, file_path: str, vehicle_id: int, priority: TaskPriority = TaskPriority.HIGH
    ) -> str:
        """Submeter tarefa de importação CSV."""

        def import_csv():
            # Simular importação CSV
            import time

            task = self.get_task_by_id(threading.current_thread().name)
            if task:
                task.update_progress(25, "Validando arquivo...")
                time.sleep(1)
                task.update_progress(50, "Processando dados...")
                time.sleep(2)
                task.update_progress(75, "Salvando no banco...")
                time.sleep(1)
                task.update_progress(100, "Concluído!")

            return {
                "session_id": f"session_{int(time.time())}",
                "rows_imported": 1000,
                "duration": 4.0,
            }

        return self.submit_task(
            func=import_csv,
            name=f"Importar CSV: {file_path}",
            task_type=TaskType.CSV_IMPORT,
            priority=priority,
            timeout=300.0,  # 5 minutos
            retries=2,
        )

    def submit_analysis(
        self,
        session_id: str,
        analysis_type: str = "full",
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """Submeter tarefa de análise."""

        def analyze_data():
            # Simular análise
            import time

            task = self.get_task_by_id(threading.current_thread().name)
            if task:
                task.update_progress(20, "Carregando dados...")
                time.sleep(1)
                task.update_progress(50, "Calculando métricas...")
                time.sleep(2)
                task.update_progress(80, "Gerando relatório...")
                time.sleep(1)
                task.update_progress(100, "Análise concluída!")

            return {
                "session_id": session_id,
                "analysis_type": analysis_type,
                "results": {"avg_rpm": 3500, "max_power": 250},
            }

        return self.submit_task(
            func=analyze_data,
            name=f"Análise: {session_id}",
            task_type=TaskType.DATA_ANALYSIS,
            priority=priority,
            timeout=600.0,  # 10 minutos
            retries=1,
        )

    def submit_export(
        self, data: Any, format: str, output_path: str, priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """Submeter tarefa de exportação."""

        def export_data():
            # Simular exportação
            import time

            task = self.get_task_by_id(threading.current_thread().name)
            if task:
                task.update_progress(30, "Preparando dados...")
                time.sleep(1)
                task.update_progress(70, "Convertendo formato...")
                time.sleep(1)
                task.update_progress(100, "Exportação concluída!")

            return {"output_path": output_path, "format": format, "file_size": 1024000}

        return self.submit_task(
            func=export_data,
            name=f"Exportar para {format}",
            task_type=TaskType.EXPORT_DATA,
            priority=priority,
            timeout=300.0,
            retries=1,
        )

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Obter tarefa por ID."""
        return self.tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancelar tarefa."""
        task = self.get_task_by_id(task_id)
        if task:
            success = task.cancel()
            if success:
                self.stats["cancelled_tasks"] += 1
                notify_info(f"Tarefa cancelada: {task.name}")
                self._emit_task_event(task, "task_cancelled")
            return success
        return False

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Obter status da tarefa."""
        task = self.get_task_by_id(task_id)
        return task.status if task else None

    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Obter progresso da tarefa."""
        task = self.get_task_by_id(task_id)
        return task.get_progress() if task else None

    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Obter resultado da tarefa."""
        task = self.get_task_by_id(task_id)
        return task.result if task else None

    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """Aguardar conclusão da tarefa."""
        task = self.get_task_by_id(task_id)
        if not task:
            return None

        start_time = time.time()

        while task.status in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]:
            if timeout and (time.time() - start_time) > timeout:
                return None

            time.sleep(0.1)

        return task.result

    def get_active_tasks(self) -> List[Task]:
        """Obter tarefas ativas."""
        return [
            task
            for task in self.tasks.values()
            if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]
        ]

    def get_completed_tasks(self, limit: int = 50) -> List[Task]:
        """Obter tarefas concluídas."""
        completed = [
            task
            for task in self.tasks.values()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        completed.sort(key=lambda t: t.completed_at or 0, reverse=True)
        return completed[:limit]

    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """Limpar tarefas concluídas antigas."""
        cutoff_time = time.time() - (max_age_hours * 3600)

        to_remove = []
        for task_id, task in self.tasks.items():
            if (
                task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_at
                and task.completed_at < cutoff_time
            ):
                to_remove.append(task_id)

        # Mover para histórico antes de remover
        for task_id in to_remove:
            task = self.tasks.pop(task_id)
            self.task_history.append(task)

        # Manter histórico limitado
        if len(self.task_history) > self.max_history:
            self.task_history = self.task_history[-self.max_history :]

        logger.info(f"Limpas {len(to_remove)} tarefas antigas")
        return len(to_remove)

    def get_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas do sistema."""
        active_tasks = len(self.get_active_tasks())

        # Estatísticas por tipo
        by_type = {}
        by_status = {}

        for task in self.tasks.values():
            task_type = task.task_type.value
            task_status = task.status.value

            by_type[task_type] = by_type.get(task_type, 0) + 1
            by_status[task_status] = by_status.get(task_status, 0) + 1

        # Estatísticas dos workers
        worker_stats = [worker.get_stats() for worker in self.workers]

        return {
            "total_tasks": self.stats["total_tasks"],
            "active_tasks": active_tasks,
            "queue_size": self.task_queue.qsize(),
            "workers_count": len(self.workers),
            "running": self.running,
            "by_type": by_type,
            "by_status": by_status,
            "worker_stats": worker_stats,
            "completed_tasks": self.stats["completed_tasks"],
            "failed_tasks": self.stats["failed_tasks"],
            "cancelled_tasks": self.stats["cancelled_tasks"],
        }

    def _emit_task_event(self, task: Task, action: str) -> None:
        """Disparar evento de tarefa."""
        try:
            event = SystemEvent(
                component="background_task_manager",
                metadata={
                    "action": action,
                    "task_id": task.task_id,
                    "task_name": task.name,
                    "task_type": task.task_type.value,
                    "priority": task.priority.value,
                    "status": task.status.value,
                    "duration": task.duration,
                    "progress": task.current_progress.progress,
                },
            )

            event_bus.publish_sync(event)
        except Exception as e:
            logger.debug(f"Erro ao disparar evento de tarefa: {e}")

    def get_queue_info(self) -> Dict[str, Any]:
        """Obter informações da fila."""
        return {
            "size": self.task_queue.qsize(),
            "max_size": self.max_queue_size,
            "full": self.task_queue.full(),
            "empty": self.task_queue.empty(),
        }


# Instância global do gerenciador de tarefas
task_manager = BackgroundTaskManager()

# Auto-inicialização
task_manager.start()
