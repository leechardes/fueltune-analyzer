# A05 - UPDATE FUEL MAPS UI

## 📋 Objetivo
Atualizar a interface `fuel_maps.py` para usar a configuração unificada `map_types.json` e implementar seletor de mapas 2D/3D com indicação visual clara da dimensão.

## 🎯 Contexto
Após a unificação das configurações (A04), precisamos atualizar a UI para:
- Usar o novo arquivo `config/map_types.json`
- Mostrar todos os mapas disponíveis (2D e 3D)
- Indicar claramente a dimensão de cada mapa
- Manter compatibilidade com as funcionalidades existentes

## 📊 Requisitos da Interface

### 1. Dropdown de Seleção de Mapas
- Exibir todos os mapas do `map_types.json`
- Formato: "Nome do Mapa (2D)" ou "Nome do Mapa (3D)"
- Usar campo `display_name` para exibição
- Manter `map_type` como valor interno

### 2. Adaptação por Dimensão
- Se mapa for 2D:
  - Mostrar apenas eixo único (RPM ou TPS ou MAP)
  - Interface de edição 2D (32 posições)
  - Gráfico de linha/barras
  
- Se mapa for 3D:
  - Mostrar dois eixos (RPM x MAP)
  - Interface de matriz (32x32)
  - Gráfico 3D surface

### 3. Seleção de Banco
- Mostrar apenas para mapas que suportam banco (main_fuel)
- Ocultar para mapas compartilhados

## 🔧 Tarefas

### FASE 1: Atualizar ConfigManager
1. Verificar se `src/core/fuel_maps/defaults.py` está usando `map_types.json`
2. Adicionar método `get_all_maps()` para retornar todos os mapas
3. Adicionar método `get_map_dimension(map_type)` para obter dimensão
4. Garantir que `get_display_name()` funciona corretamente

### FASE 2: Atualizar Interface Principal
Em `src/ui/pages/fuel_maps.py`:

1. **Atualizar função main():**
```python
def main():
    # Carregar TODOS os mapas (2D e 3D)
    ALL_MAP_TYPES = config_manager.get_all_maps()
    
    # Obter dados do veículo
    vehicle_data = session_manager.get_vehicle_data_from_session()
    vehicle_id = vehicle_data.get("vehicle_id", "default")
    
    # Renderizar interface
    render_main_interface(ALL_MAP_TYPES, vehicle_data, vehicle_id)
```

2. **Atualizar render_main_interface():**
```python
def render_main_interface(map_types, vehicle_data, vehicle_id):
    with st.sidebar:
        st.header("Configuração do Mapa")
        
        # Dropdown com display_name
        map_type = st.selectbox(
            "Tipo de Mapa",
            list(map_types.keys()),
            format_func=lambda x: map_types[x].get("display_name", x),
            key="selected_map_type"
        )
        
        # Obter dimensão do mapa selecionado
        map_config = map_types[map_type]
        dimension = map_config.get("dimension", "2D")
        
        # Mostrar badge de dimensão
        if dimension == "3D":
            st.info("🎲 Mapa Tridimensional (RPM x MAP)")
        else:
            st.info("📊 Mapa Bidimensional")
        
        # Seletor de banco (condicional)
        if "main_fuel" in map_type:
            bank_id = st.radio("Bancada", ["A", "B"])
        else:
            bank_id = "shared"
```

### FASE 3: Adaptar Renderização por Dimensão
1. **Criar função render_by_dimension():**
```python
def render_by_dimension(map_type, map_config, vehicle_id, bank_id):
    dimension = map_config.get("dimension", "2D")
    
    if dimension == "3D":
        render_3d_interface(map_type, map_config, vehicle_id, bank_id)
    else:
        render_2d_interface(map_type, map_config, vehicle_id, bank_id)
```

2. **Adaptar render_2d_interface():**
- Carregar dados 2D (array de 32 posições)
- Mostrar editor linear
- Gráfico de barras/linha

3. **Manter render_3d_interface():**
- Carregar dados 3D (matriz 32x32)
- Mostrar editor de matriz
- Gráfico 3D surface

### FASE 4: Atualizar Persistência
1. Verificar `src/core/fuel_maps/persistence.py`
2. Adicionar suporte para salvar/carregar mapas 2D
3. Usar estrutura diferente para 2D:
```json
{
  "vehicle_id": "xxx",
  "map_type": "ignition_timing_map",
  "dimension": "2D",
  "axis_values": [...],
  "values": [...],
  "enabled": [...]
}
```

### FASE 5: Unificar Componentes UI
Em `src/core/fuel_maps/ui_components.py`:
1. Criar `render_map_editor()` que detecta dimensão
2. Criar `render_map_visualization()` que adapta por dimensão
3. Reutilizar componentes existentes quando possível

### FASE 6: Testes e Validação
1. Testar carregamento de mapas 2D
2. Testar carregamento de mapas 3D
3. Verificar transição entre mapas
4. Validar salvamento de dados
5. Confirmar que visualizações funcionam

## ✅ Checklist de Validação
- [ ] Dropdown mostra todos os mapas com (2D) ou (3D)
- [ ] Seleção de banco aparece apenas para main_fuel
- [ ] Mapas 2D mostram interface linear
- [ ] Mapas 3D mostram interface de matriz
- [ ] Dados são salvos corretamente
- [ ] Visualizações adaptam por dimensão
- [ ] Sem erros ao trocar entre mapas

## 📝 Estrutura de Dados Esperada

### Mapa 2D:
```python
{
    "vehicle_id": "vehicle_001",
    "map_type": "ignition_timing_map",
    "dimension": "2D",
    "axis_type": "RPM",
    "axis_values": [500, 1000, 1500, ...],  # 32 valores
    "values": [10, 15, 20, ...],            # 32 valores
    "enabled": [True, True, False, ...],    # 32 valores
    "unit": "°"
}
```

### Mapa 3D:
```python
{
    "vehicle_id": "vehicle_001",
    "map_type": "main_fuel_map_3d",
    "dimension": "3D",
    "rpm_axis": [500, 1000, 1500, ...],     # 32 valores
    "map_axis": [-1.0, -0.8, -0.6, ...],    # 32 valores
    "values_matrix": [[...], [...]],        # 32x32 matriz
    "rpm_enabled": [True, True, ...],       # 32 valores
    "map_enabled": [True, True, ...],       # 32 valores
    "unit": "ms"
}
```

## ⚠️ Cuidados
- Manter compatibilidade com dados existentes
- Não quebrar funcionalidades 3D já implementadas
- Preservar `fuel_maps_2d.py` como referência
- Testar transições entre mapas de diferentes dimensões
- Garantir que dados não sejam perdidos ao trocar mapas

## 🚀 Resultado Esperado
1. Interface unificada para mapas 2D e 3D
2. Seletor claro com indicação de dimensão
3. Adaptação automática da UI por tipo
4. Funcionalidades preservadas e melhoradas
5. Código mais limpo e organizado

---

**Versão:** 1.0
**Data:** Janeiro 2025
**Status:** Pronto para execução
**Tipo:** Atualização de Interface