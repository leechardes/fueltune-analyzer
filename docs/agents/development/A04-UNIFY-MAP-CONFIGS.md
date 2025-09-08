# A04 - UNIFY MAP CONFIGS

## 📋 Objetivo
Unificar as configurações de mapas 2D e 3D em um único arquivo `map_types.json`, consolidando `map_types_2d.json` e `map_types_3d.json` com indicadores de dimensão.

## 🎯 Contexto
Atualmente temos dois arquivos separados:
- `config/map_types_2d.json` - Configurações de mapas 2D
- `config/map_types_3d.json` - Configurações de mapas 3D

Precisamos unificar em um único arquivo que indique claramente a dimensão de cada mapa.

## 📊 Regras de Negócio
1. **Mapa Principal de Injeção**: Disponível em 2D e 3D
2. **Mapa de Lambda**: Apenas 3D
3. **Demais mapas**: Apenas 2D (ignição, correção, etc.)

## 🔧 Tarefas

### FASE 1: Análise dos arquivos existentes
1. Ler `config/map_types_2d.json`
2. Ler `config/map_types_3d.json`
3. Identificar mapas comuns e exclusivos
4. Documentar estrutura atual

### FASE 2: Criar estrutura unificada
1. Criar novo arquivo `config/map_types.json`
2. Adicionar campo `dimension` ("2D" ou "3D") em cada mapa
3. Unificar nomenclaturas removendo sufixos "_2d" e "_3d" onde apropriado
4. Manter identificadores únicos para cada variação

### FASE 3: Estrutura do novo formato
```json
{
  "main_fuel_map_2d": {
    "name": "Mapa Principal de Injeção",
    "dimension": "2D",
    "display_name": "Mapa Principal de Injeção (2D)",
    "grid_size": 32,
    "x_axis_type": "RPM",
    "y_axis_type": "TPS",
    ...
  },
  "main_fuel_map_3d": {
    "name": "Mapa Principal de Injeção",
    "dimension": "3D", 
    "display_name": "Mapa Principal de Injeção (3D)",
    "grid_size": 32,
    "x_axis_type": "RPM",
    "y_axis_type": "MAP",
    ...
  },
  "lambda_target_3d_map": {
    "name": "Mapa de Lambda Alvo",
    "dimension": "3D",
    "display_name": "Mapa de Lambda Alvo (3D)",
    ...
  },
  "ignition_timing_map": {
    "name": "Mapa de Ignição",
    "dimension": "2D",
    "display_name": "Mapa de Ignição (2D)",
    ...
  }
}
```

### FASE 4: Atualizar modelos
1. Atualizar `src/core/fuel_maps/models.py`:
   - Adicionar campo `dimension` no MapConfig
   - Adicionar `display_name` para exibição na UI
   - Manter compatibilidade com código existente

### FASE 5: Atualizar ConfigManager
1. Modificar `src/core/fuel_maps/defaults.py`:
   - Atualizar path para `config/map_types.json`
   - Adicionar método para filtrar por dimensão
   - Adicionar método para obter display_name

### FASE 6: Criar backup e migração
1. Criar backup dos arquivos originais:
   - `config/map_types_2d.json.backup`
   - `config/map_types_3d.json.backup`
2. Manter originais para referência (não deletar ainda)

## 📝 Mapeamento de Mapas

### Mapas 2D (config/map_types_2d.json):
- main_fuel_map → main_fuel_map_2d
- ignition_timing_map → ignition_timing_map (mantém)
- injection_correction_map → injection_correction_map (mantém)
- ignition_correction_map → ignition_correction_map (mantém)
- idle_speed_map → idle_speed_map (mantém)
- acceleration_enrichment_map → acceleration_enrichment_map (mantém)

### Mapas 3D (config/map_types_3d.json):
- main_fuel_3d_map → main_fuel_map_3d
- lambda_target_3d_map → lambda_target_3d_map (mantém)
- ignition_timing_3d_map → ignition_timing_3d_map (mantém)
- ve_table_3d_map → ve_table_3d_map (mantém)

## ✅ Checklist de Validação
- [ ] Arquivo `config/map_types.json` criado
- [ ] Todos os mapas 2D migrados
- [ ] Todos os mapas 3D migrados
- [ ] Campo `dimension` presente em todos
- [ ] Campo `display_name` presente em todos
- [ ] Backups criados
- [ ] ConfigManager atualizado
- [ ] Models.py atualizado
- [ ] Testes básicos funcionando

## 🚀 Resultado Esperado
1. Um único arquivo `config/map_types.json` com todos os mapas
2. Interface capaz de mostrar todos os mapas com indicação clara de dimensão
3. Código compatível com a nova estrutura
4. Facilidade para adicionar novos mapas no futuro

## ⚠️ Cuidados
- NÃO deletar arquivos originais ainda (manter como referência)
- Manter compatibilidade com código existente
- Testar carregamento após mudanças
- Verificar que fuel_maps_2d.py continua funcionando

---

**Versão:** 1.0
**Data:** Janeiro 2025
**Status:** Pronto para execução
**Tipo:** Refatoração de Configuração