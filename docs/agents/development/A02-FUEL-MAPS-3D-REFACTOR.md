# A02 - FUEL MAPS 3D REFACTOR ANALYSIS

## 📋 Objetivo
Fazer um levantamento detalhado do arquivo `fuel_maps_3d.py`, entender o fluxo de dados, identificar problemas estruturais e propor uma refatoração completa para separar responsabilidades e simplificar o código.

## 🎯 Escopo da Análise

### 1. Mapeamento de Estrutura
- [ ] Identificar todas as funções e suas responsabilidades
- [ ] Mapear fluxo de dados (origem → processamento → destino)
- [ ] Documentar dependências entre funções
- [ ] Identificar código duplicado ou redundante

### 2. Análise de Dados
- [ ] **Origem dos dados defaults**:
  - Constantes hardcoded (DEFAULT_RPM_AXIS, RPM_ENABLED, etc.)
  - Arquivo config/map_types_3d.json
  - Session state
  - Arquivos salvos em data/fuel_maps/
- [ ] **Fluxo de carregamento**:
  - Ordem de prioridade dos dados
  - Quando usa cada fonte
  - Conflitos entre fontes
- [ ] **Persistência**:
  - Como e onde salva
  - Formato dos arquivos
  - Validações aplicadas

### 3. Problemas Identificados
- [ ] Funções com múltiplas responsabilidades
- [ ] Código de UI misturado com lógica de negócio
- [ ] Uso inconsistente de fontes de dados
- [ ] Funções muito grandes (>100 linhas)
- [ ] Parâmetros confusos ou mal documentados
- [ ] Estado global mal gerenciado

### 4. Proposta de Refatoração

#### Estrutura Proposta
```
src/
├── ui/
│   └── pages/
│       └── fuel_maps_3d.py (APENAS UI/UX - max 500 linhas)
├── core/
│   └── fuel_maps/
│       ├── __init__.py
│       ├── constants.py (constantes e configs)
│       ├── models.py (classes e tipos)
│       ├── calculations.py (lógica de cálculo)
│       ├── persistence.py (salvar/carregar)
│       ├── validation.py (validações)
│       └── defaults.py (valores padrão)
└── config/
    └── map_types_3d.json (configurações)
```

## 🔍 Análise Detalhada

### Funções de Cálculo (MOVER para calculations.py)
- `calculate_fuel_3d_matrix()` - Cálculo do mapa principal
- `calculate_lambda_3d_matrix()` - Cálculo do mapa lambda
- `calculate_ignition_3d_matrix()` - Cálculo do mapa de ignição
- `calculate_afr_3d_matrix()` - Cálculo do mapa AFR
- `calculate_3d_map_values_universal()` - Função wrapper
- Todas as funções auxiliares de cálculo

### Funções de Persistência (MOVER para persistence.py)
- `save_3d_map_data()` - Salvar dados no disco
- `load_3d_map_data()` - Carregar dados do disco
- `ensure_all_3d_maps_exist()` - Garantir existência dos mapas
- `get_default_3d_map_values()` - Obter valores padrão

### Funções de Configuração (MOVER para defaults.py)
- `load_map_types_config()` - Carregar configuração JSON
- `get_map_config_values()` - Obter valores específicos
- `get_default_3d_enabled_matrix()` - Obter matriz enabled/disabled
- Gerenciamento de constantes DEFAULT_*

### Funções de Validação (MOVER para validation.py)
- `validate_3d_map_values()` - Validar valores da matriz
- Validações de tipos e ranges
- Verificações de consistência

### UI/UX (MANTER em fuel_maps_3d.py)
- Apenas código Streamlit
- Chamadas para funções dos módulos
- Gerenciamento de session_state
- Renderização de componentes

## 📊 Métricas Atuais
- **Tamanho do arquivo**: ~3000+ linhas
- **Funções**: 30+ funções
- **Responsabilidades misturadas**: UI + Lógica + Persistência
- **Duplicação de código**: Alta
- **Complexidade ciclomática**: Muito alta

## 🎯 Objetivos da Refatoração
1. **Separação de responsabilidades**: UI vs Lógica vs Dados
2. **Redução de complexidade**: Funções menores e focadas
3. **Eliminação de duplicação**: Código reutilizável
4. **Melhoria de manutenibilidade**: Código organizado
5. **Facilitar testes**: Lógica isolada da UI
6. **Documentação clara**: Cada módulo com propósito único

## 📝 Plano de Execução

### Fase 1: Análise (Este Agente)
1. Mapear todas as funções e responsabilidades
2. Identificar dependências e fluxo de dados
3. Documentar problemas e inconsistências
4. Criar proposta detalhada de refatoração

### Fase 2: Preparação
1. Criar estrutura de diretórios proposta
2. Criar arquivos base dos módulos
3. Definir interfaces entre módulos
4. Criar testes unitários básicos

### Fase 3: Refatoração
1. Mover funções de cálculo
2. Mover funções de persistência
3. Mover funções de configuração
4. Mover funções de validação
5. Limpar arquivo principal (apenas UI)

### Fase 4: Validação
1. Testar funcionalidades
2. Verificar performance
3. Validar persistência de dados
4. Confirmar compatibilidade

## 🚀 Como Executar Este Agente

```bash
# Este agente fará apenas análise, não modificará código
# Execute no diretório raiz do projeto

1. Analisar estrutura atual do fuel_maps_3d.py
2. Mapear todas as funções e suas linhas
3. Identificar uso de dados defaults
4. Rastrear fluxo de save/load
5. Gerar relatório detalhado em:
   docs/agents/reports/FUEL-MAPS-3D-ANALYSIS.md
```

## 📊 Resultado Esperado

### Relatório de Análise
```markdown
# FUEL MAPS 3D - ANÁLISE COMPLETA

## Estrutura Atual
- Total de linhas: XXXX
- Funções identificadas: XX
- Imports: XX

## Mapeamento de Funções
| Função | Linhas | Responsabilidade | Destino Proposto |
|--------|--------|------------------|------------------|
| ... | ... | ... | ... |

## Fluxo de Dados
1. Origem → Processamento → Destino
2. Dependências identificadas
3. Problemas encontrados

## Recomendações
1. Separar em X módulos
2. Reduzir para Y linhas no arquivo principal
3. Eliminar Z duplicações
```

## ⚠️ Observações Importantes
- Este agente NÃO modifica código
- Apenas análise e documentação
- Preparação para refatoração futura
- Foco em entender antes de modificar

---

**Versão:** 1.0
**Data:** Janeiro 2025
**Status:** Pronto para execução
**Tipo:** Análise e Documentação