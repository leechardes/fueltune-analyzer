# AGENTE: Finalizar VE 3D no tests/mapa.html

Objetivo
- Concluir o painel VE 3D (MAP × RPM) em `tests/mapa.html`, com geração da matriz VE, coloração por faixa, exportação CSV e correções de interação.

Escopo
- Somente `tests/mapa.html` (painel de referência HTML). Não alterar Streamlit.

Tarefas Obrigatórias
- Renderização VE 3D
  - Construir cabeçalho `RPM` × `MAP` e corpo com VE(MAP) ajustado por `VE×RPM`.
  - Colorir células com gradiente consistente por min/max da grade.
  - Mostrar valores com 3 casas decimais.
- Interações
  - Adicionar tab “VE 3D” no seletor simples e alternar `viewVE3D` corretamente.
  - Recalcular VE 3D ao mudar `veCurve` (MAP:VE) e `veRpmCurve` (rpm:fator).
  - Incluir `applyVE3D` em binds para que a aplicação da VE 3D no cálculo de injeção reflita na visualização 3D quando pertinente.
- CSV
  - Botão “Baixar CSV VE 3D” exporta cabeçalho `RPM,<MAP...>` e linhas com VE calculado.
- Consistência
  - Não depender do toggle `applyVE3D` para exibir a matriz VE 3D (exibição deve sempre ser VE(MAP)*VE×RPM); o toggle afeta apenas a aplicação no cálculo de injeção.
  - Usar as mesmas listas `maps` e `rpmList` já construídas pelo painel para manter alinhamento com outras abas.

Critérios de Aceite
- Alternar para a aba “VE 3D” exibe matriz corretamente com o mesmo conjunto de `MAPs` e `RPMs` da sessão.
- Alterar `veCurve` e `veRpmCurve` reflete imediatamente na grade e no CSV.
- Exportação CSV contém cabeçalho e dados numéricos coerentes.
- Não quebra as outras abas (Linha, RPM 2D, Matriz MAP×RPM, 3D, Malha, Mapas 2D).

Notas Técnicas
- Color scale: usar min/max locais da grade VE.
- Manter formatação e estilo do arquivo atual (HTML+JS puro, sem libs).
- Binds: incluir `veRpmCurve`, `applyVE3D` no array de IDs observados.

Checklist de Verificação Rápida
- [ ] Tab “VE 3D” alterna `viewVE3D` e oculta as demais
- [ ] Matriz VE 3D preenche head/body
- [ ] Gradiente aplicado por min/max
- [ ] CSV exporta corretamente
- [ ] Binds atualizam VE 3D em tempo real
