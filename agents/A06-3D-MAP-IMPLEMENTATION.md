# A06 - Implementação de Melhorias nos Mapas 3D

## 📋 Objetivo
Implementar as melhorias identificadas pelo agente A05, adaptando todas as funcionalidades dos mapas 2D para os mapas 3D, seguindo rigorosamente os padrões de desenvolvimento Streamlit.

## 🎯 Escopo de Implementação

### Fase 1 - Fundação (CRÍTICO)
1. [ ] Criar e expandir `config/map_types_3d.json`
2. [ ] Implementar calculador automático 3D
3. [ ] Sistema dinâmico de enable/disable de células
4. [ ] Valores padrão estruturados

### Fase 2 - Funcionalidades Core
1. [ ] Interface modal do calculador
2. [ ] Sistema de templates inteligentes
3. [ ] Validações bidimensionais
4. [ ] Otimização de performance

## 📚 Padrões de Desenvolvimento

### OBRIGATÓRIO: Seguir docs/agents/shared/STREAMLIT-DEVELOPMENT-STANDARDS.md
- ✅ Usar session_state para gerenciamento de estado
- ✅ Implementar cache apropriado (@st.cache_data)
- ✅ Seguir padrões de UI/UX do Streamlit
- ✅ Validação de dados com feedback visual
- ✅ Modularização de código
- ✅ Documentação inline clara

## 🔧 Tarefas de Implementação

### 1. Expandir Configuração de Tipos (map_types_3d.json)
```json
{
  "main_fuel_3d_map": {
    "name": "Mapa Principal de Injeção 3D",
    "grid_size": 32,
    "x_axis_type": "RPM",
    "y_axis_type": "MAP",
    "unit": "ms",
    "min_value": 0.0,
    "max_value": 50.0,
    "description": "Mapa principal 3D baseado em RPM vs MAP",
    "default_rpm_enabled_count": 24,
    "default_map_enabled_count": 21,
    "default_rpm_values": [...],
    "default_map_values": [...],
    "default_rpm_enabled": [...],
    "default_map_enabled": [...],
    "turbo_adjustment": {
      "enable_positive_map_values": true,
      "aspirated_max_map_index": 10
    }
  },
  "ignition_timing_3d_map": {
    "name": "Mapa de Avanço de Ignição 3D",
    "grid_size": 32,
    "x_axis_type": "RPM",
    "y_axis_type": "MAP",
    "unit": "°",
    "min_value": -10.0,
    "max_value": 60.0,
    "description": "Avanço de ignição em graus"
  },
  "lambda_target_3d_map": {
    "name": "Mapa de Lambda Alvo 3D",
    "grid_size": 16,
    "x_axis_type": "RPM",
    "y_axis_type": "MAP",
    "unit": "λ",
    "min_value": 0.6,
    "max_value": 1.5,
    "description": "Target AFR/Lambda"
  }
}
```

### 2. Implementar Calculador Automático 3D

#### Arquivos a modificar:
- `src/ui/pages/fuel_maps_3d.py`

#### Funções a criar:
```python
def calculate_3d_map_values_universal(
    map_type: str,
    rpm_axis: List[float],
    map_axis: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = 'balanced',
    safety_factor: float = 1.0,
    **kwargs
) -> np.ndarray:
    """
    Calculador universal para mapas 3D.
    Adapta a lógica do 2D para superfícies.
    """
    pass

def calculate_fuel_3d_matrix(
    rpm_values: List[float],
    map_values: List[float],
    vehicle_data: Dict[str, Any],
    strategy: str = 'balanced'
) -> np.ndarray:
    """
    Calcula matriz de combustível 3D.
    Reutiliza funções do 2D adaptadas.
    """
    pass

def calculate_ignition_3d_matrix(
    rpm_values: List[float],
    map_values: List[float],
    vehicle_data: Dict[str, Any]
) -> np.ndarray:
    """
    Calcula matriz de avanço de ignição.
    """
    pass

def calculate_lambda_3d_matrix(
    rpm_values: List[float],
    map_values: List[float],
    vehicle_data: Dict[str, Any]
) -> np.ndarray:
    """
    Calcula matriz de lambda alvo.
    """
    pass
```

### 3. Interface Modal do Calculador

#### Componentes a adicionar:
```python
# Modal similar ao 2D
if st.button("🧮 Calcular Valores Automáticos"):
    st.session_state[f"show_3d_calculator_{session_key}"] = True

if st.session_state.get(f"show_3d_calculator_{session_key}", False):
    with st.container():
        st.markdown("### Calculador Automático de Mapas 3D")
        
        # Configurações em colunas
        calc_col1, calc_col2, calc_col3 = st.columns([2, 1, 1])
        
        with calc_col1:
            # Estratégia e configurações
            strategy = st.selectbox(...)
            safety_factor = st.slider(...)
            
        with calc_col2:
            # Dados do veículo
            st.metric("Cilindrada", ...)
            st.metric("Cilindros", ...)
            
        with calc_col3:
            # Preview 3D
            show_3d_preview(...)
```

### 4. Sistema Enable/Disable Dinâmico

```python
def get_default_3d_enabled_matrix(
    map_type: str,
    vehicle_data: Dict[str, Any]
) -> Tuple[List[bool], List[bool]]:
    """
    Retorna arrays de enable/disable para RPM e MAP
    baseado no tipo de motor e configuração.
    """
    config = load_3d_map_config(map_type)
    
    # Ajustar para turbo/aspirado
    if not vehicle_data.get('turbo'):
        # Desabilitar valores positivos de MAP para aspirado
        map_enabled = adjust_for_aspirated(config['default_map_enabled'])
    
    return rpm_enabled, map_enabled
```

### 5. Otimizações de Performance

```python
@st.cache_data
def calculate_3d_matrix_cached(
    map_type: str,
    rpm_axis_hash: str,
    map_axis_hash: str,
    vehicle_data_hash: str,
    strategy: str
) -> np.ndarray:
    """Versão cacheada do calculador."""
    pass

def render_matrix_viewport(
    matrix: np.ndarray,
    viewport_start: Tuple[int, int],
    viewport_size: Tuple[int, int] = (16, 16)
):
    """Renderiza apenas porção visível da matriz."""
    pass
```

### 6. Validações Avançadas

```python
def validate_3d_matrix(
    matrix: np.ndarray,
    min_value: float,
    max_value: float
) -> Tuple[bool, List[str]]:
    """
    Valida matriz 3D completa.
    Retorna status e lista de erros.
    """
    errors = []
    
    # Validar ranges
    if np.any(matrix < min_value):
        errors.append(f"Valores abaixo do mínimo: {min_value}")
    
    # Validar continuidade
    if not check_matrix_continuity(matrix):
        errors.append("Descontinuidades detectadas na matriz")
    
    # Validar gradientes
    if not check_gradient_smoothness(matrix):
        errors.append("Gradientes abruptos detectados")
    
    return len(errors) == 0, errors
```

## 🎨 Interface e UX

### Melhorias de Interface
1. **Editor de Viewport**: Mostrar apenas 16x16 células por vez
2. **Zoom/Pan**: Navegação na matriz grande
3. **Seleção de Região**: Editar múltiplas células
4. **Preview em Tempo Real**: Mostrar mudanças antes de aplicar
5. **Undo/Redo**: Histórico de alterações

### Feedback Visual
- 🟢 Valores válidos
- 🟡 Valores no limite
- 🔴 Valores inválidos
- 📊 Indicadores de gradiente
- 🎯 Células selecionadas

## 📊 Estrutura de Dados

### Formato de Arquivo 3D JSON
```json
{
  "vehicle_id": "uuid",
  "map_type": "main_fuel_3d_map",
  "bank_id": "A",
  "grid_size": 32,
  "rpm_axis": [...],
  "map_axis": [...],
  "values_matrix": [[...], ...],
  "rpm_enabled": [...],
  "map_enabled": [...],
  "metadata": {
    "timestamp": "ISO-8601",
    "version": "2.0",
    "calculated_with": "strategy_name",
    "vehicle_data_hash": "hash"
  }
}
```

## 🧪 Testes a Implementar

### Testes Unitários
```python
def test_3d_calculator():
    """Testa calculador 3D."""
    matrix = calculate_fuel_3d_matrix(
        rpm_values=[1000, 2000, 3000],
        map_values=[-0.5, 0, 0.5],
        vehicle_data=test_vehicle_data,
        strategy='balanced'
    )
    assert matrix.shape == (3, 3)
    assert np.all(matrix >= 0)

def test_3d_validation():
    """Testa validação de matriz."""
    matrix = np.random.rand(32, 32) * 50
    valid, errors = validate_3d_matrix(matrix, 0, 50)
    assert valid == True
```

## 🚀 Ordem de Execução

### Passo 1: Configuração
1. Expandir `map_types_3d.json` com configuração completa
2. Criar funções de carregamento de configuração

### Passo 2: Calculador Core
1. Portar funções de cálculo do 2D
2. Adaptar para superfície 3D
3. Implementar calculador universal

### Passo 3: Interface
1. Adicionar modal do calculador
2. Implementar preview 3D
3. Adicionar controles avançados

### Passo 4: Otimização
1. Implementar viewport para matrizes grandes
2. Adicionar cache estratégico
3. Otimizar renderização

### Passo 5: Validação
1. Implementar validações avançadas
2. Adicionar feedback visual
3. Testes completos

## ⚠️ Considerações Importantes

### Performance
- Matrizes 32x32 = 1024 valores
- Usar numpy para operações vetorizadas
- Cache agressivo para cálculos pesados
- Renderização incremental

### Compatibilidade
- Manter compatibilidade com dados existentes
- Migração automática de formatos antigos
- Fallback para valores padrão

### Padrões Streamlit
- SEMPRE usar st.session_state
- SEMPRE validar inputs
- SEMPRE dar feedback visual
- SEMPRE documentar código

## ✅ Checklist de Validação

Antes de considerar completo:
- [ ] Calculador 3D funcionando para todos os tipos
- [ ] Interface modal completa
- [ ] Sistema enable/disable dinâmico
- [ ] Validações implementadas
- [ ] Performance otimizada (< 2s para calcular 32x32)
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] Compatibilidade com FTManager

## 📝 Notas de Implementação

- Reutilizar máximo possível do código 2D
- Manter consistência visual com páginas existentes
- Priorizar funcionalidade sobre features avançadas
- Testar com dados reais de veículos

---
*Agente: A06-3D-MAP-IMPLEMENTATION*
*Criado: 2025-09-08*
*Status: PRONTO PARA EXECUÇÃO*