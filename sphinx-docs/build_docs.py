#!/usr/bin/env python3
"""
Script automático para build e validação da documentação Sphinx.
Inclui verificações de integridade, links quebrados e cobertura.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple

# Configurações
DOCS_DIR = Path(__file__).parent
PROJECT_ROOT = DOCS_DIR.parent
BUILD_DIR = DOCS_DIR / "_build"
SOURCE_DIR = DOCS_DIR


def run_command(cmd: List[str], cwd: Path = DOCS_DIR) -> Tuple[int, str, str]:
    """Executar comando e retornar código de saída e output."""
    print(f"🔄 Executando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Comando excedeu timeout de 5 minutos"
    except Exception as e:
        return 1, "", str(e)


def install_dependencies() -> bool:
    """Instalar dependências da documentação."""
    print("📦 Instalando dependências da documentação...")
    
    code, stdout, stderr = run_command([
        sys.executable, "-m", "pip", "install", "-r", "requirements-docs.txt"
    ])
    
    if code == 0:
        print("✅ Dependências instaladas com sucesso")
        return True
    else:
        print(f"❌ Erro ao instalar dependências: {stderr}")
        return False


def clean_build() -> bool:
    """Limpar diretório de build."""
    print("🧹 Limpando build anterior...")
    
    if BUILD_DIR.exists():
        code, _, stderr = run_command([
            "rm" if os.name != 'nt' else "rmdir",
            "-rf" if os.name != 'nt' else "/s",
            str(BUILD_DIR)
        ])
        
        if code != 0:
            print(f"⚠️ Aviso ao limpar build: {stderr}")
    
    # Limpar cache do autoapi também
    autoapi_dir = DOCS_DIR / "autoapi"
    if autoapi_dir.exists():
        code, _, stderr = run_command([
            "rm" if os.name != 'nt' else "rmdir",
            "-rf" if os.name != 'nt' else "/s",
            str(autoapi_dir)
        ])
        
        if code != 0:
            print(f"⚠️ Aviso ao limpar autoapi: {stderr}")
    
    print("✅ Build limpo")
    return True


def check_source_files() -> bool:
    """Verificar se arquivos fonte existem."""
    print("📋 Verificando arquivos fonte...")
    
    required_files = [
        "index.rst",
        "conf.py",
        "requirements-docs.txt",
        "user-guide/installation.rst",
        "user-guide/getting-started.rst",
        "api/index.rst",
        "tutorials/data-import.rst",
        "dev-guide/architecture.rst",
    ]
    
    missing_files = []
    for file in required_files:
        file_path = DOCS_DIR / file
        if not file_path.exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Arquivos fonte ausentes: {missing_files}")
        return False
    
    print("✅ Todos os arquivos fonte presentes")
    return True


def build_html() -> bool:
    """Build HTML da documentação."""
    print("🏗️ Construindo documentação HTML...")
    
    cmd = [
        "sphinx-build",
        "-b", "html",
        "-W",  # Tratar warnings como erros
        "--keep-going",  # Continuar mesmo com erros
        str(SOURCE_DIR),
        str(BUILD_DIR / "html")
    ]
    
    code, stdout, stderr = run_command(cmd)
    
    if code == 0:
        print("✅ Documentação HTML construída com sucesso")
        print(f"📖 Disponível em: {BUILD_DIR / 'html' / 'index.html'}")
        return True
    else:
        print(f"❌ Erro no build HTML:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def build_pdf() -> bool:
    """Build PDF da documentação."""
    print("📄 Construindo documentação PDF...")
    
    # Verificar se LaTeX está disponível
    code, _, _ = run_command(["latex", "--version"])
    if code != 0:
        print("⚠️ LaTeX não disponível, pulando build PDF")
        return True
    
    cmd = [
        "sphinx-build",
        "-b", "latex",
        str(SOURCE_DIR),
        str(BUILD_DIR / "latex")
    ]
    
    code, stdout, stderr = run_command(cmd)
    
    if code != 0:
        print(f"❌ Erro no build LaTeX: {stderr}")
        return False
    
    # Compilar PDF
    code, stdout, stderr = run_command([
        "make", "-C", str(BUILD_DIR / "latex")
    ])
    
    if code == 0:
        print("✅ Documentação PDF construída com sucesso")
        pdf_path = BUILD_DIR / "latex" / "FuelTuneAnalyzer.pdf"
        if pdf_path.exists():
            print(f"📄 PDF disponível em: {pdf_path}")
        return True
    else:
        print(f"❌ Erro na compilação PDF: {stderr}")
        return False


def check_links() -> bool:
    """Verificar links quebrados."""
    print("🔗 Verificando links...")
    
    cmd = [
        "sphinx-build",
        "-b", "linkcheck",
        str(SOURCE_DIR),
        str(BUILD_DIR / "linkcheck")
    ]
    
    code, stdout, stderr = run_command(cmd)
    
    # Linkcheck pode retornar código != 0 mesmo com links válidos
    # Vamos analisar o output
    linkcheck_output = BUILD_DIR / "linkcheck" / "output.txt"
    if linkcheck_output.exists():
        with open(linkcheck_output, 'r', encoding='utf-8') as f:
            content = f.read()
            
        broken_links = [line for line in content.split('\n') if 'broken' in line.lower()]
        
        if broken_links:
            print(f"⚠️ Links quebrados encontrados:")
            for link in broken_links[:10]:  # Mostrar apenas primeiros 10
                print(f"  - {link}")
            if len(broken_links) > 10:
                print(f"  ... e mais {len(broken_links) - 10} links")
            return False
        else:
            print("✅ Todos os links estão funcionando")
            return True
    else:
        print("⚠️ Não foi possível verificar links")
        return True


def check_docstring_coverage() -> bool:
    """Verificar cobertura de docstrings."""
    print("📊 Verificando cobertura de docstrings...")
    
    try:
        # Importar módulos do projeto para verificar docstrings
        sys.path.insert(0, str(PROJECT_ROOT))
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        
        missing_docstrings = []
        
        # Verificar módulos principais
        modules_to_check = [
            "src.data.csv_parser",
            "src.data.models", 
            "src.analysis.performance",
            "src.ui.components.chart_builder"
        ]
        
        for module_name in modules_to_check:
            try:
                module = __import__(module_name, fromlist=[''])
                
                # Verificar funções públicas
                for attr_name in dir(module):
                    if not attr_name.startswith('_'):
                        attr = getattr(module, attr_name)
                        if callable(attr) and not hasattr(attr, '__doc__') or not attr.__doc__:
                            missing_docstrings.append(f"{module_name}.{attr_name}")
                            
            except ImportError as e:
                print(f"⚠️ Não foi possível importar {module_name}: {e}")
        
        if missing_docstrings:
            print(f"⚠️ Docstrings ausentes: {len(missing_docstrings)}")
            for item in missing_docstrings[:5]:  # Mostrar apenas primeiros 5
                print(f"  - {item}")
            if len(missing_docstrings) > 5:
                print(f"  ... e mais {len(missing_docstrings) - 5} itens")
            return len(missing_docstrings) < 10  # Aceitar até 10 faltando
        else:
            print("✅ Cobertura de docstrings adequada")
            return True
            
    except Exception as e:
        print(f"⚠️ Erro ao verificar docstrings: {e}")
        return True  # Não falhar por isso


def validate_rst_syntax() -> bool:
    """Validar sintaxe RST dos arquivos."""
    print("📝 Validando sintaxe RST...")
    
    rst_files = list(DOCS_DIR.rglob("*.rst"))
    errors = []
    
    for rst_file in rst_files:
        # Usar rstcheck para validar sintaxe
        code, stdout, stderr = run_command([
            "rstcheck", str(rst_file)
        ])
        
        if code != 0:
            errors.append(f"{rst_file.name}: {stderr}")
    
    if errors:
        print(f"❌ Erros de sintaxe RST encontrados:")
        for error in errors[:5]:  # Mostrar apenas primeiros 5
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... e mais {len(errors) - 5} erros")
        return False
    else:
        print("✅ Sintaxe RST válida")
        return True


def generate_coverage_report() -> bool:
    """Gerar relatório de cobertura da documentação."""
    print("📊 Gerando relatório de cobertura...")
    
    cmd = [
        "sphinx-build",
        "-b", "coverage",
        str(SOURCE_DIR),
        str(BUILD_DIR / "coverage")
    ]
    
    code, stdout, stderr = run_command(cmd)
    
    if code == 0:
        coverage_file = BUILD_DIR / "coverage" / "python.txt"
        if coverage_file.exists():
            with open(coverage_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("✅ Relatório de cobertura gerado")
            print(f"📄 Disponível em: {coverage_file}")
            
            # Extrair estatísticas básicas
            lines = content.split('\n')
            undoc_count = len([l for l in lines if 'undocumented' in l.lower()])
            total_count = len([l for l in lines if l.strip() and not l.startswith('=')])
            
            if total_count > 0:
                coverage_pct = ((total_count - undoc_count) / total_count) * 100
                print(f"📈 Cobertura estimada: {coverage_pct:.1f}%")
                
                if coverage_pct < 80:
                    print("⚠️ Cobertura de documentação abaixo de 80%")
            
            return True
        else:
            print("⚠️ Arquivo de cobertura não encontrado")
            return True
    else:
        print(f"❌ Erro ao gerar cobertura: {stderr}")
        return False


def serve_docs(port: int = 8000) -> bool:
    """Servir documentação localmente."""
    html_dir = BUILD_DIR / "html"
    
    if not html_dir.exists():
        print("❌ Build HTML não encontrado. Execute o build primeiro.")
        return False
    
    print(f"🚀 Servindo documentação em http://localhost:{port}")
    print("Pressione Ctrl+C para parar")
    
    try:
        code, _, stderr = run_command([
            sys.executable, "-m", "http.server", str(port)
        ], cwd=html_dir)
        
        return code == 0
    except KeyboardInterrupt:
        print("\n✅ Servidor parado")
        return True


def main():
    parser = argparse.ArgumentParser(description="Build e validação da documentação")
    parser.add_argument("--clean", action="store_true", help="Limpar build anterior")
    parser.add_argument("--html", action="store_true", help="Build apenas HTML")
    parser.add_argument("--pdf", action="store_true", help="Build apenas PDF")
    parser.add_argument("--serve", action="store_true", help="Servir documentação")
    parser.add_argument("--port", type=int, default=8000, help="Porta para servir")
    parser.add_argument("--validate", action="store_true", help="Apenas validação")
    parser.add_argument("--all", action="store_true", help="Build completo (padrão)")
    parser.add_argument("--skip-deps", action="store_true", help="Pular instalação de deps")
    
    args = parser.parse_args()
    
    # Se nenhuma opção específica, fazer build completo
    if not any([args.html, args.pdf, args.serve, args.validate]):
        args.all = True
    
    print("🚀 FuelTune Analyzer - Build de Documentação")
    print("=" * 50)
    
    success = True
    
    # Instalar dependências
    if not args.skip_deps:
        if not install_dependencies():
            sys.exit(1)
    
    # Limpar build se solicitado
    if args.clean or args.all:
        clean_build()
    
    # Verificar arquivos fonte
    if not check_source_files():
        sys.exit(1)
    
    # Validação apenas
    if args.validate:
        print("\n🔍 Executando validações...")
        success &= validate_rst_syntax()
        success &= check_docstring_coverage()
        
        if success:
            print("\n✅ Todas as validações passaram!")
        else:
            print("\n❌ Algumas validações falharam")
        
        sys.exit(0 if success else 1)
    
    # Build HTML
    if args.html or args.all:
        if not build_html():
            success = False
    
    # Build PDF
    if args.pdf or args.all:
        if not build_pdf():
            success = False
    
    # Validações pós-build
    if args.all:
        print("\n🔍 Executando validações...")
        success &= check_links()
        success &= generate_coverage_report()
        success &= validate_rst_syntax()
        success &= check_docstring_coverage()
    
    # Servir documentação
    if args.serve:
        serve_docs(args.port)
    
    # Resultado final
    print("\n" + "=" * 50)
    if success:
        print("✅ Build da documentação concluído com sucesso!")
        if BUILD_DIR.exists():
            html_path = BUILD_DIR / "html" / "index.html"
            if html_path.exists():
                print(f"📖 HTML: {html_path}")
            
            pdf_path = BUILD_DIR / "latex" / "FuelTuneAnalyzer.pdf"
            if pdf_path.exists():
                print(f"📄 PDF: {pdf_path}")
    else:
        print("❌ Build da documentação falhou!")
        print("Verifique os erros acima e tente novamente.")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()