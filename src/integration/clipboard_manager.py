"""
Cross-Platform Clipboard Manager for FTManager Integration

This module provides robust cross-platform clipboard operations with comprehensive
error handling, content validation, and professional feedback mechanisms.

CRITICAL: Follows PYTHON-CODE-STANDARDS.md:
- Cross-platform clipboard compatibility
- Professional error handling
- Type hints 100% coverage
- Performance < 100ms for operations
- Robust format detection
- Zero emojis in interface
"""

import logging
import platform
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

# Import clipboard libraries with fallbacks
try:
    import pyperclip

    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    pyperclip = None

try:
    import tkinter as tk

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None

logger = logging.getLogger(__name__)


@dataclass
class ClipboardResult:
    """Type-safe clipboard operation result."""

    success: bool
    content: Optional[str] = None
    operation: Literal["get", "set", "check", "clear"] = "get"
    method_used: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize empty collections if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ClipboardStatus:
    """Type-safe clipboard system status."""

    available: bool
    methods: List[str] = field(default_factory=list)
    preferred_method: Optional[str] = None
    platform_info: Dict[str, str] = field(default_factory=dict)
    capabilities: Dict[str, bool] = field(default_factory=dict)
    last_check: Optional[datetime] = None


class ClipboardManager:
    """
    Professional cross-platform clipboard manager.

    Features:
    - Multi-method clipboard access with fallbacks
    - Platform-specific optimizations
    - Content validation and sanitization
    - Professional error handling
    - Performance monitoring
    - Comprehensive logging

    Supported Methods:
    1. pyperclip (primary) - Most reliable cross-platform
    2. tkinter - Built-in Python GUI toolkit
    3. subprocess - System clipboard commands
    4. temporary files - Ultimate fallback

    Platform Support:
    - Windows: pyperclip, tkinter, PowerShell
    - macOS: pyperclip, tkinter, pbcopy/pbpaste
    - Linux: pyperclip, tkinter, xclip/xsel

    Performance Target: < 100ms for typical operations
    """

    def __init__(self, preferred_method: Optional[str] = None):
        """Initialize clipboard manager with method detection."""

        self.platform = platform.system().lower()
        self.preferred_method = preferred_method
        self.available_methods: List[str] = []
        self.method_capabilities: Dict[str, Dict[str, bool]] = {}
        self.operation_stats: Dict[str, int] = {
            "get_success": 0,
            "get_failure": 0,
            "set_success": 0,
            "set_failure": 0,
        }

        # Detect available clipboard methods
        self._detect_methods()

        # Select best method
        self.active_method = self._select_best_method()

        logger.info(
            f"Clipboard manager initialized: platform={self.platform}, "
            f"active_method={self.active_method}, "
            f"available_methods={self.available_methods}"
        )

    def get_content(
        self, validate_content: bool = True, max_size_mb: float = 10.0
    ) -> ClipboardResult:
        """
        Get content from clipboard with validation.

        Args:
            validate_content: Whether to validate content
            max_size_mb: Maximum content size in MB

        Returns:
            ClipboardResult with content and status

        Performance: < 100ms for typical operations
        """

        operation_start = datetime.now()

        try:
            # Try methods in order of preference
            for method in self._get_method_order():
                try:
                    content = self._get_by_method(method)

                    if content is not None:
                        # Validate content if requested
                        if validate_content:
                            validation_result = self._validate_content(content, max_size_mb)
                            if not validation_result["valid"]:
                                return ClipboardResult(
                                    success=False,
                                    operation="get",
                                    method_used=method,
                                    errors=validation_result["errors"],
                                    warnings=validation_result["warnings"],
                                    metadata={
                                        "operation_time": operation_start.isoformat(),
                                        "method_tried": method,
                                        "content_length": len(content) if content else 0,
                                    },
                                )

                        # Success
                        self.operation_stats["get_success"] += 1

                        return ClipboardResult(
                            success=True,
                            content=content,
                            operation="get",
                            method_used=method,
                            metadata={
                                "operation_time": operation_start.isoformat(),
                                "processing_duration_ms": (
                                    datetime.now() - operation_start
                                ).total_seconds()
                                * 1000,
                                "content_length": len(content),
                                "content_lines": content.count("\n") + 1 if content else 0,
                                "method_used": method,
                            },
                        )

                except Exception as e:
                    logger.warning(f"Method {method} failed for get_content: {e}")
                    continue

            # All methods failed
            self.operation_stats["get_failure"] += 1

            return ClipboardResult(
                success=False,
                operation="get",
                errors=["All clipboard access methods failed"],
                metadata={
                    "operation_time": operation_start.isoformat(),
                    "methods_tried": self.available_methods,
                    "platform": self.platform,
                },
            )

        except Exception as e:
            logger.error(f"Clipboard get operation failed: {e}")
            self.operation_stats["get_failure"] += 1

            return ClipboardResult(
                success=False,
                operation="get",
                errors=[f"Get operation failed: {str(e)}"],
                metadata={"operation_time": operation_start.isoformat()},
            )

    def set_content(
        self, content: str, validate_content: bool = True, backup_to_temp: bool = True
    ) -> ClipboardResult:
        """
        Set clipboard content with validation and backup.

        Args:
            content: Content to set in clipboard
            validate_content: Whether to validate content before setting
            backup_to_temp: Whether to backup content to temp file

        Returns:
            ClipboardResult with operation status

        Performance: < 100ms for typical operations
        """

        operation_start = datetime.now()

        try:
            # Validate input
            if content is None:
                return ClipboardResult(
                    success=False,
                    operation="set",
                    errors=["Cannot set None content to clipboard"],
                    metadata={"operation_time": operation_start.isoformat()},
                )

            # Validate content if requested
            if validate_content:
                validation_result = self._validate_content(
                    content, max_size_mb=50.0
                )  # Larger limit for setting
                if not validation_result["valid"]:
                    return ClipboardResult(
                        success=False,
                        operation="set",
                        errors=validation_result["errors"],
                        warnings=validation_result["warnings"],
                        metadata={
                            "operation_time": operation_start.isoformat(),
                            "content_length": len(content),
                        },
                    )

            # Backup to temp file if requested
            backup_path = None
            if backup_to_temp:
                try:
                    backup_path = self._backup_to_temp(content)
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")

            # Try methods in order of preference
            for method in self._get_method_order():
                try:
                    success = self._set_by_method(method, content)

                    if success:
                        # Verify the content was set correctly
                        verify_result = self._verify_clipboard_content(content, method)

                        if verify_result["verified"]:
                            self.operation_stats["set_success"] += 1

                            return ClipboardResult(
                                success=True,
                                content=content,
                                operation="set",
                                method_used=method,
                                warnings=verify_result.get("warnings", []),
                                metadata={
                                    "operation_time": operation_start.isoformat(),
                                    "processing_duration_ms": (
                                        datetime.now() - operation_start
                                    ).total_seconds()
                                    * 1000,
                                    "content_length": len(content),
                                    "method_used": method,
                                    "backup_created": backup_path is not None,
                                    "backup_path": str(backup_path) if backup_path else None,
                                    "verification_performed": True,
                                },
                            )
                        else:
                            logger.warning(f"Content verification failed for method {method}")
                            continue

                except Exception as e:
                    logger.warning(f"Method {method} failed for set_content: {e}")
                    continue

            # All methods failed
            self.operation_stats["set_failure"] += 1

            return ClipboardResult(
                success=False,
                operation="set",
                errors=["All clipboard write methods failed"],
                metadata={
                    "operation_time": operation_start.isoformat(),
                    "methods_tried": self.available_methods,
                    "platform": self.platform,
                    "content_length": len(content),
                },
            )

        except Exception as e:
            logger.error(f"Clipboard set operation failed: {e}")
            self.operation_stats["set_failure"] += 1

            return ClipboardResult(
                success=False,
                operation="set",
                errors=[f"Set operation failed: {str(e)}"],
                metadata={"operation_time": operation_start.isoformat()},
            )

    def clear_clipboard(self) -> ClipboardResult:
        """
        Clear clipboard content.

        Returns:
            ClipboardResult with operation status
        """

        return self.set_content("", validate_content=False, backup_to_temp=False)

    def check_availability(self) -> ClipboardResult:
        """
        Check clipboard system availability.

        Returns:
            ClipboardResult with availability status
        """

        try:
            # Re-detect methods
            self._detect_methods()

            # Test basic functionality
            test_content = "clipboard_test_" + str(datetime.now().timestamp())

            for method in self.available_methods:
                try:
                    if self._set_by_method(method, test_content):
                        retrieved_content = self._get_by_method(method)
                        if retrieved_content == test_content:
                            return ClipboardResult(
                                success=True,
                                operation="check",
                                method_used=method,
                                metadata={
                                    "test_successful": True,
                                    "available_methods": self.available_methods,
                                    "platform": self.platform,
                                },
                            )
                except Exception:
                    continue

            return ClipboardResult(
                success=False,
                operation="check",
                errors=["No working clipboard methods found"],
                metadata={"available_methods": self.available_methods, "platform": self.platform},
            )

        except Exception as e:
            return ClipboardResult(
                success=False, operation="check", errors=[f"Availability check failed: {str(e)}"]
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive clipboard manager status.

        Returns:
            Dictionary with status information
        """

        try:
            return {
                "available": len(self.available_methods) > 0,
                "platform": self.platform,
                "active_method": self.active_method,
                "available_methods": self.available_methods,
                "method_capabilities": self.method_capabilities,
                "operation_stats": self.operation_stats.copy(),
                "last_check": datetime.now().isoformat(),
                "dependencies": {"pyperclip": PYPERCLIP_AVAILABLE, "tkinter": TKINTER_AVAILABLE},
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"available": False, "error": str(e)}

    # Private methods for clipboard operations

    def _detect_methods(self) -> None:
        """Detect available clipboard methods for current platform."""

        self.available_methods = []
        self.method_capabilities = {}

        # Test pyperclip
        if PYPERCLIP_AVAILABLE:
            try:
                test_content = "test_" + str(datetime.now().timestamp())
                pyperclip.copy(test_content)
                if pyperclip.paste() == test_content:
                    self.available_methods.append("pyperclip")
                    self.method_capabilities["pyperclip"] = {
                        "reliable": True,
                        "fast": True,
                        "cross_platform": True,
                    }
            except Exception as e:
                logger.debug(f"pyperclip not available: {e}")

        # Test tkinter
        if TKINTER_AVAILABLE:
            try:
                root = tk.Tk()
                root.withdraw()  # Hide window
                test_content = "test_tk_" + str(datetime.now().timestamp())
                root.clipboard_clear()
                root.clipboard_append(test_content)
                root.update()

                retrieved = root.clipboard_get()
                root.destroy()

                if retrieved == test_content:
                    self.available_methods.append("tkinter")
                    self.method_capabilities["tkinter"] = {
                        "reliable": True,
                        "fast": False,
                        "cross_platform": True,
                    }
            except Exception as e:
                logger.debug(f"tkinter clipboard not available: {e}")

        # Test platform-specific methods
        if self.platform == "windows":
            if self._test_windows_clipboard():
                self.available_methods.append("windows_powershell")
                self.method_capabilities["windows_powershell"] = {
                    "reliable": True,
                    "fast": False,
                    "cross_platform": False,
                }

        elif self.platform == "darwin":  # macOS
            if self._test_macos_clipboard():
                self.available_methods.append("macos_pbcopy")
                self.method_capabilities["macos_pbcopy"] = {
                    "reliable": True,
                    "fast": True,
                    "cross_platform": False,
                }

        elif self.platform == "linux":
            if self._test_linux_clipboard():
                self.available_methods.append("linux_xclip")
                self.method_capabilities["linux_xclip"] = {
                    "reliable": False,  # Depends on X11
                    "fast": True,
                    "cross_platform": False,
                }

    def _select_best_method(self) -> Optional[str]:
        """Select the best available clipboard method."""

        if not self.available_methods:
            return None

        # Use preferred method if available and specified
        if self.preferred_method and self.preferred_method in self.available_methods:
            return self.preferred_method

        # Priority order: pyperclip > platform-specific > tkinter
        priority_order = [
            "pyperclip",
            "windows_powershell",
            "macos_pbcopy",
            "linux_xclip",
            "tkinter",
        ]

        for method in priority_order:
            if method in self.available_methods:
                return method

        # Fallback to first available
        return self.available_methods[0]

    def _get_method_order(self) -> List[str]:
        """Get methods in order of preference for operations."""

        if not self.available_methods:
            return []

        # Start with active method, then others
        methods = [self.active_method] if self.active_method else []
        methods.extend([m for m in self.available_methods if m != self.active_method])

        return methods

    def _get_by_method(self, method: str) -> Optional[str]:
        """Get clipboard content using specific method."""

        try:
            if method == "pyperclip" and PYPERCLIP_AVAILABLE:
                return pyperclip.paste()

            elif method == "tkinter" and TKINTER_AVAILABLE:
                root = tk.Tk()
                root.withdraw()
                try:
                    content = root.clipboard_get()
                    return content
                finally:
                    root.destroy()

            elif method == "windows_powershell" and self.platform == "windows":
                result = subprocess.run(
                    ["powershell", "-command", "Get-Clipboard"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return result.stdout

            elif method == "macos_pbcopy" and self.platform == "darwin":
                result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout

            elif method == "linux_xclip" and self.platform == "linux":
                # Try xclip first, then xsel
                for cmd in [
                    ["xclip", "-selection", "clipboard", "-o"],
                    ["xsel", "--clipboard", "--output"],
                ]:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            return result.stdout
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue

            return None

        except Exception as e:
            logger.error(f"Failed to get clipboard via {method}: {e}")
            return None

    def _set_by_method(self, method: str, content: str) -> bool:
        """Set clipboard content using specific method."""

        try:
            if method == "pyperclip" and PYPERCLIP_AVAILABLE:
                pyperclip.copy(content)
                return True

            elif method == "tkinter" and TKINTER_AVAILABLE:
                root = tk.Tk()
                root.withdraw()
                try:
                    root.clipboard_clear()
                    root.clipboard_append(content)
                    root.update()
                    return True
                finally:
                    root.destroy()

            elif method == "windows_powershell" and self.platform == "windows":
                process = subprocess.Popen(
                    ["powershell", "-command", "Set-Clipboard"],
                    stdin=subprocess.PIPE,
                    text=True,
                    timeout=5,
                )
                process.communicate(input=content)
                return process.returncode == 0

            elif method == "macos_pbcopy" and self.platform == "darwin":
                process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True, timeout=5)
                process.communicate(input=content)
                return process.returncode == 0

            elif method == "linux_xclip" and self.platform == "linux":
                # Try xclip first, then xsel
                for cmd in [
                    ["xclip", "-selection", "clipboard"],
                    ["xsel", "--clipboard", "--input"],
                ]:
                    try:
                        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True, timeout=5)
                        process.communicate(input=content)
                        if process.returncode == 0:
                            return True
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue

            return False

        except Exception as e:
            logger.error(f"Failed to set clipboard via {method}: {e}")
            return False

    def _validate_content(self, content: str, max_size_mb: float) -> Dict[str, Any]:
        """Validate clipboard content."""

        errors = []
        warnings = []

        try:
            # Size validation
            content_size_mb = len(content.encode("utf-8")) / (1024 * 1024)
            if content_size_mb > max_size_mb:
                errors.append(
                    f"Content size ({content_size_mb:.1f} MB) exceeds maximum ({max_size_mb} MB)"
                )

            # Check for binary content
            try:
                content.encode("utf-8")
            except UnicodeEncodeError:
                errors.append("Content contains invalid UTF-8 characters")

            # Check for excessively long lines
            if "\n" in content:
                lines = content.split("\n")
                max_line_length = max(len(line) for line in lines) if lines else 0
                if max_line_length > 10000:
                    warnings.append(f"Very long line detected ({max_line_length} characters)")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "size_mb": content_size_mb,
            }

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Content validation failed: {str(e)}"],
                "warnings": warnings,
            }

    def _verify_clipboard_content(self, expected_content: str, method: str) -> Dict[str, Any]:
        """Verify clipboard content matches expected content."""

        try:
            # Small delay to ensure clipboard is updated
            import time

            time.sleep(0.05)

            actual_content = self._get_by_method(method)

            if actual_content == expected_content:
                return {"verified": True, "warnings": []}

            elif actual_content is None:
                return {
                    "verified": False,
                    "warnings": ["Could not retrieve clipboard content for verification"],
                }

            else:
                # Check if content is approximately correct (handle line ending differences)
                normalized_expected = expected_content.replace("\r\n", "\n").replace("\r", "\n")
                normalized_actual = actual_content.replace("\r\n", "\n").replace("\r", "\n")

                if normalized_expected == normalized_actual:
                    return {
                        "verified": True,
                        "warnings": ["Line endings were normalized during clipboard operation"],
                    }

                return {
                    "verified": False,
                    "warnings": [
                        f"Content verification failed. Expected {len(expected_content)} chars, "
                        f"got {len(actual_content)} chars"
                    ],
                }

        except Exception as e:
            return {"verified": False, "warnings": [f"Verification failed: {str(e)}"]}

    def _backup_to_temp(self, content: str) -> Path:
        """Backup content to temporary file."""

        try:
            temp_dir = Path(tempfile.gettempdir())
            backup_file = (
                temp_dir
                / f"ftmanager_clipboard_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(content)

            logger.debug(f"Created clipboard backup: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def _test_windows_clipboard(self) -> bool:
        """Test Windows PowerShell clipboard access."""

        try:
            result = subprocess.run(
                ["powershell", "-command", "Get-Command", "Set-Clipboard"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _test_macos_clipboard(self) -> bool:
        """Test macOS pbcopy/pbpaste availability."""

        try:
            result = subprocess.run(["which", "pbcopy"], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def _test_linux_clipboard(self) -> bool:
        """Test Linux clipboard utilities."""

        try:
            # Check for xclip or xsel
            for cmd in ["xclip", "xsel"]:
                result = subprocess.run(["which", cmd], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return True
            return False
        except Exception:
            return False
