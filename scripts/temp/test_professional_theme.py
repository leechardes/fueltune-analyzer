"""
Teste básico do tema profissional - FuelTune Analyzer
====================================================

Script de teste para validar a implementação do tema corporativo
sem executar toda a aplicação.

Author: A04-STREAMLIT-PROFESSIONAL Agent
Created: 2025-01-03
"""

import sys
from pathlib import Path

# Add src directory to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def test_theme_import():
    """Testar importação do tema profissional."""
    try:
        from src.ui.theme_config import ProfessionalTheme, ThemeColors, apply_professional_theme
        print("✓ Importação do tema profissional: OK")
        return True
    except ImportError as e:
        print(f"✗ Erro na importação do tema: {e}")
        return False

def test_theme_colors():
    """Testar configuração de cores."""
    try:
        from src.ui.theme_config import ThemeColors
        
        colors = ThemeColors()
        
        # Testar cores principais
        assert colors.primary == "#1976D2", "Cor primária incorreta"
        assert colors.success == "#4CAF50", "Cor de sucesso incorreta"
        assert colors.error == "#F44336", "Cor de erro incorreta"
        
        print("✓ Configuração de cores: OK")
        return True
    except Exception as e:
        print(f"✗ Erro na configuração de cores: {e}")
        return False

def test_theme_generation():
    """Testar geração de CSS."""
    try:
        from src.ui.theme_config import ProfessionalTheme
        
        theme = ProfessionalTheme()
        css = theme._generate_professional_css()
        
        # Verificar se contém elementos essenciais
        assert "Material Icons" in css, "Material Icons não encontrado"
        assert "--primary-color" in css, "Variáveis CSS não encontradas"
        assert ".material-icons" in css, "Classe de ícones não encontrada"
        
        print("✓ Geração de CSS: OK")
        return True
    except Exception as e:
        print(f"✗ Erro na geração de CSS: {e}")
        return False

def test_theme_components():
    """Testar componentes do tema."""
    try:
        from src.ui.theme_config import ProfessionalTheme
        
        theme = ProfessionalTheme()
        
        # Testar criação de badge
        badge = theme.create_status_badge("success", "Teste")
        assert "check_circle" in badge, "Ícone de sucesso não encontrado"
        assert "Teste" in badge, "Texto do badge não encontrado"
        
        # Testar criação de botão
        button = theme.create_icon_button("settings", "Configurações")
        assert "settings" in button, "Ícone do botão não encontrado"
        assert "Configurações" in button, "Texto do botão não encontrado"
        
        # Testar cabeçalho
        header = theme.create_section_header("dashboard", "Dashboard", "Teste")
        assert "dashboard" in header, "Ícone do cabeçalho não encontrado"
        assert "Dashboard" in header, "Título do cabeçalho não encontrado"
        
        print("✓ Componentes do tema: OK")
        return True
    except Exception as e:
        print(f"✗ Erro nos componentes do tema: {e}")
        return False

def test_material_cards():
    """Testar criação de cards."""
    try:
        from src.ui.theme_config import create_material_card
        
        card = create_material_card("Teste", "Conteúdo do teste", "info")
        assert "Teste" in card, "Título do card não encontrado"
        assert "Conteúdo do teste" in card, "Conteúdo do card não encontrado"
        assert "info" in card, "Ícone do card não encontrado"
        
        print("✓ Material Cards: OK")
        return True
    except Exception as e:
        print(f"✗ Erro nos Material Cards: {e}")
        return False

def main():
    """Executar todos os testes."""
    print("=" * 60)
    print("TESTE DO TEMA PROFISSIONAL - FUELTUNE ANALYZER")
    print("=" * 60)
    print()
    
    tests = [
        test_theme_import,
        test_theme_colors,
        test_theme_generation,
        test_theme_components,
        test_material_cards,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Erro inesperado no teste {test.__name__}: {e}")
    
    print()
    print("=" * 60)
    print(f"RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Tema profissional funcionando corretamente.")
        print()
        print("PRÓXIMOS PASSOS:")
        print("1. Execute a aplicação: python main.py")
        print("2. Verifique se os Material Icons carregam corretamente")
        print("3. Teste a responsividade em diferentes tamanhos de tela")
        print("4. Valide a aparência corporativa em todas as páginas")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)