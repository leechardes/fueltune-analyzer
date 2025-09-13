"""
FuelTune Plugin System

Sistema de plugins/extensões para permitir funcionalidades personalizadas
e extensibilidade do aplicativo FuelTune Streamlit.

Classes:
    PluginSystem: Sistema principal de plugins
    Plugin: Classe base para plugins
    PluginManager: Gerenciador de plugins
    PluginRegistry: Registro de plugins
    HookManager: Sistema de hooks

Author: FuelTune Development Team
Version: 1.0.0
"""

import importlib
import importlib.util
import inspect
import json
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from ..utils.logger import get_logger
from .events import SystemEvent, event_bus
from .notifications import notify_error, notify_info

logger = get_logger(__name__)


class PluginStatus(Enum):
    """Status do plugin."""

    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class PluginType(Enum):
    """Tipos de plugins suportados."""

    ANALYSIS = "analysis"  # Plugins de análise personalizada
    EXPORT = "export"  # Plugins de exportação
    IMPORT = "import"  # Plugins de importação
    VISUALIZATION = "visualization"  # Plugins de visualização
    UI_COMPONENT = "ui_component"  # Componentes UI personalizados
    DATA_TRANSFORMER = "data_transformer"  # Transformadores de dados
    NOTIFICATION = "notification"  # Canais de notificação personalizados
    INTEGRATION = "integration"  # Integrações externas
    UTILITY = "utility"  # Utilitários gerais


class HookPoint(Enum):
    """Pontos de hook disponíveis no sistema."""

    # Data processing hooks
    BEFORE_CSV_IMPORT = "before_csv_import"
    AFTER_CSV_IMPORT = "after_csv_import"
    BEFORE_DATA_VALIDATION = "before_data_validation"
    AFTER_DATA_VALIDATION = "after_data_validation"

    # Analysis hooks
    BEFORE_ANALYSIS = "before_analysis"
    AFTER_ANALYSIS = "after_analysis"
    CUSTOM_ANALYSIS_STEP = "custom_analysis_step"

    # UI hooks
    SIDEBAR_EXTENSION = "sidebar_extension"
    MAIN_CONTENT_EXTENSION = "main_content_extension"
    FOOTER_EXTENSION = "footer_extension"

    # Export/Import hooks
    BEFORE_EXPORT = "before_export"
    AFTER_EXPORT = "after_export"
    CUSTOM_EXPORT_FORMAT = "custom_export_format"

    # System hooks
    APPLICATION_STARTUP = "application_startup"
    APPLICATION_SHUTDOWN = "application_shutdown"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


@dataclass
class PluginMetadata:
    """Metadados do plugin."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = ""
    homepage: str = ""
    plugin_type: PluginType = PluginType.UTILITY

    # Dependências
    requires: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    # Compatibilidade
    min_fueltune_version: str = "1.0.0"
    max_fueltune_version: str = ""

    # Configuração
    configurable: bool = False
    config_schema: Dict[str, Any] = field(default_factory=dict)

    # Segurança
    trusted: bool = False
    sandbox: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "homepage": self.homepage,
            "plugin_type": self.plugin_type.value,
            "requires": self.requires,
            "conflicts": self.conflicts,
            "min_fueltune_version": self.min_fueltune_version,
            "max_fueltune_version": self.max_fueltune_version,
            "configurable": self.configurable,
            "config_schema": self.config_schema,
            "trusted": self.trusted,
            "sandbox": self.sandbox,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginMetadata":
        """Criar instância a partir de dicionário."""
        plugin_type = PluginType(data.get("plugin_type", "utility"))

        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", ""),
            homepage=data.get("homepage", ""),
            plugin_type=plugin_type,
            requires=data.get("requires", []),
            conflicts=data.get("conflicts", []),
            min_fueltune_version=data.get("min_fueltune_version", "1.0.0"),
            max_fueltune_version=data.get("max_fueltune_version", ""),
            configurable=data.get("configurable", False),
            config_schema=data.get("config_schema", {}),
            trusted=data.get("trusted", False),
            sandbox=data.get("sandbox", True),
        )


class Plugin(ABC):
    """Classe base para todos os plugins."""

    def __init__(self):
        self.metadata: Optional[PluginMetadata] = None
        self.config: Dict[str, Any] = {}
        self.status = PluginStatus.UNLOADED
        self.error_message = ""
        self._hooks: Dict[HookPoint, List[Callable]] = {}

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Retornar metadados do plugin."""

    def initialize(self) -> bool:
        """Inicializar plugin. Override se necessário."""
        return True

    def shutdown(self) -> bool:
        """Finalizar plugin. Override se necessário."""
        return True

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configurar plugin. Override se necessário."""
        self.config = config.copy()
        return True

    def register_hook(self, hook_point: HookPoint, handler: Callable) -> None:
        """Registrar handler para um hook."""
        if hook_point not in self._hooks:
            self._hooks[hook_point] = []
        self._hooks[hook_point].append(handler)

    def get_hooks(self) -> Dict[HookPoint, List[Callable]]:
        """Obter todos os hooks registrados."""
        return self._hooks.copy()

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validar configuração. Override se necessário."""
        return []  # Sem erros


class AnalysisPlugin(Plugin):
    """Plugin base para análises personalizadas."""

    @abstractmethod
    def analyze(self, data: Any, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Executar análise personalizada."""


class ExportPlugin(Plugin):
    """Plugin base para exportadores personalizados."""

    @abstractmethod
    def export(self, data: Any, output_path: Path, options: Dict[str, Any]) -> bool:
        """Exportar dados no formato personalizado."""

    @abstractmethod
    def get_file_extension(self) -> str:
        """Retornar extensão do arquivo."""


class VisualizationPlugin(Plugin):
    """Plugin base para visualizações personalizadas."""

    @abstractmethod
    def create_visualization(self, data: Any, options: Dict[str, Any]) -> Any:
        """Criar visualização personalizada."""


class UIComponentPlugin(Plugin):
    """Plugin base para componentes UI personalizados."""

    @abstractmethod
    def render_component(self, **kwargs) -> None:
        """Renderizar componente na interface."""


class HookManager:
    """Gerenciador de hooks do sistema."""

    def __init__(self):
        self._hooks: Dict[HookPoint, List[Callable]] = {}
        self._lock = threading.Lock()

    def register_hook(
        self, hook_point: HookPoint, handler: Callable, plugin_name: str = "unknown"
    ) -> None:
        """Registrar hook handler."""
        with self._lock:
            if hook_point not in self._hooks:
                self._hooks[hook_point] = []

            # Adicionar informação do plugin ao handler
            handler._plugin_name = plugin_name
            self._hooks[hook_point].append(handler)

            logger.debug(f"Hook registrado: {hook_point.value} por {plugin_name}")

    def unregister_hook(self, hook_point: HookPoint, plugin_name: str) -> int:
        """Remover hooks de um plugin."""
        with self._lock:
            if hook_point not in self._hooks:
                return 0

            original_count = len(self._hooks[hook_point])
            self._hooks[hook_point] = [
                handler
                for handler in self._hooks[hook_point]
                if getattr(handler, "_plugin_name", "") != plugin_name
            ]

            removed_count = original_count - len(self._hooks[hook_point])
            if removed_count > 0:
                logger.debug(
                    f"Removidos {removed_count} hooks de {plugin_name} para {hook_point.value}"
                )

            return removed_count

    def execute_hook(self, hook_point: HookPoint, *args, **kwargs) -> List[Any]:
        """Executar todos os handlers de um hook."""
        with self._lock:
            handlers = self._hooks.get(hook_point, []).copy()

        results = []

        for handler in handlers:
            try:
                plugin_name = getattr(handler, "_plugin_name", "unknown")
                logger.debug(f"Executando hook {hook_point.value} de {plugin_name}")

                result = handler(*args, **kwargs)
                results.append(result)

            except Exception as e:
                plugin_name = getattr(handler, "_plugin_name", "unknown")
                logger.error(f"Erro no hook {hook_point.value} do plugin {plugin_name}: {e}")

                # Notificar erro
                notify_error(
                    f"Erro no plugin {plugin_name}",
                    error_message=str(e),
                    hook_point=hook_point.value,
                )

        return results

    def get_hook_count(
        self, hook_point: Optional[HookPoint] = None
    ) -> Union[int, Dict[HookPoint, int]]:
        """Obter contagem de hooks."""
        with self._lock:
            if hook_point:
                return len(self._hooks.get(hook_point, []))
            else:
                return {point: len(handlers) for point, handlers in self._hooks.items()}


class PluginRegistry:
    """Registro de plugins disponíveis e carregados."""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
        self._status: Dict[str, PluginStatus] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register_plugin(self, plugin: Plugin) -> bool:
        """Registrar plugin no sistema."""
        try:
            metadata = plugin.get_metadata()

            with self._lock:
                # Verificar se plugin já existe
                if metadata.name in self._plugins:
                    logger.warning(f"Plugin {metadata.name} já está registrado")
                    return False

                # Registrar plugin
                self._plugins[metadata.name] = plugin
                self._metadata[metadata.name] = metadata
                self._status[metadata.name] = PluginStatus.LOADED

                plugin.metadata = metadata
                plugin.status = PluginStatus.LOADED

                logger.info(f"Plugin registrado: {metadata.name} v{metadata.version}")
                return True

        except Exception as e:
            logger.error(f"Erro ao registrar plugin: {e}")
            return False

    def unregister_plugin(self, plugin_name: str) -> bool:
        """Remover plugin do registro."""
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            plugin = self._plugins[plugin_name]

            # Finalizar plugin
            try:
                plugin.shutdown()
            except Exception as e:
                logger.error(f"Erro ao finalizar plugin {plugin_name}: {e}")

            # Remover do registro
            del self._plugins[plugin_name]
            del self._metadata[plugin_name]
            del self._status[plugin_name]

            if plugin_name in self._configs:
                del self._configs[plugin_name]

            logger.info(f"Plugin removido: {plugin_name}")
            return True

    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Obter plugin por nome."""
        with self._lock:
            return self._plugins.get(plugin_name)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Obter plugins por tipo."""
        with self._lock:
            return [
                plugin
                for plugin in self._plugins.values()
                if plugin.metadata and plugin.metadata.plugin_type == plugin_type
            ]

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Listar todos os plugins."""
        with self._lock:
            result = {}
            for name, plugin in self._plugins.items():
                metadata = self._metadata.get(name)
                status = self._status.get(name, PluginStatus.UNLOADED)

                result[name] = {
                    "metadata": metadata.to_dict() if metadata else {},
                    "status": status.value,
                    "config": self._configs.get(name, {}),
                    "error_message": (
                        plugin.error_message if hasattr(plugin, "error_message") else ""
                    ),
                }

            return result

    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """Configurar plugin."""
        with self._lock:
            plugin = self._plugins.get(plugin_name)
            if not plugin:
                return False

            try:
                # Validar configuração
                errors = plugin.validate_config(config)
                if errors:
                    logger.error(f"Configuração inválida para plugin {plugin_name}: {errors}")
                    return False

                # Aplicar configuração
                success = plugin.configure(config)
                if success:
                    self._configs[plugin_name] = config.copy()

                return success

            except Exception as e:
                logger.error(f"Erro ao configurar plugin {plugin_name}: {e}")
                return False

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Obter configuração do plugin."""
        with self._lock:
            return self._configs.get(plugin_name, {}).copy()


class PluginLoader:
    """Carregador de plugins de arquivos."""

    def __init__(self, plugin_dirs: List[Path] = None):
        self.plugin_dirs = plugin_dirs or []
        self.loaded_modules: Dict[str, Any] = {}

    def add_plugin_directory(self, plugin_dir: Path) -> None:
        """Adicionar diretório de plugins."""
        if plugin_dir.exists() and plugin_dir.is_dir():
            self.plugin_dirs.append(plugin_dir)
            logger.info(f"Diretório de plugins adicionado: {plugin_dir}")

    def discover_plugins(self) -> List[Path]:
        """Descobrir arquivos de plugin nos diretórios."""
        plugin_files = []

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue

            # Procurar arquivos .py
            for py_file in plugin_dir.glob("**/*.py"):
                if py_file.name.startswith("plugin_") or py_file.name.endswith("_plugin.py"):
                    plugin_files.append(py_file)

            # Procurar arquivos de manifesto
            for manifest_file in plugin_dir.glob("**/plugin.json"):
                plugin_files.append(manifest_file)

        logger.info(f"Descobertos {len(plugin_files)} arquivos de plugin")
        return plugin_files

    def load_plugin_from_file(self, plugin_file: Path) -> Optional[Plugin]:
        """Carregar plugin de arquivo."""
        try:
            if plugin_file.suffix == ".py":
                return self._load_python_plugin(plugin_file)
            elif plugin_file.name == "plugin.json":
                return self._load_manifest_plugin(plugin_file)
            else:
                logger.warning(f"Tipo de arquivo de plugin não suportado: {plugin_file}")
                return None

        except Exception as e:
            logger.error(f"Erro ao carregar plugin {plugin_file}: {e}")
            return None

    def _load_python_plugin(self, py_file: Path) -> Optional[Plugin]:
        """Carregar plugin Python."""
        try:
            # Carregar módulo
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            if not spec or not spec.loader:
                logger.error(f"Não foi possível carregar especificação do módulo: {py_file}")
                return None

            module = importlib.util.module_from_spec(spec)
            self.loaded_modules[py_file.stem] = module

            spec.loader.exec_module(module)

            # Procurar classes de plugin
            plugin_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj != Plugin and issubclass(obj, Plugin) and obj.__module__ == module.__name__:
                    plugin_classes.append(obj)

            if not plugin_classes:
                logger.warning(f"Nenhuma classe de plugin encontrada em {py_file}")
                return None

            # Instanciar primeira classe encontrada
            plugin_class = plugin_classes[0]
            plugin = plugin_class()

            logger.info(f"Plugin Python carregado: {py_file}")
            return plugin

        except Exception as e:
            logger.error(f"Erro ao carregar plugin Python {py_file}: {e}")
            return None

    def _load_manifest_plugin(self, manifest_file: Path) -> Optional[Plugin]:
        """Carregar plugin baseado em manifesto."""
        try:
            # Carregar manifesto
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Verificar se há arquivo Python principal
            main_file = manifest.get("main", "main.py")
            plugin_py = manifest_file.parent / main_file

            if not plugin_py.exists():
                logger.error(f"Arquivo principal do plugin não encontrado: {plugin_py}")
                return None

            # Carregar plugin Python
            plugin = self._load_python_plugin(plugin_py)

            if plugin:
                # Aplicar metadados do manifesto se disponível
                try:
                    metadata = PluginMetadata.from_dict(manifest.get("metadata", {}))
                    plugin.metadata = metadata
                except Exception as e:
                    logger.warning(f"Erro ao aplicar metadados do manifesto: {e}")

            return plugin

        except Exception as e:
            logger.error(f"Erro ao carregar plugin de manifesto {manifest_file}: {e}")
            return None


class PluginSystem:
    """Sistema principal de plugins."""

    def __init__(self):
        self.registry = PluginRegistry()
        self.hook_manager = HookManager()
        self.loader = PluginLoader()

        # Configuração
        self.auto_load_plugins = True
        self.enable_sandbox = True
        self.trusted_plugins: Set[str] = set()

        # Adicionar diretório de plugins padrão
        default_plugin_dir = Path(__file__).parent.parent.parent / "plugins"
        if default_plugin_dir.exists():
            self.loader.add_plugin_directory(default_plugin_dir)

        logger.info("PluginSystem inicializado")

    def initialize(self) -> None:
        """Inicializar sistema de plugins."""
        if self.auto_load_plugins:
            self.discover_and_load_plugins()

        # Executar hook de inicialização
        self.hook_manager.execute_hook(HookPoint.APPLICATION_STARTUP)

        logger.info("PluginSystem inicializado com sucesso")

    def shutdown(self) -> None:
        """Finalizar sistema de plugins."""
        # Executar hook de finalização
        self.hook_manager.execute_hook(HookPoint.APPLICATION_SHUTDOWN)

        # Finalizar todos os plugins
        for plugin_name in list(self.registry._plugins.keys()):
            self.unload_plugin(plugin_name)

        logger.info("PluginSystem finalizado")

    def discover_and_load_plugins(self) -> Dict[str, bool]:
        """Descobrir e carregar plugins automaticamente."""
        plugin_files = self.loader.discover_plugins()
        results = {}

        for plugin_file in plugin_files:
            try:
                plugin = self.loader.load_plugin_from_file(plugin_file)
                if plugin:
                    success = self.load_plugin(plugin)
                    results[str(plugin_file)] = success
                else:
                    results[str(plugin_file)] = False

            except Exception as e:
                logger.error(f"Erro ao carregar plugin {plugin_file}: {e}")
                results[str(plugin_file)] = False

        successful = sum(1 for success in results.values() if success)
        logger.info(f"Carregados {successful}/{len(results)} plugins automaticamente")

        return results

    def load_plugin(self, plugin: Plugin) -> bool:
        """Carregar e ativar plugin."""
        try:
            # Registrar plugin
            if not self.registry.register_plugin(plugin):
                return False

            metadata = plugin.get_metadata()

            # Verificar dependências
            if not self._check_dependencies(metadata):
                logger.error(f"Dependências não atendidas para plugin {metadata.name}")
                self.registry.unregister_plugin(metadata.name)
                return False

            # Verificar conflitos
            if not self._check_conflicts(metadata):
                logger.error(f"Conflitos detectados para plugin {metadata.name}")
                self.registry.unregister_plugin(metadata.name)
                return False

            # Inicializar plugin
            if not plugin.initialize():
                logger.error(f"Falha na inicialização do plugin {metadata.name}")
                self.registry.unregister_plugin(metadata.name)
                return False

            # Registrar hooks
            self._register_plugin_hooks(plugin)

            # Marcar como ativo
            plugin.status = PluginStatus.ACTIVE
            self.registry._status[metadata.name] = PluginStatus.ACTIVE

            # Notificar
            notify_info(f"Plugin carregado: {metadata.name} v{metadata.version}")

            # Disparar evento
            self._emit_plugin_event(metadata.name, "plugin_loaded")

            logger.info(f"Plugin {metadata.name} carregado e ativado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao carregar plugin: {e}")

            if hasattr(plugin, "metadata") and plugin.metadata:
                plugin.error_message = str(e)
                plugin.status = PluginStatus.ERROR
                self.registry._status[plugin.metadata.name] = PluginStatus.ERROR

            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Descarregar plugin."""
        try:
            plugin = self.registry.get_plugin(plugin_name)
            if not plugin:
                return False

            # Remover hooks
            self._unregister_plugin_hooks(plugin_name)

            # Desregistrar plugin
            success = self.registry.unregister_plugin(plugin_name)

            if success:
                notify_info(f"Plugin descarregado: {plugin_name}")
                self._emit_plugin_event(plugin_name, "plugin_unloaded")

            return success

        except Exception as e:
            logger.error(f"Erro ao descarregar plugin {plugin_name}: {e}")
            return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """Recarregar plugin."""
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            return False

        # Descarregar
        if not self.unload_plugin(plugin_name):
            return False

        # Recarregar (requer novo carregamento do arquivo)
        # Por simplicidade, retornar True aqui
        # Em implementação completa, seria necessário recarregar do arquivo original

        return True

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Obter informações detalhadas do plugin."""
        plugin_info = self.registry.list_plugins().get(plugin_name)

        if plugin_info:
            plugin = self.registry.get_plugin(plugin_name)
            if plugin:
                # Adicionar informações de hooks
                hooks = plugin.get_hooks()
                plugin_info["hooks"] = {
                    hook_point.value: len(handlers) for hook_point, handlers in hooks.items()
                }

        return plugin_info

    def configure_plugin(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """Configurar plugin."""
        return self.registry.set_plugin_config(plugin_name, config)

    def execute_hook(self, hook_point: HookPoint, *args, **kwargs) -> List[Any]:
        """Executar hook no sistema."""
        return self.hook_manager.execute_hook(hook_point, *args, **kwargs)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Obter plugins por tipo."""
        return self.registry.get_plugins_by_type(plugin_type)

    def _check_dependencies(self, metadata: PluginMetadata) -> bool:
        """Verificar dependências do plugin."""
        for dependency in metadata.requires:
            if dependency not in self.registry._plugins:
                logger.warning(f"Dependência não encontrada: {dependency}")
                return False
        return True

    def _check_conflicts(self, metadata: PluginMetadata) -> bool:
        """Verificar conflitos do plugin."""
        for conflict in metadata.conflicts:
            if conflict in self.registry._plugins:
                logger.warning(f"Conflito detectado com plugin: {conflict}")
                return False
        return True

    def _register_plugin_hooks(self, plugin: Plugin) -> None:
        """Registrar hooks do plugin."""
        if not plugin.metadata:
            return

        hooks = plugin.get_hooks()
        for hook_point, handlers in hooks.items():
            for handler in handlers:
                self.hook_manager.register_hook(hook_point, handler, plugin.metadata.name)

    def _unregister_plugin_hooks(self, plugin_name: str) -> None:
        """Remover hooks do plugin."""
        for hook_point in HookPoint:
            self.hook_manager.unregister_hook(hook_point, plugin_name)

    def _emit_plugin_event(self, plugin_name: str, action: str) -> None:
        """Disparar evento de plugin."""
        try:
            event = SystemEvent(
                component="plugin_system",
                metadata={"action": action, "plugin_name": plugin_name, "timestamp": time.time()},
            )

            event_bus.publish_sync(event)
        except Exception as e:
            logger.debug(f"Erro ao disparar evento de plugin: {e}")

    def get_system_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do sistema de plugins."""
        plugins_info = self.registry.list_plugins()

        stats_by_type = {}
        stats_by_status = {}

        for plugin_info in plugins_info.values():
            plugin_type = plugin_info["metadata"].get("plugin_type", "unknown")
            status = plugin_info["status"]

            stats_by_type[plugin_type] = stats_by_type.get(plugin_type, 0) + 1
            stats_by_status[status] = stats_by_status.get(status, 0) + 1

        hook_counts = self.hook_manager.get_hook_count()

        return {
            "total_plugins": len(plugins_info),
            "by_type": stats_by_type,
            "by_status": stats_by_status,
            "hook_points": len(hook_counts) if isinstance(hook_counts, dict) else 0,
            "total_hooks": sum(hook_counts.values()) if isinstance(hook_counts, dict) else 0,
            "plugin_directories": len(self.loader.plugin_dirs),
        }


# Instância global do sistema de plugins
plugin_system = PluginSystem()

# Auto-inicialização será feita pelo integration manager
# plugin_system.initialize()
