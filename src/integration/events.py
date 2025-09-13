"""
FuelTune Event System

Sistema de eventos publish/subscribe para comunicação assíncrona entre módulos
do aplicativo FuelTune Streamlit.

Classes:
    Event: Classe base para eventos
    EventBus: Barramento de eventos central
    EventHandler: Manipulador de eventos base
    EventSubscription: Representação de uma inscrição

Author: FuelTune Development Team
Version: 1.0.0
"""

import asyncio
import inspect
import threading
import time
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
)

from ..utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound="Event")


class EventPriority(Enum):
    """Prioridade dos eventos."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventStatus(Enum):
    """Status do processamento de eventos."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Event:
    """Classe base para todos os eventos do sistema."""

    event_id: str = field(default_factory=lambda: f"evt_{int(time.time() * 1000)}")
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Inicialização pós-criação."""
        if not self.source:
            # Tentar determinar a origem do evento
            frame = inspect.currentframe()
            try:
                while frame:
                    frame = frame.f_back
                    if frame and "self" in frame.f_locals:
                        self.source = frame.f_locals["self"].__class__.__name__
                        break
            finally:
                del frame


# Eventos específicos do sistema


@dataclass
class DataEvent(Event):
    """Evento relacionado a dados."""

    data_type: str = ""
    data_size: int = 0


@dataclass
class CSVImportStartedEvent(DataEvent):
    """Evento disparado quando importação CSV inicia."""

    file_path: str = ""
    vehicle_id: Optional[int] = None


@dataclass
class CSVImportCompletedEvent(DataEvent):
    """Evento disparado quando importação CSV termina."""

    session_id: str = ""
    rows_imported: int = 0
    warnings: List[str] = field(default_factory=list)


@dataclass
class CSVImportFailedEvent(DataEvent):
    """Evento disparado quando importação CSV falha."""

    error_message: str = ""
    file_path: str = ""


@dataclass
class AnalysisStartedEvent(Event):
    """Evento disparado quando análise inicia."""

    session_id: str = ""
    analysis_type: str = ""


@dataclass
class AnalysisCompletedEvent(Event):
    """Evento disparado quando análise termina."""

    session_id: str = ""
    analysis_type: str = ""
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisFailedEvent(Event):
    """Evento disparado quando análise falha."""

    session_id: str = ""
    analysis_type: str = ""
    error_message: str = ""


@dataclass
class UIEvent(Event):
    """Evento relacionado à interface do usuário."""

    component: str = ""
    action: str = ""


@dataclass
class PageChangedEvent(UIEvent):
    """Evento disparado quando página muda."""

    old_page: str = ""
    new_page: str = ""


@dataclass
class VehicleSelectedEvent(UIEvent):
    """Evento disparado quando veículo é selecionado."""

    vehicle_id: int = 0
    vehicle_name: str = ""


@dataclass
class SystemEvent(Event):
    """Evento do sistema."""

    component: str = ""


@dataclass
class ErrorEvent(SystemEvent):
    """Evento de erro do sistema."""

    error: Exception = None
    error_message: str = ""
    stack_trace: str = ""


@dataclass
class NotificationEvent(SystemEvent):
    """Evento de notificação."""

    message: str = ""
    notification_type: str = "info"
    duration: float = 5.0


@dataclass
class EventSubscription:
    """Representa uma inscrição de evento."""

    event_type: Type[Event]
    handler: Callable[[Event], Any]
    subscriber_id: str
    priority: EventPriority = EventPriority.NORMAL
    async_handler: bool = False
    created_at: float = field(default_factory=time.time)


class EventHandler(ABC):
    """Classe base para manipuladores de eventos."""

    def __init__(self, handler_id: str = None):
        self.handler_id = handler_id or f"handler_{id(self)}"
        self.subscriptions: List[EventSubscription] = []

    @abstractmethod
    async def handle_event(self, event: Event) -> Any:
        """Manipular evento. Deve ser implementado pelas subclasses."""

    def subscribe_to(self, event_bus: "EventBus", event_type: Type[Event]) -> None:
        """Inscrever-se em um tipo de evento."""
        subscription = event_bus.subscribe(event_type, self.handle_event, self.handler_id)
        self.subscriptions.append(subscription)

    def unsubscribe_from(self, event_bus: "EventBus", event_type: Type[Event]) -> None:
        """Cancelar inscrição em um tipo de evento."""
        event_bus.unsubscribe(event_type, self.handler_id)
        self.subscriptions = [
            sub
            for sub in self.subscriptions
            if not (sub.event_type == event_type and sub.subscriber_id == self.handler_id)
        ]


class EventBus:
    """Barramento de eventos central do sistema."""

    def __init__(self, max_workers: int = 4):
        self._subscribers: Dict[Type[Event], List[EventSubscription]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "subscribers_count": 0,
        }

        # Sistema de middlewares
        self._middlewares: List[Callable[[Event], Event]] = []

        # Filtros globais
        self._filters: List[Callable[[Event], bool]] = []

        logger.info("EventBus inicializado")

    def add_middleware(self, middleware: Callable[[Event], Event]) -> None:
        """Adicionar middleware para processamento de eventos."""
        self._middlewares.append(middleware)
        logger.debug(f"Middleware adicionado: {middleware.__name__}")

    def add_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """Adicionar filtro global de eventos."""
        self._filters.append(filter_func)
        logger.debug(f"Filtro adicionado: {filter_func.__name__}")

    def subscribe(
        self,
        event_type: Type[Event],
        handler: Callable[[Event], Any],
        subscriber_id: str = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> EventSubscription:
        """Inscrever-se em um tipo de evento."""

        if subscriber_id is None:
            subscriber_id = f"sub_{len(self._subscribers[event_type])}"

        # Verificar se handler é assíncrono
        async_handler = asyncio.iscoroutinefunction(handler)

        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            subscriber_id=subscriber_id,
            priority=priority,
            async_handler=async_handler,
        )

        with self._lock:
            self._subscribers[event_type].append(subscription)
            # Ordenar por prioridade (maior prioridade primeiro)
            self._subscribers[event_type].sort(key=lambda s: s.priority.value, reverse=True)
            self._stats["subscribers_count"] = sum(len(subs) for subs in self._subscribers.values())

        logger.debug(f"Nova inscrição: {subscriber_id} -> {event_type.__name__}")
        return subscription

    def unsubscribe(self, event_type: Type[Event], subscriber_id: str) -> bool:
        """Cancelar inscrição em um tipo de evento."""

        with self._lock:
            if event_type in self._subscribers:
                original_count = len(self._subscribers[event_type])
                self._subscribers[event_type] = [
                    sub
                    for sub in self._subscribers[event_type]
                    if sub.subscriber_id != subscriber_id
                ]
                removed = original_count - len(self._subscribers[event_type])

                if removed > 0:
                    self._stats["subscribers_count"] = sum(
                        len(subs) for subs in self._subscribers.values()
                    )
                    logger.debug(f"Inscrição removida: {subscriber_id} -> {event_type.__name__}")
                    return True

        return False

    def unsubscribe_all(self, subscriber_id: str) -> int:
        """Cancelar todas as inscrições de um subscriber."""

        removed_count = 0
        with self._lock:
            for event_type in list(self._subscribers.keys()):
                original_count = len(self._subscribers[event_type])
                self._subscribers[event_type] = [
                    sub
                    for sub in self._subscribers[event_type]
                    if sub.subscriber_id != subscriber_id
                ]
                removed_count += original_count - len(self._subscribers[event_type])

            self._stats["subscribers_count"] = sum(len(subs) for subs in self._subscribers.values())

        if removed_count > 0:
            logger.info(f"Removidas {removed_count} inscrições do subscriber: {subscriber_id}")

        return removed_count

    async def publish(self, event: Event) -> List[Any]:
        """Publicar um evento para todos os subscribers."""

        # Aplicar middlewares
        processed_event = event
        for middleware in self._middlewares:
            try:
                processed_event = middleware(processed_event)
            except Exception as e:
                logger.error(f"Erro no middleware: {e}")
                continue

        # Aplicar filtros
        for filter_func in self._filters:
            try:
                if not filter_func(processed_event):
                    logger.debug(f"Evento filtrado: {event.event_id}")
                    return []
            except Exception as e:
                logger.error(f"Erro no filtro: {e}")
                continue

        # Adicionar ao histórico
        self._add_to_history(processed_event)

        # Incrementar estatísticas
        with self._lock:
            self._stats["events_published"] += 1

        logger.debug(f"Publicando evento: {event.__class__.__name__} (ID: {event.event_id})")

        # Encontrar subscribers
        event_type = type(processed_event)
        subscribers = []

        with self._lock:
            # Buscar subscribers exatos
            if event_type in self._subscribers:
                subscribers.extend(self._subscribers[event_type])

            # Buscar subscribers de classes pai
            for registered_type, subs in self._subscribers.items():
                if registered_type != event_type and isinstance(processed_event, registered_type):
                    subscribers.extend(subs)

        if not subscribers:
            logger.debug(f"Nenhum subscriber para evento: {event_type.__name__}")
            return []

        # Executar handlers
        results = []
        tasks = []

        for subscription in subscribers:
            try:
                if subscription.async_handler:
                    # Handler assíncrono
                    task = asyncio.create_task(
                        self._execute_async_handler(subscription, processed_event)
                    )
                    tasks.append(task)
                else:
                    # Handler síncrono - executar em thread
                    future = self._executor.submit(
                        self._execute_sync_handler, subscription, processed_event
                    )
                    tasks.append(future)

            except Exception as e:
                logger.error(f"Erro ao executar handler {subscription.subscriber_id}: {e}")
                with self._lock:
                    self._stats["events_failed"] += 1

        # Aguardar todos os handlers
        if tasks:
            for task in tasks:
                try:
                    if asyncio.iscoroutine(task) or hasattr(task, "__await__"):
                        result = await task
                    else:
                        # Future
                        result = task.result(timeout=30)  # Timeout de 30s
                    results.append(result)

                    with self._lock:
                        self._stats["events_processed"] += 1

                except Exception as e:
                    logger.error(f"Erro ao aguardar handler: {e}")
                    with self._lock:
                        self._stats["events_failed"] += 1

        logger.debug(f"Evento processado por {len(results)} handlers")
        return results

    def publish_sync(self, event: Event) -> List[Any]:
        """Publicar evento de forma síncrona."""
        return asyncio.run(self.publish(event))

    async def _execute_async_handler(self, subscription: EventSubscription, event: Event) -> Any:
        """Executar handler assíncrono."""
        try:
            return await subscription.handler(event)
        except Exception as e:
            logger.error(
                f"Erro no handler assíncrono {subscription.subscriber_id}: {e}\n"
                f"{traceback.format_exc()}"
            )
            raise

    def _execute_sync_handler(self, subscription: EventSubscription, event: Event) -> Any:
        """Executar handler síncrono."""
        try:
            return subscription.handler(event)
        except Exception as e:
            logger.error(
                f"Erro no handler síncrono {subscription.subscriber_id}: {e}\n"
                f"{traceback.format_exc()}"
            )
            raise

    def _add_to_history(self, event: Event) -> None:
        """Adicionar evento ao histórico."""
        with self._lock:
            self._event_history.append(event)
            # Manter apenas os últimos N eventos
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history :]

    def get_event_history(self, limit: int = 100, event_type: Type[Event] = None) -> List[Event]:
        """Obter histórico de eventos."""
        with self._lock:
            events = self._event_history[-limit:]

            if event_type:
                events = [e for e in events if isinstance(e, event_type)]

            return events

    def get_subscribers(
        self, event_type: Type[Event] = None
    ) -> Dict[Type[Event], List[EventSubscription]]:
        """Obter lista de subscribers."""
        with self._lock:
            if event_type:
                return {event_type: self._subscribers.get(event_type, [])}
            return dict(self._subscribers)

    def get_stats(self) -> Dict[str, int]:
        """Obter estatísticas do event bus."""
        with self._lock:
            return self._stats.copy()

    def clear_history(self) -> None:
        """Limpar histórico de eventos."""
        with self._lock:
            self._event_history.clear()
        logger.info("Histórico de eventos limpo")

    def shutdown(self) -> None:
        """Desligar o event bus."""
        logger.info("Desligando EventBus...")
        self._executor.shutdown(wait=True)
        self.clear_history()

        with self._lock:
            self._subscribers.clear()
            self._stats["subscribers_count"] = 0

        logger.info("EventBus desligado")


# Handlers específicos do sistema


class LoggingEventHandler(EventHandler):
    """Handler que registra todos os eventos em log."""

    def __init__(self):
        super().__init__("logging_handler")
        self.logger = get_logger(f"{__name__}.LoggingHandler")

    async def handle_event(self, event: Event) -> None:
        """Registrar evento em log."""
        self.logger.info(
            f"Evento: {event.__class__.__name__} " f"(ID: {event.event_id}, Source: {event.source})"
        )


class NotificationEventHandler(EventHandler):
    """Handler que converte eventos em notificações Streamlit."""

    def __init__(self):
        super().__init__("notification_handler")

    async def handle_event(self, event: Event) -> None:
        """Converter evento em notificação."""
        import streamlit as st

        if isinstance(event, CSVImportCompletedEvent):
            st.success(f"Importação concluída: {event.rows_imported} linhas importadas")
        elif isinstance(event, CSVImportFailedEvent):
            st.error(f"Erro na importação: {event.error_message}")
        elif isinstance(event, AnalysisCompletedEvent):
            st.info(f"Análise concluída: {event.analysis_type}")
        elif isinstance(event, AnalysisFailedEvent):
            st.error(f"Erro na análise: {event.error_message}")
        elif isinstance(event, ErrorEvent):
            st.error(f"Erro do sistema: {event.error_message}")
        elif isinstance(event, NotificationEvent):
            if event.notification_type == "error":
                st.error(event.message)
            elif event.notification_type == "warning":
                st.warning(event.message)
            elif event.notification_type == "success":
                st.success(event.message)
            else:
                st.info(event.message)


class MetricsEventHandler(EventHandler):
    """Handler que coleta métricas dos eventos."""

    def __init__(self):
        super().__init__("metrics_handler")
        self.metrics = defaultdict(int)
        self.timing_metrics = defaultdict(list)

    async def handle_event(self, event: Event) -> None:
        """Coletar métricas do evento."""
        event_type = event.__class__.__name__
        self.metrics[event_type] += 1

        # Coletar timing se disponível
        if hasattr(event, "duration"):
            self.timing_metrics[event_type].append(event.duration)

    def get_metrics(self) -> Dict[str, Any]:
        """Obter métricas coletadas."""
        timing_stats = {}
        for event_type, durations in self.timing_metrics.items():
            if durations:
                timing_stats[event_type] = {
                    "count": len(durations),
                    "avg_duration": sum(durations) / len(durations),
                    "max_duration": max(durations),
                    "min_duration": min(durations),
                }

        return {"event_counts": dict(self.metrics), "timing_stats": timing_stats}


# Instância global do event bus
event_bus = EventBus()

# Registrar handlers padrão
logging_handler = LoggingEventHandler()
notification_handler = NotificationEventHandler()
metrics_handler = MetricsEventHandler()

# Inscrever handlers em todos os tipos de eventos
event_bus.subscribe(Event, logging_handler.handle_event, "logging_handler")
event_bus.subscribe(Event, notification_handler.handle_event, "notification_handler")
event_bus.subscribe(Event, metrics_handler.handle_event, "metrics_handler")
