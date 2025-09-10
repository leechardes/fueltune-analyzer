Título: Unificar bloco “Valores” entre 2D e 3D (info, gradiente e ações)

Objetivo
- Exibir também nos mapas 3D o cabeçalho informativo (Tipo de Mapa | Unidade | Grade), a “Visualização com Gradiente” e as ações “Salvar”, “Restaurar Padrão” e “Validar”, evitando duplicação de código com os mapas 2D.

Escopo
- Arquivo: src/ui/pages/fuel_maps.py
- Subaba: Editar → Valores para mapas 2D e 3D
- Não alterar lógica de “Aplicar Cálculo”/“Preview Gráfico”.

Abordagem
1) Extrair helpers reutilizáveis (no próprio fuel_maps.py):
   - render_map_info_header(map_type, map_config, dimension, grid_shape=None)
     - Mostra: “Tipo de Mapa: {display_name|name} | Unidade: {unit}”
     - Se 3D: também “Grade: {linhas}×{colunas} (ativos)”
   - render_gradient_table(values, x_labels, y_labels, unit)
     - 2D: lista (1×N) com gradiente horizontal
     - 3D: matriz [linhas=y][colunas=x] com gradiente, respeitando enabled
   - render_action_buttons(on_save, on_reset, on_validate)
     - Três botões chamando callbacks injetados

2) Adaptar 2D (render_2d_values_editor):
   - Substituir cabeçalho inline por render_map_info_header(..., dimension="2D")
   - Substituir bloco “Visualização com Gradiente” por render_gradient_table
   - Substituir botões por render_action_buttons com callbacks atuais:
     - on_save → save_2d_map_data(...)
     - on_reset → create_default_2d_map(...)
     - on_validate → checagem min/max do map_config

3) Adaptar 3D (render_3d_values_editor):
   - Antes/abaixo do editor, mostrar:
     - render_map_info_header(..., dimension="3D", grid_shape=(len(RPM ativos), len(MAP ativos)))
     - render_gradient_table com a matriz filtrada (mesmos dados exibidos no editor)
     - render_action_buttons com callbacks 3D:
       - on_save → persistence_manager.save_3d_map_data(...)
       - on_reset → persistence_manager.create_default_map(...)
       - on_validate → validate_3d_map_values(matrix_full, map_type)

4) Ajustes em render_editor_view (3D):
   - Retornar um dicionário com:
     - matrix_display: matriz visível (filtrada e na orientação exibida)
     - matrix_full_current: matriz completa (com edições aplicadas se houver)
     - rpm_axis, map_axis, rpm_enabled, map_enabled
     - changed: bool indicando se houve edição
   - Não renderizar botões “Salvar/Restaurar/Validar” dentro do editor; usar os helpers do chamador.

5) Mensagens/validação:
   - 2D: manter checagem de limites simples
   - 3D: usar validate_3d_map_values (strict=False) e exibir erros/avisos

Critérios de Aceite
- Mapas 3D mostram: cabeçalho info, gradiente e botões (Salvar/Restaurar/Validar).
- 2D mantém comportamento, porém usando os helpers (sem regressão).
- Nenhuma duplicação de lógica de UI para esses blocos.
- Filtragem por enabled aplicada à visualização/gradiente.
- Eixos consistentes: X=MAP (desc), Y=RPM (ordem original) nas visualizações.

Testes Manuais
- 2D: editar valores, salvar, restaurar, validar, conferir gradiente/estatísticas.
- 3D: editar células, salvar, restaurar, validar, gradiente com eixos habilitados.
- Persistência: reabrir e confirmar dados salvos.

Notas
- Manter títulos de eixos: “MAP (bar)” e “RPM” nos gráficos.
- Não alterar “Aplicar Cálculo”/“Preview Gráfico”.

