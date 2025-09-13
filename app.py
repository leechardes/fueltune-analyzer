"""
FuelTune Streamlit - Main Application with Modern Navigation
A comprehensive FuelTech data analysis platform built with Streamlit.

This application provides tools for analyzing automotive engine data
with support for 64 FuelTech fields and advanced visualization capabilities.
"""

import sys
from pathlib import Path

import streamlit as st

# Add src directory to path for imports
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import config
from src.data.cache import get_cache_manager
from src.data.database import get_database, get_vehicle_by_id

# Import integration system
from src.integration import (
    clipboard_manager,
    export_import_manager,
    initialize_integration_system,
    integration_manager,
    notification_system,
    plugin_system,
    shutdown_integration_system,
    task_manager,
    workflow_manager,
)
from src.ui.components.vehicle_selector import (
    get_vehicle_context,
    render_vehicle_selector,
    set_vehicle_context,
)
from src.ui.theme_config import apply_professional_theme, professional_theme
from src.utils.logger import get_logger

# Configure page
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="settings",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply professional theme
apply_professional_theme()

# Additional CSS fix for sidebar selectbox
st.markdown(
    """
<style>
    /* Force selectbox in sidebar to use theme colors */
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox label {
        color: var(--text-color) !important;
    }
    
    /* Fix dropdown menu background */
    div[data-baseweb="select"] > div {
        background-color: var(--background-color) !important;
    }
    
    div[data-baseweb="popover"] {
        background-color: var(--background-color) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize logger
logger = get_logger("fueltune_app")


# Initialize global components
@st.cache_resource
def get_database_connection():
    """Get database connection (cached)."""
    return get_database()


@st.cache_resource
def get_cache():
    """Get cache manager (cached)."""
    return get_cache_manager()


def initialize_integration():
    """Initialize the integration system."""
    if "integration_initialized" not in st.session_state:
        try:
            logger.info("Initializing integration system...")
            initialize_integration_system()
            st.session_state.integration_initialized = True
            logger.info("Integration system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize integration system: {e}")
            st.error(f"Integration system initialization failed: {e}")


def initialize_session_state():
    """Initialize session state variables."""
    # Global state for sessions
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    if "available_sessions" not in st.session_state:
        st.session_state.available_sessions = []
    if "uploaded_data" not in st.session_state:
        st.session_state.uploaded_data = None
    if "menu_page" not in st.session_state:
        st.session_state.menu_page = "Início"


def show_system_status():
    """Display system status indicators."""
    try:
        db = get_database_connection()
        cache = get_cache()

        # Get database status
        db_status = "connected" if db else "disconnected"
        cache_status = "active" if cache else "inactive"

        # Create status indicators
        status_html = f"""
        <div style="position: fixed; top: 10px; right: 10px; z-index: 999; 
                    background: var(--background-color, #ffffff); padding: 8px 12px; border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); font-size: 0.85rem; color: var(--text-color, #000000);">
            <div style="display: flex; gap: 15px; align-items: center;">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; 
                               background: {'#4CAF50' if db_status == 'connected' else '#F44336'};"></div>
                    <span style="color: #666;">Database</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; 
                               background: {'#4CAF50' if cache_status == 'active' else '#F44336'};"></div>
                    <span style="color: #666;">Cache</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <span style="color: #999; font-size: 0.8rem;">v{config.APP_VERSION}</span>
                </div>
            </div>
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error showing system status: {e}")


def main():
    """Main application function using st.navigation."""
    logger.info("Starting FuelTune Streamlit application with modern navigation")

    # Initialize session state
    initialize_session_state()

    # Initialize integration system
    initialize_integration()

    # Show system status
    show_system_status()

    # Create navigation with Material Design icons
    # Using the existing pages in src/ui/pages/
    pages = st.navigation(
        [
            st.Page("src/ui/pages/dashboard.py", title="Dashboard", icon=":material/dashboard:"),
            st.Page("src/ui/pages/vehicles.py", title="Veículos", icon=":material/directions_car:"),
            st.Page(
                "src/ui/pages/bank_configuration.py",
                title="Configuração de Bancadas",
                icon=":material/settings_input_component:",
            ),
            # st.Page("src/ui/pages/fuel_maps_2d.py", title="Mapas de Injeção 2D", icon=":material/tune:"),  # Backup - removido do menu
            st.Page(
                "src/ui/pages/fuel_maps.py", title="Mapas de Injeção", icon=":material/3d_rotation:"
            ),
            st.Page(
                "src/ui/pages/upload.py", title="Upload de Dados", icon=":material/upload_file:"
            ),
            st.Page("src/ui/pages/analysis.py", title="Análise", icon=":material/analytics:"),
            st.Page(
                "src/ui/pages/consumption.py", title="Consumo", icon=":material/local_gas_station:"
            ),
            st.Page("src/ui/pages/performance.py", title="Performance", icon=":material/speed:"),
            st.Page("src/ui/pages/imu.py", title="IMU", icon=":material/sensors:"),
            st.Page("src/ui/pages/versioning.py", title="Versionamento", icon=":material/history:"),
            st.Page("src/ui/pages/reports.py", title="Relatórios", icon=":material/description:"),
        ]
    )

    # Add custom CSS for navigation styling - Dark theme compatible
    st.markdown(
        """
    <style>
        /* Custom navigation styles - adaptive for dark/light theme */
        [data-testid="stSidebarNav"] {
            background-color: transparent;
            border-radius: 8px;
            padding: 0.5rem;
        }
        
        [data-testid="stSidebarNav"] a {
            border-radius: 6px;
            margin: 2px 0;
            transition: all 0.3s ease;
            color: inherit;
        }
        
        [data-testid="stSidebarNav"] a:hover {
            background-color: var(--primary-color-10, rgba(25, 118, 210, 0.15));
            transform: translateX(4px);
        }
        
        /* Style for active page */
        [data-testid="stSidebarNav"] a[aria-selected="true"] {
            background-color: var(--primary-color-20, rgba(25, 118, 210, 0.2));
            border-left: 3px solid var(--primary-color, #1976D2);
        }
        
        /* Fix text color in navigation */
        [data-testid="stSidebarNav"] span {
            color: inherit;
        }
        
        /* Material icons in navigation */
        [data-testid="stSidebarNav"] span[data-testid="stMarkdownContainer"] {
            display: flex;
            align-items: center;
            gap: 8px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Add sidebar header with branding
    with st.sidebar:
        st.markdown(
            """
        <div style="text-align: center; padding: 1.5rem 0 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; justify-content: center; gap: 0.75rem;">
                <i class="material-icons" style="font-size: 2.5rem; color: #4FC3F7;">settings</i>
                <div style="text-align: left;">
                    <h2 style="margin: 0; color: #4FC3F7; font-size: 1.75rem;">FuelTune</h2>
                    <p style="margin: 0; color: rgba(255,255,255,0.7); font-size: 0.85rem;">Data Analysis Platform</p>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Vehicle selector
        st.markdown("### Contexto do Veículo")
        selected_vehicle_id = render_vehicle_selector(
            label="Veículo Ativo",
            key="global_vehicle_context",
            help_text="Todos os dados serão filtrados por este veículo",
            show_create_button=True,
        )

        # Update global context
        if selected_vehicle_id:
            set_vehicle_context(selected_vehicle_id)

            # Show vehicle summary
            vehicle = get_vehicle_by_id(selected_vehicle_id)
            if vehicle:
                st.markdown(
                    f"""
                <div style="background: linear-gradient(135deg, #1976D2, #42A5F5); padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0; color: white;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="material-icons" style="font-size: 1.2rem;">directions_car</i>
                        <strong style="font-size: 0.9rem;">{vehicle.display_name}</strong>
                    </div>
                    <div style="font-size: 0.8rem; margin-top: 0.25rem; opacity: 0.9;">
                        {vehicle.technical_summary}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            set_vehicle_context(None)

        st.divider()

        # Session selector (if needed for multiple pages)
        st.markdown("### Sessão de Dados")
        db = get_database_connection()
        sessions = db.get_sessions()
        st.session_state.available_sessions = sessions

        if sessions:
            session_names = [f"{s['name']}" for s in sessions]
            selected_idx = st.selectbox(
                "Sessão ativa:",
                range(len(sessions)),
                format_func=lambda x: session_names[x] if x < len(session_names) else "None",
                index=(
                    0
                    if st.session_state.current_session_id is None
                    else next(
                        (
                            i
                            for i, s in enumerate(sessions)
                            if s["id"] == st.session_state.current_session_id
                        ),
                        0,
                    )
                ),
            )
            st.session_state.current_session_id = sessions[selected_idx]["id"]

            # Show session info
            current_session = sessions[selected_idx]
            st.markdown(
                f"""
            <div style="background: var(--secondary-background-color); padding: 0.5rem; border-radius: 6px; margin-top: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-color); font-size: 0.85rem;">
                    <i class="material-icons" style="font-size: 1rem;">storage</i>
                    <span>{current_session['records']:,} registros</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Nenhuma sessão disponível. Faça upload de dados primeiro.")
            st.session_state.current_session_id = None

        # Footer in sidebar
        st.markdown("---")
        st.markdown(
            f"""
        <div style="text-align: center; color: #999; font-size: 0.75rem;">
            <p style="margin: 0;">FuelTune v{config.APP_VERSION}</p>
            <p style="margin: 0;">© 2024 FuelTech Analysis</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Run the navigation
    pages.run()


if __name__ == "__main__":
    main()
