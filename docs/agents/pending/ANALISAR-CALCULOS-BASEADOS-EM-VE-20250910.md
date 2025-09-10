# AGENTE: Analisar Cálculos Baseados em VE (2D/3D + Malha Fechada)

Objetivo
- Levantar e validar todos os cálculos de injeção que dependem do mapa de VE (3D) e da malha fechada (λ 3D), cobrindo mapas: Injeção 3D (MAP×RPM), Injeção 2D (MAP) e Fator 2D por RPM.
- Produzir documentação técnica detalhada com fórmulas, unidades, suposições, bordas e critérios de aceite.
- Indicar gaps entre implementação atual (Python/Streamlit e painel HTML) e o modelo proposto, com plano de atualização.

Escopo
- VE como fonte principal: matriz VE 3D persistida (MAP×RPM), com fallback default quando ausente.
- λ-alvo (malha 3D) por estratégia ou manual, aplicável por célula quando ativada.
- Parâmetros físicos: bicos, pressão base, regulador (1:1/fixo), AFR estequiométrico, IAT, DT/voltagem, PW mínimo, fator global 3D.

Entregáveis
- docs/FUEL-INJECTION-CALCULATION-SPEC.md (especificação técnica completa)
- Matriz de testes (sanidade e bordas) com valores esperados
- Checklist de conformidade (unidades, limites, clamps, 1:1 vs fixo)
- Relatório de gaps + plano de ação (issues/tarefas)

Tarefas
1) Mapear entradas, unidades e convenções (MAP, P_abs, ΔP, AFR_stq, IAT, R=287, etc.)
2) Descrever o cálculo físico por célula (m,r): m_ar, m_comb, fluxo, PW_teo, compensações, DT, PW_min
3) Descrever Injeção 2D (MAP): uso de VE(map, rpm_ref) e λ(m)
4) Descrever Injeção 3D:
   - Sem malha: PW(m,r) = PW_line(m,rpm_ref) × VE(m,r)/VE(m,rpm_ref) × G3D
   - Com malha: física por célula com λ_target(m,r)
5) Descrever Fator 2D RPM: extraído por VE como VE(m,r)/VE(m,rpm_ref)
6) Malha Fechada (λ 3D): estratégia/manual, fatores rpm e limites, aplicação por célula
7) Compensações: temp (motor/ar) multiplicativas, voltagem (DT) aditiva
8) Bordas: ΔP<=0, PW_min, saturações, ranges aspirado/turbo
9) Testes: casos de sanidade e extremos
10) Gaps e plano: alinhar Streamlit/core com a especificação; interpolação (nearest/bilinear); expor rpm_ref

Critérios de Aceite
- Documentos claros e auditáveis; fórmulas com unidades; exemplos numéricos
- Testes reproduzíveis no painel HTML (tests/mapa.html) e no core
- Checklist concluído sem pendências críticas

Artefatos a inspecionar
- tests/mapa.html (cálculo atual de preview)
- src/core/fuel_maps/calculations.py (pipeline base)
- src/core/fuel_maps/persistence.py (persistência de mapas)
- src/ui/pages/fuel_maps.py (UI e hooks)

Saídas extras (opcional)
- Template de curvas/limites por combustível
- Guia de migração para uso obrigatório da VE 3D
