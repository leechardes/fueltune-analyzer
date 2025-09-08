# A07 - UNIFY 2D/3D TOOLS

## 📋 Objetivo
Unificar as ferramentas de cálculo entre mapas 2D e 3D, reutilizando a mesma interface e movendo toda lógica para o módulo core.

## 🎯 Tarefas

### 1. Análise da Estrutura Atual
- [ ] Identificar ferramentas existentes para mapas 3D
- [ ] Mapear funções de cálculo que precisam ser movidas
- [ ] Verificar dados do veículo vindos da sessão

### 2. Refatoração do Código
- [ ] Remover ferramentas incorretas da aba Eixos em 2D
- [ ] Mover funções de cálculo para `src/core/fuel_maps/calculations.py`
- [ ] Criar função unificada de ferramentas que funcione para 2D e 3D
- [ ] Usar dados do veículo da sessão, não inputs manuais

### 3. Implementação da Interface Unificada
- [ ] Adicionar aba "Ferramentas" para mapas 2D (igual ao 3D)
- [ ] Reutilizar `render_tools()` existente adaptando para 2D
- [ ] Garantir que UI seja apenas interface, sem lógica

### 4. Funções a Mover para Core
- [ ] `calculate_2d_map_values()` → `calculations.py`
- [ ] Lógica de interpolação 2D → já existe em `map_interpolation.py`
- [ ] Lógica de suavização 2D → já existe em `map_interpolation.py`
- [ ] Validação de mapas 2D → `validation.py`

## 🔧 Comandos

```bash
# Nenhum comando bash necessário - apenas refatoração de código
```

## ✅ Checklist de Validação
- [ ] Ferramentas 2D usando mesma interface que 3D
- [ ] Toda lógica movida para módulo core
- [ ] Dados do veículo vindos da sessão
- [ ] Sem inputs manuais de parâmetros
- [ ] fuel_maps.py apenas com UI/UX

## 📊 Resultado Esperado
- Interface unificada para ferramentas 2D/3D
- Código mais limpo e organizado
- Reutilização máxima de componentes
- Separação clara entre UI e lógica de negócio

---

**Versão:** 1.0
**Data:** Janeiro 2025
**Status:** Pronto para execução
**Tipo:** Refatoração