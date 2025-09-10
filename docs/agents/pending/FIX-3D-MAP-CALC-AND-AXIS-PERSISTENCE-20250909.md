# FIX-3D-MAP-CALC-AND-AXIS-PERSISTENCE-20250909

## Objetivo
Corrigir dois problemas em mapas 3D: (1) cálculo gerando valores constantes/irreais; (2) persistência de eixos habilitados (rpm_enabled/map_enabled) não salvando corretamente e perdendo estado após refresh.

## Escopo
- Apenas 3D. Nada muda em 2D.
- Arquivos-alvo: `src/core/fuel_maps/calculations.py`, `src/core/fuel_maps/persistence.py`, `src/ui/pages/fuel_maps.py` (seções 3D: Ferramentas/Eixos/Preview).

## Contexto Atual (Sintomas)
- Preview 3D mostra matriz com “Valores únicos = 1” (e.g., todos 0.500 ms), independente de parâmetros.
- Ao desativar posições em RPM/MAP e salvar, o arquivo JSON não reflete `rpm_enabled`/`map_enabled` e o grid só atualiza após reiniciar; configurações se perdem.

## Tarefas
1) Persistência robusta dos eixos 3D
- Em `persistence.py::save_3d_map_data` coagir `values_matrix = np.array(values_matrix)` antes de serializar (`.tolist()`).
- Em `fuel_maps.py::render_3d_axes_editor`, garantir que `values_matrix` enviado ao salvar seja `np.array(...)` e reportar falhas de salvamento com `st.error`.

2) Revisão do cálculo 3D (combustível)
- Ajustar unidades e dados do veículo:
  - `displacement`: aceitar litros (p. ex. 1.9) e converter para cc automaticamente (< 50 ⇒ L → cc).
  - `injector_flow`: aceitar `injector_flow`, `injector_flow_cc` (por bico) ou converter de `injector_flow_lbs` (total) ≈ `lb/h * 10.5` cc/min; se parecer total (valor muito alto), dividir por nº de cilindros.
- Corrigir unidade do boost: passar BAR relativo (não kPa) para `calculate_base_injection_time_3d`.
- Respeitar parâmetros da UI:
  - `consider_boost`: se falso, limitar MAP ≤ 100 kPa e `boost_pressure = 0`.
  - `apply_fuel_corr`: ajustar AFR alvo por combustível (e.g., Etanol: 9.0/14.7; E85: 9.8/14.7).
- Tornar piso configurável: usar `vehicle_data.get("min_pulse_ms", 1.0)` ao invés de 0.5 ms fixo.
- Revisar modelo `calculate_base_injection_time_3d` para escalar com RPM/VE por ciclo, evitando saturar no piso.

3) Padrões de UI (3D)
- Remover emojis restantes do 3D; manter texto simples ou Material Icons somente onde suportado (ver `STREAMLIT-DEVELOPMENT-STANDARDS.md`).
- Opcional: adicionar checkbox “Modo de Depuração” no 3D para esconder `st.write` de debug.

## Passos de Implementação
1. `src/core/fuel_maps/persistence.py`
- Editar `save_3d_map_data`: se `not isinstance(values_matrix, np.ndarray)`, fazer `values_matrix = np.array(values_matrix)`.

2. `src/ui/pages/fuel_maps.py`
- Em `render_3d_axes_editor`, nas chamadas `persistence_manager.save_3d_map_data(...)`, enviar `np.array(map_data.get("values_matrix", []))`.
- Exibir `st.error` em caso de falha de salvamento; manter `st.rerun()` após sucesso.
- Opcional: checkbox `modo_debug` e esconder blocos de DEBUG quando desmarcado.

3. `src/core/fuel_maps/calculations.py`
- Em `calculate_3d_map_values_universal` (main fuel): encaminhar `consider_boost` e `apply_fuel_corr`.
- Em `calculate_fuel_3d_matrix`:
  - Converter litros→cc; resolver vazão do injetor; dividir total pelos cilindros quando aplicável.
  - Passar `boost_pressure` em BAR relativo.
  - Aplicar correção por combustível quando `apply_fuel_corr=True`.
  - Usar `min_pulse_ms = vehicle_data.get("min_pulse_ms", 1.0)` dentro de `calculate_base_injection_time_3d` (ou clamp pós-cálculo).
- Em `calculate_base_injection_time_3d`: ajustar fórmula para escalar com RPM/VE/ciclos por minuto, evitando truncar em piso.

## Critérios de Aceitação
- Persistência: Após desativar posições em RPM/MAP e salvar, o arquivo JSON correspondente em `data/fuel_maps/` deve refletir `rpm_enabled`/`map_enabled`; o grid atualiza no refresh sem perder estado.
- Cálculo 3D: Em “Ferramentas”, variar `consider_boost` e `apply_fuel_corr` altera Min/Max e “Valores únicos” (> 1); sem saturar no piso global.
- UI 3D: Sem emojis; debug controlado (checkbox) ou reduzido; conformidade com os padrões de Streamlit.

## Validação
1. Executar local: `make dev` e abrir “Mapas de Injeção 3D → Ferramentas”.
2. Desabilitar 5 posições em RPM e 5 em MAP, salvar cada eixo; confirmar atualização e persistência no JSON.
3. Com `consider_boost` ligado/desligado, observar variações na matriz; idem para `apply_fuel_corr` com `fuel_type = Ethanol`.
4. Verificar que `Valores únicos` > 1 e `Min < Max`.

## Saída
- PR com mensagem: `fix(3d): cálculo de combustível e persistência de eixos; conformidade UI`
- Arquivos modificados conforme “Passos de Implementação”.
- Opcional: relatório curto em `docs/agents/reports/analysis/fix-3d-20250909.md` com antes/depois (Min/Max/Unique).

## Observações
- Não alterar 2D.
- Seguir `docs/agents/shared/STREAMLIT-DEVELOPMENT-STANDARDS.md` (sem emojis; sem HTML onde não suportado).
- Rodar `make quality && make test` antes do PR.

