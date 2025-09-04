"""
FuelTune Clipboard Integration

Sistema de integração com clipboard do sistema operacional para copiar/colar
dados entre aplicações e dentro do FuelTune Streamlit.

Classes:
    ClipboardManager: Gerenciador principal do clipboard
    ClipboardData: Representação de dados do clipboard
    DataFormatter: Formatador para diferentes tipos de dados

Author: FuelTune Development Team
Version: 1.0.0
"""

import io
import json
import platform
import subprocess
import tempfile
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ClipboardFormat(Enum):
    """Formatos suportados no clipboard."""

    TEXT = "text"
    CSV = "csv"
    TSV = "tsv"
    JSON = "json"
    HTML = "html"
    EXCEL = "excel"


class DataType(Enum):
    """Tipos de dados suportados."""

    STRING = "string"
    NUMBER = "number"
    DATAFRAME = "dataframe"
    DICT = "dict"
    LIST = "list"
    ANALYSIS_RESULT = "analysis_result"


@dataclass
class ClipboardData:
    """Representação de dados no clipboard."""

    content: Any
    format: ClipboardFormat
    data_type: DataType
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__("time").time())

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
        return {
            "content": self.content,
            "format": self.format.value,
            "data_type": self.data_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClipboardData":
        """Criar instância a partir de dicionário."""
        return cls(
            content=data["content"],
            format=ClipboardFormat(data["format"]),
            data_type=DataType(data["data_type"]),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", __import__("time").time()),
        )


class DataFormatter(ABC):
    """Classe base para formatadores de dados."""

    @abstractmethod
    def format_for_clipboard(self, data: Any, metadata: Dict[str, Any] = None) -> str:
        """Formatar dados para o clipboard."""
        pass

    @abstractmethod
    def parse_from_clipboard(self, content: str) -> Any:
        """Analisar dados do clipboard."""
        pass


class TextFormatter(DataFormatter):
    """Formatador para texto simples."""

    def format_for_clipboard(self, data: Any, metadata: Dict[str, Any] = None) -> str:
        """Formatar como texto."""
        return str(data)

    def parse_from_clipboard(self, content: str) -> str:
        """Retornar texto como está."""
        return content


class CSVFormatter(DataFormatter):
    """Formatador para dados CSV."""

    def format_for_clipboard(self, data: Any, metadata: Dict[str, Any] = None) -> str:
        """Formatar dados como CSV."""
        if isinstance(data, pd.DataFrame):
            return data.to_csv(index=False)
        elif isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                df = pd.DataFrame(data)
                return df.to_csv(index=False)
            else:
                # Lista simples
                return "\n".join(str(item) for item in data)
        elif isinstance(data, dict):
            # Converter dict para DataFrame
            if all(isinstance(v, (list, tuple)) for v in data.values()):
                df = pd.DataFrame(data)
                return df.to_csv(index=False)
            else:
                # Dict simples - converter para duas colunas
                df = pd.DataFrame(list(data.items()), columns=["Key", "Value"])
                return df.to_csv(index=False)
        else:
            return str(data)

    def parse_from_clipboard(self, content: str) -> pd.DataFrame:
        """Analisar CSV do clipboard."""
        try:
            return pd.read_csv(io.StringIO(content))
        except Exception as e:
            logger.warning(f"Erro ao analisar CSV: {e}")
            # Fallback: tentar como TSV
            try:
                return pd.read_csv(io.StringIO(content), sep="\t")
            except:
                raise ValueError(f"Não foi possível analisar dados CSV: {e}")


class JSONFormatter(DataFormatter):
    """Formatador para dados JSON."""

    def format_for_clipboard(self, data: Any, metadata: Dict[str, Any] = None) -> str:
        """Formatar como JSON."""
        if isinstance(data, pd.DataFrame):
            return data.to_json(orient="records", indent=2)
        else:
            return json.dumps(data, indent=2, default=self._json_serializer)

    def parse_from_clipboard(self, content: str) -> Any:
        """Analisar JSON do clipboard."""
        return json.loads(content)

    def _json_serializer(self, obj):
        """Serializador personalizado para JSON."""
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        elif hasattr(obj, "isoformat"):  # datetime objects
            return obj.isoformat()
        else:
            return str(obj)


class HTMLFormatter(DataFormatter):
    """Formatador para dados HTML."""

    def format_for_clipboard(self, data: Any, metadata: Dict[str, Any] = None) -> str:
        """Formatar como HTML."""
        if isinstance(data, pd.DataFrame):
            return data.to_html(index=False, classes="fueltune-table")
        elif isinstance(data, dict):
            html = "<table class='fueltune-dict'>\n"
            for key, value in data.items():
                html += f"<tr><td>{key}</td><td>{value}</td></tr>\n"
            html += "</table>"
            return html
        elif isinstance(data, list):
            html = "<ul class='fueltune-list'>\n"
            for item in data:
                html += f"<li>{item}</li>\n"
            html += "</ul>"
            return html
        else:
            return f"<p>{data}</p>"

    def parse_from_clipboard(self, content: str) -> pd.DataFrame:
        """Analisar HTML do clipboard."""
        try:
            tables = pd.read_html(content)
            if tables:
                return tables[0]  # Retornar primeira tabela
            else:
                raise ValueError("Nenhuma tabela encontrada no HTML")
        except Exception as e:
            raise ValueError(f"Erro ao analisar HTML: {e}")


class ClipboardManager:
    """Gerenciador principal do sistema de clipboard."""

    def __init__(self):
        self.formatters = {
            ClipboardFormat.TEXT: TextFormatter(),
            ClipboardFormat.CSV: CSVFormatter(),
            ClipboardFormat.TSV: CSVFormatter(),  # Usar mesmo formatter que CSV
            ClipboardFormat.JSON: JSONFormatter(),
            ClipboardFormat.HTML: HTMLFormatter(),
        }

        # Detectar sistema operacional
        self.system = platform.system().lower()
        self.clipboard_available = self._check_clipboard_availability()

        logger.info(f"ClipboardManager inicializado (Sistema: {self.system})")

    def _check_clipboard_availability(self) -> bool:
        """Verificar se clipboard está disponível."""
        try:
            if self.system == "windows":
                import win32clipboard

                return True
            elif self.system == "darwin":  # macOS
                result = subprocess.run(["which", "pbcopy"], capture_output=True)
                return result.returncode == 0
            elif self.system == "linux":
                # Verificar xclip ou xsel
                xclip_result = subprocess.run(["which", "xclip"], capture_output=True)
                xsel_result = subprocess.run(["which", "xsel"], capture_output=True)
                return xclip_result.returncode == 0 or xsel_result.returncode == 0
            else:
                return False
        except Exception as e:
            logger.warning(f"Erro ao verificar clipboard: {e}")
            return False

    def copy_to_clipboard(
        self,
        data: Any,
        format: ClipboardFormat = ClipboardFormat.TEXT,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Copiar dados para o clipboard."""

        if not self.clipboard_available:
            logger.error("Clipboard não está disponível no sistema")
            return False

        try:
            # Formatar dados
            formatter = self.formatters.get(format)
            if not formatter:
                logger.error(f"Formatador não encontrado para: {format}")
                return False

            formatted_data = formatter.format_for_clipboard(data, metadata or {})

            # Copiar para clipboard baseado no sistema operacional
            success = self._copy_to_system_clipboard(formatted_data, format)

            if success:
                logger.info(f"Dados copiados para clipboard: {len(formatted_data)} caracteres")

                # Disparar evento de cópia
                self._emit_copy_event(data, format, metadata)

            return success

        except Exception as e:
            logger.error(f"Erro ao copiar para clipboard: {e}")
            return False

    def paste_from_clipboard(
        self, format: ClipboardFormat = ClipboardFormat.TEXT, expected_type: DataType = None
    ) -> Optional[ClipboardData]:
        """Colar dados do clipboard."""

        if not self.clipboard_available:
            logger.error("Clipboard não está disponível no sistema")
            return None

        try:
            # Obter dados do clipboard
            content = self._get_from_system_clipboard()
            if not content:
                return None

            # Analisar dados
            formatter = self.formatters.get(format)
            if not formatter:
                logger.error(f"Formatador não encontrado para: {format}")
                return None

            parsed_data = formatter.parse_from_clipboard(content)

            # Determinar tipo de dados
            data_type = self._determine_data_type(parsed_data)

            clipboard_data = ClipboardData(
                content=parsed_data,
                format=format,
                data_type=data_type,
                metadata={"original_length": len(content)},
            )

            logger.info(f"Dados colados do clipboard: {format.value}")

            # Disparar evento de colagem
            self._emit_paste_event(clipboard_data)

            return clipboard_data

        except Exception as e:
            logger.error(f"Erro ao colar do clipboard: {e}")
            return None

    def _copy_to_system_clipboard(self, data: str, format: ClipboardFormat) -> bool:
        """Copiar dados para clipboard do sistema operacional."""

        try:
            if self.system == "windows":
                return self._copy_windows(data, format)
            elif self.system == "darwin":
                return self._copy_macos(data, format)
            elif self.system == "linux":
                return self._copy_linux(data, format)
            else:
                logger.error(f"Sistema operacional não suportado: {self.system}")
                return False
        except Exception as e:
            logger.error(f"Erro ao copiar para clipboard do sistema: {e}")
            return False

    def _get_from_system_clipboard(self) -> Optional[str]:
        """Obter dados do clipboard do sistema operacional."""

        try:
            if self.system == "windows":
                return self._get_windows()
            elif self.system == "darwin":
                return self._get_macos()
            elif self.system == "linux":
                return self._get_linux()
            else:
                logger.error(f"Sistema operacional não suportado: {self.system}")
                return None
        except Exception as e:
            logger.error(f"Erro ao obter dados do clipboard: {e}")
            return None

    def _copy_windows(self, data: str, format: ClipboardFormat) -> bool:
        """Copiar para clipboard no Windows."""
        try:
            import win32clipboard

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()

            if format == ClipboardFormat.HTML:
                # HTML específico do Windows
                import win32con

                win32clipboard.SetClipboardData(win32con.CF_HTML, data)
            else:
                win32clipboard.SetClipboardText(data)

            win32clipboard.CloseClipboard()
            return True

        except ImportError:
            # Fallback usando subprocess
            return self._copy_subprocess(["clip"], data)
        except Exception as e:
            logger.error(f"Erro no clipboard do Windows: {e}")
            return False

    def _get_windows(self) -> Optional[str]:
        """Obter dados do clipboard no Windows."""
        try:
            import win32clipboard

            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()

            return data

        except ImportError:
            # Fallback não é facilmente implementável no Windows
            return None
        except Exception as e:
            logger.error(f"Erro ao obter dados do Windows clipboard: {e}")
            return None

    def _copy_macos(self, data: str, format: ClipboardFormat) -> bool:
        """Copiar para clipboard no macOS."""
        return self._copy_subprocess(["pbcopy"], data)

    def _get_macos(self) -> Optional[str]:
        """Obter dados do clipboard no macOS."""
        try:
            result = subprocess.run(["pbpaste"], capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else None
        except Exception as e:
            logger.error(f"Erro ao obter dados do macOS clipboard: {e}")
            return None

    def _copy_linux(self, data: str, format: ClipboardFormat) -> bool:
        """Copiar para clipboard no Linux."""
        # Tentar xclip primeiro
        if self._copy_subprocess(["xclip", "-selection", "clipboard"], data):
            return True

        # Tentar xsel como fallback
        return self._copy_subprocess(["xsel", "--clipboard", "--input"], data)

    def _get_linux(self) -> Optional[str]:
        """Obter dados do clipboard no Linux."""
        # Tentar xclip primeiro
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout
        except:
            pass

        # Tentar xsel como fallback
        try:
            result = subprocess.run(
                ["xsel", "--clipboard", "--output"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout
        except:
            pass

        return None

    def _copy_subprocess(self, command: List[str], data: str) -> bool:
        """Copiar usando subprocess."""
        try:
            process = subprocess.run(
                command, input=data, text=True, capture_output=True, timeout=10
            )
            return process.returncode == 0
        except Exception as e:
            logger.error(f"Erro no subprocess clipboard: {e}")
            return False

    def _determine_data_type(self, data: Any) -> DataType:
        """Determinar o tipo de dados."""
        if isinstance(data, str):
            return DataType.STRING
        elif isinstance(data, (int, float)):
            return DataType.NUMBER
        elif isinstance(data, pd.DataFrame):
            return DataType.DATAFRAME
        elif isinstance(data, dict):
            return DataType.DICT
        elif isinstance(data, list):
            return DataType.LIST
        else:
            return DataType.STRING

    def _emit_copy_event(
        self, data: Any, format: ClipboardFormat, metadata: Dict[str, Any]
    ) -> None:
        """Disparar evento de cópia."""
        try:
            from .events import event_bus, SystemEvent

            event = SystemEvent(
                component="clipboard",
                metadata={
                    "action": "copy",
                    "format": format.value,
                    "data_type": type(data).__name__,
                    "metadata": metadata or {},
                },
            )

            event_bus.publish_sync(event)
        except Exception as e:
            logger.debug(f"Erro ao disparar evento de cópia: {e}")

    def _emit_paste_event(self, clipboard_data: ClipboardData) -> None:
        """Disparar evento de colagem."""
        try:
            from .events import event_bus, SystemEvent

            event = SystemEvent(
                component="clipboard",
                metadata={
                    "action": "paste",
                    "format": clipboard_data.format.value,
                    "data_type": clipboard_data.data_type.value,
                    "metadata": clipboard_data.metadata,
                },
            )

            event_bus.publish_sync(event)
        except Exception as e:
            logger.debug(f"Erro ao disparar evento de colagem: {e}")

    def copy_dataframe(
        self, df: pd.DataFrame, format: ClipboardFormat = ClipboardFormat.CSV
    ) -> bool:
        """Copiar DataFrame para clipboard."""
        return self.copy_to_clipboard(df, format, {"rows": len(df), "cols": len(df.columns)})

    def copy_analysis_results(self, results: Dict[str, Any]) -> bool:
        """Copiar resultados de análise para clipboard."""
        metadata = {"source": "fueltune_analysis", "results_count": len(results)}
        return self.copy_to_clipboard(results, ClipboardFormat.JSON, metadata)

    def copy_session_data(
        self, session_id: str, data: Any, format: ClipboardFormat = ClipboardFormat.CSV
    ) -> bool:
        """Copiar dados de sessão para clipboard."""
        metadata = {"source": "fueltune_session", "session_id": session_id}
        return self.copy_to_clipboard(data, format, metadata)

    def paste_as_dataframe(self) -> Optional[pd.DataFrame]:
        """Colar dados como DataFrame."""
        # Tentar CSV primeiro
        csv_data = self.paste_from_clipboard(ClipboardFormat.CSV)
        if csv_data and isinstance(csv_data.content, pd.DataFrame):
            return csv_data.content

        # Tentar HTML como fallback
        html_data = self.paste_from_clipboard(ClipboardFormat.HTML)
        if html_data and isinstance(html_data.content, pd.DataFrame):
            return html_data.content

        return None

    def is_available(self) -> bool:
        """Verificar se clipboard está disponível."""
        return self.clipboard_available

    def get_formatters(self) -> Dict[ClipboardFormat, DataFormatter]:
        """Obter formatadores disponíveis."""
        return self.formatters.copy()


# Instância global do gerenciador de clipboard
clipboard_manager = ClipboardManager()
