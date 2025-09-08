# A04 - FUEL MAPS 2D IMPLEMENTATION

## 📋 Objetivo
Implementar a padronização da interface fuel_maps_2d.py baseado no relatório A03-STANDARDIZATION-REPORT, mantendo compatibilidade com dados existentes e preservando funcionalidades específicas do mapa 2D.

## 🎯 Missão Específica
Este agente é responsável por:
1. **Reestruturar interface** com sistema de tabs e sub-tabs
2. **Migrar sistema FTManager** para aba dedicada
3. **Criar configuração JSON** externa para tipos de mapas 2D
4. **Padronizar componentes** mantendo funcionalidades únicas
5. **Melhorar sistema enable/disable** de eixos
6. **Adicionar estatísticas** faltantes (desvio padrão)
7. **Garantir compatibilidade** com dados salvos existentes

## 🔧 Contexto de Execução
- **Arquivo principal**: `/src/ui/pages/fuel_maps_2d.py`
- **Arquivo de referência**: `/src/ui/pages/fuel_maps_3d.py`
- **Configuração a criar**: `/config/map_types_2d.json`
- **Relatório base**: `/docs/agents/reports/A03-STANDARDIZATION-REPORT.md`

## 📋 Processo de Execução

### FASE 1 - Preparação
1. Fazer backup do arquivo atual fuel_maps_2d.py
2. Criar arquivo de configuração map_types_2d.json
3. Verificar compatibilidade com dados existentes

### FASE 2 - Reestruturação de Tabs
1. Implementar sistema de sub-tabs na aba "Editar"
   - Sub-tab "Valores" - editor horizontal atual
   - Sub-tab "Eixos" - configuração de eixos
2. Manter aba "Visualizar" com melhorias
3. Reorganizar aba "Importar/Exportar"
   - Mover seções FTManager para cá
   - Organizar em seções claras

### FASE 3 - Sistema de Configuração
1. Criar `/config/map_types_2d.json` com todos os tipos
2. Implementar função `load_map_types_config()`
3. Adicionar fallback para configuração padrão
4. Garantir compatibilidade com dados antigos

### FASE 4 - Padronização de Componentes
1. Adicionar desvio padrão nas estatísticas
2. Padronizar formatação para 3 casas decimais
3. Melhorar sistema enable/disable
4. Implementar filtros para valores ativos

### FASE 5 - Testes e Validação
1. Testar carregamento de dados antigos
2. Validar todas as funcionalidades
3. Verificar navegação entre tabs
4. Testar import/export

## 📊 Estrutura do map_types_2d.json

```json
{
  "main_fuel_2d_map_32": {
    "name": "Mapa Principal de Injeção (MAP) - 32 posições",
    "positions": 32,
    "axis_type": "MAP",
    "unit": "ms",
    "min_value": 0.0,
    "max_value": 50.0,
    "description": "Mapa principal de combustível baseado na pressão MAP",
    "default_enabled_count": 21
  },
  "main_fuel_2d_map_20": {
    "name": "Mapa Principal de Injeção (MAP) - 20 posições",
    "positions": 20,
    "axis_type": "MAP",
    "unit": "ms",
    "min_value": 0.0,
    "max_value": 50.0,
    "description": "Mapa principal com 20 posições",
    "default_enabled_count": 18
  },
  "main_fuel_2d_map_16": {
    "name": "Mapa Principal de Injeção (MAP) - 16 posições",
    "positions": 16,
    "axis_type": "MAP",
    "unit": "ms",
    "min_value": 0.0,
    "max_value": 50.0,
    "description": "Mapa principal com 16 posições",
    "default_enabled_count": 14
  },
  "main_fuel_2d_map_9": {
    "name": "Mapa Principal de Injeção (MAP) - 9 posições",
    "positions": 9,
    "axis_type": "MAP",
    "unit": "ms",
    "min_value": 0.0,
    "max_value": 50.0,
    "description": "Mapa principal com 9 posições",
    "default_enabled_count": 9
  },
  "main_fuel_2d_map_8": {
    "name": "Mapa Principal de Injeção (MAP) - 8 posições",
    "positions": 8,
    "axis_type": "MAP",
    "unit": "ms",
    "min_value": 0.0,
    "max_value": 50.0,
    "description": "Mapa principal com 8 posições",
    "default_enabled_count": 8
  },
  "tps_correction_2d": {
    "name": "Correção por TPS",
    "positions": 32,
    "axis_type": "TPS",
    "unit": "%",
    "min_value": -50.0,
    "max_value": 50.0,
    "description": "Correção de combustível baseada no TPS",
    "default_enabled_count": 16
  },
  "temp_correction_2d": {
    "name": "Correção por Temperatura",
    "positions": 32,
    "axis_type": "TEMP",
    "unit": "%",
    "min_value": -30.0,
    "max_value": 30.0,
    "description": "Correção baseada na temperatura do motor",
    "default_enabled_count": 12
  },
  "air_temp_correction_2d": {
    "name": "Correção por Temperatura do Ar",
    "positions": 32,
    "axis_type": "AIR_TEMP",
    "unit": "%",
    "min_value": -20.0,
    "max_value": 20.0,
    "description": "Correção baseada na temperatura do ar de admissão",
    "default_enabled_count": 10
  },
  "voltage_correction_2d": {
    "name": "Correção por Voltagem",
    "positions": 32,
    "axis_type": "VOLTAGE",
    "unit": "ms",
    "min_value": -5.0,
    "max_value": 5.0,
    "description": "Correção do tempo de injeção baseada na voltagem",
    "default_enabled_count": 8
  }
}
```

## 🔧 Estrutura de Tabs Proposta

```python
# Tab 1: Editar
tab1_subtabs = st.tabs(["📊 Valores", "⚙️ Eixos"])

with tab1_subtabs[0]:  # Valores
    # Editor horizontal de valores
    # Gradiente de cores
    # Operações (resetar, etc)
    # Formulário de salvar

with tab1_subtabs[1]:  # Eixos  
    # Configuração do eixo X
    # Sistema enable/disable
    # Valores personalizados
    # Aplicar valores ativos

# Tab 2: Visualizar
    # Gráfico 2D linha + markers
    # Estatísticas (min, max, média, desvio)
    # Visualização com valores ativos

# Tab 3: Importar/Exportar
    # Seção: Copiar para FTManager
    # Seção: Colar do FTManager
    # Seção: Importar Dados (JSON/CSV)
    # Seção: Exportar Dados (JSON/CSV)
```

## ⚠️ Pontos Críticos

### Compatibilidade
1. **SEMPRE** verificar se dados antigos existem antes de criar novos
2. **NUNCA** quebrar compatibilidade com mapas salvos
3. **SEMPRE** adicionar campos opcionais com valores padrão

### Preservar
1. Layout horizontal para edição (arrays 1D)
2. Suporte a múltiplos tamanhos de mapa
3. Sistema de copiar/colar FTManager existente
4. Tipos específicos de correção

### Melhorar
1. Sistema enable/disable mais robusto
2. Filtros para usar apenas valores ativos
3. Formatação consistente (3 decimais)
4. Estatísticas completas

## 📊 Checklist de Implementação

- [ ] Backup do arquivo original
- [ ] Criar map_types_2d.json
- [ ] Implementar função load_map_types_config()
- [ ] Reestruturar tabs principais
- [ ] Adicionar sub-tabs em "Editar"
- [ ] Mover configuração de eixos para sub-tab
- [ ] Mover FTManager para "Importar/Exportar"
- [ ] Adicionar desvio padrão nas estatísticas
- [ ] Implementar filtros para valores ativos
- [ ] Padronizar formatação 3 decimais
- [ ] Testar compatibilidade com dados antigos
- [ ] Validar todas as funcionalidades
- [ ] Documentar mudanças

## 📈 Métricas de Sucesso

- Interface 100% consistente com fuel_maps_3d.py
- Todas funcionalidades preservadas
- Dados antigos carregam corretamente
- Navegação intuitiva entre tabs
- Código mais maintível
- Performance mantida ou melhorada

## 🆘 Tratamento de Erros

### Dados Incompatíveis
Se dados antigos não tiverem campos novos:
1. Adicionar campos com valores padrão
2. Migrar silenciosamente
3. Salvar no novo formato

### Configuração Ausente
Se map_types_2d.json não existir:
1. Usar configuração hardcoded como fallback
2. Avisar no log
3. Continuar funcionando normalmente

---

**Versão:** 1.0
**Última atualização:** Janeiro 2025
**Tipo:** Implementação de Padronização UI