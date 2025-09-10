# IMPLEMENT-REF-PANEL-MAPS-20250909

## Objetivo
Expandir o `tests/mapa.html` para ser o painel de referência único e funcional para todos os mapas (2D e 3D), incluindo Malha Fechada (alvos de lambda), eixos separados (MAP e RPM), e aplicação de compensações de temperatura e voltagem via sliders. Tornar possível avaliar e exportar rapidamente linhas, matrizes e 3D sem tocar no app.

## Escopo
- Apenas `tests/mapa.html` (HTML+JS). Nenhuma alteração em código Python/Streamlit.
- Manter a tabela original de Linha (MAP) e adicionar novas abas e controles.

## Requisitos
1) Abas no painel de resultados
- Linha MAP (já existe, manter)
- RPM (2D) – linha vs RPM a partir de um MAP de referência
- Matriz MAP×RPM (2D/3D)
- Mapa 3D (heatmap)
- Malha Fechada (λ-alvo MAP×RPM)

2) Seletor de mapa (já iniciado)
- 2D: Injeção (MAP), Compensações: TPS, RPM, Temperatura, Voltagem
- 3D: Injeção 3D, Lambda 3D, AFR 3D, Ignição 3D
- Mostrar apenas controles relevantes por tipo

3) Sliders de correção (aplicação sobre o PW final)
- Temperatura do motor (°C) – default neutro (sem compensação)
- Temperatura do ar (°C) – default neutro
- Tensão da bateria (V) – default neutro
- Interruptores para ligar/desligar a aplicação de cada correção
- Curvas configuráveis (já existem inputs para Temp/Volt; usar também para ar):
  - Temperatura motor/air → fator multiplicativo (ex.: 1.00 neutro)
  - Voltagem → correção de dead time (ms) adicionada antes do PW mínimo

4) Malha Fechada (λ-alvo)
- Nova aba com tabela MAP×RPM de λ-alvo:
  - Modo “Estratégia” (Conservadora/Balanceada/Agressiva) → usa curva λ por MAP
  - Modo “Manual” → curva λ por MAP (input já existente) e fator por RPM (lista+pontos)
- Export CSV da malha fechada (MAP, RPM, lambda)
- Opção na aba “Mapa 3D (Injeção)” para “Aplicar alvo de sonda (λ)” → substitui afr_target por afr_estq×λ_alvo(rpm,map) no cálculo

5) Eixos separados (MAP e RPM)
- Aba “MAP (2D)”: já contemplada (Linha)
- Aba “RPM (2D)”: linha vs RPM utilizando um MAP de referência (seleção simples: -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)
- Export CSV para cada aba

6) Defaults neutros
- Curva VE default: `-1.0:0.70,-0.5:0.80,-0.3:0.85,0.0:0.90,0.5:0.92,1.0:0.95,1.5:0.93,2.0:0.91`
- Temperatura motor default neutra (ex.: 80°C → fator 1.00)
- Temperatura ar default neutra (ex.: 25–30°C → fator 1.00)
- Tensão default neutra (13.8V → DT adicional 0.00ms)
- Turbo? Sim/Não; Boost máx; P_base=3.0bar; Regulador 1:1; inj per bico lb/h; dt; PWmin

## Tarefas
1. UI/HTML
- Adicionar sliders e switches no card de “Resultado” (acima das abas):
  - `#engTemp`, `#airTemp`, `#battVolt` (type=range) e `#applyEng`, `#applyAir`, `#applyVolt` (checkbox)
  - Nota “Compensações ativas são aplicadas sobre Linha, Matriz e 3D”
- Adicionar aba “RPM (2D)” com tabela de linha RPM (seleção de MAP ref.)
- Adicionar aba “Malha Fechada” com tabela λ MAP×RPM, seletor de modo (Estratégia/Manual), export CSV

2. JS – Cálculos
- Calcular Linha (MAP) como já feito (ΔP por lei da raiz, VE/λ)
- Aplicar correções se switches ligados:
  - Fator temp motor: `pw = pw * f_motor(engTemp)`
  - Fator temp ar: `pw = pw * f_air(airTemp)`
  - Voltagem: `pw = max((pw_teo + dt + dt_extra(volt)), pwmin)`
- Matriz MAP×RPM: multiplicar pela curva RPM (exceto λ/AFR), e aplicar correções ativas
- 3D heatmap: usar matriz resultante após correções; para “Injeção 3D”, se “Aplicar λ-alvo” estiver on, usar λ da malha
- RPM (2D): para o MAP de referência escolhido, gerar linha vs RPM usando a matriz e correções

3. Export
- CSV por aba: cabeçalhos adequados (MAP×RPM inclui eixos na primeira linha/coluna)

4. Robustez
- Garantir que `getElementById` não é chamado em elementos inexistentes
- Nenhum erro no console ao alternar tipos de mapa/abas/compensações

## Critérios de Aceitação
- Abrir `tests/mapa.html` no navegador → sem erros de console
- Alternar tipos de mapa e abas funciona e atualiza tabelas
- Sliders de compensação alteram Linha/Matriz/3D com switches ligados; com switches desligados, resultados voltam ao neutro
- “Aplicar alvo de sonda” em Injeção 3D muda a matriz conforme a malha fechada
- Export CSV de cada aba gera arquivos coerentes com os dados exibidos

## Entregáveis
- `tests/mapa.html` atualizado com:
  - Abas: Linha MAP, RPM (2D), Matriz MAP×RPM, Mapa 3D, Malha Fechada
  - Sliders (Temp motor, Temp ar, Bateria) + switches de aplicação
  - Modo λ-alvo (malha) e aplicação no 3D de injeção
  - Exports CSV por aba

## Observações
- Sem dependências externas (apenas HTML+JS)
- Manter o estilo simples e a tabela original (Linha)
- Qualquer funcionalidade “placeholder” (p. ex., ignição 3D avançada) deve estar estável e sem erros
