"""
FuelTune Notification System

Sistema avançado de notificações para comunicação com usuário através de
múltiplos canais: Streamlit, email, sistema operacional e logs.

Classes:
    NotificationSystem: Sistema principal de notificações
    NotificationChannel: Canais de notificação
    NotificationTemplate: Templates de notificação
    NotificationQueue: Fila de notificações

Author: FuelTune Development Team
Version: 1.0.0
"""

import platform
import smtplib
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart as MimeMultipart
from email.mime.text import MIMEText as MimeText
from enum import Enum
from queue import Empty, Queue
from typing import Any, Dict, List, Optional, Set

import streamlit as st

from ..utils.logger import get_logger
from .events import NotificationEvent, event_bus

logger = get_logger(__name__)


class NotificationType(Enum):
    """Tipos de notificação."""

    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"
    SYSTEM = "system"


class NotificationPriority(Enum):
    """Prioridade das notificações."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class NotificationChannel(Enum):
    """Canais de notificação disponíveis."""

    STREAMLIT = "streamlit"
    EMAIL = "email"
    SYSTEM = "system"  # Notificações do OS
    LOG = "log"
    CONSOLE = "console"
    WEBHOOK = "webhook"


@dataclass
class NotificationSettings:
    """Configurações de notificação."""

    # Configurações de email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    sender_email: str = ""
    sender_name: str = "FuelTune Analyzer"

    # Configurações gerais
    enabled_channels: Set[NotificationChannel] = field(
        default_factory=lambda: {NotificationChannel.STREAMLIT, NotificationChannel.LOG}
    )
    max_queue_size: int = 1000
    batch_size: int = 10
    batch_timeout: float = 5.0

    # Configurações por tipo
    type_channels: Dict[NotificationType, Set[NotificationChannel]] = field(default_factory=dict)

    # Configurações de rate limiting
    rate_limit_window: float = 60.0  # janela em segundos
    rate_limit_count: int = 100  # máximo de notificações por janela

    def __post_init__(self):
        """Inicialização das configurações padrão."""
        if not self.type_channels:
            self.type_channels = {
                NotificationType.SUCCESS: {NotificationChannel.STREAMLIT, NotificationChannel.LOG},
                NotificationType.INFO: {NotificationChannel.STREAMLIT, NotificationChannel.LOG},
                NotificationType.WARNING: {NotificationChannel.STREAMLIT, NotificationChannel.LOG},
                NotificationType.ERROR: {
                    NotificationChannel.STREAMLIT,
                    NotificationChannel.EMAIL,
                    NotificationChannel.LOG,
                },
                NotificationType.PROGRESS: {NotificationChannel.STREAMLIT},
                NotificationType.SYSTEM: {NotificationChannel.LOG, NotificationChannel.SYSTEM},
            }


@dataclass
class Notification:
    """Representação de uma notificação."""

    id: str = field(default_factory=lambda: f"notif_{int(time.time() * 1000)}")
    title: str = ""
    message: str = ""
    type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: Set[NotificationChannel] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # Configurações específicas
    duration: float = 5.0  # duração para notificações temporárias
    dismissible: bool = True
    actions: List[Dict[str, Any]] = field(default_factory=list)

    # Status
    sent_channels: Set[NotificationChannel] = field(default_factory=set)
    failed_channels: Set[NotificationChannel] = field(default_factory=set)

    def is_expired(self) -> bool:
        """Verificar se a notificação expirou."""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False

    def mark_sent(self, channel: NotificationChannel) -> None:
        """Marcar canal como enviado."""
        self.sent_channels.add(channel)
        if channel in self.failed_channels:
            self.failed_channels.remove(channel)

    def mark_failed(self, channel: NotificationChannel) -> None:
        """Marcar canal como falhado."""
        self.failed_channels.add(channel)
        if channel in self.sent_channels:
            self.sent_channels.remove(channel)

    def is_complete(self) -> bool:
        """Verificar se notificação foi enviada para todos os canais."""
        return len(self.sent_channels) == len(self.channels)

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value,
            "priority": self.priority.value,
            "channels": [c.value for c in self.channels],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "dismissible": self.dismissible,
            "actions": self.actions,
        }


class NotificationHandler(ABC):
    """Classe base para manipuladores de notificação."""

    def __init__(self, channel: NotificationChannel):
        self.channel = channel
        self.enabled = True

    @abstractmethod
    def send_notification(self, notification: Notification) -> bool:
        """Enviar notificação através do canal."""

    def is_available(self) -> bool:
        """Verificar se o canal está disponível."""
        return self.enabled

    def format_message(self, notification: Notification) -> str:
        """Formatar mensagem para o canal."""
        if notification.title:
            return f"{notification.title}: {notification.message}"
        return notification.message


class StreamlitHandler(NotificationHandler):
    """Handler para notificações Streamlit."""

    def __init__(self):
        super().__init__(NotificationChannel.STREAMLIT)

    def send_notification(self, notification: Notification) -> bool:
        """Enviar notificação via Streamlit."""
        try:
            message = self.format_message(notification)

            # Mapear tipos para funções Streamlit
            if notification.type == NotificationType.SUCCESS:
                st.success(message)
            elif notification.type == NotificationType.ERROR:
                st.error(message)
            elif notification.type == NotificationType.WARNING:
                st.warning(message)
            elif notification.type == NotificationType.PROGRESS:
                # Para notificações de progresso, usar progress bar se disponível
                if "progress" in notification.metadata:
                    progress = notification.metadata["progress"]
                    if "progress_bar" not in st.session_state:
                        st.session_state.progress_bar = st.progress(0)
                    st.session_state.progress_bar.progress(progress / 100.0)
                    st.info(message)
                else:
                    st.info(message)
            else:
                st.info(message)

            return True

        except Exception as e:
            logger.error(f"Erro ao enviar notificação Streamlit: {e}")
            return False


class EmailHandler(NotificationHandler):
    """Handler para notificações por email."""

    def __init__(self, settings: NotificationSettings):
        super().__init__(NotificationChannel.EMAIL)
        self.settings = settings

    def is_available(self) -> bool:
        """Verificar se email está configurado."""
        return (
            super().is_available()
            and bool(self.settings.smtp_username)
            and bool(self.settings.smtp_password)
            and bool(self.settings.sender_email)
        )

    def send_notification(self, notification: Notification) -> bool:
        """Enviar notificação por email."""
        if not self.is_available():
            return False

        try:
            # Obter destinatários dos metadados
            recipients = notification.metadata.get("recipients", [])
            if not recipients:
                # Se não especificado, usar email do remetente
                recipients = [self.settings.sender_email]

            # Criar mensagem
            msg = MimeMultipart()
            msg["From"] = f"{self.settings.sender_name} <{self.settings.sender_email}>"
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = notification.title or f"FuelTune - {notification.type.value.title()}"

            # Corpo do email
            body = self._format_email_body(notification)
            msg.attach(MimeText(body, "html"))

            # Enviar email
            server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
            server.starttls()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email enviado para {len(recipients)} destinatários")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False

    def _format_email_body(self, notification: Notification) -> str:
        """Formatar corpo do email em HTML."""
        color_map = {
            NotificationType.SUCCESS: "#28a745",
            NotificationType.ERROR: "#dc3545",
            NotificationType.WARNING: "#ffc107",
            NotificationType.INFO: "#17a2b8",
            NotificationType.SYSTEM: "#6c757d",
        }

        color = color_map.get(notification.type, "#17a2b8")

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="border-left: 4px solid {color}; padding-left: 20px;">
                <h2 style="color: {color}; margin-top: 0;">
                    {notification.title or f"FuelTune {notification.type.value.title()}"}
                </h2>
                <p style="font-size: 16px; line-height: 1.6;">
                    {notification.message}
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    Enviado em: {notification.timestamp.strftime("%d/%m/%Y %H:%M:%S")}<br>
                    Prioridade: {notification.priority.name}
                </p>
            </div>
        </body>
        </html>
        """

        return html


class SystemHandler(NotificationHandler):
    """Handler para notificações do sistema operacional."""

    def __init__(self):
        super().__init__(NotificationChannel.SYSTEM)
        self.system = platform.system().lower()

    def is_available(self) -> bool:
        """Verificar se notificações do sistema estão disponíveis."""
        if not super().is_available():
            return False

        if self.system == "windows":
            try:
                pass

                return True
            except ImportError:
                return False
        elif self.system == "darwin":  # macOS
            return True
        elif self.system == "linux":
            # Verificar se notify-send está disponível
            try:
                subprocess.run(["which", "notify-send"], check=True, capture_output=True)
                return True
            except subprocess.CalledProcessError:
                return False

        return False

    def send_notification(self, notification: Notification) -> bool:
        """Enviar notificação do sistema."""
        if not self.is_available():
            return False

        try:
            title = notification.title or "FuelTune"
            message = notification.message

            if self.system == "windows":
                return self._send_windows(title, message, notification)
            elif self.system == "darwin":
                return self._send_macos(title, message, notification)
            elif self.system == "linux":
                return self._send_linux(title, message, notification)

            return False

        except Exception as e:
            logger.error(f"Erro ao enviar notificação do sistema: {e}")
            return False

    def _send_windows(self, title: str, message: str, notification: Notification) -> bool:
        """Enviar notificação no Windows."""
        try:
            from win10toast import ToastNotifier

            toaster = ToastNotifier()
            duration = min(int(notification.duration), 60)  # Max 60 segundos

            toaster.show_toast(title=title, msg=message, duration=duration, threaded=True)

            return True
        except Exception as e:
            logger.error(f"Erro na notificação Windows: {e}")
            return False

    def _send_macos(self, title: str, message: str, notification: Notification) -> bool:
        """Enviar notificação no macOS."""
        try:
            subprocess.run(
                ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
                check=True,
            )

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro na notificação macOS: {e}")
            return False

    def _send_linux(self, title: str, message: str, notification: Notification) -> bool:
        """Enviar notificação no Linux."""
        try:
            # Mapear tipos para ícones
            icon_map = {
                NotificationType.SUCCESS: "dialog-information",
                NotificationType.ERROR: "dialog-error",
                NotificationType.WARNING: "dialog-warning",
                NotificationType.INFO: "dialog-information",
            }

            icon = icon_map.get(notification.type, "dialog-information")
            urgency = (
                "critical" if notification.priority == NotificationPriority.URGENT else "normal"
            )

            subprocess.run(
                [
                    "notify-send",
                    "-u",
                    urgency,
                    "-i",
                    icon,
                    "-t",
                    str(int(notification.duration * 1000)),
                    title,
                    message,
                ],
                check=True,
            )

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro na notificação Linux: {e}")
            return False


class LogHandler(NotificationHandler):
    """Handler para log das notificações."""

    def __init__(self):
        super().__init__(NotificationChannel.LOG)

    def send_notification(self, notification: Notification) -> bool:
        """Registrar notificação no log."""
        try:
            message = self.format_message(notification)
            level_map = {
                NotificationType.SUCCESS: "info",
                NotificationType.INFO: "info",
                NotificationType.WARNING: "warning",
                NotificationType.ERROR: "error",
                NotificationType.SYSTEM: "info",
            }

            level = level_map.get(notification.type, "info")
            log_message = f"[NOTIFICATION] {message}"

            if level == "error":
                logger.error(log_message)
            elif level == "warning":
                logger.warning(log_message)
            else:
                logger.info(log_message)

            return True

        except Exception as e:
            logger.error(f"Erro ao registrar notificação no log: {e}")
            return False


class NotificationQueue:
    """Fila de notificações com processamento assíncrono."""

    def __init__(self, max_size: int = 1000):
        self.queue = Queue(maxsize=max_size)
        self.processing = False
        self.processor_thread: Optional[threading.Thread] = None

    def enqueue(self, notification: Notification) -> bool:
        """Adicionar notificação à fila."""
        try:
            self.queue.put_nowait(notification)
            return True
        except:
            logger.warning("Fila de notificações cheia, descartando notificação mais antiga")
            try:
                self.queue.get_nowait()  # Remove a mais antiga
                self.queue.put_nowait(notification)
                return True
            except:
                return False

    def dequeue(self, timeout: float = 1.0) -> Optional[Notification]:
        """Remover notificação da fila."""
        try:
            return self.queue.get(timeout=timeout)
        except Empty:
            return None

    def size(self) -> int:
        """Tamanho da fila."""
        return self.queue.qsize()

    def is_empty(self) -> bool:
        """Verificar se fila está vazia."""
        return self.queue.empty()


class NotificationSystem:
    """Sistema principal de notificações."""

    def __init__(self, settings: Optional[NotificationSettings] = None):
        self.settings = settings or NotificationSettings()
        self.handlers: Dict[NotificationChannel, NotificationHandler] = {}
        self.queue = NotificationQueue(self.settings.max_queue_size)
        self.notification_history: List[Notification] = []
        self.rate_limiter = {}

        # Inicializar handlers
        self._initialize_handlers()

        # Thread de processamento
        self.processing = True
        self.processor_thread = threading.Thread(target=self._process_notifications, daemon=True)
        self.processor_thread.start()

        logger.info("NotificationSystem inicializado")

    def _initialize_handlers(self) -> None:
        """Inicializar handlers de notificação."""
        # Sempre disponível
        self.handlers[NotificationChannel.STREAMLIT] = StreamlitHandler()
        self.handlers[NotificationChannel.LOG] = LogHandler()

        # Opcionais baseados na configuração
        if NotificationChannel.EMAIL in self.settings.enabled_channels:
            email_handler = EmailHandler(self.settings)
            if email_handler.is_available():
                self.handlers[NotificationChannel.EMAIL] = email_handler

        if NotificationChannel.SYSTEM in self.settings.enabled_channels:
            system_handler = SystemHandler()
            if system_handler.is_available():
                self.handlers[NotificationChannel.SYSTEM] = system_handler

        available_channels = [c.value for c in self.handlers.keys()]
        logger.info(f"Canais de notificação disponíveis: {available_channels}")

    def send(
        self,
        message: str,
        type: NotificationType = NotificationType.INFO,
        title: str = "",
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[Set[NotificationChannel]] = None,
        duration: float = 5.0,
        **metadata,
    ) -> str:
        """Enviar notificação."""

        # Verificar rate limiting
        if not self._check_rate_limit():
            logger.warning("Rate limit atingido, ignorando notificação")
            return ""

        # Determinar canais
        if channels is None:
            channels = self.settings.type_channels.get(
                type, {NotificationChannel.STREAMLIT, NotificationChannel.LOG}
            )

        # Filtrar apenas canais disponíveis
        available_channels = channels.intersection(self.handlers.keys())

        # Criar notificação
        notification = Notification(
            title=title,
            message=message,
            type=type,
            priority=priority,
            channels=available_channels,
            duration=duration,
            metadata=metadata,
        )

        # Adicionar à fila
        if self.queue.enqueue(notification):
            logger.debug(f"Notificação adicionada à fila: {notification.id}")
            return notification.id
        else:
            logger.error("Falha ao adicionar notificação à fila")
            return ""

    def send_success(self, message: str, title: str = "Sucesso", **kwargs) -> str:
        """Enviar notificação de sucesso."""
        return self.send(message, NotificationType.SUCCESS, title, **kwargs)

    def send_error(self, message: str, title: str = "Erro", **kwargs) -> str:
        """Enviar notificação de erro."""
        return self.send(
            message, NotificationType.ERROR, title, NotificationPriority.HIGH, **kwargs
        )

    def send_warning(self, message: str, title: str = "Aviso", **kwargs) -> str:
        """Enviar notificação de aviso."""
        return self.send(message, NotificationType.WARNING, title, **kwargs)

    def send_info(self, message: str, title: str = "", **kwargs) -> str:
        """Enviar notificação informativa."""
        return self.send(message, NotificationType.INFO, title, **kwargs)

    def send_progress(
        self, message: str, progress: float, title: str = "Progresso", **kwargs
    ) -> str:
        """Enviar notificação de progresso."""
        kwargs["progress"] = progress
        return self.send(message, NotificationType.PROGRESS, title, **kwargs)

    def _process_notifications(self) -> None:
        """Processar notificações na fila."""
        batch = []
        last_batch_time = time.time()

        while self.processing:
            try:
                # Tentar obter notificação da fila
                notification = self.queue.dequeue(timeout=1.0)

                if notification:
                    if notification.is_expired():
                        continue

                    batch.append(notification)

                # Processar batch se atingiu tamanho ou timeout
                current_time = time.time()
                should_process = len(batch) >= self.settings.batch_size or (
                    batch and current_time - last_batch_time >= self.settings.batch_timeout
                )

                if should_process and batch:
                    self._process_batch(batch)
                    batch.clear()
                    last_batch_time = current_time

            except Exception as e:
                logger.error(f"Erro no processamento de notificações: {e}")
                time.sleep(1)

        # Processar notificações restantes
        if batch:
            self._process_batch(batch)

    def _process_batch(self, notifications: List[Notification]) -> None:
        """Processar lote de notificações."""
        for notification in notifications:
            try:
                self._send_notification(notification)
                self.notification_history.append(notification)

                # Manter histórico limitado
                if len(self.notification_history) > 1000:
                    self.notification_history = self.notification_history[-1000:]

            except Exception as e:
                logger.error(f"Erro ao processar notificação {notification.id}: {e}")

    def _send_notification(self, notification: Notification) -> None:
        """Enviar notificação através dos canais."""
        for channel in notification.channels:
            handler = self.handlers.get(channel)
            if handler and handler.is_available():
                try:
                    success = handler.send_notification(notification)
                    if success:
                        notification.mark_sent(channel)
                    else:
                        notification.mark_failed(channel)
                except Exception as e:
                    logger.error(f"Erro no handler {channel.value}: {e}")
                    notification.mark_failed(channel)

        # Disparar evento de notificação
        self._emit_notification_event(notification)

    def _check_rate_limit(self) -> bool:
        """Verificar rate limiting."""
        now = time.time()
        window_start = now - self.settings.rate_limit_window

        # Limpar entradas antigas
        self.rate_limiter = {
            timestamp: count
            for timestamp, count in self.rate_limiter.items()
            if timestamp > window_start
        }

        # Contar notificações na janela atual
        total_count = sum(self.rate_limiter.values())

        if total_count >= self.settings.rate_limit_count:
            return False

        # Incrementar contador
        minute_key = int(now // 60) * 60
        self.rate_limiter[minute_key] = self.rate_limiter.get(minute_key, 0) + 1

        return True

    def _emit_notification_event(self, notification: Notification) -> None:
        """Disparar evento de notificação."""
        try:
            event = NotificationEvent(
                component="notification_system",
                message=notification.message,
                notification_type=notification.type.value,
                duration=notification.duration,
                metadata={
                    "notification_id": notification.id,
                    "channels": [c.value for c in notification.channels],
                    "priority": notification.priority.value,
                    "sent_channels": [c.value for c in notification.sent_channels],
                    "failed_channels": [c.value for c in notification.failed_channels],
                },
            )

            event_bus.publish_sync(event)
        except Exception as e:
            logger.debug(f"Erro ao disparar evento de notificação: {e}")

    def get_history(
        self, limit: int = 100, type_filter: Optional[NotificationType] = None
    ) -> List[Notification]:
        """Obter histórico de notificações."""
        history = self.notification_history[-limit:]

        if type_filter:
            history = [n for n in history if n.type == type_filter]

        return history

    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do sistema."""
        total = len(self.notification_history)
        by_type = {}
        by_channel = {}

        for notification in self.notification_history[-1000:]:  # Últimas 1000
            # Contar por tipo
            type_name = notification.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

            # Contar por canal
            for channel in notification.sent_channels:
                channel_name = channel.value
                by_channel[channel_name] = by_channel.get(channel_name, 0) + 1

        return {
            "total_notifications": total,
            "queue_size": self.queue.size(),
            "available_channels": [c.value for c in self.handlers.keys()],
            "by_type": by_type,
            "by_channel": by_channel,
            "rate_limiter_status": len(self.rate_limiter),
        }

    def shutdown(self) -> None:
        """Desligar sistema de notificações."""
        logger.info("Desligando NotificationSystem...")

        self.processing = False
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=5)

        # Processar notificações restantes
        remaining = []
        while not self.queue.is_empty():
            notification = self.queue.dequeue(timeout=0.1)
            if notification:
                remaining.append(notification)

        if remaining:
            logger.info(f"Processando {len(remaining)} notificações restantes...")
            self._process_batch(remaining)

        logger.info("NotificationSystem desligado")


# Instância global do sistema de notificações
notification_system = NotificationSystem()

# Conveniência para uso direto
notify = notification_system.send
notify_success = notification_system.send_success
notify_error = notification_system.send_error
notify_warning = notification_system.send_warning
notify_info = notification_system.send_info
notify_progress = notification_system.send_progress
