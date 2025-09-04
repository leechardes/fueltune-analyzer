"""
Map Editor - Professional UI Component for FuelTech Tuning Maps

This module provides the main map editing interface with AG-Grid integration,
professional Material Design styling, and adaptive CSS theming.

CRITICAL: This module follows PYTHON-CODE-STANDARDS.md requirements:
- ZERO emojis in interface (Material Icons only)
- CSS adaptive theming (light/dark support)
- Type hints 100% coverage
- Performance < 100ms for typical operations
- Professional UI standards enforced
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime
import logging

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
from st_aggrid.shared import GridUpdateMode, DataReturnMode

from .operations import MapOperations
from .algorithms import MapAlgorithms  
from .visualization import MapVisualization
from .snapshots import MapSnapshots

logger = logging.getLogger(__name__)

@dataclass
class MapMetadata:
    """Type-safe map metadata container."""
    
    name: str
    map_type: str  # 'fuel', 'ignition', 'boost'
    dimensions: Tuple[int, int]  # (rows, cols)
    rpm_range: Tuple[int, int]
    load_range: Tuple[float, float] 
    created_at: datetime
    modified_at: datetime
    version: int = 1
    description: Optional[str] = None
    vehicle_id: Optional[int] = None

class MapEditor:
    """
    Professional map editor component with Material Design interface.
    
    Features:
    - AG-Grid based table editing
    - Material Icons for actions  
    - Adaptive CSS theming
    - Performance optimized operations
    - Professional error handling
    """
    
    def __init__(self):
        """Initialize map editor with professional styling."""
        self.operations = MapOperations()
        self.algorithms = MapAlgorithms()
        self.visualization = MapVisualization() 
        self.snapshots = MapSnapshots()
        
        # Initialize session state
        self._initialize_session_state()
        
        # Load professional CSS
        self._load_professional_css()
    
    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state for map editor."""
        
        if 'current_map' not in st.session_state:
            st.session_state.current_map = None
        
        if 'map_history' not in st.session_state:
            st.session_state.map_history = []
        
        if 'selected_cells' not in st.session_state:
            st.session_state.selected_cells = []
        
        if 'map_metadata' not in st.session_state:
            st.session_state.map_metadata = None
    
    def _load_professional_css(self) -> None:
        """Load adaptive CSS theming for professional interface."""
        
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">
        <style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            vertical-align: middle;
            margin-right: 8px;
        }
        
        /* Map Editor Professional Styling */
        .map-editor-container {
            background: var(--background-color);
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid var(--secondary-background-color);
        }
        
        .map-toolbar {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            padding: 0.5rem;
            background: var(--secondary-background-color);
            border-radius: 4px;
            flex-wrap: wrap;
        }
        
        .map-status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem;
            background: var(--secondary-background-color);
            border-radius: 4px;
            margin-top: 1rem;
            font-size: 0.875rem;
            color: var(--text-color);
        }
        
        .map-info {
            display: flex;
            gap: 1rem;
            color: var(--text-color);
        }
        
        .map-stats {
            font-family: 'Courier New', monospace;
            color: var(--text-color);
        }
        
        /* AG-Grid Professional Styling */
        .ag-theme-streamlit {
            --ag-background-color: var(--background-color);
            --ag-foreground-color: var(--text-color);
            --ag-border-color: var(--secondary-background-color);
            --ag-header-background-color: var(--secondary-background-color);
            --ag-header-foreground-color: var(--text-color);
            --ag-selected-row-background-color: var(--primary-color-light);
        }
        
        /* Remove any hardcoded colors - use CSS variables only */
        .stButton > button {
            background-color: var(--primary-color);
            color: var(--background-color);
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        
        .stButton > button:hover {
            background-color: var(--primary-color-dark);
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render(self) -> None:
        """
        Render the complete map editor interface.
        
        Returns:
            None
        """
        
        st.markdown('<div class="map-editor-container">', unsafe_allow_html=True)
        
        # Render header with Material Icons
        self._render_header()
        
        # Render toolbar
        self._render_toolbar()
        
        # Main editing area
        col1, col2 = st.columns([3, 1])
        
        with col1:
            self._render_map_grid()
        
        with col2:
            self._render_map_info_panel()
        
        # Status bar
        self._render_status_bar()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_header(self) -> None:
        """Render professional header with Material Icons."""
        
        st.markdown("""
        <h2>
            <span class="material-symbols-outlined">grid_on</span>
            Map Editor
        </h2>
        """, unsafe_allow_html=True)
    
    def _render_toolbar(self) -> None:
        """Render professional toolbar with Material Design buttons."""
        
        st.markdown('<div class="map-toolbar">', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        
        with col1:
            if st.button("Save", key="save_map"):
                self._save_current_map()
        
        with col2:
            if st.button("Undo", key="undo_map"):
                self._undo_operation()
        
        with col3:
            if st.button("Redo", key="redo_map"):
                self._redo_operation()
        
        with col4:
            if st.button("Smooth", key="smooth_map"):
                self._apply_smoothing()
        
        with col5:
            if st.button("Interpolate", key="interpolate_map"):
                self._apply_interpolation()
        
        with col6:
            if st.button("3D View", key="view_3d"):
                self._show_3d_visualization()
        
        with col7:
            if st.button("Export", key="export_map"):
                self._export_to_ftmanager()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_map_grid(self) -> None:
        """
        Render the main map editing grid using AG-Grid.
        
        Performance target: < 100ms for typical operations
        """
        
        if st.session_state.current_map is None:
            self._show_map_creation_dialog()
            return
        
        try:
            # Configure AG-Grid with professional settings
            gb = GridOptionsBuilder.from_dataframe(st.session_state.current_map)
            gb.configure_default_column(
                editable=True,
                sortable=False,
                filter=False,
                resizable=True,
                minWidth=60,
                maxWidth=120
            )
            
            # Enable cell editing with validation
            gb.configure_grid_options(
                enableRangeSelection=True,
                enableCellTextSelection=True,
                suppressRowClickSelection=True,
                rowSelection='multiple',
                animateRows=True
            )
            
            grid_options = gb.build()
            
            # Render AG-Grid with professional theme
            grid_response = AgGrid(
                st.session_state.current_map,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                theme='streamlit',  # Professional theme
                height=400,
                width='100%',
                allow_unsafe_jscode=True
            )
            
            # Handle grid updates
            if grid_response['data'] is not None:
                self._handle_grid_update(grid_response['data'])
                
        except Exception as e:
            logger.error(f"Grid rendering error: {e}")
            st.error("Map grid rendering failed. Please check console logs.")
    
    def _render_map_info_panel(self) -> None:
        """Render map information and statistics panel."""
        
        st.markdown("### Map Information")
        
        if st.session_state.map_metadata:
            metadata = st.session_state.map_metadata
            
            st.markdown(f"""
            **Name:** {metadata.name}  
            **Type:** {metadata.map_type.title()}  
            **Dimensions:** {metadata.dimensions[0]} × {metadata.dimensions[1]}  
            **RPM Range:** {metadata.rpm_range[0]} - {metadata.rpm_range[1]}  
            **Load Range:** {metadata.load_range[0]:.2f} - {metadata.load_range[1]:.2f}  
            **Version:** {metadata.version}
            """)
        
        # Map statistics
        if st.session_state.current_map is not None:
            self._render_map_statistics()
        
        # Quick operations
        st.markdown("### Quick Operations")
        
        increment_value = st.number_input(
            "Increment/Decrement Value", 
            value=0.1, 
            step=0.1,
            format="%.2f"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("+ Inc", key="increment"):
                self._increment_selected_cells(increment_value)
        
        with col2:
            if st.button("- Dec", key="decrement"):
                self._increment_selected_cells(-increment_value)
    
    def _render_map_statistics(self) -> None:
        """Render real-time map statistics."""
        
        if st.session_state.current_map is None:
            return
        
        try:
            df = st.session_state.current_map
            
            # Calculate statistics
            mean_val = df.select_dtypes(include=[np.number]).mean().mean()
            min_val = df.select_dtypes(include=[np.number]).min().min()
            max_val = df.select_dtypes(include=[np.number]).max().max()
            std_val = df.select_dtypes(include=[np.number]).std().mean()
            
            st.markdown("### Statistics")
            st.markdown(f"""
            **Mean:** {mean_val:.3f}  
            **Min:** {min_val:.3f}  
            **Max:** {max_val:.3f}  
            **Std Dev:** {std_val:.3f}
            """)
            
        except Exception as e:
            logger.error(f"Statistics calculation error: {e}")
            st.error("Statistics calculation failed")
    
    def _render_status_bar(self) -> None:
        """Render professional status bar."""
        
        st.markdown('<div class="map-status-bar">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.session_state.current_map is not None:
                cells_modified = len(st.session_state.selected_cells)
                st.markdown(f'<span class="map-info">Modified cells: {cells_modified}</span>', 
                          unsafe_allow_html=True)
        
        with col2:
            if st.session_state.map_metadata:
                last_modified = st.session_state.map_metadata.modified_at.strftime("%H:%M:%S")
                st.markdown(f'<span class="map-info">Last modified: {last_modified}</span>', 
                          unsafe_allow_html=True)
        
        with col3:
            st.markdown('<span class="map-stats">Ready</span>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _show_map_creation_dialog(self) -> None:
        """Show dialog for creating new map."""
        
        st.markdown("### Create New Map")
        
        col1, col2 = st.columns(2)
        
        with col1:
            map_name = st.text_input("Map Name", value="New Map")
            map_type = st.selectbox("Map Type", ["fuel", "ignition", "boost"])
            rows = st.number_input("Rows", min_value=8, max_value=32, value=16)
        
        with col2:
            cols = st.number_input("Columns", min_value=8, max_value=32, value=16)
            rpm_min = st.number_input("Min RPM", min_value=500, value=1000)
            rpm_max = st.number_input("Max RPM", min_value=2000, value=8000)
        
        if st.button("Create Map", key="create_new_map"):
            self._create_new_map(map_name, map_type, (rows, cols), (rpm_min, rpm_max))
    
    def _create_new_map(
        self, 
        name: str, 
        map_type: str, 
        dimensions: Tuple[int, int],
        rpm_range: Tuple[int, int]
    ) -> None:
        """
        Create new map with specified parameters.
        
        Args:
            name: Map display name
            map_type: Type of map ('fuel', 'ignition', 'boost')
            dimensions: (rows, cols) dimensions
            rpm_range: (min_rpm, max_rpm) range
        """
        
        try:
            rows, cols = dimensions
            
            # Create default map data based on type
            if map_type == 'fuel':
                default_value = 12.5  # Default AFR
                load_range = (0.0, 2.0)  # MAP pressure
            elif map_type == 'ignition':
                default_value = 25.0  # Default timing
                load_range = (0.0, 2.0)  # MAP pressure
            else:  # boost
                default_value = 0.5  # Default boost
                load_range = (0.0, 2.0)  # Target pressure
            
            # Create DataFrame with RPM/Load labels
            rpm_values = np.linspace(rpm_range[0], rpm_range[1], cols)
            load_values = np.linspace(load_range[0], load_range[1], rows)
            
            # Initialize with default values
            map_data = np.full((rows, cols), default_value)
            
            # Create DataFrame with proper column names
            column_names = [f"RPM_{int(rpm)}" for rpm in rpm_values]
            index_names = [f"Load_{load:.2f}" for load in load_values]
            
            df = pd.DataFrame(map_data, columns=column_names, index=index_names)
            
            # Store in session state
            st.session_state.current_map = df
            
            # Create metadata
            st.session_state.map_metadata = MapMetadata(
                name=name,
                map_type=map_type,
                dimensions=dimensions,
                rpm_range=rpm_range,
                load_range=load_range,
                created_at=datetime.now(),
                modified_at=datetime.now()
            )
            
            st.success(f"Map '{name}' created successfully!")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Map creation error: {e}")
            st.error(f"Failed to create map: {str(e)}")
    
    def _handle_grid_update(self, updated_data: pd.DataFrame) -> None:
        """
        Handle AG-Grid data updates with validation.
        
        Args:
            updated_data: Updated DataFrame from AG-Grid
        """
        
        try:
            # Validate numeric data
            numeric_columns = updated_data.select_dtypes(include=[np.number]).columns
            
            for col in numeric_columns:
                # Check for reasonable ranges based on map type
                if st.session_state.map_metadata:
                    map_type = st.session_state.map_metadata.map_type
                    
                    if map_type == 'fuel':
                        # AFR should be reasonable (8-20)
                        updated_data[col] = updated_data[col].clip(8.0, 20.0)
                    elif map_type == 'ignition':
                        # Timing should be reasonable (-10 to 50 degrees)
                        updated_data[col] = updated_data[col].clip(-10.0, 50.0)
                    elif map_type == 'boost':
                        # Boost should be reasonable (0-3.0)
                        updated_data[col] = updated_data[col].clip(0.0, 3.0)
            
            # Update session state
            st.session_state.current_map = updated_data
            
            # Update metadata
            if st.session_state.map_metadata:
                st.session_state.map_metadata.modified_at = datetime.now()
                st.session_state.map_metadata.version += 1
            
        except Exception as e:
            logger.error(f"Grid update error: {e}")
            st.error("Failed to update map data")
    
    def _save_current_map(self) -> None:
        """Save current map to snapshots."""
        try:
            if st.session_state.current_map is not None:
                self.snapshots.save_snapshot(
                    st.session_state.current_map,
                    st.session_state.map_metadata
                )
                st.success("Map saved successfully!")
        except Exception as e:
            logger.error(f"Save error: {e}")
            st.error("Failed to save map")
    
    def _undo_operation(self) -> None:
        """Undo last operation."""
        # TODO: Implement undo functionality
        st.info("Undo functionality will be implemented")
    
    def _redo_operation(self) -> None:
        """Redo last undone operation."""
        # TODO: Implement redo functionality  
        st.info("Redo functionality will be implemented")
    
    def _apply_smoothing(self) -> None:
        """Apply smoothing algorithm to selected cells."""
        try:
            if st.session_state.current_map is not None:
                smoothed_map = self.algorithms.gaussian_smooth(
                    st.session_state.current_map,
                    sigma=1.0
                )
                st.session_state.current_map = smoothed_map
                st.success("Smoothing applied!")
                st.rerun()
        except Exception as e:
            logger.error(f"Smoothing error: {e}")
            st.error("Smoothing failed")
    
    def _apply_interpolation(self) -> None:
        """Apply interpolation to fill missing values."""
        # TODO: Implement interpolation
        st.info("Interpolation functionality will be implemented")
    
    def _show_3d_visualization(self) -> None:
        """Show 3D visualization of current map."""
        try:
            if st.session_state.current_map is not None:
                fig = self.visualization.create_3d_surface(
                    st.session_state.current_map,
                    st.session_state.map_metadata
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"3D visualization error: {e}")
            st.error("3D visualization failed")
    
    def _export_to_ftmanager(self) -> None:
        """Export current map for FTManager compatibility."""
        # TODO: Implement FTManager export
        st.info("FTManager export functionality will be implemented")
    
    def _increment_selected_cells(self, value: float) -> None:
        """Increment selected cells by specified value."""
        try:
            if st.session_state.current_map is not None:
                # For now, increment all numeric cells
                numeric_columns = st.session_state.current_map.select_dtypes(include=[np.number]).columns
                st.session_state.current_map[numeric_columns] += value
                st.success(f"Incremented by {value}")
                st.rerun()
        except Exception as e:
            logger.error(f"Increment error: {e}")
            st.error("Increment operation failed")