"""
FuelTune Integration Module

Este módulo fornece sistemas de integração e orquestração para coordenar
todos os componentes do aplicativo FuelTune Streamlit.

Modules:
    workflow: Sistema de gerenciamento de workflows
    events: Sistema de eventos e comunicação entre módulos
    clipboard: Integração com clipboard do sistema
    pipeline: Pipeline de dados unificado
    notifications: Sistema de notificações
    export_import: Sistema avançado de exportação/importação
    background: Tarefas em background com threading
    plugins: Sistema de plugins/extensões
    ftmanager_bridge: Integração principal com FTManager
    format_detector: Detecção avançada de formatos FTManager
    clipboard_manager: Gerenciador cross-platform de clipboard
    validators: Validadores de compatibilidade FTManager

Author: FuelTune Development Team
Version: 1.0.0
"""

from .background import BackgroundTaskManager, task_manager
from .clipboard import ClipboardManager, clipboard_manager
from .clipboard_manager import ClipboardManager as FTClipboardManager
from .clipboard_manager import ClipboardResult
from .events import EventBus
from .export_import import ExportImportManager, export_import_manager
from .format_detector import DetectionResult, FormatCandidate, FTManagerFormatDetector

# FTManager Integration Components
from .ftmanager_bridge import FTManagerIntegrationBridge, IntegrationResult
from .integration_manager import (
    IntegrationManager,
    initialize_integration_system,
    integration_manager,
    shutdown_integration_system,
)
from .notifications import NotificationSystem, notification_system
from .pipeline import DataPipeline
from .plugins import PluginSystem, plugin_system
from .validators import FTManagerValidator, ValidationIssue, ValidationResult
from .workflow import WorkflowManager, workflow_manager

__all__ = [
    "IntegrationManager",
    "WorkflowManager",
    "EventBus",
    "ClipboardManager",
    "DataPipeline",
    "NotificationSystem",
    "ExportImportManager",
    "BackgroundTaskManager",
    "PluginSystem",
    # FTManager Integration Components
    "FTManagerIntegrationBridge",
    "FTManagerFormatDetector",
    "FTClipboardManager",
    "FTManagerValidator",
    "IntegrationResult",
    "DetectionResult",
    "FormatCandidate",
    "ClipboardResult",
    "ValidationResult",
    "ValidationIssue",
    # Functions
    "initialize_integration_system",
    "shutdown_integration_system",
    # Global instances
    "integration_manager",
    "workflow_manager",
    "clipboard_manager",
    "notification_system",
    "export_import_manager",
    "task_manager",
    "plugin_system",
]

__version__ = "1.0.0"
