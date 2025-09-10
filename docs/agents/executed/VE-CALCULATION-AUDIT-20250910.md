# AUDITORIA DE CÁLCULOS BASEADOS EM VE (2D/3D + MALHA FECHADA)

Status: EXECUTADO em 2025-09-10
Escopo: Mapear com precisão a cadeia de cálculos de injeção (2D MAP, 3D MAP×RPM, 2D RPM) a partir da VE 3D e malha fechada (λ 3D), abrangendo unidades, fórmulas, bordas e passos de validação.

## 1) Entradas, Convenções e Unidades
- Pressões
  - MAP relativo `MAP_rel` [bar]. Pressão absoluta `P_abs_bar = 1 + MAP_rel` [bar], `P_abs_Pa = P_abs_bar × 1e5` [Pa].
  - Regulador 1:1 (referenciado ao coletor): `P_rail_bar = P_base + MAP_rel`; `ΔP_bar = P_base` (constante).
  - Regulador fixo: `P_rail_bar = P_base`; `ΔP_bar = P_base − MAP_rel`.
- Injetores (por bico)
  - Vazão nominal a 3 bar: `Q_lbph` [lb/h] por injetor; conversão: `1 lb/h = 0,126 mg/ms` ⇒ `flow_nom_mg_ms = Q_lbph × 0,126`.
  - Vazão com pressão: `flow_mg_ms = flow_nom_mg_ms × sqrt(max(ΔP_bar, 0) / 3)` (lei da raiz). Se `ΔP_bar ≤ 0` ⇒ fluxo 0.
- Combustível
  - AFR estequiométrico `AFR_stq` (Etanol 9.0; Gasolina 14.7; etc.). `AFR_target = AFR_stq × λ`.
- Gás ideal
  - `R = 287 J/(kg·K)`; `T = IAT_C + 273,15` [K]; `Disp_L` [L]; `N_cyl` [−]; `V_cyl = (Disp_L / N_cyl) × 1e-3` [m³].
- VE 3D (fonte única): `VE(m,r)` persistida com eixos (MAP×RPM). Fallback `VE_default = 0,90`.
- λ 3D (malha): `λ_target(m,r)` (estratégia/manual) ∈ [0,6 … 1,5].
- Elétrico e compensações
  - Dead Time base `DT` [ms] @13V; curva `DT(V)` dá `DT_extra = DT(V_batt) − DT(13V)`.
  - Compensações temperatura (motor/ar) em %, multiplicativas sobre PW_teo.
  - PW mínimo `PW_min` [ms]. Fator global 3D `G3D` (multiplicativo no preview 3D).

## 2) Cálculo físico por célula (m,r)
Dado `MAP_rel = m` [bar] e `RPM = r` [rpm]:
1. Pressões: `P_abs_bar = 1 + m`; `P_abs_Pa = P_abs_bar × 1e5`. `ΔP_bar` conforme regulador.
2. VE da célula: `VE_cell = VE(m,r)`; se ausente, usar `VE_default`.
3. Massa de ar por ciclo e por cilindro: `m_air_kg = (P_abs_Pa × V_cyl) / (R × T) × VE_cell`; `m_air_mg = m_air_kg × 1e6`.
4. Massa de combustível: `m_fuel_mg = m_air_mg / AFR_target` (com `AFR_target = AFR_stq × λ` apropriado).
5. Vazão do bico: `flow_mg_ms = flow_nom_mg_ms × sqrt(max(ΔP_bar,0)/3)`; se `ΔP_bar ≤ 0` ⇒ `flow=0`.
6. PW teórico: `PW_teo_ms = m_fuel_mg / flow_mg_ms` (se `flow>0`; senão `∞`).
7. Compensações multiplicativas de temperatura: `PW_comp = PW_teo × (1 + comp_motor) × (1 + comp_ar)` (compensações em fração).
8. Dead time e mínimo: `PW_final = max(PW_comp + DT + DT_extra, PW_min)`.
9. Se aplicável, fator `G3D` é multiplicado na visualização 3D: `PW_final_3D = PW_final × G3D`.

Observações:
- `ΔP` em bar; sqrt usa razão sobre 3 bar (referência de especificação do bico). Em regulador 1:1, `ΔP` é constante; em regulador fixo, `ΔP` cai no boost (reduz vazão).
- AFR menor (λ menor) ⇒ mistura mais rica ⇒ `AFR_target` menor ⇒ `PW` maior.

## 3) Injeção 2D (MAP)
- Eixo X: MAP relativo (bar). A linha 2D é calculada em um RPM de referência `rpm_ref` (mediana dos RPMs configurados).
- VE de linha: `VE_line(m) = VE(m, rpm_ref)` (ou `VE_default`).
- λ de linha: `λ_line(m)` via estratégia/manual, sem variação por RPM.
- `AFR_line(m) = AFR_stq × λ_line(m)`.
- Aplicar o cálculo físico com `VE_line` para obter `PW_line_final(m)`; modo ΔPW opcional: `PW_line_final(m) − PW_line_final(0)`.

## 4) Injeção 3D (MAP×RPM)
Dois modos de construção prática do mapa:

4.1) Sem malha fechada (λ OFF)
- Evitar custo de recalcular AFR por célula quando a malha está OFF. Construir o 3D a partir da linha 2D e do comportamento da VE por RPM:
- Fórmula coerente:
  - `PW_3D(m,r) = PW_line_final(m) × [ VE(m,r) / VE(m, rpm_ref) ] × G3D`
  - Onde `PW_line_final(m)` já inclui `AFR_line(m)` e compensações (motor/ar/DT/PW_min). O termo entre colchetes injeta a variação de carga por RPM segundo a malha VE, mantendo o “shape” de AFR da linha.

4.2) Com malha fechada (λ ON)
- Recalcular por célula (m,r):
  - `λ_target(m,r) = λ_base(m) × clFactor × f_rpm_shape(r) × f_rpm_user(r)` (limitado à faixa segura)
  - `AFR_target(m,r) = AFR_stq × λ_target(m,r)`
  - `VE_cell = VE(m,r)`
  - Aplicar cálculo físico 2)–8) por célula (e então `× G3D` se for o caso na visualização)

## 5) Fator 2D por RPM
- Conceitualmente, `f_RPM(r) = VE(m,r) / VE(m, rpm_ref)` para um `MAP_ref` (ou média de uma faixa útil).
- Uso típico no preview: `PW_3D(m,r) = PW_line_final(m) × f_RPM(r)` quando λ OFF.

## 6) Malha Fechada (λ 3D)
- Construção da malha alvo:
  - `λ_base(m)` por estratégia (conservadora/balanceada/agressiva) ou manual.
  - `λ_target(m,r) = λ_base(m) × clFactor × f_rpm_shape(r) × f_rpm_user(r)`.
- Aplicação:
  - Quando ON: cálculos por célula com `AFR_target(m,r)`.
  - Quando OFF: usar apenas `λ_line(m)` na linha e o fator `VE(m,r)/VE(m,rpm_ref)` para popular o 3D.

## 7) Compensações e Elétrico
- Temperatura motor/ar: curvas em %, multiplicativas sobre `PW_teo`.
- Bateria/voltagem: `DT_extra = DT(V_batt) − DT(13V)` aditivo.
- PW mínimo `PW_min` sempre aplicado ao fim de cada trilha de cálculo.

## 8) Bordas e Segurança
- Regulador fixo: atenção para `ΔP` caindo em boost (pode resultar em fluxo baixo e PW muito alto).
- `ΔP ≤ 0`: tratar fluxo 0; PW tende ao infinito ⇒ clampar e sinalizar célula inválida/saturada.
- IAT extremos alteram massa de ar (via T). Validar limites de temperatura.

## 9) Interpolação e Persistência
- VE(m,r) e λ(m,r) devem ser amostrados de acordo com os eixos da malha; nearest (atual) ou bilinear (recomendado para suavidade).
- Persistir eixos junto com a malha; invalidar ou reamostrar quando o usuário altera os eixos.

## 10) Exemplos Numéricos (sanidade)
Assuma: Etanol (AFR_stq=9,0), `Disp_L=1,9`, `N_cyl=4`, `IAT=40°C` ⇒ `T=313K`. `Q_lbph=112` lb/h ⇒ `flow_nom=112×0,126=14,112 mg/ms`.
- Regulador 1:1, `P_base=3,0 bar`, `MAP=0,0 bar` (P_abs=1,0): `ΔP=3,0` ⇒ `flow=14,112 mg/ms`.
- VE_cell=0,90; `V_cyl=0,475 L = 4,75e-4 m³` ⇒ `m_air_kg = (1e5 × 4,75e-4)/(287×313) × 0,90 ≈ 0,000476/898... ×0,90 ≈ 4,77e-7 kg ≈ 0,477 mg` (aprox.).
- λ=0,85 ⇒ `AFR_target=7,65` ⇒ `m_fuel=0,477/7,65 ≈ 0,0623 mg` ⇒ `PW_teo=0,0623/14,112 ≈ 0,00442 ms`.
- Compensações/DT aplicar conforme curvas; PW_final = `max(PW_comp + DT + DT_extra, PW_min)`.
Observação: valores exemplificativos; na prática, P_abs real, T e VE variarão.

## 11) Alinhamento com Implementação Atual
- Painel HTML (tests/mapa.html)
  - VE 3D é a fonte única (curvas antigas removidas). Linha 2D usa VE(m,rpm_ref); 3D sem malha usa razão VE; com malha recalcula por célula.
  - Regulador 1:1 vs fixo: `ΔP` tratado corretamente; fluxo derivado via sqrt.
  - Compensações: temp multiplicativas; DT por voltagem aditivo; PW_min aplicado.
- Core Python (src/core/fuel_maps/calculations.py)
  - Necessário revisar para espelhar exatamente as fórmulas e o caminho OFF/ON da malha.
  - Confirmar unidades (bar/Pa, mg/ms, ms) e posição do PW_min/DT.

## 12) Gaps Identificados e Ações Recomendadas
- Expor `rpm_ref` (UI/Core) para o cálculo da linha 2D e fator VE.
- Adotar interpolação bilinear para VE e λ nas amostragens 3D.
- Unificar lógica do Core com a da referência HTML (mesmo pipeline, mesmas bordas/clamps).
- Checklist de unidades e clamps em testes automatizados.
- Opção de sinalização de saturação (ΔP≤0 e fluxo=0) por célula.

## 13) Checklist de Validação
- [ ] 1:1 vs fixo (ΔP) coerente; sqrt(ΔP/3) aplicado
- [ ] Conversão lb/h → mg/ms correta
- [ ] λ OFF: 3D = 2D × VE_ratio × G3D
- [ ] λ ON: por célula com VE e AFR_target
- [ ] Compensações temp e DT nas posições corretas
- [ ] PW_min aplicado ao fim
- [ ] Interpolação consistente (nearest/bilinear)
- [ ] Eixos persistidos e compatíveis com as malhas

---
Este relatório serve de base para implementação/ajustes e para a criação dos testes de sanidade e de bordas. Recomenda-se evoluir para interpolação bilinear e parametrizar `rpm_ref` na UI.
