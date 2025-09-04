#!/usr/bin/env python3
"""
FuelTune Streamlit - Main Entry Point
=====================================

Ponto de entrada principal para a aplicação FuelTune Streamlit.
Este arquivo coordena a inicialização de todos os sistemas e fornece
uma interface unificada para execução da aplicação.

Usage:
    python main.py --help                    # Mostrar ajuda
    python main.py --streamlit              # Executar Streamlit (default)
    python main.py --test                   # Executar testes
    python main.py --docs                   # Gerar documentação
    python main.py --version                # Mostrar versão
    python main.py --health-check          # Verificar saúde do sistema
    python main.py --setup                  # Setup inicial
    python main.py --clean                  # Limpar caches e temporários

Environment Variables:
    FUELTUNE_DEBUG=1                        # Habilitar modo debug
    FUELTUNE_LOG_LEVEL=INFO                 # Nível de log
    FUELTUNE_PORT=8501                      # Porta do Streamlit
    FUELTUNE_HOST=localhost                 # Host do Streamlit

Author: FuelTune Development Team
Version: 1.0.0
"""

import argparse
import atexit
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import NoReturn, Optional

# Add src directory to Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

# Import configuration and core modules
try:
    from config import config
    from src.utils.logger import get_logger
except ImportError as e:
    print(f"ERRO: Falha ao importar módulos essenciais: {e}")
    print("Certifique-se de que o ambiente está configurado corretamente.")
    sys.exit(1)

# Global logger
logger = get_logger("fueltune_main")


class FuelTuneApplication:
    """Classe principal para gerenciar a aplicação FuelTune."""

    def __init__(self):
        """Inicializar a aplicação."""
        self.initialized = False
        self.shutdown_handlers = []

        # Register cleanup handlers
        atexit.register(self.cleanup)
        # Comentado: signal handlers não funcionam em threads do Streamlit
        # signal.signal(signal.SIGTERM, self._signal_handler)
        # signal.signal(signal.SIGINT, self._signal_handler)

        logger.info(f"FuelTune Application v{config.APP_VERSION} inicializada")

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        logger.info(f"Sinal recebido: {signum}. Iniciando shutdown graceful...")
        self.cleanup()
        sys.exit(0)

    def initialize_system(self) -> bool:
        """
        Inicializar todos os sistemas da aplicação.

        Returns:
            bool: True se inicialização foi bem-sucedida
        """
        if self.initialized:
            return True

        logger.info("Inicializando sistemas...")

        try:
            # Initialize database
            logger.info("Inicializando database...")
            from src.data.database import get_database

            db = get_database()

            # Initialize cache
            logger.info("Inicializando cache...")
            from src.data.cache import get_cache_manager

            cache = get_cache_manager()

            # Initialize integration system
            logger.info("Inicializando sistema de integração...")
            from src.integration import initialize_integration_system

            integration_success = initialize_integration_system()

            if not integration_success:
                logger.warning("Sistema de integração falhou ao inicializar")

            # Create necessary directories
            self._create_directories()

            self.initialized = True
            logger.info("Todos os sistemas inicializados com sucesso")
            return True

        except Exception as e:
            logger.error(f"Falha na inicialização: {e}", exc_info=True)
            return False

    def _create_directories(self):
        """Criar diretórios necessários se não existirem."""
        directories = [
            PROJECT_ROOT / "logs",
            PROJECT_ROOT / "cache",
            PROJECT_ROOT / "data" / "exports",
            PROJECT_ROOT / "data" / "processed",
            PROJECT_ROOT / "data" / "raw",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Diretórios criados/verificados: {len(directories)}")

    def run_streamlit(self, host: str = "localhost", port: int = 8501) -> NoReturn:
        """
        Executar a aplicação Streamlit.

        Args:
            host: Host para bind
            port: Porta para bind
        """
        if not self.initialize_system():
            logger.error("Falha na inicialização. Não é possível executar Streamlit.")
            sys.exit(1)

        logger.info(f"Iniciando Streamlit em {host}:{port}")

        # Prepare Streamlit command
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(PROJECT_ROOT / "app.py"),
            "--server.address",
            host,
            "--server.port",
            str(port),
            "--server.headless",
            "true" if os.getenv("FUELTUNE_HEADLESS") else "false",
            "--browser.gatherUsageStats",
            "false",
            "--server.fileWatcherType",
            "none" if os.getenv("FUELTUNE_PRODUCTION") else "auto",
        ]

        # Add theme configuration
        cmd.extend(
            [
                "--theme.base",
                "light",
                "--theme.primaryColor",
                "#FF6B35",
                "--theme.backgroundColor",
                "#FFFFFF",
                "--theme.secondaryBackgroundColor",
                "#F0F2F6",
                "--theme.textColor",
                "#262730",
            ]
        )

        try:
            # Execute Streamlit
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Streamlit terminou com erro: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Shutdown solicitado pelo usuário")
            sys.exit(0)

    def run_tests(self, coverage: bool = True, verbose: bool = True) -> int:
        """
        Executar suite de testes.

        Args:
            coverage: Incluir relatório de cobertura
            verbose: Modo verboso

        Returns:
            int: Código de saída dos testes
        """
        logger.info("Executando testes...")

        cmd = [sys.executable, "-m", "pytest"]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(
                [
                    "--cov=src",
                    "--cov-report=html:htmlcov",
                    "--cov-report=term-missing",
                    "--cov-fail-under=75",
                ]
            )

        cmd.append("tests/")

        try:
            result = subprocess.run(cmd, cwd=PROJECT_ROOT)
            return result.returncode
        except Exception as e:
            logger.error(f"Erro ao executar testes: {e}")
            return 1

    def generate_docs(self) -> int:
        """
        Gerar documentação.

        Returns:
            int: Código de saída da geração
        """
        logger.info("Gerando documentação...")

        docs_dir = PROJECT_ROOT / "docs"

        if not (docs_dir / "conf.py").exists():
            logger.error("Configuração do Sphinx não encontrada")
            return 1

        cmd = [
            sys.executable,
            "-m",
            "sphinx",
            "-b",
            "html",
            str(docs_dir),
            str(docs_dir / "_build" / "html"),
        ]

        try:
            result = subprocess.run(cmd, cwd=PROJECT_ROOT)
            if result.returncode == 0:
                logger.info(f"Documentação gerada em: {docs_dir / '_build' / 'html'}")
            return result.returncode
        except Exception as e:
            logger.error(f"Erro ao gerar documentação: {e}")
            return 1

    def health_check(self) -> int:
        """
        Verificar saúde do sistema.

        Returns:
            int: 0 se saudável, 1 se problema
        """
        logger.info("Executando verificação de saúde...")

        checks = []

        # Check system initialization
        try:
            success = self.initialize_system()
            checks.append(("System Initialization", success))
        except Exception as e:
            checks.append(("System Initialization", False, str(e)))

        # Check database
        try:
            from src.data.database import get_database

            db = get_database()
            stats = db.get_database_stats()
            checks.append(("Database", True))
        except Exception as e:
            checks.append(("Database", False, str(e)))

        # Check cache
        try:
            from src.data.cache import get_cache_manager

            cache = get_cache_manager()
            cache_stats = cache.get_stats()
            checks.append(("Cache System", True))
        except Exception as e:
            checks.append(("Cache System", False, str(e)))

        # Check dependencies
        required_modules = [
            "streamlit",
            "pandas",
            "numpy",
            "plotly",
            "pandera",
            "sqlalchemy",
            "scipy",
        ]

        for module in required_modules:
            try:
                __import__(module)
                checks.append((f"Module {module}", True))
            except ImportError as e:
                checks.append((f"Module {module}", False, str(e)))

        # Print results
        print("\\n" + "=" * 60)
        print("FUELTUNE HEALTH CHECK REPORT")
        print("=" * 60)

        all_healthy = True
        for check in checks:
            status = "PASS" if check[1] else "FAIL"
            print(f"{check[0]:.<40} {status}")

            if not check[1]:
                all_healthy = False
                if len(check) > 2:
                    print(f"    Error: {check[2]}")

        print("=" * 60)

        if all_healthy:
            print("Sistema totalmente saudável!")
            logger.info("Health check passou - sistema saudável")
            return 0
        else:
            print("Sistema tem problemas que precisam de atenção")
            logger.warning("Health check falhou - sistema tem problemas")
            return 1

    def setup(self) -> int:
        """
        Executar setup inicial do sistema.

        Returns:
            int: Código de saída do setup
        """
        logger.info("Executando setup inicial...")

        try:
            # Initialize system
            if not self.initialize_system():
                logger.error("Falha na inicialização durante setup")
                return 1

            # Install pre-commit hooks
            if (PROJECT_ROOT / ".pre-commit-config.yaml").exists():
                logger.info("Instalando pre-commit hooks...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pre_commit", "install"],
                        cwd=PROJECT_ROOT,
                        check=True,
                    )
                    logger.info("Pre-commit hooks instalados")
                except subprocess.CalledProcessError:
                    logger.warning("Falha ao instalar pre-commit hooks")

            # Run health check
            logger.info("Verificando configuração...")
            health_result = self.health_check()

            if health_result == 0:
                logger.info("Setup concluído com sucesso!")
                return 0
            else:
                logger.warning("Setup concluído com avisos")
                return 1

        except Exception as e:
            logger.error(f"Erro durante setup: {e}", exc_info=True)
            return 1

    def clean(self) -> int:
        """
        Limpar caches e arquivos temporários.

        Returns:
            int: Código de saída da limpeza
        """
        logger.info("Limpando caches e arquivos temporários...")

        try:
            # Clean cache
            from src.data.cache import get_cache_manager

            cache = get_cache_manager()
            cache.clear_all()
            logger.info("Cache limpo")

            # Clean temporary directories
            temp_dirs = [
                PROJECT_ROOT / "__pycache__",
                PROJECT_ROOT / "src" / "__pycache__",
                PROJECT_ROOT / ".pytest_cache",
                PROJECT_ROOT / "htmlcov",
                PROJECT_ROOT / ".mypy_cache",
                PROJECT_ROOT / "logs" / "old",
            ]

            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    import shutil

                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.debug(f"Removido: {temp_dir}")

            # Clean log files older than 7 days
            logs_dir = PROJECT_ROOT / "logs"
            if logs_dir.exists():
                import time

                current_time = time.time()
                week_ago = current_time - (7 * 24 * 60 * 60)

                for log_file in logs_dir.glob("*.log*"):
                    if log_file.stat().st_mtime < week_ago:
                        log_file.unlink(missing_ok=True)
                        logger.debug(f"Log antigo removido: {log_file}")

            logger.info("Limpeza concluída")
            return 0

        except Exception as e:
            logger.error(f"Erro durante limpeza: {e}", exc_info=True)
            return 1

    def add_shutdown_handler(self, handler):
        """Adicionar handler de shutdown."""
        self.shutdown_handlers.append(handler)

    def cleanup(self):
        """Executar limpeza durante shutdown."""
        if not self.initialized:
            return

        logger.info("Executando shutdown graceful...")

        # Execute shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Erro em shutdown handler: {e}")

        # Shutdown integration system
        try:
            from src.integration import shutdown_integration_system

            shutdown_integration_system()
        except Exception as e:
            logger.error(f"Erro ao desligar sistema de integração: {e}")

        logger.info("Shutdown concluído")


def main():
    """Função principal."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="FuelTune Streamlit - Plataforma de Análise de Dados FuelTech",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    %(prog)s                              # Executar Streamlit (default)
    %(prog)s --test                      # Executar testes
    %(prog)s --test --no-coverage       # Executar testes sem cobertura
    %(prog)s --docs                     # Gerar documentação
    %(prog)s --health-check            # Verificar saúde do sistema
    %(prog)s --setup                   # Setup inicial
    %(prog)s --clean                   # Limpar caches

Variáveis de ambiente:
    FUELTUNE_DEBUG=1                   # Habilitar modo debug
    FUELTUNE_LOG_LEVEL=INFO           # Nível de log (DEBUG,INFO,WARNING,ERROR)
    FUELTUNE_PORT=8501                # Porta do Streamlit
    FUELTUNE_HOST=localhost           # Host do Streamlit
    FUELTUNE_HEADLESS=1               # Modo headless (sem browser)
    FUELTUNE_PRODUCTION=1             # Modo produção (desabilita file watcher)
        """,
    )

    # Command options
    parser.add_argument(
        "--version", action="version", version=f"FuelTune Streamlit v{config.APP_VERSION}"
    )

    parser.add_argument(
        "--streamlit", action="store_true", help="Executar aplicação Streamlit (default)"
    )

    parser.add_argument("--test", action="store_true", help="Executar suite de testes")

    parser.add_argument(
        "--no-coverage", action="store_true", help="Desabilitar relatório de cobertura nos testes"
    )

    parser.add_argument("--docs", action="store_true", help="Gerar documentação Sphinx")

    parser.add_argument(
        "--health-check", action="store_true", help="Executar verificação de saúde do sistema"
    )

    parser.add_argument("--setup", action="store_true", help="Executar setup inicial")

    parser.add_argument("--clean", action="store_true", help="Limpar caches e arquivos temporários")

    # Streamlit options
    parser.add_argument(
        "--host",
        default=os.getenv("FUELTUNE_HOST", "localhost"),
        help="Host para Streamlit (default: localhost)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("FUELTUNE_PORT", "8501")),
        help="Porta para Streamlit (default: 8501)",
    )

    parser.add_argument("--debug", action="store_true", help="Habilitar modo debug")

    args = parser.parse_args()

    # Set debug mode if requested
    if args.debug or os.getenv("FUELTUNE_DEBUG"):
        os.environ["FUELTUNE_DEBUG"] = "1"
        logging.getLogger().setLevel(logging.DEBUG)

    # Create application instance
    app = FuelTuneApplication()

    # Determine action
    if args.test:
        return app.run_tests(coverage=not args.no_coverage)
    elif args.docs:
        return app.generate_docs()
    elif args.health_check:
        return app.health_check()
    elif args.setup:
        return app.setup()
    elif args.clean:
        return app.clean()
    else:
        # Default: run Streamlit
        app.run_streamlit(host=args.host, port=args.port)


if __name__ == "__main__":
    sys.exit(main())
