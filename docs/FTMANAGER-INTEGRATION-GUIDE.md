# FTManager Integration Guide

## Guia Completo de Integração FTManager

Este guia fornece instruções detalhadas para usar a integração FTManager no FuelTune Streamlit, permitindo import/export sem perdas de dados entre as duas plataformas.

## 🎯 Visão Geral

A integração FTManager oferece:
- **Import automático** de tabelas via clipboard
- **Export compatível** para FTManager  
- **Detecção inteligente** de formatos
- **Validação robusta** de dados
- **Interface profissional** sem emojis
- **Performance otimizada** (< 1s)

## 📦 Componentes Principais

### FTManagerIntegrationBridge
Classe principal que orquestra todas as operações de integração.

```python
from src.integration import FTManagerIntegrationBridge

# Inicialização
bridge = FTManagerIntegrationBridge()
```

### Principais Métodos

#### 1. Import de Dados
```python
# Import automático com validação
result = bridge.import_from_clipboard(
    validate_data=True,          # Validar dados
    auto_detect_format=True,     # Detecção automática
    expected_dimensions=(16, 16) # Dimensões esperadas
)

if result.success:
    map_data = result.data                    # DataFrame com dados
    detected_format = result.detected_format # Formato detectado
    print(f"Importado: {map_data.shape}")
else:
    print(f"Erro: {result.errors}")
```

#### 2. Export de Dados  
```python
# Export com formato específico
result = bridge.export_to_clipboard(
    map_data,                        # DataFrame para exportar
    format_name="standard_16x16",    # Formato FTManager
    validate_before_export=True      # Validação prévia
)

if result.success:
    print("✅ Dados no clipboard para FTManager")
    print(f"Formato usado: {result.detected_format}")
else:
    print(f"Erro: {result.errors}")
```

#### 3. Interface Streamlit
```python
# UI completa integrada
bridge.create_streamlit_ui()
```

Esta função cria uma interface completa com:
- Tab de Import com controles de validação
- Tab de Export com seleção de formato  
- Tab de Detecção de formato
- Tab de Validação de dados
- Feedback profissional sem emojis

## 🔍 Detecção de Formatos

### Formatos Suportados

| Formato | Descrição | Separador | Exemplo |
|---------|-----------|-----------|---------|
| `tabulated` | Tab-separated (padrão FTManager) | `\t` | `0.85\t0.86\t0.87` |
| `csv` | Comma-separated values | `,` | `0.85,0.86,0.87` |
| `hex` | Hexadecimal format | `\t` | `A5\tB6\tC7` |
| `binary` | Binary format | `\t` | `101\t110\t111` |

### Dimensões Comuns

| Tamanho | Uso Típico | Suporte |
|---------|------------|---------|
| 8x8 | Mapas pequenos | ✅ |
| 12x12 | Mapas médios | ✅ |
| 16x16 | **Padrão FTManager** | ✅ |
| 20x20 | Mapas grandes | ✅ |
| 32x32 | Mapas muito grandes | ✅ |

### Exemplo de Detecção
```python
from src.integration import FTManagerFormatDetector

detector = FTManagerFormatDetector()

# Detectar formato em conteúdo
content = """0.850\t0.860\t0.870
0.840\t0.850\t0.860
0.830\t0.840\t0.850"""

result = detector.detect_format(content)

if result.success:
    format_spec = result.format_spec
    print(f"Formato: {format_spec.format_type}")
    print(f"Dimensões: {format_spec.dimensions}") 
    print(f"Separador: '{format_spec.separator}'")
    print(f"Headers: {format_spec.has_headers}")
    print(f"Confiança: {result.confidence:.2f}")
```

## ✅ Validação de Dados

### Validação Automática
```python
from src.integration import FTManagerValidator

validator = FTManagerValidator()

# Validar conteúdo do clipboard
result = validator.validate_clipboard_data(
    content,
    expected_dimensions=(16, 16),
    strict_mode=False
)

if result.is_valid:
    print(f"✅ Dados válidos (confiança: {result.confidence:.2f})")
else:
    print("❌ Problemas encontrados:")
    for error in result.errors:
        print(f"  - {error}")
    
    for warning in result.warnings:
        print(f"  ⚠️ {warning}")
```

### Validação de DataFrame
```python
# Validar DataFrame antes do export
result = validator.validate_map_data(
    map_dataframe,
    check_numeric=True,
    check_dimensions=True,
    check_completeness=True
)
```

## 📋 Clipboard Management

### Gerenciamento Cross-Platform
```python
from src.integration import FTClipboardManager

clipboard = FTClipboardManager()

# Verificar disponibilidade
status = clipboard.get_status()
print(f"Clipboard disponível: {status['available']}")
print(f"Métodos: {status['available_methods']}")

# Operações básicas
content_result = clipboard.get_content()
if content_result.success:
    print(f"Conteúdo: {len(content_result.content)} chars")

set_result = clipboard.set_content("Dados para FTManager")
if set_result.success:
    print("✅ Dados copiados para clipboard")
```

### Fallbacks Automáticos
O gerenciador tenta múltiplos métodos automaticamente:
1. **pyperclip** (preferido) - Cross-platform
2. **tkinter** - Built-in Python
3. **PowerShell** (Windows) - Comandos do sistema
4. **pbcopy/pbpaste** (macOS) - Comandos nativos
5. **xclip/xsel** (Linux) - Utilitários X11

## 🎨 Interface Streamlit

### Criação de UI Profissional
```python
import streamlit as st
from src.integration import FTManagerIntegrationBridge

def create_ftmanager_page():
    """Página dedicada ao FTManager."""
    
    st.title("FTManager Integration")
    st.markdown("---")
    
    # Inicializar bridge
    if 'ftmanager_bridge' not in st.session_state:
        st.session_state.ftmanager_bridge = FTManagerIntegrationBridge()
    
    bridge = st.session_state.ftmanager_bridge
    
    # Interface completa
    bridge.create_streamlit_ui()
    
    # Estatísticas da integração
    with st.expander("Integration Statistics"):
        stats = bridge.get_integration_stats()
        st.json(stats)
```

### Componentes UI Incluídos

#### Tab de Import
- Checkbox para validação de dados
- Checkbox para detecção automática  
- Inputs para dimensões esperadas
- Botão de import com spinner
- Display de resultados profissional

#### Tab de Export  
- Seletor de formato de export
- Checkbox para validação prévia
- Botão de export com feedback
- Preview do conteúdo formatado

#### Tab de Detecção
- Botão para detecção de formato
- Display detalhado do formato detectado
- Métricas de confiança

#### Tab de Validação
- Seletor de formato esperado
- Controles de validação de dimensões
- Botão de validação
- Relatório detalhado de issues

## 🔧 Configuração Avançada

### Formatos Personalizados
```python
# Criar formato personalizado
custom_format = bridge.core_bridge.create_custom_format(
    name="custom_24x24",
    dimensions=(24, 24),
    separator=',',
    has_headers=False,
    decimal_places=4
)

# Usar no export
result = bridge.export_to_clipboard(
    map_data,
    custom_format={'format_type': 'csv', 'dimensions': (24, 24), ...}
)
```

### Configuração de Performance
```python
# Ajustar limites de performance
detector = FTManagerFormatDetector()
detector.performance_limits['max_validation_time_ms'] = 300  # 300ms
detector.performance_limits['max_data_size_mb'] = 100        # 100MB
```

## 📊 Monitoramento e Debugging

### Estatísticas de Uso
```python
# Obter estatísticas detalhadas
stats = bridge.get_integration_stats()

print(f"Operações: {stats['operation_count']}")  
print(f"Última operação: {stats['last_operation_time']}")
print(f"Status clipboard: {stats['clipboard_status']}")
print(f"Componentes: {stats['components_status']}")
```

### Análise de Conteúdo
```python
# Analisar estrutura do conteúdo
analysis = detector.analyze_content_structure(clipboard_content)

print(f"Linhas: {analysis['line_statistics']['total_lines']}")
print(f"Caracteres: {analysis['character_analysis']['total_characters']}")
print(f"Separadores detectados: {analysis['separator_analysis']}")
print(f"Ratio numérico: {analysis['content_type']['numeric_ratio']:.2f}")
```

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Clipboard não funciona
```python
# Verificar status
status = clipboard.check_availability()
if not status.success:
    print("Métodos tentados:", status.metadata.get('methods_tried', []))
    print("Instalar dependências: pip install pyperclip")
```

#### 2. Formato não detectado  
```python
# Debug detecção
result = detector.detect_format(content, confidence_threshold=0.5)
print(f"Candidatos: {len(result.candidates)}")
for candidate in result.candidates:
    print(f"  {candidate.format_type}: {candidate.confidence:.2f}")
```

#### 3. Validação falhando
```python  
# Validação detalhada
result = validator.validate_clipboard_data(content, strict_mode=False)
print(f"Issues encontrados: {len(result.issues)}")
for issue in result.issues:
    print(f"  {issue.severity}: {issue.message}")
    if issue.suggestion:
        print(f"    Sugestão: {issue.suggestion}")
```

## 🚀 Exemplos de Uso Completos

### Exemplo 1: Workflow Básico
```python
import streamlit as st
from src.integration import FTManagerIntegrationBridge

def ftmanager_workflow():
    """Workflow básico de integração."""
    
    bridge = FTManagerIntegrationBridge()
    
    st.header("FTManager Integration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Import")
        if st.button("Import from FTManager"):
            with st.spinner("Importing..."):
                result = bridge.import_from_clipboard()
            
            if result.success:
                st.success("✅ Import successful!")
                st.dataframe(result.data.head())
                
                # Salvar no session state
                st.session_state['current_map'] = result.data
            else:
                st.error("❌ Import failed")
                for error in result.errors:
                    st.write(f"• {error}")
    
    with col2:
        st.subheader("Export")
        if 'current_map' in st.session_state:
            if st.button("Export to FTManager"):
                with st.spinner("Exporting..."):
                    result = bridge.export_to_clipboard(
                        st.session_state['current_map']
                    )
                
                if result.success:
                    st.success("✅ Export successful!")
                    st.info("Data copied to clipboard - paste in FTManager")
                else:
                    st.error("❌ Export failed")
        else:
            st.info("Import data first to enable export")
```

### Exemplo 2: Validação Avançada
```python
def advanced_validation_example():
    """Exemplo de validação avançada."""
    
    bridge = FTManagerIntegrationBridge()
    validator = bridge.validator
    
    st.header("Advanced Validation")
    
    # Upload de arquivo para teste
    uploaded_file = st.file_uploader("Upload test data", type=['txt', 'csv'])
    
    if uploaded_file:
        content = uploaded_file.read().decode('utf-8')
        
        # Validação completa
        result = validator.validate_clipboard_data(
            content,
            expected_dimensions=(16, 16),
            strict_mode=st.checkbox("Strict mode")
        )
        
        # Display detalhado dos resultados
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if result.is_valid:
                st.success(f"✅ Valid (confidence: {result.confidence:.2f})")
            else:
                st.error("❌ Invalid")
        
        with col2:
            st.metric("Errors", len(result.errors))
            st.metric("Warnings", len(result.warnings))
        
        with col3:
            if 'validation_duration_ms' in result.performance_metrics:
                duration = result.performance_metrics['validation_duration_ms']
                st.metric("Validation Time", f"{duration:.0f}ms")
        
        # Detalhes dos problemas
        if result.issues:
            st.subheader("Issues Found")
            for issue in result.issues:
                if issue.severity == 'error':
                    st.error(f"**{issue.rule_name}**: {issue.message}")
                elif issue.severity == 'warning':
                    st.warning(f"**{issue.rule_name}**: {issue.message}")
                else:
                    st.info(f"**{issue.rule_name}**: {issue.message}")
                
                if issue.suggestion:
                    st.write(f"💡 **Suggestion**: {issue.suggestion}")
```

## 📚 Referências Adicionais

### Documentação Técnica
- [PYTHON-CODE-STANDARDS.md](PYTHON-CODE-STANDARDS.md) - Padrões de código
- [FTMANAGER-BRIDGE-LOG.md](agents/executed/FTMANAGER-BRIDGE-LOG.md) - Log de implementação

### Testes
- [test_ftmanager_integration.py](../tests/unit/test_ftmanager_integration.py) - Testes unitários completos

### Performance
- Detecção de formato: < 100ms
- Validação completa: < 200ms  
- Import/export: < 500ms
- Operações típicas: < 1s

---

*Este guia cobre todos os aspectos da integração FTManager. Para suporte adicional, consulte os logs de implementação e testes unitários.*