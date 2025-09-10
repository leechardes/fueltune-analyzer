# Especificação de Cálculo – Mapas de Injeção (2D/3D) baseados em VE

Esta especificação descreve, com detalhes e unidades, os cálculos usados para construir os mapas de injeção 2D (MAP), 3D (MAP×RPM) e o fator 2D por RPM, a partir de uma malha VE 3D persistente e da malha fechada (λ 3D). O objetivo é padronizar o comportamento físico e alinhar a UI (Streamlit) e o painel HTML de referência.

## Entradas e Convenções
- MAP relativo `MAP_rel` [bar]; pressão absoluta `P_abs_bar = 1 + MAP_rel` [bar], `P_abs_Pa = P_abs_bar × 1e5` [Pa]
- Regulador:
  - 1:1: `P_rail_bar = P_base + MAP_rel`; `ΔP_bar = P_base`
  - Fixo: `P_rail_bar = P_base`; `ΔP_bar = P_base − MAP_rel`
- Injetor por bico:
  - Vazão nominal a 3 bar: `Q_lbph` [lb/h]; 1 lb/h = 0.126 mg/ms ⇒ `flow_nom_mg_ms = Q_lbph × 0.126`
  - Com pressão: `flow_mg_ms = flow_nom_mg_ms × sqrt(max(ΔP_bar,0)/3)`; se `ΔP_bar ≤ 0` ⇒ fluxo 0
- Combustível: AFR estequiométrico `AFR_stq` (Etanol 9.0, Gasolina 14.7, etc.)
- Gás ideal: R=287 J/(kg·K), temperatura `T = IAT_C + 273.15` [K]
- VE 3D: matriz `VE(m,r)` persistida (MAP×RPM); fallback `VE_default = 0.90` quando ausente
- λ 3D (malha fechada): `λ_target(m,r)` (estratégia/manual), 0.6–1.5
- Dead time: `DT(13V)` base e `DT_extra = DT(V_batt) − DT(13V)`
- Compensações de temperatura (motor/ar): curvas [%], multiplicativas
- PW mínimo: `PW_min` [ms]
- Fator global 3D: `G3D` (multiplicativo no 3D)

## Cálculo Físico por Célula (m,r)
1) Massa de ar por ciclo e por cilindro:
   - `V_cyl = (Disp_L / N_cyl) × 1e-3` [m³]
   - `m_air_kg = (P_abs_Pa × V_cyl) / (R × T) × VE(m,r)`; `m_air_mg = m_air_kg × 1e6`
2) Massa de combustível alvo: `m_fuel_mg = m_air_mg / AFR_target`
3) Fluxo do injetor: `flow_mg_ms = flow_nom_mg_ms × sqrt(max(ΔP_bar,0)/3)`
4) PW teórico: `PW_teo = m_fuel_mg / flow_mg_ms` (se fluxo>0; senão `∞`)
5) Compensações: `PW_comp = PW_teo × (1+comp_temp_motor) × (1+comp_temp_ar)`
6) Dead time e mínimo: `PW_final = max(PW_comp + DT(13V) + DT_extra, PW_min)`
7) Fator global 3D (se aplicável ao preview 3D): `PW_final × G3D`

## Injeção 2D (MAP)
- Eixo: MAP; usa um RPM de referência `rpm_ref` (mediana da lista atual)
- `VE_line = VE(m, rpm_ref)` (ou `VE_default`)
- `λ_line(m)`: manual/estratégia; `AFR_target = AFR_stq × λ_line(m)`
- Aplicar o cálculo físico com `VE_line` para obter `PW_final(m)`
- Modo ΔPW: `PW_final(m) − PW_final(m=0)`

## Injeção 3D (MAP×RPM)
### Sem malha fechada (λ OFF)
- Construção por fator de VE coerente:
  - `PW_3D(m,r) = PW_2D_line(m, rpm_ref) × [VE(m,r)/VE(m,rpm_ref)] × G3D`
  - Evita recalcular AFR por célula quando malha está OFF
### Com malha fechada (λ ON)
- `λ_target(m,r) = λ_base(m) × clFactor × f_rpm_shape(r) × f_rpm_user(r)`
- `AFR_target = AFR_stq × λ_target(m,r)`
- Cálculo físico completo por célula usando `VE(m,r)` e `AFR_target`

## Fator 2D por RPM
- Para um MAP de referência (ou média em faixa útil):
  - `f_RPM(r) = VE(m,r)/VE(m,rpm_ref)`
- Uso: `PW_3D(m,r) = PW_2D_line(m,rpm_ref) × f_RPM(r)` quando λ OFF

## Compensações e Bordas
- Temperatura: multiplicativas (%); Voltagem: DT aditivo (vs 13V)
- Regulador 1:1: ΔP constante; Fixo: ΔP decresce no boost
- `ΔP_bar ≤ 0` ⇒ fluxo=0 ⇒ PW→∞ ⇒ clampar com `PW_min` e sinalizar saturação

## Interpolação
- VE e λ: nearest (atual) ou bilinear (recomendado) ao amostrar eixos arbitrários
- Persistir e validar eixos no localStorage/DB; invalidar malhas incompatíveis

## Testes de Sanidade
- 1:1, P_base=3bar: `flow ≈ Q_lbph×0.126`; variar MAP não altera fluxo
- Fixo, MAP=+1.0, P_base=3.0: `ΔP=2.0` ⇒ `flow ≈ nominal×sqrt(2/3)`
- λ reduzido (mais rico) ⇒ AFR_target menor ⇒ PW maior
- Em alta RPM, VE↓ ⇒ PW↓ (λ OFF); com λ ON, λ_target pode compensar

## Gaps e Plano
- Expor `rpm_ref` na UI/Core
- Adotar interpolação bilinear para VE e λ
- Consolidar mesma física no Core (Python) usada no painel HTML
- Normalizar unidades e clamps (ms, bar, Pa, mg/ms)
