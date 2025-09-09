# A10 - ANALYZE ALL CALCULATIONS

## 📋 Objetivo
Fazer um levantamento completo de todos os cálculos existentes nos arquivos de backup e na estrutura atual, documentando cada tipo de cálculo, suas estratégias, parâmetros e particularidades para organizar a implementação correta na interface unificada.

## 🎯 Escopo da Análise

### 1. Arquivos a Analisar

#### A. fuel_maps_2d.py.backup
- **Localização**: `/Users/leechardes/Projetos/fueltune/fueltune-analyzer/src/ui/pages/fuel_maps_2d.py.backup`
- **Focar em**:
  - Função `calculate_map_values_universal()` (procurar todas as ocorrências)
  - Diferentes tipos de mapas 2D e seus cálculos específicos
  - Estratégias aplicadas (Conservative, Balanced, Aggressive, etc.)
  - Parâmetros específicos para cada tipo

#### B. fuel_maps_3d.py.backup
- **Localização**: `/Users/leechardes/Projetos/fueltune/fueltune-analyzer/src/ui/pages/fuel_maps_3d.py.backup`
- **Focar em**:
  - Função `calculate_3d_map_values_universal()` ou similar
  - Cálculos para mapas 3D (Combustível Principal, Lambda, Ignição, VE)
  - Como as estratégias afetam matrizes 3D
  - Interpolações e suavizações 3D

#### C. src/core/fuel_maps/calculations.py
- **Localização**: `/Users/leechardes/Projetos/fueltune/fueltune-analyzer/src/core/fuel_maps/calculations.py`
- **Focar em**:
  - Funções já migradas
  - Estrutura atual de cálculos
  - O que já foi implementado vs o que falta

#### D. config/map_types.json
- **Localização**: `/Users/leechardes/Projetos/fueltune/fueltune-analyzer/config/map_types.json`
- **Focar em**:
  - Todos os tipos de mapas configurados
  - Parâmetros min/max para cada tipo
  - Unidades e ranges

## 🔍 Análise Detalhada a Realizar

### FASE 1: Mapeamento de Tipos de Mapas

Para cada tipo de mapa encontrado, documentar:

#### Mapas 2D:
1. **main_fuel_2d_map** - Mapa principal de combustível 2D
2. **tps_correction_2d** - Correção por TPS
3. **temp_correction_2d** - Correção por temperatura do motor
4. **air_temp_correction_2d** - Correção por temperatura do ar
5. **voltage_correction_2d** - Correção por voltagem
6. **rpm_compensation_2d** - Compensação por RPM

#### Mapas 3D:
1. **main_fuel_3d_map** - Mapa principal de combustível 3D
2. **lambda_target_3d_map** - Alvo de lambda
3. **ignition_timing_3d_map** - Tempo de ignição
4. **ve_table_3d_map** - Tabela de eficiência volumétrica

### FASE 2: Análise de Cálculos por Tipo

Para cada tipo de mapa, identificar:

```markdown
## [NOME DO MAPA]

### Parâmetros de Entrada:
- Lista de parâmetros necessários
- Dados do veículo utilizados

### Estratégias Disponíveis:
- Conservative: [descrição do comportamento]
- Balanced: [descrição do comportamento]
- Aggressive: [descrição do comportamento]
- Economy: [descrição do comportamento]
- Sport: [descrição do comportamento]

### Fórmula/Lógica de Cálculo:
```python
# Código ou pseudocódigo do cálculo
```

### Particularidades:
- Notas especiais sobre este tipo
- Validações específicas
- Ranges recomendados
```

### FASE 3: Análise de Estratégias

Documentar como cada estratégia afeta os cálculos:

```markdown
## STRATEGY_PRESETS

### Conservative (Conservador)
- Fator multiplicador: X.X
- Comportamento: Valores mais seguros
- Aplicação: [onde e como é aplicado]

### Balanced (Balanceado)
- Fator multiplicador: X.X
- Comportamento: Valores de fábrica
- Aplicação: [onde e como é aplicado]

### Aggressive (Agressivo)
- Fator multiplicador: X.X
- Comportamento: Performance
- Aplicação: [onde e como é aplicado]
```

### FASE 4: Parâmetros do Veículo

Listar todos os parâmetros do veículo utilizados nos cálculos:

```markdown
## Parâmetros do Veículo Utilizados

### Obrigatórios:
- displacement (cilindrada)
- cylinders (número de cilindros)
- injector_flow (vazão dos bicos)
- fuel_type (tipo de combustível)

### Opcionais:
- has_turbo (tem turbo)
- max_boost (pressão máxima)
- redline_rpm (RPM máximo)
- idle_rpm (RPM marcha lenta)
- cooling_type (tipo de arrefecimento)
- injector_impedance (impedância dos bicos)
```

### FASE 5: Funções de Cálculo Auxiliares

Identificar funções auxiliares importantes:

```markdown
## Funções Auxiliares

### Interpolação:
- interpolate_2d()
- interpolate_3d_matrix()

### Suavização:
- smooth_values()
- apply_gaussian_filter()

### Validação:
- validate_range()
- check_monotonic()

### Conversão:
- ms_to_duty_cycle()
- lambda_to_afr()
```

## 📊 Resultado Esperado

### Documento de Saída: `CALCULATIONS-ANALYSIS-REPORT.md`

O agente deve gerar um relatório completo contendo:

1. **Resumo Executivo**
   - Total de tipos de mapas encontrados
   - Total de estratégias identificadas
   - Funções principais mapeadas

2. **Catálogo de Cálculos**
   - Documentação completa de cada tipo
   - Código/pseudocódigo dos cálculos
   - Parâmetros necessários

3. **Matriz de Estratégias**
   - Como cada estratégia afeta cada tipo de mapa
   - Fatores e multiplicadores

4. **Dependências**
   - Parâmetros do veículo necessários
   - Funções auxiliares utilizadas

5. **Recomendações de Implementação**
   - Ordem sugerida de implementação
   - Pontos de atenção
   - Validações necessárias

## ✅ Checklist de Validação

- [ ] Todos os tipos de mapas foram documentados
- [ ] Todas as estratégias foram mapeadas
- [ ] Fórmulas de cálculo identificadas
- [ ] Parâmetros do veículo listados
- [ ] Funções auxiliares catalogadas
- [ ] Diferenças 2D vs 3D documentadas
- [ ] Validações e ranges anotados

## 🚀 Como Executar

1. Ler completamente cada arquivo mencionado
2. Extrair e documentar cada função de cálculo
3. Identificar padrões e estratégias
4. Criar matriz relacionando tipo x estratégia
5. Gerar relatório consolidado
6. Salvar em `docs/agents/reports/CALCULATIONS-ANALYSIS-REPORT.md`

## 🎯 Uso do Resultado

O relatório gerado será usado para:
1. Implementar corretamente todos os cálculos na interface unificada
2. Garantir que nenhuma funcionalidade seja perdida
3. Manter consistência entre tipos de mapas
4. Validar implementação final

---

**Versão:** 1.0
**Data:** Janeiro 2025
**Status:** Pronto para execução
**Tipo:** Análise e Documentação
**Prioridade:** Alta