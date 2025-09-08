# A05 - BANK CONFIGURATION POWER CALCULATOR

## 📋 Objetivo
Implementar cálculo de potência suportada pelos bicos de injeção na página de configuração de bancadas, centralizando todas as informações relevantes na seção "Informações do Veículo".

## 🎯 Tarefas

### 1. Análise e Preparação
- [ ] Ler arquivo bank_configuration.py
- [ ] Identificar estrutura atual de dados do veículo
- [ ] Verificar campos necessários no banco de dados
- [ ] Confirmar padrões de desenvolvimento em STREAMLIT-DEVELOPMENT-STANDARDS.md

### 2. Implementação de Campos no Banco
- [ ] Adicionar campo `boost_pressure` para pressão máxima (turbo/super)
- [ ] Adicionar campo `bsfc_factor` para fator BSFC customizável
- [ ] Adicionar campos calculados: `max_supported_hp`, `required_hp`, `hp_margin`
- [ ] Atualizar funções de update_vehicle para novos campos

### 3. Reestruturação da Seção "Informações do Veículo"
- [ ] Reorganizar layout em seções lógicas:
  - Dados do Motor
  - Sistema de Injeção
  - Análise de Potência
  - Indicadores de Capacidade
- [ ] Implementar campos editáveis:
  - Pressão Máxima (se turbo/super)
  - BSFC Factor (com padrão baseado no combustível)

### 4. Implementação dos Cálculos
- [ ] Criar função `get_default_bsfc(fuel_type)`:
  - Gasolina: 0.50
  - Etanol: 0.60
  - Metanol: 0.65
  - Flex: 0.55
  - GNV: 0.45
- [ ] Criar função `calculate_turbo_hp(base_hp, boost_pressure)`:
  - Fórmula: base_hp × (1 + boost_pressure/14.7)
- [ ] Criar função `calculate_max_supported_hp(total_flow, bsfc)`:
  - Fórmula: total_flow ÷ bsfc
- [ ] Criar função `calculate_hp_margin(supported, required)`:
  - Margem absoluta: supported - required
  - Margem percentual: (margin / required) × 100

### 5. Interface Visual
- [ ] Adicionar campo editável para Pressão Máxima (apenas se turbo/super)
- [ ] Adicionar campo editável para BSFC com valor padrão
- [ ] Exibir métricas calculadas:
  - Vazão Total das Bancadas
  - Potência Aspirada
  - Potência Turbo (se aplicável)
  - Potência Máxima Suportada
  - Margem Disponível
- [ ] Implementar indicadores visuais:
  - Verde: Margem > 20%
  - Amarelo: Margem 10-20%
  - Vermelho: Margem < 10%

### 6. Ajustes na Aba Sincronização
- [ ] Remover exibição de vazão total (movida para Informações)
- [ ] Manter apenas configurações de sincronização
- [ ] Ajustar gráfico de balanceamento

### 7. Validações e Testes
- [ ] Validar cálculos com diferentes configurações
- [ ] Testar com apenas Bancada A ativa
- [ ] Testar com ambas as bancadas ativas
- [ ] Verificar salvamento no banco de dados
- [ ] Garantir responsividade dos indicadores

## 🔧 Comandos
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Testar aplicação
make run

# Verificar alterações
git status
git diff src/ui/pages/bank_configuration.py
```

## 📝 Estrutura de Dados Esperada

### Novos Campos no Veículo
```python
{
    # Campos existentes...
    "boost_pressure": 1.5,        # bar (apenas turbo/super)
    "bsfc_factor": 0.50,          # customizável
    "max_supported_hp": 450,      # calculado
    "required_hp_na": 250,        # aspirado
    "required_hp_boost": 375,     # turbo
    "hp_margin": 75,              # absoluto
    "hp_margin_percent": 20       # percentual
}
```

### Layout de Informações
```
┌─────────────────────────────────────────────────────┐
│               Informações do Veículo                 │
├─────────────┬─────────────┬─────────────┬──────────┤
│ Motor       │ Injeção     │ Potência    │ Status   │
├─────────────┼─────────────┼─────────────┼──────────┤
│ Marca/Model │ Combustível │ Aspirada    │ Margem   │
│ Cilindrada  │ BSFC [____] │ Turbo @bar  │ [████░░] │
│ Aspiração   │ Vazão Total │ Máx Suport. │ 20%      │
└─────────────┴─────────────┴─────────────┴──────────┘
```

## ✅ Checklist de Validação
- [ ] Interface 100% em português
- [ ] Sem emojis no código
- [ ] Padrão A04-STREAMLIT-PROFESSIONAL aplicado
- [ ] Campos editáveis funcionando
- [ ] Cálculos precisos
- [ ] Indicadores visuais claros
- [ ] Salvamento no banco funcionando
- [ ] Testes com diferentes configurações
- [ ] Código limpo e documentado

## 📊 Resultado Esperado
Sistema de análise de capacidade integrado que permite ao usuário:
1. Ver instantaneamente se a configuração dos bicos é adequada
2. Ajustar BSFC para combustíveis específicos
3. Simular diferentes pressões de turbo
4. Tomar decisões informadas sobre upgrades
5. Visualizar margens de segurança claramente

---
**Agente**: A05-BANK-CONFIGURATION-POWER-CALCULATOR
**Versão**: 1.0
**Data**: Janeiro 2025