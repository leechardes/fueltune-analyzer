# FUEL-MAPS-UI-IMPLEMENTATION

## Objetivo
Implementar interface profissional completa para edição de mapas de injeção 2D/3D com visualização em tempo real, editores de eixos, importação/exportação e todas as funcionalidades especificadas no sistema de mapas.

## Contexto
Você é um especialista em interfaces de usuário para aplicações automotivas com foco em sistemas de injeção eletrônica. Deve criar uma interface intuitiva e profissional que permita editar mapas complexos de forma eficiente, seguindo as melhores práticas de UX.

## Padrões de Desenvolvimento
Este agente segue os padrões definidos em:
- /srv/projects/shared/docs/agents/development/A04-STREAMLIT-PROFESSIONAL.md

### Princípios Fundamentais:
1. **ZERO emojis** - Usar apenas Material Design Icons
2. **Interface profissional** - Sem decorações infantis  
3. **CSS adaptativo** - Funciona em tema claro e escuro
4. **Português brasileiro** - Todos os textos traduzidos
5. **Ícones consistentes** - Material Icons em todos os componentes
6. **Varredura PROFUNDA** - Não deixar NENHUM emoji escapar
7. **NUNCA usar !important no CSS** - Para permitir adaptação de temas

## Entrada Esperada
- **Modelos implementados**: src/data/fuel_maps_models.py (do primeiro agente)
- **Sistema de bancadas**: src/components/bank_configurator.py (do segundo agente)
- **Documentação**: docs/FUEL-MAPS-SPECIFICATION.md
- **Diretório base**: /home/lee/projects/fueltune-streamlit/

## Tarefas

### 1. Criar Página Principal de Mapas

#### 1.1 Arquivo: src/ui/pages/fuel_maps.py
```python
"""
Página principal do sistema de mapas de injeção.
Inclui lista de mapas, editores 2D/3D e configuração de eixos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple
import json

from ...data.fuel_maps_models import FuelMap, MapData2D, MapData3D
from ...data.models import Vehicle, get_database
from ...components.bank_selector import BankSelector
from ...components.map_editors import Map2DEditor, Map3DEditor, AxisEditor
from ...services.map_duplication import MapDuplicationService
from ...utils.map_interpolation import MapInterpolator
from ...services.map_import_export import MapImportExportService

def render_fuel_maps_page():
    """Renderiza página principal de mapas de injeção."""
    
    st.markdown(
        '<div class="main-header">'
        '<span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">tune</span>'
        'Sistema de Mapas de Injeção'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Seleção de veículo
    vehicle_id = _render_vehicle_selector()
    if not vehicle_id:
        st.warning("Selecione um veículo para acessar os mapas")
        return
    
    # Verificar configuração de bancadas
    vehicle = _load_vehicle_data(vehicle_id)
    if not vehicle:
        st.error("Dados do veículo não encontrados")
        return
    
    # Seletor de bancada
    selected_bank = BankSelector.render_bank_selector(
        vehicle.bank_b_enabled or False,
        key_prefix="fuel_maps"
    )
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Lista de Mapas",
        "Editor 2D",
        "Editor 3D", 
        "Configurar Eixos",
        "Importar/Exportar"
    ])
    
    with tab1:
        _render_maps_list_tab(vehicle_id, selected_bank)
    
    with tab2:
        _render_2d_editor_tab(vehicle_id, selected_bank)
    
    with tab3:
        _render_3d_editor_tab(vehicle_id, selected_bank)
    
    with tab4:
        _render_axis_config_tab(vehicle_id, selected_bank)
    
    with tab5:
        _render_import_export_tab(vehicle_id, selected_bank)

def _render_vehicle_selector() -> Optional[str]:
    """Renderiza seletor de veículo."""
    db = get_database()
    db_session = db.get_session()
    
    try:
        vehicles = db_session.query(Vehicle).filter(Vehicle.is_active == True).all()
        
        if not vehicles:
            st.error("Nenhum veículo ativo encontrado")
            return None
        
        vehicle_options = {
            f"{v.display_name} - {v.technical_summary}": v.id 
            for v in vehicles
        }
        
        selected_display = st.selectbox(
            "Selecionar Veículo",
            options=list(vehicle_options.keys()),
            key="fuel_maps_vehicle_selector"
        )
        
        return vehicle_options.get(selected_display)
        
    finally:
        db_session.close()

def _render_maps_list_tab(vehicle_id: str, selected_bank: str):
    """Tab com lista de mapas disponíveis."""
    
    st.markdown(
        '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">list</span>Lista de Mapas - Bancada {}</h3>'.format(selected_bank),
        unsafe_allow_html=True
    )
    
    # Carregar mapas da bancada selecionada
    maps_data = _load_maps_for_bank(vehicle_id, selected_bank)
    
    if not maps_data:
        st.info(f"Nenhum mapa encontrado para a Bancada {selected_bank}")
        
        if st.button(":material/add: Criar Mapas Padrão"):
            _create_default_maps(vehicle_id, selected_bank)
            st.rerun()
        
        return
    
    # Exibir mapas em cards
    _render_maps_cards(maps_data, selected_bank)
    
    # Ações em lote
    st.markdown("---")
    _render_batch_actions(vehicle_id, selected_bank)

def _render_maps_cards(maps_data: List[Dict], selected_bank: str):
    """Renderiza cards dos mapas."""
    
    # Agrupar mapas por categoria
    categories = {
        "Mapas Principais": ["main_fuel_2d_map", "main_fuel_2d_rpm", "main_fuel_3d"],
        "Compensação": ["rpm_compensation", "temp_compensation", "tps_compensation", 
                       "battery_voltage_compensation", "air_temp_compensation"],
        "Partida": ["first_pulse_cold_start", "cranking_pulse", "after_start_enrichment"],
        "Malha Fechada": ["target_lambda"],
        "Ignição": ["ignition"]
    }
    
    for category, map_types in categories.items():
        category_maps = [m for m in maps_data if m['map_type'] in map_types]
        
        if not category_maps:
            continue
        
        st.markdown(f"#### {category}")
        
        cols = st.columns(min(3, len(category_maps)))
        
        for idx, map_data in enumerate(category_maps):
            with cols[idx % 3]:
                _render_single_map_card(map_data, selected_bank)

def _render_single_map_card(map_data: Dict, selected_bank: str):
    """Renderiza card de um mapa individual."""
    
    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: var(--secondary-background-color);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span class="material-icons" style="margin-right: 0.5rem; color: var(--primary-color);">
                    {"show_chart" if map_data['dimensions'] == 1 else "3d_rotation"}
                </span>
                <strong>{map_data['name']}</strong>
            </div>
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                {map_data['description'] or 'Sem descrição'}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem;">
                <span>{"2D" if map_data['dimensions'] == 1 else "3D"}</span>
                <span>v{map_data['version']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Editar", key=f"edit_{map_data['id']}"):
                st.session_state['selected_map_id'] = map_data['id']
                if map_data['dimensions'] == 1:
                    st.session_state['active_tab'] = 'Editor 2D'
                else:
                    st.session_state['active_tab'] = 'Editor 3D'
        
        with col2:
            if st.button("Duplicar", key=f"duplicate_{map_data['id']}"):
                _duplicate_map(map_data['id'])
        
        with col3:
            if st.button("Histórico", key=f"history_{map_data['id']}"):
                _show_map_history(map_data['id'])

def _render_2d_editor_tab(vehicle_id: str, selected_bank: str):
    """Tab do editor de mapas 2D."""
    
    st.markdown(
        '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">show_chart</span>Editor de Mapas 2D</h3>',
        unsafe_allow_html=True
    )
    
    # Seleção do mapa 2D
    maps_2d = _load_2d_maps_for_bank(vehicle_id, selected_bank)
    
    if not maps_2d:
        st.info("Nenhum mapa 2D disponível para esta bancada")
        return
    
    map_options = {f"{m['name']} ({m['map_type']})": m['id'] for m in maps_2d}
    
    selected_map_name = st.selectbox(
        "Selecionar Mapa 2D",
        options=list(map_options.keys()),
        key="selected_2d_map"
    )
    
    if not selected_map_name:
        return
    
    map_id = map_options[selected_map_name]
    
    # Renderizar editor 2D
    editor_2d = Map2DEditor(map_id)
    editor_2d.render()

def _render_3d_editor_tab(vehicle_id: str, selected_bank: str):
    """Tab do editor de mapas 3D."""
    
    st.markdown(
        '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">3d_rotation</span>Editor de Mapas 3D</h3>',
        unsafe_allow_html=True
    )
    
    # Seleção do mapa 3D
    maps_3d = _load_3d_maps_for_bank(vehicle_id, selected_bank)
    
    if not maps_3d:
        st.info("Nenhum mapa 3D disponível para esta bancada")
        return
    
    map_options = {f"{m['name']} ({m['map_type']})": m['id'] for m in maps_3d}
    
    selected_map_name = st.selectbox(
        "Selecionar Mapa 3D",
        options=list(map_options.keys()),
        key="selected_3d_map"
    )
    
    if not selected_map_name:
        return
    
    map_id = map_options[selected_map_name]
    
    # Renderizar editor 3D
    editor_3d = Map3DEditor(map_id)
    editor_3d.render()

def _render_axis_config_tab(vehicle_id: str, selected_bank: str):
    """Tab de configuração de eixos."""
    
    st.markdown(
        '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">tune</span>Configuração de Eixos</h3>',
        unsafe_allow_html=True
    )
    
    # Seleção do mapa para configurar eixos
    all_maps = _load_maps_for_bank(vehicle_id, selected_bank)
    
    if not all_maps:
        st.info("Nenhum mapa disponível para configuração")
        return
    
    map_options = {f"{m['name']} ({m['map_type']})": m['id'] for m in all_maps}
    
    selected_map_name = st.selectbox(
        "Selecionar Mapa para Configurar Eixos",
        options=list(map_options.keys()),
        key="axis_config_map"
    )
    
    if not selected_map_name:
        return
    
    map_id = map_options[selected_map_name]
    
    # Renderizar editor de eixos
    axis_editor = AxisEditor(map_id)
    axis_editor.render()

def _render_import_export_tab(vehicle_id: str, selected_bank: str):
    """Tab de importação/exportação."""
    
    st.markdown(
        '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">import_export</span>Importar/Exportar Mapas</h3>',
        unsafe_allow_html=True
    )
    
    # Duas seções: Importar e Exportar
    col1, col2 = st.columns(2)
    
    with col1:
        _render_import_section(vehicle_id, selected_bank)
    
    with col2:
        _render_export_section(vehicle_id, selected_bank)

def _render_import_section(vehicle_id: str, selected_bank: str):
    """Seção de importação."""
    
    st.markdown(
        '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">file_upload</span>Importar</h4>',
        unsafe_allow_html=True
    )
    
    # Seleção do tipo de arquivo
    import_format = st.selectbox(
        "Formato do Arquivo",
        options=["FTManager (.ftm)", "CSV", "JSON"],
        key="import_format"
    )
    
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "Selecionar Arquivo",
        type=['ftm', 'csv', 'json'] if import_format == "Todos" else 
             ['ftm'] if 'FTManager' in import_format else
             ['csv'] if 'CSV' in import_format else ['json'],
        key="map_import_file"
    )
    
    if uploaded_file:
        # Preview dos dados
        if st.button(":material/preview: Visualizar Dados"):
            _preview_import_data(uploaded_file, import_format)
        
        # Botão de importação
        if st.button(":material/cloud_upload: Importar Mapas"):
            _import_maps(uploaded_file, vehicle_id, selected_bank, import_format)

def _render_export_section(vehicle_id: str, selected_bank: str):
    """Seção de exportação."""
    
    st.markdown(
        '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">file_download</span>Exportar</h4>',
        unsafe_allow_html=True
    )
    
    # Seleção dos mapas para exportar
    available_maps = _load_maps_for_bank(vehicle_id, selected_bank)
    
    if not available_maps:
        st.info("Nenhum mapa disponível para exportação")
        return
    
    map_options = {f"{m['name']} ({m['map_type']})": m['id'] for m in available_maps}
    
    selected_maps = st.multiselect(
        "Mapas para Exportar",
        options=list(map_options.keys()),
        default=list(map_options.keys())[:5],  # Primeiros 5 por padrão
        key="export_maps_selection"
    )
    
    # Formato de exportação
    export_format = st.selectbox(
        "Formato de Exportação",
        options=["FTManager (.ftm)", "CSV", "JSON", "Backup Completo"],
        key="export_format"
    )
    
    # Botão de exportação
    if selected_maps and st.button(":material/cloud_download: Exportar"):
        map_ids = [map_options[name] for name in selected_maps]
        _export_maps(map_ids, vehicle_id, selected_bank, export_format)

# Funções auxiliares...
def _load_vehicle_data(vehicle_id: str) -> Optional[Vehicle]:
    """Carrega dados do veículo."""
    db = get_database()
    db_session = db.get_session()
    try:
        return db_session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    finally:
        db_session.close()

def _load_maps_for_bank(vehicle_id: str, bank_id: str) -> List[Dict]:
    """Carrega mapas para uma bancada específica."""
    db = get_database()
    db_session = db.get_session()
    
    try:
        maps = db_session.query(FuelMap).filter(
            FuelMap.vehicle_id == vehicle_id,
            FuelMap.bank_id == bank_id,
            FuelMap.is_active == True
        ).all()
        
        return [
            {
                'id': m.id,
                'name': m.name,
                'map_type': m.map_type,
                'description': m.description,
                'dimensions': m.dimensions,
                'version': m.version,
                'x_axis_type': m.x_axis_type,
                'y_axis_type': m.y_axis_type,
                'data_unit': m.data_unit
            }
            for m in maps
        ]
    finally:
        db_session.close()

# Mais funções auxiliares continuam...
```

### 2. Criar Componentes de Edição

#### 2.1 Arquivo: src/components/map_editors.py
```python
"""
Componentes especializados para edição de mapas 2D e 3D.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple, Any
import json

from ..data.fuel_maps_models import FuelMap, MapData2D, MapData3D, MapAxisData
from ..data.models import get_database
from ..utils.map_interpolation import MapInterpolator
from ..utils.map_validation import MapValidator

class Map2DEditor:
    """Editor especializado para mapas 2D."""
    
    def __init__(self, map_id: str):
        self.map_id = map_id
        self.db = get_database()
        self.interpolator = MapInterpolator()
        self.validator = MapValidator()
    
    def render(self):
        """Renderiza editor completo para mapa 2D."""
        
        # Carregar dados do mapa
        map_data = self._load_map_data()
        if not map_data:
            st.error("Mapa não encontrado")
            return
        
        st.markdown(f"**Editando**: {map_data['name']} ({map_data['data_unit']})")
        
        # Layout em colunas
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._render_2d_plot(map_data)
        
        with col2:
            self._render_2d_controls(map_data)
        
        # Editor de tabela
        st.markdown("---")
        self._render_2d_table_editor(map_data)
    
    def _render_2d_plot(self, map_data: Dict):
        """Renderiza gráfico 2D interativo."""
        
        st.markdown(
            '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">show_chart</span>Visualização Gráfica</h4>',
            unsafe_allow_html=True
        )
        
        # Carregar dados dos eixos e valores
        axis_data, values_data = self._load_2d_data(map_data['id'])
        
        if not axis_data or not values_data:
            st.warning("Dados não encontrados para este mapa")
            return
        
        # Preparar dados para o gráfico
        x_values = [axis_data.get(f'slot_{i}') for i in range(map_data['x_slots_active'])]
        y_values = [values_data.get(f'value_{i}') for i in range(map_data['x_slots_active'])]
        
        # Remover valores None
        plot_data = [(x, y) for x, y in zip(x_values, y_values) if x is not None and y is not None]
        
        if not plot_data:
            st.warning("Nenhum ponto de dados válido encontrado")
            return
        
        x_clean, y_clean = zip(*plot_data)
        
        # Criar gráfico Plotly
        fig = go.Figure()
        
        # Linha principal
        fig.add_trace(go.Scatter(
            x=x_clean,
            y=y_clean,
            mode='lines+markers',
            name='Mapa Base',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8, color='#3b82f6'),
            hovertemplate=f'%{{x}} {map_data["x_axis_type"]}<br>%{{y}} {map_data["data_unit"]}<extra></extra>'
        ))
        
        # Pontos interpolados (se habilitado)
        if st.session_state.get('show_interpolation', False):
            x_interp, y_interp = self._calculate_interpolation(x_clean, y_clean)
            
            fig.add_trace(go.Scatter(
                x=x_interp,
                y=y_interp,
                mode='lines',
                name='Interpolação',
                line=dict(color='#10b981', width=1, dash='dot'),
                opacity=0.7,
                hovertemplate='Interpolado<br>%{x}<br>%{y}<extra></extra>'
            ))
        
        # Configurar layout
        fig.update_layout(
            title=f"Mapa: {map_data['name']}",
            xaxis_title=f"{map_data['x_axis_type']}",
            yaxis_title=f"Valores ({map_data['data_unit']})",
            height=400,
            hovermode='x unified',
            template='plotly_white'
        )
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_2d_controls(self, map_data: Dict):
        """Renderiza controles do editor 2D."""
        
        st.markdown(
            '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">tune</span>Controles</h4>',
            unsafe_allow_html=True
        )
        
        # Mostrar interpolação
        show_interp = st.checkbox(
            "Mostrar Interpolação",
            key="show_interpolation",
            help="Exibe curva interpolada entre pontos"
        )
        
        # Ferramentas de edição
        st.markdown("**Ferramentas:**")
        
        if st.button(":material/auto_fix_high: Auto Suavizar"):
            self._apply_smoothing(map_data['id'])
        
        if st.button(":material/linear_scale: Interpolar Lacunas"):
            self._fill_gaps(map_data['id'])
        
        if st.button(":material/content_copy: Copiar para Bancada B"):
            self._copy_to_bank_b(map_data['id'])
        
        # Validações
        st.markdown("---")
        st.markdown("**Validações:**")
        
        validations = self.validator.validate_2d_map(map_data['id'])
        
        for validation in validations:
            if validation['status'] == 'OK':
                st.success(f"✓ {validation['message']}")
            elif validation['status'] == 'WARNING':
                st.warning(f"⚠ {validation['message']}")
            else:
                st.error(f"✗ {validation['message']}")
    
    def _render_2d_table_editor(self, map_data: Dict):
        """Renderiza editor tabular para edição direta."""
        
        st.markdown(
            '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">table_chart</span>Editor Tabular</h4>',
            unsafe_allow_html=True
        )
        
        # Carregar dados
        axis_data, values_data = self._load_2d_data(map_data['id'])
        
        if not axis_data or not values_data:
            return
        
        # Criar DataFrame para edição
        active_slots = map_data['x_slots_active']
        
        edit_data = []
        for i in range(active_slots):
            edit_data.append({
                'Slot': i,
                f'{map_data["x_axis_type"]}': axis_data.get(f'slot_{i}', 0.0),
                f'Valor ({map_data["data_unit"]})': values_data.get(f'value_{i}', 0.0)
            })
        
        # Editor de dados
        edited_df = st.data_editor(
            pd.DataFrame(edit_data),
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "Slot": st.column_config.NumberColumn(
                    "Slot",
                    disabled=True
                ),
                f'{map_data["x_axis_type"]}': st.column_config.NumberColumn(
                    f'{map_data["x_axis_type"]}',
                    format="%.2f"
                ),
                f'Valor ({map_data["data_unit"]})': st.column_config.NumberColumn(
                    f'Valor ({map_data["data_unit"]})',
                    format="%.3f"
                )
            }
        )
        
        # Botão para salvar alterações
        if st.button(":material/save: Salvar Alterações"):
            self._save_2d_data(map_data['id'], edited_df)
    
    def _load_map_data(self) -> Optional[Dict]:
        """Carrega dados básicos do mapa."""
        db_session = self.db.get_session()
        try:
            fuel_map = db_session.query(FuelMap).filter(FuelMap.id == self.map_id).first()
            if not fuel_map:
                return None
            
            return {
                'id': fuel_map.id,
                'name': fuel_map.name,
                'description': fuel_map.description,
                'x_axis_type': fuel_map.x_axis_type,
                'y_axis_type': fuel_map.y_axis_type,
                'data_unit': fuel_map.data_unit,
                'x_slots_active': fuel_map.x_slots_active,
                'y_slots_active': fuel_map.y_slots_active
            }
        finally:
            db_session.close()
    
    def _load_2d_data(self, map_id: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Carrega dados do eixo e valores 2D."""
        db_session = self.db.get_session()
        try:
            # Dados do eixo X
            axis_data = db_session.query(MapAxisData).filter(
                MapAxisData.map_id == map_id,
                MapAxisData.axis_type == 'X'
            ).first()
            
            # Dados dos valores
            values_data = db_session.query(MapData2D).filter(
                MapData2D.map_id == map_id
            ).first()
            
            axis_dict = None
            if axis_data:
                axis_dict = {f'slot_{i}': getattr(axis_data, f'slot_{i}') for i in range(32)}
            
            values_dict = None
            if values_data:
                values_dict = {f'value_{i}': getattr(values_data, f'value_{i}') for i in range(32)}
            
            return axis_dict, values_dict
            
        finally:
            db_session.close()
    
    def _save_2d_data(self, map_id: str, edited_df: pd.DataFrame):
        """Salva dados editados."""
        db_session = self.db.get_session()
        try:
            # Atualizar dados dos eixos
            axis_data = db_session.query(MapAxisData).filter(
                MapAxisData.map_id == map_id,
                MapAxisData.axis_type == 'X'
            ).first()
            
            # Atualizar dados dos valores
            values_data = db_session.query(MapData2D).filter(
                MapData2D.map_id == map_id
            ).first()
            
            if axis_data and values_data:
                for index, row in edited_df.iterrows():
                    slot_idx = int(row['Slot'])
                    
                    # Atualizar eixo
                    axis_col = [col for col in edited_df.columns if 'RPM' in col or 'MAP' in col or 'Temp' in col][0]
                    setattr(axis_data, f'slot_{slot_idx}', float(row[axis_col]))
                    
                    # Atualizar valor
                    value_col = [col for col in edited_df.columns if 'Valor' in col][0]
                    setattr(values_data, f'value_{slot_idx}', float(row[value_col]))
                
                db_session.commit()
                st.success("Dados salvos com sucesso!")
                st.rerun()
            
        except Exception as e:
            db_session.rollback()
            st.error(f"Erro ao salvar: {str(e)}")
        finally:
            db_session.close()

class Map3DEditor:
    """Editor especializado para mapas 3D."""
    
    def __init__(self, map_id: str):
        self.map_id = map_id
        self.db = get_database()
        self.interpolator = MapInterpolator()
    
    def render(self):
        """Renderiza editor completo para mapa 3D."""
        
        # Carregar dados do mapa
        map_data = self._load_map_data()
        if not map_data:
            st.error("Mapa não encontrado")
            return
        
        st.markdown(f"**Editando**: {map_data['name']} ({map_data['data_unit']})")
        
        # Tabs de visualização
        tab1, tab2, tab3 = st.tabs([
            "Superfície 3D",
            "Mapa de Calor",
            "Editor de Células"
        ])
        
        with tab1:
            self._render_3d_surface(map_data)
        
        with tab2:
            self._render_heatmap(map_data)
        
        with tab3:
            self._render_cell_editor(map_data)
    
    def _render_3d_surface(self, map_data: Dict):
        """Renderiza superfície 3D interativa."""
        
        st.markdown(
            '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">3d_rotation</span>Superfície 3D</h4>',
            unsafe_allow_html=True
        )
        
        # Carregar dados 3D
        matrix_data = self._load_3d_matrix(map_data['id'])
        
        if matrix_data is None:
            st.warning("Dados não encontrados para este mapa")
            return
        
        # Criar superfície 3D
        fig = go.Figure(data=[
            go.Surface(
                z=matrix_data,
                colorscale='RdYlBu_r',
                showscale=True,
                colorbar=dict(title=map_data['data_unit'])
            )
        ])
        
        fig.update_layout(
            title=f"Mapa 3D: {map_data['name']}",
            scene=dict(
                xaxis_title=map_data['x_axis_type'],
                yaxis_title=map_data['y_axis_type'],
                zaxis_title=map_data['data_unit']
            ),
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_heatmap(self, map_data: Dict):
        """Renderiza mapa de calor 2D."""
        
        st.markdown(
            '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">grid_on</span>Mapa de Calor</h4>',
            unsafe_allow_html=True
        )
        
        # Carregar dados 3D
        matrix_data = self._load_3d_matrix(map_data['id'])
        
        if matrix_data is None:
            return
        
        # Criar heatmap
        fig = px.imshow(
            matrix_data,
            color_continuous_scale='RdYlBu_r',
            aspect='auto',
            title=f"Mapa de Calor: {map_data['name']}",
            labels=dict(
                x=map_data['x_axis_type'],
                y=map_data['y_axis_type'],
                color=map_data['data_unit']
            )
        )
        
        fig.update_layout(height=500)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Controles do mapa de calor
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(":material/palette: Alterar Cores"):
                self._change_colorscale(map_data['id'])
        
        with col2:
            if st.button(":material/zoom_in: Focar Região"):
                self._focus_region(map_data['id'])
    
    def _render_cell_editor(self, map_data: Dict):
        """Renderiza editor célula por célula."""
        
        st.markdown(
            '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">apps</span>Editor de Células</h4>',
            unsafe_allow_html=True
        )
        
        # Seleção da célula
        col1, col2 = st.columns(2)
        
        with col1:
            x_cell = st.number_input(
                f"Posição X ({map_data['x_axis_type']})",
                min_value=0,
                max_value=map_data['x_slots_active']-1,
                value=0,
                key="cell_x"
            )
        
        with col2:
            y_cell = st.number_input(
                f"Posição Y ({map_data['y_axis_type']})",
                min_value=0,
                max_value=map_data['y_slots_active']-1,
                value=0,
                key="cell_y"
            )
        
        # Valor atual da célula
        current_value = self._get_cell_value(map_data['id'], x_cell, y_cell)
        
        st.info(f"Valor atual da célula [{x_cell}, {y_cell}]: {current_value} {map_data['data_unit']}")
        
        # Editor do valor
        new_value = st.number_input(
            f"Novo valor ({map_data['data_unit']})",
            value=float(current_value) if current_value else 0.0,
            step=0.001,
            format="%.3f",
            key="new_cell_value"
        )
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(":material/edit: Atualizar Célula"):
                self._update_cell(map_data['id'], x_cell, y_cell, new_value)
        
        with col2:
            if st.button(":material/select_all: Aplicar em Região"):
                self._apply_to_region(map_data['id'], x_cell, y_cell, new_value)
        
        with col3:
            if st.button(":material/gradient: Interpolar Vizinhos"):
                self._interpolate_neighbors(map_data['id'], x_cell, y_cell)
    
    # Métodos auxiliares do Map3DEditor
    def _load_map_data(self) -> Optional[Dict]:
        """Carrega dados básicos do mapa."""
        # Similar ao Map2DEditor
        pass
    
    def _load_3d_matrix(self, map_id: str) -> Optional[np.ndarray]:
        """Carrega matriz 3D do banco."""
        db_session = self.db.get_session()
        try:
            data_3d = db_session.query(MapData3D).filter(MapData3D.map_id == map_id).first()
            
            if not data_3d:
                return None
            
            # Converter dados do banco para matriz numpy
            matrix = np.zeros((32, 32))
            
            for x in range(32):
                for y in range(32):
                    value = getattr(data_3d, f'value_{x}_{y}', None)
                    if value is not None:
                        matrix[x, y] = value
            
            return matrix
            
        finally:
            db_session.close()

class AxisEditor:
    """Editor especializado para configuração de eixos."""
    
    def __init__(self, map_id: str):
        self.map_id = map_id
        self.db = get_database()
    
    def render(self):
        """Renderiza editor de eixos."""
        
        st.markdown(
            '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">tune</span>Configuração de Eixos</h4>',
            unsafe_allow_html=True
        )
        
        # Carregar dados do mapa
        map_data = self._load_map_data()
        if not map_data:
            st.error("Mapa não encontrado")
            return
        
        # Editor do eixo X
        st.markdown("### Eixo X")
        self._render_axis_editor('X', map_data)
        
        # Editor do eixo Y (se 3D)
        if map_data['dimensions'] == 2:
            st.markdown("### Eixo Y")
            self._render_axis_editor('Y', map_data)
    
    def _render_axis_editor(self, axis_type: str, map_data: Dict):
        """Renderiza editor para um eixo específico."""
        
        # Determinar tipo do eixo
        axis_data_type = map_data['x_axis_type'] if axis_type == 'X' else map_data['y_axis_type']
        slots_active = map_data['x_slots_active'] if axis_type == 'X' else map_data['y_slots_active']
        
        st.markdown(f"**Tipo**: {axis_data_type}")
        
        # Carregar dados do eixo
        axis_data = self._load_axis_data(axis_type)
        
        if not axis_data:
            st.warning(f"Dados do eixo {axis_type} não encontrados")
            return
        
        # Configuração de slots ativos
        new_active_slots = st.slider(
            f"Slots Ativos - Eixo {axis_type}",
            min_value=2,
            max_value=32,
            value=slots_active,
            key=f"active_slots_{axis_type}"
        )
        
        # Editor dos valores dos slots
        slot_values = []
        
        cols = st.columns(4)
        for i in range(new_active_slots):
            with cols[i % 4]:
                current_value = axis_data.get(f'slot_{i}', 0.0)
                new_value = st.number_input(
                    f"Slot {i}",
                    value=float(current_value) if current_value else 0.0,
                    key=f"slot_{axis_type}_{i}",
                    format="%.2f"
                )
                slot_values.append(new_value)
        
        # Ferramentas automáticas
        st.markdown("**Ferramentas Automáticas:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f":material/linear_scale: Distribuição Linear", key=f"linear_{axis_type}"):
                self._apply_linear_distribution(axis_type, slot_values)
        
        with col2:
            if st.button(f":material/functions: Distribuição Logarítmica", key=f"log_{axis_type}"):
                self._apply_log_distribution(axis_type, slot_values)
        
        with col3:
            if st.button(f":material/save: Salvar Eixo {axis_type}", key=f"save_{axis_type}"):
                self._save_axis_data(axis_type, slot_values, new_active_slots)
    
    def _load_map_data(self) -> Optional[Dict]:
        """Carrega dados do mapa."""
        db_session = self.db.get_session()
        try:
            fuel_map = db_session.query(FuelMap).filter(FuelMap.id == self.map_id).first()
            if not fuel_map:
                return None
            
            return {
                'dimensions': fuel_map.dimensions,
                'x_axis_type': fuel_map.x_axis_type,
                'y_axis_type': fuel_map.y_axis_type,
                'x_slots_active': fuel_map.x_slots_active,
                'y_slots_active': fuel_map.y_slots_active
            }
        finally:
            db_session.close()
    
    def _load_axis_data(self, axis_type: str) -> Optional[Dict]:
        """Carrega dados de um eixo."""
        db_session = self.db.get_session()
        try:
            axis_data = db_session.query(MapAxisData).filter(
                MapAxisData.map_id == self.map_id,
                MapAxisData.axis_type == axis_type
            ).first()
            
            if not axis_data:
                return None
            
            return {f'slot_{i}': getattr(axis_data, f'slot_{i}') for i in range(32)}
            
        finally:
            db_session.close()
    
    def _save_axis_data(self, axis_type: str, slot_values: List[float], active_slots: int):
        """Salva dados do eixo."""
        db_session = self.db.get_session()
        try:
            # Atualizar dados do eixo
            axis_data = db_session.query(MapAxisData).filter(
                MapAxisData.map_id == self.map_id,
                MapAxisData.axis_type == axis_type
            ).first()
            
            if axis_data:
                for i, value in enumerate(slot_values):
                    setattr(axis_data, f'slot_{i}', value)
                
                # Limpar slots não utilizados
                for i in range(len(slot_values), 32):
                    setattr(axis_data, f'slot_{i}', None)
                
                axis_data.active_slots = active_slots
                
                # Atualizar mapa principal
                fuel_map = db_session.query(FuelMap).filter(FuelMap.id == self.map_id).first()
                if fuel_map:
                    if axis_type == 'X':
                        fuel_map.x_slots_active = active_slots
                    else:
                        fuel_map.y_slots_active = active_slots
                
                db_session.commit()
                st.success(f"Eixo {axis_type} salvo com sucesso!")
                st.rerun()
            
        except Exception as e:
            db_session.rollback()
            st.error(f"Erro ao salvar eixo: {str(e)}")
        finally:
            db_session.close()
```

### 3. Criar Utilitários de Interpolação

#### 3.1 Arquivo: src/utils/map_interpolation.py
```python
"""
Utilitários para interpolação de mapas de injeção.
Implementa as regras específicas da documentação.
"""

import numpy as np
from typing import List, Tuple, Optional
from scipy.interpolate import interp1d, griddata

class MapInterpolator:
    """Classe para interpolação de dados de mapas."""
    
    def linear_interpolation_2d(self, x_values: List[float], y_values: List[float], 
                               target_x: float) -> float:
        """
        Interpolação linear 2D seguindo regras da especificação.
        
        Regras:
        - Entre pontos existentes: Interpolação linear
        - Antes do primeiro ponto: Repete primeiro valor
        - Após o último ponto: Repete último valor
        """
        if not x_values or not y_values or len(x_values) != len(y_values):
            raise ValueError("Listas de valores inválidas")
        
        # Filtrar valores válidos
        valid_points = [(x, y) for x, y in zip(x_values, y_values) 
                       if x is not None and y is not None]
        
        if not valid_points:
            return 0.0
        
        # Ordenar por X
        valid_points.sort(key=lambda p: p[0])
        x_clean, y_clean = zip(*valid_points)
        
        # Antes do primeiro ponto
        if target_x <= x_clean[0]:
            return y_clean[0]
        
        # Após o último ponto
        if target_x >= x_clean[-1]:
            return y_clean[-1]
        
        # Interpolação linear
        return np.interp(target_x, x_clean, y_clean)
    
    def interpolate_missing_points(self, x_values: List[float], y_values: List[float]) -> Tuple[List[float], List[float]]:
        """
        Interpola pontos faltantes em uma série 2D.
        """
        valid_indices = [i for i, (x, y) in enumerate(zip(x_values, y_values)) 
                        if x is not None and y is not None]
        
        if len(valid_indices) < 2:
            return x_values, y_values
        
        # Valores válidos
        x_valid = [x_values[i] for i in valid_indices]
        y_valid = [y_values[i] for i in valid_indices]
        
        # Criar interpolador
        interpolator = interp1d(x_valid, y_valid, kind='linear', 
                               bounds_error=False, fill_value='extrapolate')
        
        # Preencher pontos faltantes
        x_result = x_values.copy()
        y_result = y_values.copy()
        
        for i in range(len(x_values)):
            if x_values[i] is not None and y_values[i] is None:
                y_result[i] = float(interpolator(x_values[i]))
        
        return x_result, y_result
    
    def smooth_2d_data(self, y_values: List[float], window_size: int = 3) -> List[float]:
        """
        Aplica suavização em dados 2D usando média móvel.
        """
        if window_size < 3 or window_size % 2 == 0:
            window_size = 3
        
        # Filtrar valores válidos
        valid_values = [y for y in y_values if y is not None]
        
        if len(valid_values) < window_size:
            return y_values
        
        # Aplicar média móvel
        smoothed = []
        half_window = window_size // 2
        
        for i in range(len(y_values)):
            if y_values[i] is None:
                smoothed.append(None)
                continue
            
            # Definir janela
            start_idx = max(0, i - half_window)
            end_idx = min(len(y_values), i + half_window + 1)
            
            # Calcular média dos valores válidos na janela
            window_values = [y_values[j] for j in range(start_idx, end_idx) 
                           if y_values[j] is not None]
            
            if window_values:
                smoothed.append(sum(window_values) / len(window_values))
            else:
                smoothed.append(y_values[i])
        
        return smoothed
    
    def interpolate_3d_matrix(self, matrix: np.ndarray, method: str = 'linear') -> np.ndarray:
        """
        Interpola valores faltantes em matriz 3D.
        
        Args:
            matrix: Matriz numpy com dados (NaN para valores faltantes)
            method: Método de interpolação ('linear', 'cubic', 'nearest')
        
        Returns:
            Matriz interpolada
        """
        # Encontrar posições com dados válidos
        valid_mask = ~np.isnan(matrix)
        
        if not np.any(valid_mask):
            return matrix
        
        # Coordenadas de todos os pontos
        x_coords, y_coords = np.meshgrid(np.arange(matrix.shape[1]), 
                                        np.arange(matrix.shape[0]))
        
        # Pontos com dados válidos
        valid_points = np.column_stack((
            x_coords[valid_mask].ravel(),
            y_coords[valid_mask].ravel()
        ))
        valid_values = matrix[valid_mask]
        
        # Pontos a interpolar
        all_points = np.column_stack((x_coords.ravel(), y_coords.ravel()))
        
        # Interpolação
        try:
            interpolated_values = griddata(
                valid_points, valid_values, all_points,
                method=method, fill_value=np.nan
            )
            
            # Reshape para matriz original
            result = interpolated_values.reshape(matrix.shape)
            
            # Preservar valores originais válidos
            result[valid_mask] = matrix[valid_mask]
            
            return result
            
        except Exception:
            # Fallback para método nearest se linear falhar
            if method != 'nearest':
                return self.interpolate_3d_matrix(matrix, 'nearest')
            else:
                return matrix
    
    def convert_2d_maps_to_3d(self, map_2d_data: np.ndarray, rpm_2d_data: np.ndarray,
                             map_axis: np.ndarray, rpm_axis: np.ndarray) -> np.ndarray:
        """
        Converte mapas 2D (MAP e RPM) em mapa 3D combinado.
        
        Args:
            map_2d_data: Valores do mapa MAP 2D
            rpm_2d_data: Valores do mapa RPM 2D  
            map_axis: Eixo de pressão MAP
            rpm_axis: Eixo de RPM
        
        Returns:
            Matriz 3D combinada
        """
        # Criar malha 3D
        map_grid, rpm_grid = np.meshgrid(map_axis, rpm_axis, indexing='ij')
        
        # Interpoladores para cada mapa 2D
        map_interpolator = interp1d(map_axis, map_2d_data, kind='linear',
                                   bounds_error=False, fill_value='extrapolate')
        rpm_interpolator = interp1d(rpm_axis, rpm_2d_data, kind='linear', 
                                   bounds_error=False, fill_value='extrapolate')
        
        # Calcular valores base de cada mapa
        map_base_values = map_interpolator(map_grid)
        rpm_base_values = rpm_interpolator(rpm_grid)
        
        # Combinar usando média ponderada ou fórmula específica
        # Aqui implementamos uma estratégia de combinação baseada na carga
        result = np.zeros_like(map_grid)
        
        for i in range(len(map_axis)):
            for j in range(len(rpm_axis)):
                # Peso baseado na pressão MAP (maior peso em alta carga)
                map_weight = (map_axis[i] + 1.0) / 3.0  # Normalizado 0-1
                map_weight = np.clip(map_weight, 0.1, 0.9)
                rpm_weight = 1.0 - map_weight
                
                # Combinação ponderada
                result[i, j] = (map_base_values[i, j] * map_weight + 
                               rpm_base_values[j] * rpm_weight)
        
        return result
    
    def calculate_interpolation_preview(self, x_values: List[float], y_values: List[float],
                                      resolution: int = 100) -> Tuple[List[float], List[float]]:
        """
        Calcula preview da interpolação para visualização.
        
        Args:
            x_values: Valores do eixo X
            y_values: Valores correspondentes
            resolution: Número de pontos para o preview
        
        Returns:
            Tupla com (x_interpolated, y_interpolated)
        """
        # Filtrar valores válidos
        valid_points = [(x, y) for x, y in zip(x_values, y_values) 
                       if x is not None and y is not None]
        
        if len(valid_points) < 2:
            return [], []
        
        # Ordenar e extrair
        valid_points.sort(key=lambda p: p[0])
        x_clean, y_clean = zip(*valid_points)
        
        # Criar eixo interpolado
        x_min, x_max = min(x_clean), max(x_clean)
        x_interp = np.linspace(x_min, x_max, resolution)
        
        # Interpolação
        y_interp = [self.linear_interpolation_2d(list(x_clean), list(y_clean), x) 
                   for x in x_interp]
        
        return list(x_interp), y_interp
```

### 4. Sistema de Importação/Exportação

#### 4.1 Arquivo: src/services/map_import_export.py
```python
"""
Serviço para importação e exportação de mapas.
Suporte aos formatos FTManager (.ftm), CSV e JSON.
"""

import json
import csv
import io
import zipfile
from typing import Dict, List, Optional, Any, BinaryIO
import pandas as pd
import numpy as np
from datetime import datetime

from ..data.fuel_maps_models import FuelMap, MapData2D, MapData3D, MapAxisData
from ..data.models import Vehicle, get_database

class MapImportExportService:
    """Serviço para importação e exportação de mapas."""
    
    def __init__(self):
        self.db = get_database()
    
    def export_maps_to_ftm(self, vehicle_id: str, map_ids: List[str]) -> bytes:
        """
        Exporta mapas para formato FTManager (.ftm).
        
        Args:
            vehicle_id: ID do veículo
            map_ids: Lista de IDs dos mapas a exportar
        
        Returns:
            Bytes do arquivo .ftm
        """
        # Carregar dados dos mapas
        maps_data = self._load_maps_data(map_ids)
        vehicle_data = self._load_vehicle_data(vehicle_id)
        
        # Estrutura do arquivo FTM
        ftm_data = {
            "header": {
                "version": "2.0",
                "created": datetime.now().isoformat(),
                "vehicle": {
                    "name": vehicle_data.name if vehicle_data else "Unknown",
                    "id": vehicle_id
                },
                "maps_count": len(maps_data)
            },
            "vehicle_config": self._export_vehicle_config(vehicle_data),
            "maps": {}
        }
        
        # Adicionar cada mapa
        for map_data in maps_data:
            ftm_map = self._convert_map_to_ftm_format(map_data)
            ftm_data["maps"][map_data["map_type"]] = ftm_map
        
        # Converter para bytes (JSON compactado)
        json_string = json.dumps(ftm_data, indent=2)
        return json_string.encode('utf-8')
    
    def export_maps_to_csv(self, map_ids: List[str]) -> bytes:
        """
        Exporta mapas para formato CSV (ZIP com múltiplos CSVs).
        
        Args:
            map_ids: Lista de IDs dos mapas
        
        Returns:
            Bytes do arquivo ZIP com CSVs
        """
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for map_id in map_ids:
                # Carregar dados do mapa
                map_data = self._load_single_map_data(map_id)
                if not map_data:
                    continue
                
                # Exportar como CSV
                if map_data["dimensions"] == 1:  # 2D
                    csv_content = self._export_2d_map_to_csv(map_data)
                    filename = f"{map_data['name']}_2D.csv"
                else:  # 3D
                    csv_content = self._export_3d_map_to_csv(map_data)
                    filename = f"{map_data['name']}_3D.csv"
                
                # Adicionar ao ZIP
                zip_file.writestr(filename, csv_content)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def export_maps_to_json(self, vehicle_id: str, map_ids: List[str]) -> bytes:
        """
        Exporta mapas para formato JSON estruturado.
        
        Args:
            vehicle_id: ID do veículo
            map_ids: Lista de IDs dos mapas
        
        Returns:
            Bytes do arquivo JSON
        """
        # Carregar todos os dados
        maps_data = self._load_maps_data(map_ids)
        vehicle_data = self._load_vehicle_data(vehicle_id)
        
        # Estrutura JSON
        export_data = {
            "export_info": {
                "format": "FuelTune JSON",
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "maps_count": len(maps_data)
            },
            "vehicle": self._export_vehicle_config(vehicle_data),
            "maps": []
        }
        
        # Adicionar mapas detalhados
        for map_data in maps_data:
            json_map = self._convert_map_to_json_format(map_data)
            export_data["maps"].append(json_map)
        
        # Converter para bytes
        json_string = json.dumps(export_data, indent=2)
        return json_string.encode('utf-8')
    
    def import_maps_from_ftm(self, file_content: bytes, vehicle_id: str) -> Dict[str, Any]:
        """
        Importa mapas de arquivo FTManager (.ftm).
        
        Args:
            file_content: Conteúdo do arquivo .ftm
            vehicle_id: ID do veículo de destino
        
        Returns:
            Resultado da importação
        """
        try:
            # Decodificar arquivo
            json_string = file_content.decode('utf-8')
            ftm_data = json.loads(json_string)
            
            # Validar estrutura
            if not self._validate_ftm_structure(ftm_data):
                return {"success": False, "error": "Estrutura de arquivo FTM inválida"}
            
            # Importar mapas
            imported_maps = []
            errors = []
            
            for map_type, map_data in ftm_data.get("maps", {}).items():
                try:
                    map_id = self._import_single_ftm_map(map_data, vehicle_id, map_type)
                    imported_maps.append({"map_type": map_type, "map_id": map_id})
                except Exception as e:
                    errors.append(f"Erro ao importar {map_type}: {str(e)}")
            
            return {
                "success": len(imported_maps) > 0,
                "imported_maps": imported_maps,
                "errors": errors,
                "total_maps": len(ftm_data.get("maps", {}))
            }
            
        except Exception as e:
            return {"success": False, "error": f"Erro na importação: {str(e)}"}
    
    def import_maps_from_csv(self, file_content: bytes, vehicle_id: str, 
                           map_type: str, bank_id: str) -> Dict[str, Any]:
        """
        Importa mapa de arquivo CSV.
        
        Args:
            file_content: Conteúdo do arquivo CSV
            vehicle_id: ID do veículo de destino
            map_type: Tipo do mapa
            bank_id: ID da bancada
        
        Returns:
            Resultado da importação
        """
        try:
            # Decodificar CSV
            csv_string = file_content.decode('utf-8')
            
            # Detectar formato (2D ou 3D)
            if self._is_3d_csv(csv_string):
                return self._import_3d_csv(csv_string, vehicle_id, map_type, bank_id)
            else:
                return self._import_2d_csv(csv_string, vehicle_id, map_type, bank_id)
                
        except Exception as e:
            return {"success": False, "error": f"Erro na importação CSV: {str(e)}"}
    
    def preview_import_data(self, file_content: bytes, file_format: str) -> Dict[str, Any]:
        """
        Gera preview dos dados de importação.
        
        Args:
            file_content: Conteúdo do arquivo
            file_format: Formato do arquivo (ftm, csv, json)
        
        Returns:
            Preview dos dados
        """
        try:
            if file_format == "ftm":
                return self._preview_ftm_data(file_content)
            elif file_format == "csv":
                return self._preview_csv_data(file_content)
            elif file_format == "json":
                return self._preview_json_data(file_content)
            else:
                return {"error": "Formato não suportado"}
                
        except Exception as e:
            return {"error": f"Erro no preview: {str(e)}"}
    
    # Métodos auxiliares privados
    def _load_maps_data(self, map_ids: List[str]) -> List[Dict]:
        """Carrega dados completos dos mapas."""
        db_session = self.db.get_session()
        try:
            maps_data = []
            
            for map_id in map_ids:
                fuel_map = db_session.query(FuelMap).filter(FuelMap.id == map_id).first()
                if not fuel_map:
                    continue
                
                # Carregar dados dos eixos
                axis_data = self._load_map_axis_data(db_session, map_id)
                
                # Carregar dados dos valores
                if fuel_map.dimensions == 1:
                    values_data = self._load_2d_values_data(db_session, map_id)
                else:
                    values_data = self._load_3d_values_data(db_session, map_id)
                
                maps_data.append({
                    "id": fuel_map.id,
                    "name": fuel_map.name,
                    "map_type": fuel_map.map_type,
                    "bank_id": fuel_map.bank_id,
                    "dimensions": fuel_map.dimensions,
                    "x_axis_type": fuel_map.x_axis_type,
                    "y_axis_type": fuel_map.y_axis_type,
                    "data_unit": fuel_map.data_unit,
                    "x_slots_active": fuel_map.x_slots_active,
                    "y_slots_active": fuel_map.y_slots_active,
                    "version": fuel_map.version,
                    "axis_data": axis_data,
                    "values_data": values_data
                })
            
            return maps_data
            
        finally:
            db_session.close()
    
    def _export_vehicle_config(self, vehicle: Vehicle) -> Dict:
        """Exporta configuração do veículo."""
        if not vehicle:
            return {}
        
        return {
            "name": vehicle.name,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "year": vehicle.year,
            "engine": {
                "displacement": vehicle.engine_displacement,
                "cylinders": vehicle.engine_cylinders,
                "configuration": vehicle.engine_configuration,
                "aspiration": vehicle.engine_aspiration
            },
            "banks": {
                "a": {
                    "enabled": vehicle.bank_a_enabled,
                    "mode": vehicle.bank_a_mode,
                    "outputs": json.loads(vehicle.bank_a_outputs or "[]"),
                    "injector_flow": vehicle.bank_a_injector_flow,
                    "injector_count": vehicle.bank_a_injector_count,
                    "dead_time": vehicle.bank_a_dead_time
                },
                "b": {
                    "enabled": vehicle.bank_b_enabled,
                    "mode": vehicle.bank_b_mode,
                    "outputs": json.loads(vehicle.bank_b_outputs or "[]"),
                    "injector_flow": vehicle.bank_b_injector_flow,
                    "injector_count": vehicle.bank_b_injector_count,
                    "dead_time": vehicle.bank_b_dead_time
                } if vehicle.bank_b_enabled else None
            }
        }
    
    def _convert_map_to_ftm_format(self, map_data: Dict) -> Dict:
        """Converte mapa para formato FTM."""
        return {
            "name": map_data["name"],
            "type": map_data["map_type"],
            "bank": map_data["bank_id"],
            "dimensions": map_data["dimensions"],
            "axis": {
                "x": {
                    "type": map_data["x_axis_type"],
                    "active_slots": map_data["x_slots_active"],
                    "values": [map_data["axis_data"]["x"].get(f"slot_{i}") 
                              for i in range(map_data["x_slots_active"])]
                },
                "y": {
                    "type": map_data["y_axis_type"],
                    "active_slots": map_data["y_slots_active"],
                    "values": [map_data["axis_data"]["y"].get(f"slot_{i}") 
                              for i in range(map_data["y_slots_active"])]
                } if map_data["dimensions"] == 2 else None
            },
            "data": {
                "unit": map_data["data_unit"],
                "values": self._format_values_for_ftm(map_data)
            },
            "version": map_data["version"]
        }
    
    def _format_values_for_ftm(self, map_data: Dict) -> List:
        """Formata valores para estrutura FTM."""
        if map_data["dimensions"] == 1:  # 2D
            return [map_data["values_data"].get(f"value_{i}") 
                   for i in range(map_data["x_slots_active"])]
        else:  # 3D
            matrix = []
            for x in range(map_data["x_slots_active"]):
                row = []
                for y in range(map_data["y_slots_active"]):
                    value = map_data["values_data"].get(f"value_{x}_{y}")
                    row.append(value)
                matrix.append(row)
            return matrix
    
    # Mais métodos auxiliares...
    def _validate_ftm_structure(self, ftm_data: Dict) -> bool:
        """Valida estrutura do arquivo FTM."""
        required_keys = ["header", "maps"]
        return all(key in ftm_data for key in required_keys)
    
    def _is_3d_csv(self, csv_content: str) -> bool:
        """Detecta se CSV é formato 3D."""
        lines = csv_content.strip().split('\n')
        if len(lines) < 2:
            return False
        
        # CSV 3D tem múltiplas colunas de dados
        first_data_line = lines[1].split(',')
        return len(first_data_line) > 3  # Mais de 3 colunas indica 3D
```

## Saída Esperada

### 1. Página Principal de Mapas
- Interface completa com 5 tabs organizadas
- Seleção de veículo e bancada integrada
- Lista visual de mapas em cards
- Navegação intuitiva entre editores

### 2. Editores Especializados
- **Editor 2D**: Gráfico interativo + tabela editável
- **Editor 3D**: Superfície 3D + heatmap + editor célular
- **Editor de Eixos**: Configuração de slots e distribuições

### 3. Visualizações Profissionais
- Gráficos Plotly responsivos e interativos
- Mapas de calor com escalas de cores adaptativas
- Superfícies 3D navegáveis
- Preview de interpolações em tempo real

### 4. Sistema de Import/Export
- Suporte completo ao formato FTManager (.ftm)
- Exportação/importação CSV e JSON
- Preview de dados antes da importação
- Validações e tratamento de erros

### 5. Funcionalidades Avançadas
- Interpolação automática de lacunas
- Suavização de dados
- Sincronização entre bancadas
- Versionamento com histórico

## Validações Finais

### Checklist A04-STREAMLIT-PROFESSIONAL:
- [ ] ZERO emojis em toda interface
- [ ] Material Icons em TODOS os headers e botões
- [ ] Interface 100% em português
- [ ] CSS adaptativo sem !important
- [ ] Sem decorações infantis
- [ ] Ícones consistentes em todos os componentes

### Checklist Funcional:
- [ ] Edição completa de mapas 2D funcionando
- [ ] Edição completa de mapas 3D funcionando
- [ ] Configuração de eixos operacional
- [ ] Sistema de import/export funcional
- [ ] Visualizações responsivas e profissionais
- [ ] Interpolação automática implementada
- [ ] Validações de dados integradas
- [ ] Navegação fluida entre funcionalidades

### Checklist Técnico:
- [ ] Performance otimizada para grandes datasets
- [ ] Tratamento adequado de erros
- [ ] Validações de entrada robustas
- [ ] Compatibilidade com formato FTManager
- [ ] Backup automático antes de alterações

Este agente implementa a interface completa e profissional para edição de mapas, proporcionando uma experiência de usuário similar ou superior ao FTManager original.