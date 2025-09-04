"""
FuelTune Streamlit - Main Application
A comprehensive FuelTech data analysis platform built with Streamlit.

This application provides tools for analyzing automotive engine data
with support for 64 FuelTech fields and advanced visualization capabilities.
"""

import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

# Add src directory to path for imports
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import config
from src.data.cache import get_cache_manager

# Import new data modules
from src.data.database import get_database
from src.utils.logger import get_logger
from src.ui.theme_config import apply_professional_theme, professional_theme

# Import integration system
from src.integration import (
    integration_manager,
    initialize_integration_system,
    shutdown_integration_system,
    workflow_manager,
    task_manager,
    notification_system,
    clipboard_manager,
    export_import_manager,
    plugin_system,
)

# Configure page
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply professional theme
apply_professional_theme()

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


# Global state for sessions
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "available_sessions" not in st.session_state:
    st.session_state.available_sessions = []
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None


def main():
    """Main application function."""
    logger.info("Starting FuelTune Streamlit application")

    # Initialize integration system
    initialize_integration()

    # Header using professional theme
    st.markdown(professional_theme.create_section_header(
        "settings", 
        "FuelTune - Análise de Dados Automotivos",
        f"Versão: {config.APP_VERSION}"
    ), unsafe_allow_html=True)

    # System status indicator
    show_system_status()

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2;">menu</i>
            <h3 style="margin: 0;">Navegação</h3>
        </div>
        """, unsafe_allow_html=True)

        # Session selector
        db = get_database_connection()
        sessions = db.get_sessions()
        st.session_state.available_sessions = sessions

        if sessions:
            session_names = [f"{s['name']} ({s['records']} records)" for s in sessions]
            selected_idx = st.selectbox(
                "Selecionar Sessão de Dados:",
                range(len(sessions)),
                format_func=lambda x: (session_names[x] if x < len(session_names) else "None"),
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
        else:
            st.info("Nenhuma sessão de dados disponível. Por favor, faça upload dos dados primeiro.")
            st.session_state.current_session_id = None

        st.divider()

        page_options = [
            ("Início", "home"),
            ("Upload de Dados", "upload_file"),
            ("Análise", "analytics"),
            ("Visualização", "visibility"),
            ("Integração", "integration_instructions"),
            ("Configurações", "settings")
        ]
        
        # Create custom navigation
        st.markdown("**Selecionar Página:**")
        page = st.selectbox(
            "Selecionar Página:",
            [option[0] for option in page_options],
            format_func=lambda x: x
        )

    # Main content area
    if page == "Início":
        show_home_page()
    elif page == "Upload de Dados":
        show_upload_page()
    elif page == "Análise":
        show_analysis_page()
    elif page == "Visualização":
        show_visualization_page()
    elif page == "Integração":
        show_integration_page()
    elif page == "Configurações":
        show_settings_page()

    # Footer
    st.markdown("---")
    st.markdown("**FuelTune** - Plataforma Profissional de Análise de Dados FuelTech")


def show_home_page():
    """Display the home page."""
    st.header("Bem-vindo ao FuelTune")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 1px solid #E0E0E0;">
            <i class="material-icons" style="font-size: 3rem; color: #1976D2; margin-bottom: 1rem;">analytics</i>
            <h3 style="color: #1976D2; margin-bottom: 0.5rem;">Análise de Dados</h3>
            <p style="color: #6C757D; margin: 0;">Análise abrangente de dados do motor FuelTech com estatísticas avançadas e insights.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 1px solid #E0E0E0;">
            <i class="material-icons" style="font-size: 3rem; color: #1976D2; margin-bottom: 1rem;">show_chart</i>
            <h3 style="color: #1976D2; margin-bottom: 0.5rem;">Visualização</h3>
            <p style="color: #6C757D; margin: 0;">Gráficos interativos para exploração profunda e apresentação de dados.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 1px solid #E0E0E0;">
            <i class="material-icons" style="font-size: 3rem; color: #1976D2; margin-bottom: 1rem;">precision_manufacturing</i>
            <h3 style="color: #1976D2; margin-bottom: 0.5rem;">64 Campos FuelTech</h3>
            <p style="color: #6C757D; margin: 0;">Suporte completo para todos os 64 campos de dados FuelTech com mapeamento inteligente.</p>
        </div>
        """, unsafe_allow_html=True)

    # Feature highlights
    st.subheader("Recursos Principais")

    features = [
        ("Suporte para 64 campos de dados FuelTech", "check_circle"),
        ("Validação avançada de dados com Pandera", "verified"),
        ("Visualizações interativas com Plotly", "timeline"),
        ("Processamento de dados em tempo real", "speed"),
        ("Recursos de exportação", "file_download"),
        ("Log profissional e tratamento de erros", "bug_report"),
        ("Configurações personalizáveis", "tune"),
        ("Cobertura abrangente de testes", "task_alt"),
    ]

    col1, col2 = st.columns(2)
    with col1:
        for feature_text, icon in features[:4]:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                <i class="material-icons" style="color: #4CAF50; font-size: 1.25rem;">{icon}</i>
                <span style="color: #212529;">{feature_text}</span>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        for feature_text, icon in features[4:]:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                <i class="material-icons" style="color: #4CAF50; font-size: 1.25rem;">{icon}</i>
                <span style="color: #212529;">{feature_text}</span>
            </div>
            """, unsafe_allow_html=True)

    # Getting started
    st.subheader("Como Começar")
    st.info(
        "1. Navegue até **Upload de Dados** para carregar seus arquivos CSV FuelTech\n\n"
        "2. Use **Análise** para explorar seus dados com insights estatísticos\n\n"
        "3. Crie **Visualizações** com gráficos interativos\n\n"
        "4. Ajuste as **Configurações** para personalizar sua experiência"
    )


def show_upload_page():
    """Display the data upload page with full processing pipeline."""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
        <i class="material-icons" style="font-size: 2rem; color: #1976D2;">upload_file</i>
        <h2 style="margin: 0; color: #1976D2;">Upload e Processamento de Dados</h2>
    </div>
    """, unsafe_allow_html=True)
    st.write(
        "Faça upload dos seus arquivos CSV FuelTech para análise com validação completa e avaliação de qualidade."
    )

    # File uploader
    uploaded_file = st.file_uploader(
        "Escolha um arquivo CSV",
        type=["csv"],
        help=f"Formatos suportados: {', '.join(config.ALLOWED_EXTENSIONS)}",
    )

    if uploaded_file is not None:
        st.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso!")

        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_file_path = tmp_file.name

        try:
            # Show file details
            st.subheader("Detalhes do Arquivo")
            file_details = {
                "Nome do arquivo": uploaded_file.name,
                "Tamanho do arquivo": f"{uploaded_file.size:,} bytes",
                "Tipo do arquivo": uploaded_file.type,
            }

            for key, value in file_details.items():
                st.write(f"**{key}:** {value}")

            # Processing options
            st.subheader("Opções de Processamento")

            col1, col2, col3 = st.columns(3)
            with col1:
                validate_data = st.checkbox(
                    "Validar Dados", value=True, help="Validar dados conforme o esquema"
                )
            with col2:
                normalize_data = st.checkbox(
                    "Normalizar Dados", value=True, help="Limpar e normalizar dados"
                )
            with col3:
                assess_quality = st.checkbox(
                    "Avaliar Qualidade", value=True, help="Realizar avaliação de qualidade"
                )

            # Session name input
            session_name = st.text_input(
                "Nome da Sessão",
                value=uploaded_file.name.replace(".csv", ""),
                help="Nome para esta sessão de dados",
            )

            # Process button
            if st.button("Processar Arquivo", type="primary"):
                st.markdown("""
                <style>
                .stButton > button:before {
                    content: "\e2c6";
                    font-family: 'Material Icons';
                    margin-right: 0.5rem;
                }
                </style>
                """, unsafe_allow_html=True)
                if not session_name.strip():
                    st.error("Por favor, forneça um nome para a sessão.")
                    return

                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    db = get_database_connection()

                    # Update progress
                    status_text.text("Iniciando processamento do arquivo...")
                    progress_bar.progress(10)

                    # Import file
                    import_results = db.import_csv_file(
                        file_path=temp_file_path,
                        session_name=session_name.strip(),
                        validate_data=validate_data,
                        normalize_data=normalize_data,
                        assess_quality=assess_quality,
                    )

                    progress_bar.progress(100)
                    status_text.text("Processamento concluído!")

                    # Show results
                    st.markdown("""
                    <div class="alert-success" style="background-color: #E8F5E8; border-left: 4px solid #4CAF50; padding: 1rem 1.5rem; border-radius: 8px; margin: 1rem 0;">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <i class="material-icons" style="color: #4CAF50;">check_circle</i>
                            <span style="color: #2E7D32; font-weight: 500;">Arquivo processado com sucesso!</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Display import results
                    with st.expander("📊 Resultados do Processamento", expanded=True):
                        st.markdown("""
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                            <i class="material-icons" style="color: #1976D2;">assessment</i>
                            <span style="font-weight: 600; color: #1976D2;">Resultados do Processamento</span>
                        </div>
                        """, unsafe_allow_html=True)
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "Versão do Formato",
                                import_results.get("format_version", "Unknown"),
                            )
                        with col2:
                            st.metric("Quantidade de Campos", import_results.get("field_count", 0))
                        with col3:
                            st.metric(
                                "Total de Registros",
                                f"{import_results.get('total_records', 0):,}",
                            )
                        with col4:
                            quality_score = None
                            if assess_quality and "quality_results" in import_results:
                                quality_score = import_results["quality_results"].get(
                                    "overall_score"
                                )
                            st.metric(
                                "Pontuação de Qualidade",
                                (
                                    f"{quality_score:.1f}/100"
                                    if quality_score is not None
                                    else "N/A"
                                ),
                            )

                        # Steps completed
                        st.write("**Etapas de Processamento Concluídas:**")
                        for step in import_results.get("steps_completed", []):
                            st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                                <i class="material-icons" style="color: #4CAF50; font-size: 1.1rem;">check</i>
                                <span style="color: #2E7D32;">{step.replace('_', ' ').title()}</span>
                            </div>
                            """, unsafe_allow_html=True)

                        # Show warnings if any
                        if import_results.get("warnings"):
                            st.warning("Avisos:")
                            for warning in import_results["warnings"]:
                                st.markdown(f"""
                                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                                    <i class="material-icons" style="color: #FF9800; font-size: 1.1rem;">warning</i>
                                    <span style="color: #F57C00;">{warning}</span>
                                </div>
                                """, unsafe_allow_html=True)

                    # Show validation results if available
                    if validate_data and "validation_results" in import_results:
                        validation = import_results["validation_results"]
                        with st.expander("🔍 Resultados da Validação"):
                            st.markdown("""
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                                <i class="material-icons" style="color: #1976D2;">fact_check</i>
                                <span style="font-weight: 600; color: #1976D2;">Resultados da Validação</span>
                            </div>
                            """, unsafe_allow_html=True)
                            if validation["is_valid"]:
                                st.success("Validação de dados aprovada!")
                            else:
                                st.error(
                                    f"Validação falhou com {len(validation.get('errors', []))} erros"
                                )
                                for error in validation.get("errors", [])[
                                    :5
                                ]:  # Show first 5 errors
                                    st.markdown(f"""
                                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                                        <i class="material-icons" style="color: #F44336; font-size: 1.1rem;">error</i>
                                        <span style="color: #C62828;">{error}</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                    # Show quality assessment if available
                    if assess_quality and "quality_results" in import_results:
                        quality = import_results["quality_results"]
                        with st.expander("📋 Quality Assessment"):
                            st.markdown("""
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                                <i class="material-icons" style="color: #1976D2;">checklist</i>
                                <span style="font-weight: 600; color: #1976D2;">Avaliação de Qualidade</span>
                            </div>
                            """, unsafe_allow_html=True)

                            # Overall metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(
                                    "Checks Performed",
                                    quality.get("checks_performed", 0),
                                )
                            with col2:
                                st.metric("Passed", quality.get("checks_passed", 0))
                            with col3:
                                st.metric("Warnings", quality.get("checks_warning", 0))
                            with col4:
                                st.metric("Failed", quality.get("checks_failed", 0))

                            # Detailed results
                            for result in quality.get("detailed_results", []):
                                status_icon = {
                                    "passed": "check_circle",
                                    "warning": "warning", 
                                    "failed": "error"
                                }.get(result["status"], "help")
                                
                                status_color = {
                                    "passed": "#4CAF50",
                                    "warning": "#FF9800",
                                    "failed": "#F44336"
                                }.get(result["status"], "#757575")
                                st.markdown(f"""
                                <div style="display: flex; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.75rem; padding: 0.75rem; background-color: #F8F9FA; border-radius: 8px; border-left: 3px solid {status_color};">
                                    <i class="material-icons" style="color: {status_color}; margin-top: 2px;">{status_icon}</i>
                                    <div>
                                        <strong style="color: #212529;">{result['check_name'].replace('_', ' ').title()}</strong>
                                        <div style="color: #6C757D; margin-top: 0.25rem;">{result['message']}</div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                    # Update session state
                    st.session_state.current_session_id = import_results.get("session_id")
                    st.rerun()

                except Exception as e:
                    progress_bar.progress(0)
                    status_text.text("")
                    logger.error(f"File processing failed: {str(e)}")
                    st.error(f"Processing failed: {str(e)}")
                    st.info("Please check the file format and try again.")

        finally:
            # Clean up temporary file
            Path(temp_file_path).unlink(missing_ok=True)

    # Information about supported data
    st.subheader("Formato de Dados Suportado")
    st.write(
        f"Esta aplicação suporta dados FuelTech com **37 ou 64 campos** com detecção automática de formato."
    )

    # Feature overview
    with st.expander("Recursos de Processamento"):
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2;">build</i>
            <span style="font-weight: 600; color: #1976D2;">Recursos de Processamento</span>
        </div>
        """, unsafe_allow_html=True)
        features = {
            "Detecção de Formato": "Detecta automaticamente formato de 37 ou 64 campos",
            "Validação de Dados": "Valida tipos de dados, intervalos e campos obrigatórios",
            "Normalização de Dados": "Limpa outliers, trata valores ausentes, aplica suavização",
            "Avaliação de Qualidade": "Verificações abrangentes de qualidade e pontuação",
            "Mapeamento de Campos": "Mapeia nomes de campos em português para inglês",
            "Armazenamento em Banco": "Armazena dados processados em banco SQLite",
            "Cache": "Cache inteligente para performance",
        }

        for feature, description in features.items():
            st.write(f"**{feature}:** {description}")

    with st.expander("Campos FuelTech Suportados (64 campos)"):
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2;">data_object</i>
            <span style="font-weight: 600; color: #1976D2;">Campos FuelTech Suportados (64 campos)</span>
        </div>
        """, unsafe_allow_html=True)
        field_categories = {
            "Motor Principal (1-37)": [
                "TIME, RPM, TPS, Throttle Position, Ignition Timing",
                "MAP, Lambda Sensors, O2 Sensors, Fuel System",
                "Engine Temperature, Air Temperature, Pressures",
                "Battery Voltage, Ignition Dwell, Control Outputs",
            ],
            "Consumo & Performance (38-44)": [
                "Total Consumption, Average Consumption, Instant Consumption",
                "Estimated Power, Estimated Torque, Total Distance, Range",
            ],
            "Dinâmica & IMU (45-58)": [
                "Traction Speed, Acceleration Speed, G-Forces",
                "Pitch/Roll Angles and Rates, Heading, Distance",
            ],
            "Controle Avançado (59-64)": [
                "Traction Control Slip, Acceleration/Deceleration Enrichment",
                "Injection Controls, Start Button Toggle",
            ],
        }

        for category, fields in field_categories.items():
            st.write(f"**{category}:**")
            for field_group in fields:
                st.write(f"• {field_group}")
            st.write("")


def show_analysis_page():
    """Display the analysis page with real data analysis."""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
        <i class="material-icons" style="font-size: 2rem; color: #1976D2;">analytics</i>
        <h2 style="margin: 0; color: #1976D2;">Análise de Dados</h2>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.current_session_id is None:
        st.warning(
            "Nenhuma sessão de dados selecionada. Por favor, faça upload dos dados primeiro ou selecione uma sessão na barra lateral."
        )
        return

    try:
        db = get_database_connection()
        get_cache()
        session_id = st.session_state.current_session_id

        # Get session info
        sessions = db.get_sessions()
        current_session = next((s for s in sessions if s["id"] == session_id), None)

        if not current_session:
            st.error("Sessão selecionada não encontrada.")
            return

        st.info(
            f"Analisando sessão: **{current_session['name']}** ({current_session['records']:,} registros)"
        )

        # Analysis options
        st.subheader("Opções de Análise")

        col1, col2 = st.columns(2)
        with col1:
            time_range_filter = st.checkbox("Aplicar Filtro de Intervalo de Tempo", value=False)
            if time_range_filter:
                # Get data sample to determine time range
                sample_data = db.get_session_data(session_id, columns=["time"])
                if not sample_data.empty:
                    min_time = float(sample_data["time"].min())
                    max_time = float(sample_data["time"].max())

                    time_range = st.slider(
                        "Intervalo de Tempo (segundos)",
                        min_value=min_time,
                        max_value=max_time,
                        value=(min_time, max_time),
                        step=0.1,
                    )
                else:
                    time_range = None
            else:
                time_range = None

        with col2:
            include_extended = st.checkbox(
                "Include Extended Fields",
                value=current_session["format"] == "v2.0",
                help="Include 64-field format data if available",
            )

        # Load data
        @st.cache_data
        def load_session_data(session_id, include_extended, time_range):
            return db.get_session_data(
                session_id, include_extended=include_extended, time_range=time_range
            )

        data = load_session_data(session_id, include_extended, time_range)

        if data.empty:
            st.error("No data found for the selected session.")
            return

        # Tabs for different analysis types
        # Custom tabs with Material Icons
        tab_options = [
            ("Statistical Summary", "insert_chart"),
            ("Data Quality", "high_quality"),
            ("Correlations", "scatter_plot"),
            ("Performance", "speed"),
            ("Anomalies", "report_problem")
        ]
        
        # Create tabs using radio buttons for better styling control
        selected_tab = st.radio(
            "Selecionar Análise:",
            [tab[0] for tab in tab_options],
            horizontal=True,
            format_func=lambda x: x
        )
        
        # Map selection to tab index
        tab_index = next(i for i, (name, _) in enumerate(tab_options) if name == selected_tab)
        
        st.markdown("")
        
        if tab_index == 0:
            show_statistical_analysis(data)
        elif tab_index == 1:
            show_quality_analysis(db, session_id)
        elif tab_index == 2:
            show_correlation_analysis(data)
        elif tab_index == 3:
            show_performance_analysis(data)
        elif tab_index == 4:
            show_anomaly_analysis(data)

        # This is now handled above in the radio button logic

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        st.error(f"Analysis failed: {str(e)}")


def show_statistical_analysis(data):
    """Show statistical analysis tab."""
    st.subheader("Statistical Summary")

    # Basic info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", f"{len(data):,}")
    with col2:
        st.metric("Fields", len(data.columns))
    with col3:
        duration = data["time"].max() - data["time"].min() if "time" in data.columns else 0
        st.metric("Duration", f"{duration:.1f}s")
    with col4:
        sample_rate = 1 / data["time"].diff().median() if "time" in data.columns else 0
        st.metric("Sample Rate", f"{sample_rate:.1f} Hz")

    # Numeric fields summary
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    if "time" in numeric_cols:
        numeric_cols.remove("time")  # Remove time from statistical analysis

    if numeric_cols:
        st.subheader("Numeric Fields Statistics")

        # Field selector
        selected_fields = st.multiselect(
            "Select fields for detailed statistics:",
            numeric_cols,
            default=numeric_cols[:5],  # Default to first 5
        )

        if selected_fields:
            stats_df = data[selected_fields].describe().round(2)
            st.dataframe(stats_df, use_container_width=True)

            # Missing values
            missing_data = data[selected_fields].isnull().sum()
            if missing_data.sum() > 0:
                st.subheader("Missing Values")
                st.bar_chart(missing_data[missing_data > 0])


def show_quality_analysis(db, session_id):
    """Show data quality analysis tab."""
    st.subheader("Data Quality Assessment")

    # Get quality results
    quality_results = db.get_session_quality(session_id)

    if "checks" not in quality_results:
        st.info("No quality assessment data available for this session.")
        return

    # Overall quality metrics
    checks = quality_results["checks"]
    passed = len([c for c in checks if c["status"] == "passed"])
    warnings = len([c for c in checks if c["status"] == "warning"])
    failed = len([c for c in checks if c["status"] == "failed"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Checks", len(checks))
    with col2:
        st.metric("Passed", passed, delta=None)
    with col3:
        st.metric("Warnings", warnings, delta=None)
    with col4:
        st.metric("Failed", failed, delta=None)

    # Quality check details
    st.subheader("Quality Check Results")

    for check in checks:
        status_color = {
            "passed": "success",
            "warning": "warning",
            "failed": "error",
        }.get(check["status"], "info")

        status_icon_map = {
            "passed": ("check_circle", "#4CAF50"),
            "warning": ("warning", "#FF9800"), 
            "failed": ("error", "#F44336")
        }
        
        icon_name, icon_color = status_icon_map.get(check["status"], ("help", "#757575"))

        with st.expander(f"{check['check_type'].replace('_', ' ').title()}"):
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <i class="material-icons" style="color: {icon_color};">{icon_name}</i>
                <strong style="color: #212529;">{check['check_type'].replace('_', ' ').title()}</strong>
            </div>
            """, unsafe_allow_html=True)
            if status_color == "success":
                st.success(check["message"])
            elif status_color == "warning":
                st.warning(check["message"])
            else:
                st.error(check["message"])

            if check.get("error_percentage", 0) > 0:
                st.write(f"**Error Rate:** {check['error_percentage']:.2f}%")

            if check.get("details"):
                st.json(check["details"])


def show_correlation_analysis(data):
    """Show correlation analysis tab."""
    st.subheader("Correlation Analysis")

    # Get numeric columns
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    if "time" in numeric_cols:
        numeric_cols.remove("time")

    if len(numeric_cols) < 2:
        st.warning("Need at least 2 numeric fields for correlation analysis.")
        return

    # Field selection
    selected_fields = st.multiselect(
        "Select fields for correlation analysis:",
        numeric_cols,
        default=numeric_cols[:8],  # Default to first 8
    )

    if len(selected_fields) >= 2:
        corr_matrix = data[selected_fields].corr()

        # Display correlation matrix
        st.subheader("Correlation Matrix")

        # Create a more readable format
        import plotly.graph_objects as go

        fig = go.Figure(
            data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale="RdBu",
                zmid=0,
                text=corr_matrix.round(2).values,
                texttemplate="%{text}",
                textfont={"size": 10},
                hoverongaps=False,
            )
        )

        fig.update_layout(title="Field Correlation Matrix", width=600, height=600)

        st.plotly_chart(fig, use_container_width=True)

        # Strong correlations
        st.subheader("Strong Correlations")
        strong_corrs = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:  # Strong correlation threshold
                    strong_corrs.append(
                        {
                            "Field 1": corr_matrix.columns[i],
                            "Field 2": corr_matrix.columns[j],
                            "Correlation": round(corr_val, 3),
                        }
                    )

        if strong_corrs:
            st.dataframe(pd.DataFrame(strong_corrs), use_container_width=True)
        else:
            st.info("No strong correlations (|r| > 0.7) found.")


def show_performance_analysis(data):
    """Show performance analysis tab."""
    st.subheader("Performance Analysis")

    performance_fields = ["rpm", "estimated_power", "estimated_torque", "tps", "map"]
    available_fields = [f for f in performance_fields if f in data.columns]

    if not available_fields:
        st.warning("No performance fields available in this dataset.")
        return

    # Performance metrics
    if "rpm" in data.columns:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("RPM Analysis")
            st.metric("Max RPM", f"{data['rpm'].max():,}")
            st.metric("Average RPM", f"{data['rpm'].mean():.0f}")
            st.metric("RPM Range", f"{data['rpm'].max() - data['rpm'].min():,}")

        with col2:
            if "estimated_power" in data.columns:
                st.subheader("Power Analysis")
                st.metric("Max Power", f"{data['estimated_power'].max()} HP")
                st.metric("Average Power", f"{data['estimated_power'].mean():.0f} HP")

    # Performance over time charts
    if "time" in data.columns and available_fields:
        st.subheader("Performance Over Time")

        chart_field = st.selectbox("Select field to plot:", available_fields)

        import plotly.express as px

        fig = px.line(
            data,
            x="time",
            y=chart_field,
            title=f"{chart_field.replace('_', ' ').title()} vs Time",
        )
        fig.update_xaxes(title="Time (seconds)")
        fig.update_yaxes(title=chart_field.replace("_", " ").title())

        st.plotly_chart(fig, use_container_width=True)


def show_anomaly_analysis(data):
    """Show anomaly analysis tab."""
    st.subheader("Anomaly Detection")

    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    if "time" in numeric_cols:
        numeric_cols.remove("time")

    if not numeric_cols:
        st.warning("No numeric fields available for anomaly detection.")
        return

    # Field selection
    field_to_analyze = st.selectbox("Select field for anomaly detection:", numeric_cols)

    if field_to_analyze:
        # Calculate outliers using IQR method
        Q1 = data[field_to_analyze].quantile(0.25)
        Q3 = data[field_to_analyze].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = data[
            (data[field_to_analyze] < lower_bound) | (data[field_to_analyze] > upper_bound)
        ]

        # Display results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(data))
        with col2:
            st.metric("Outliers Found", len(outliers))
        with col3:
            outlier_percent = (len(outliers) / len(data)) * 100 if len(data) > 0 else 0
            st.metric("Outlier Percentage", f"{outlier_percent:.2f}%")

        # Show outlier details
        if len(outliers) > 0:
            st.subheader("Outlier Summary")
            st.write(f"**Normal Range:** {lower_bound:.2f} to {upper_bound:.2f}")
            st.write(
                f"**Outlier Values:** {outliers[field_to_analyze].min():.2f} to {outliers[field_to_analyze].max():.2f}"
            )

            # Plot with outliers highlighted
            if "time" in data.columns:
                import plotly.express as px

                # Create plot data
                plot_data = data.copy()
                plot_data["is_outlier"] = plot_data.index.isin(outliers.index)

                fig = px.scatter(
                    plot_data,
                    x="time",
                    y=field_to_analyze,
                    color="is_outlier",
                    title=f"Outliers in {field_to_analyze.replace('_', ' ').title()}",
                    color_discrete_map={True: "red", False: "blue"},
                )

                st.plotly_chart(fig, use_container_width=True)


def show_visualization_page():
    """Display the visualization page."""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
        <i class="material-icons" style="font-size: 2rem; color: #1976D2;">show_chart</i>
        <h2 style="margin: 0; color: #1976D2;">Visualização</h2>
    </div>
    """, unsafe_allow_html=True)
    st.info("A funcionalidade de visualização de dados será implementada na próxima fase de desenvolvimento.")

    # Placeholder content
    st.subheader("Tipos de Gráficos Disponíveis")

    chart_types = [
        ("Gráficos de Linha", "Visualização de séries temporais"),
        ("Gráficos de Dispersão", "Análise de correlação e relacionamentos"),
        ("Histogramas", "Análise de distribuição de dados"),
        ("Mapas de Calor", "Relacionamentos de dados multidimensionais"),
        ("Box Plots", "Visualização de distribuição estatística"),
        ("Gráficos 3D", "Análise multivariável"),
    ]

    col1, col2 = st.columns(2)

    for i, (chart_type, description) in enumerate(chart_types):
        with col1 if i % 2 == 0 else col2:
            st.subheader(chart_type)
            st.write(description)


def show_settings_page():
    """Display the settings page."""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
        <i class="material-icons" style="font-size: 2rem; color: #1976D2;">settings</i>
        <h2 style="margin: 0; color: #1976D2;">Configurações</h2>
    </div>
    """, unsafe_allow_html=True)

    # Application settings
    st.subheader("Configuração da Aplicação")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Nome da Aplicação:** {config.APP_NAME}")
        st.write(f"**Versão:** {config.APP_VERSION}")
        st.write(f"**Modo Debug:** {'Ativado' if config.DEBUG else 'Desativado'}")
        st.write(f"**Nível de Log:** {config.LOG_LEVEL}")

    with col2:
        st.write(f"**Max File Size:** {config.MAX_FILE_SIZE}")
        st.write(f"**Supported Extensions:** {', '.join(config.ALLOWED_EXTENSIONS)}")
        st.write(f"**FuelTech Fields:** 64 (auto-detection)")
        st.write(f"**Cache Expiry:** {config.CACHE_EXPIRY_HOURS} hours")

    # Database information
    st.subheader("Database Information")

    try:
        db = get_database_connection()
        db_stats = db.get_database_stats()

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Database Path:** {db_stats['database']['file_path']}")
            st.write(f"**Database Size:** {db_stats['database']['size_mb']:.2f} MB")
            st.write(f"**Total Sessions:** {db_stats['sessions']['total']}")
            st.write(f"**Completed Sessions:** {db_stats['sessions']['completed']}")

        with col2:
            st.write(f"**Core Records:** {db_stats['records']['core_data']:,}")
            st.write(f"**Extended Records:** {db_stats['records']['extended_data']:,}")
            st.write(f"**Quality Checks:** {db_stats['quality']['total_checks']:,}")
            st.write(f"**Quality Pass Rate:** {db_stats['quality']['pass_rate']:.1f}%")

    except Exception as e:
        st.error(f"Unable to load database information: {str(e)}")

    # Cache information
    st.subheader("Cache Information")

    try:
        cache = get_cache()
        cache_stats = cache.get_stats()

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Memory Cache:**")
            st.write(f"• Entries: {cache_stats['memory_cache']['entries']}")
            st.write(f"• Size: {cache_stats['memory_cache']['total_size_mb']:.2f} MB")
            st.write(f"• Utilization: {cache_stats['memory_cache']['utilization']:.1f}%")

        with col2:
            st.write("**Disk Cache:**")
            st.write(f"• Entries: {cache_stats['disk_cache']['entries']}")
            st.write(f"• Size: {cache_stats['disk_cache']['total_size_mb']:.2f} MB")
            st.write(f"• Utilization: {cache_stats['disk_cache']['size_utilization']:.1f}%")

        # Cache management
        st.subheader("Cache Management")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Clear Memory Cache"):
                cache.memory_cache.clear()
                st.success("Memory cache cleared!")
                st.rerun()

        with col2:
            if st.button("Clear All Caches"):
                cache.clear_all()
                st.success("All caches cleared!")
                st.rerun()

    except Exception as e:
        st.error(f"Unable to load cache information: {str(e)}")

    # System information
    st.subheader("System Information")

    import platform

    import pandas as pd
    import pandera
    import plotly
    import sqlalchemy

    system_info = {
        "Python Version": platform.python_version(),
        "Platform": platform.platform(),
        "Pandas Version": pd.__version__,
        "Plotly Version": plotly.__version__,
        "Streamlit Version": st.__version__,
        "SQLAlchemy Version": sqlalchemy.__version__,
        "Pandera Version": pandera.__version__,
    }

    for key, value in system_info.items():
        st.write(f"**{key}:** {value}")

    # Data processing modules status
    st.subheader("Data Processing Modules")

    modules_status = {
        "CSV Parser": "Active",
        "Data Validator": "Active",
        "Data Normalizer": "Active",
        "Quality Assessor": "Active",
        "Database Manager": "Active",
        "Cache Manager": "Active",
    }

    for module, status in modules_status.items():
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <i class="material-icons" style="color: #4CAF50; font-size: 1.1rem;">check_circle</i>
            <strong style="color: #212529;">{module}:</strong>
            <span style="color: #2E7D32;">{status}</span>
        </div>
        """, unsafe_allow_html=True)

    # Project structure
    with st.expander("Project Structure"):
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: #1976D2;">folder</i>
            <span style="font-weight: 600; color: #1976D2;">Estrutura do Projeto</span>
        </div>
        """, unsafe_allow_html=True)
        st.code(
            """
fueltune-streamlit/
├── app.py                     # Main Streamlit app with full integration
├── requirements.txt           # Dependencies
├── .env.example              # Environment variables template
├── config.py                 # Configuration settings
├── src/                      # Source code
│   ├── __init__.py
│   ├── data/                # ✅ Complete data processing pipeline
│   │   ├── csv_parser.py    # CSV parsing with auto-detection
│   │   ├── validators.py    # Pandera data validation
│   │   ├── normalizer.py    # Data cleaning & normalization
│   │   ├── quality.py       # Quality assessment
│   │   ├── models.py        # SQLAlchemy database models
│   │   ├── database.py      # Database interface
│   │   └── cache.py         # Multi-level caching
│   ├── ui/                  # UI components
│   ├── analysis/            # Analysis modules
│   └── utils/               # Utilities
├── tests/                   # ✅ Complete test suite
│   ├── unit/               # Unit tests for all modules
│   │   ├── test_csv_parser.py
│   │   ├── test_validators.py
│   │   ├── test_data_quality.py
│   │   └── test_cache.py
│   └── integration/        # Integration tests
├── docs/                   # Documentation
├── data/                   # Data files
└── fueltech_data.db        # SQLite database
        """
        )


# Integration system functions
def initialize_integration():
    """Initialize the integration system."""
    if "integration_initialized" not in st.session_state:
        try:
            success = initialize_integration_system()
            st.session_state.integration_initialized = success
            if success:
                logger.info("Integration system initialized successfully")
            else:
                logger.error("Failed to initialize integration system")
        except Exception as e:
            logger.error(f"Integration system initialization error: {e}")
            st.session_state.integration_initialized = False


def show_system_status():
    """Show system status indicator."""
    if st.session_state.get("integration_initialized", False):
        with st.container():
            status = integration_manager.get_system_status()

            if status["system_status"] == "running":
                st.markdown("""
                <div class="alert-success" style="background-color: #E8F5E8; border-left: 4px solid #4CAF50; padding: 1rem 1.5rem; border-radius: 8px; margin: 1rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="material-icons" style="color: #4CAF50;">check_circle</i>
                        <span style="color: #2E7D32; font-weight: 500;">Todos os sistemas operacionais</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif status["system_status"] == "degraded":
                st.markdown("""
                <div class="alert-warning" style="background-color: #FFF3E0; border-left: 4px solid #FF9800; padding: 1rem 1.5rem; border-radius: 8px; margin: 1rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="material-icons" style="color: #FF9800;">warning</i>
                        <span style="color: #F57C00; font-weight: 500;">Sistema em modo degradado</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif status["system_status"] == "error":
                st.markdown("""
                <div class="alert-error" style="background-color: #FFEBEE; border-left: 4px solid #F44336; padding: 1rem 1.5rem; border-radius: 8px; margin: 1rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="material-icons" style="color: #F44336;">error</i>
                        <span style="color: #C62828; font-weight: 500;">Erro no sistema</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="alert-info" style="background-color: #E3F2FD; border-left: 4px solid #2196F3; padding: 1rem 1.5rem; border-radius: 8px; margin: 1rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <i class="material-icons" style="color: #2196F3;">info</i>
                        <span style="color: #1565C0; font-weight: 500;">Sistema inicializando...</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)


def show_integration_page():
    """Display the integration system management page."""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
        <i class="material-icons" style="font-size: 2rem; color: #1976D2;">integration_instructions</i>
        <h2 style="margin: 0; color: #1976D2;">Sistema de Integração</h2>
    </div>
    """, unsafe_allow_html=True)
    st.write("Monitore e gerencie todos os sistemas de integração do FuelTune")

    if not st.session_state.get("integration_initialized", False):
        st.error("Sistema de integração não inicializado")
        if st.button("Tentar Reinicializar"):
            initialize_integration()
            st.rerun()
        return

    # System overview
    st.subheader("Status Geral do Sistema")
    status = integration_manager.get_system_status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Status", status["system_status"].title())
    with col2:
        uptime_hours = status["uptime_seconds"] / 3600
        st.metric("Uptime", f"{uptime_hours:.1f}h")
    with col3:
        st.metric("Sessões Ativas", status["active_sessions"])
    with col4:
        st.metric("Componentes", len(status["components"]))

    # System tabs
    # Integration system tabs with Material Icons
    integration_tabs = [
        ("Workflows", "workflow"),
        ("Tarefas", "task"),
        ("Notificações", "notifications"),
        ("Clipboard", "content_paste"),
        ("Plugins", "extension")
    ]
    
    selected_integration_tab = st.radio(
        "Selecionar Seção:",
        [tab[0] for tab in integration_tabs],
        horizontal=True
    )
    
    # Map selection to functions
    tab_functions = {
        "Workflows": show_workflows_tab,
        "Tarefas": show_tasks_tab,
        "Notificações": show_notifications_tab,
        "Clipboard": show_clipboard_tab,
        "Plugins": show_plugins_tab
    }
    
    # Execute selected function
    if selected_integration_tab in tab_functions:
        tab_functions[selected_integration_tab]()

    # Tab content is now handled above


def show_workflows_tab():
    """Show workflows management tab."""
    st.subheader("Gerenciamento de Workflows")

    # Quick workflow actions
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Workflows Predefinidos:**")
        if st.button("Importar CSV"):
            st.markdown("<i class='material-icons' style='color: #1976D2;'>sync</i>", unsafe_allow_html=True)
            session_id = st.session_state.get("current_session_id", "demo")
            task_id = integration_manager.create_integrated_workflow(
                "csv_import", session_id=session_id, file_path="/path/to/demo.csv", vehicle_id=1
            )
            st.success(f"Workflow iniciado: {task_id}")

        if st.button("Análise Completa"):
            st.markdown("<i class='material-icons' style='color: #1976D2;'>analytics</i>", unsafe_allow_html=True)
            session_id = st.session_state.get("current_session_id", "demo")
            task_id = integration_manager.create_integrated_workflow(
                "full_analysis", session_id=session_id
            )
            st.success(f"Análise iniciada: {task_id}")

    with col2:
        st.write("**Workflows Disponíveis:**")
        workflows = workflow_manager.workflows
        for name, steps in workflows.items():
            st.write(f"• {name} ({len(steps)} etapas)")


def show_tasks_tab():
    """Show background tasks tab."""
    st.subheader("Tarefas em Background")

    # Task statistics
    stats = task_manager.get_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Tarefas Ativas", stats["active_tasks"])
    with col2:
        st.metric("Concluídas", stats["completed_tasks"])
    with col3:
        st.metric("Falhadas", stats["failed_tasks"])
    with col4:
        st.metric("Fila", stats.get("queue_size", 0))

    # Active tasks
    st.write("**Tarefas Ativas:**")
    active_tasks = task_manager.get_active_tasks()

    if active_tasks:
        for task in active_tasks:
            with st.expander(f"{task.name} ({task.status.value})"):
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <i class="material-icons" style="color: #1976D2;">sync</i>
                    <strong>{task.name}</strong>
                    <span style="color: #6C757D;">({task.status.value})</span>
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ID:** {task.task_id}")
                    st.write(f"**Tipo:** {task.task_type.value}")
                    st.write(f"**Prioridade:** {task.priority.value}")

                with col2:
                    progress = task.get_progress()
                    st.progress(progress.progress / 100.0)
                    st.write(f"**Progresso:** {progress.progress:.1f}%")
                    if progress.message:
                        st.write(f"**Status:** {progress.message}")

                if st.button(f"Cancelar {task.task_id}", key=f"cancel_{task.task_id}"):
                    success = task_manager.cancel_task(task.task_id)
                    if success:
                        st.success("Tarefa cancelada")
                        st.rerun()
    else:
        st.info("Nenhuma tarefa ativa")

    # Quick task actions
    st.write("**Ações Rápidas:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Demo CSV Import"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>file_upload</i>", unsafe_allow_html=True)
            task_id = task_manager.submit_csv_import("/demo/file.csv", 1)
            st.success(f"Tarefa criada: {task_id}")

    with col2:
        if st.button("Demo Analysis"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>analytics</i>", unsafe_allow_html=True)
            task_id = task_manager.submit_analysis("demo_session")
            st.success(f"Análise iniciada: {task_id}")

    with col3:
        if st.button("Demo Export"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>file_download</i>", unsafe_allow_html=True)
            task_id = task_manager.submit_export({}, "csv", "/tmp/export.csv")
            st.success(f"Exportação iniciada: {task_id}")


def show_notifications_tab():
    """Show notifications system tab."""
    st.subheader("Sistema de Notificações")

    # Notification stats
    stats = notification_system.get_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", stats["total_notifications"])
    with col2:
        st.metric("Fila", stats["queue_size"])
    with col3:
        st.metric("Canais", len(stats["available_channels"]))
    with col4:
        st.metric("Rate Limit", stats.get("rate_limiter_status", 0))

    # Test notifications
    st.write("**Testar Notificações:**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Info"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>info</i>", unsafe_allow_html=True)
            notification_system.send_info("Teste de notificação info")

    with col2:
        if st.button("Sucesso"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #4CAF50;'>check_circle</i>", unsafe_allow_html=True)
            notification_system.send_success("Operação realizada com sucesso!")

    with col3:
        if st.button("Aviso"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #FF9800;'>warning</i>", unsafe_allow_html=True)
            notification_system.send_warning("Isto é um aviso de teste")

    with col4:
        if st.button("Erro"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #F44336;'>error</i>", unsafe_allow_html=True)
            notification_system.send_error("Erro de teste simulado")

    # Notification history
    st.write("**Histórico de Notificações:**")
    history = notification_system.get_history(limit=10)

    if history:
        for notification in history[-5:]:  # Show last 5
            icon_map = {
                "success": ("check_circle", "#4CAF50"),
                "error": ("error", "#F44336"),
                "warning": ("warning", "#FF9800"),
                "info": ("info", "#2196F3")
            }
            
            icon_name, icon_color = icon_map.get(notification.type.value, ("notifications", "#757575"))
            st.markdown(f"""
            <div style="display: flex; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.75rem; padding: 0.75rem; background-color: #F8F9FA; border-radius: 8px; border-left: 3px solid {icon_color};">
                <i class="material-icons" style="color: {icon_color}; margin-top: 2px;">{icon_name}</i>
                <div>
                    <strong style="color: #212529;">{notification.title or notification.type.value.title()}</strong>
                    <div style="color: #6C757D; margin-top: 0.25rem;">{notification.message}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma notificação no histórico")


def show_clipboard_tab():
    """Show clipboard integration tab."""
    st.subheader("Integração com Clipboard")

    if not clipboard_manager.is_available():
        st.warning("Clipboard não disponível neste sistema")
        return

    # Clipboard status
    formats = clipboard_manager.get_formatters()
    st.write(f"**Formatos Suportados:** {len(formats)}")

    for format_type in formats.keys():
        st.write(f"• {format_type.value}")

    # Copy data actions
    st.write("**Copiar Dados de Exemplo:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Texto"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>text_fields</i>", unsafe_allow_html=True)
            success = clipboard_manager.copy_to_clipboard(
                "Dados de teste do FuelTune", clipboard_manager.ClipboardFormat.TEXT
            )
            if success:
                st.success("Texto copiado!")

    with col2:
        if st.button("CSV"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>table_chart</i>", unsafe_allow_html=True)
            import pandas as pd

            sample_df = pd.DataFrame(
                {"time": [0, 1, 2], "rpm": [800, 1000, 1200], "throttle": [0, 10, 20]}
            )
            success = clipboard_manager.copy_dataframe(sample_df)
            if success:
                st.success("DataFrame copiado como CSV!")

    with col3:
        if st.button("JSON"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>code</i>", unsafe_allow_html=True)
            sample_data = {
                "session_id": "demo",
                "analysis_results": {"avg_rpm": 1000, "max_rpm": 7000},
            }
            success = clipboard_manager.copy_analysis_results(sample_data)
            if success:
                st.success("JSON copiado!")

    # Paste data
    st.write("**Colar do Clipboard:**")
    if st.button("Colar Texto"):
        st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>content_paste</i>", unsafe_allow_html=True)
        clipboard_data = clipboard_manager.paste_from_clipboard(
            clipboard_manager.ClipboardFormat.TEXT
        )
        if clipboard_data:
            st.code(str(clipboard_data.content))
        else:
            st.warning("Nenhum dado encontrado no clipboard")


def show_plugins_tab():
    """Show plugins system tab."""
    st.subheader("Sistema de Plugins")

    # Plugin stats
    stats = plugin_system.get_system_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Plugins", stats["total_plugins"])
    with col2:
        st.metric("Ativos", stats["by_status"].get("active", 0))
    with col3:
        st.metric("Hook Points", stats["hook_points"])
    with col4:
        st.metric("Total Hooks", stats["total_hooks"])

    # Plugin list
    st.write("**Plugins Carregados:**")
    plugins_info = plugin_system.registry.list_plugins()

    if plugins_info:
        for plugin_name, plugin_info in plugins_info.items():
            status_icon_map = {
                "active": ("check_circle", "#4CAF50"),
                "loaded": ("radio_button_checked", "#2196F3"),
                "error": ("error", "#F44336")
            }
            
            icon_name, icon_color = status_icon_map.get(plugin_info["status"], ("help", "#757575"))

            with st.expander(
                f"{plugin_name} v{plugin_info['metadata'].get('version', '1.0')}"
            ):
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                    <i class="material-icons" style="color: {icon_color};">{icon_name}</i>
                    <strong style="color: #212529;">{plugin_name}</strong>
                    <span style="color: #6C757D;">v{plugin_info['metadata'].get('version', '1.0')}</span>
                </div>
                """, unsafe_allow_html=True)
                st.write(f"**Tipo:** {plugin_info['metadata'].get('plugin_type', 'unknown')}")
                st.write(f"**Status:** {plugin_info['status']}")
                st.write(
                    f"**Descrição:** {plugin_info['metadata'].get('description', 'Sem descrição')}"
                )

                if plugin_info.get("error_message"):
                    st.error(f"Erro: {plugin_info['error_message']}")

                if plugin_info.get("hooks"):
                    st.write("**Hooks:**")
                    for hook_name, count in plugin_info["hooks"].items():
                        st.write(f"• {hook_name}: {count}")
    else:
        st.info("Nenhum plugin carregado")

    # Plugin actions
    st.write("**Ações de Plugin:**")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Descobrir Plugins"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>search</i>", unsafe_allow_html=True)
            results = plugin_system.discover_and_load_plugins()
            st.write("**Resultados da Descoberta:**")
            for plugin_file, success in results.items():
                icon_name = "check_circle" if success else "error"
                icon_color = "#4CAF50" if success else "#F44336"
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                    <i class="material-icons" style="color: {icon_color}; font-size: 1.1rem;">{icon_name}</i>
                    <span style="color: #212529;">{plugin_file}</span>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        if st.button("Recarregar Sistema"):
            st.markdown("<i class='material-icons' style='margin-right: 0.5rem; color: #1976D2;'>refresh</i>", unsafe_allow_html=True)
            plugin_system.shutdown()
            plugin_system.initialize()
            st.success("Sistema de plugins reiniciado")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        st.info("Please check the logs for more details.")

    finally:
        # Ensure cleanup on app shutdown
        if st.session_state.get("integration_initialized", False):
            try:
                shutdown_integration_system()
            except Exception as e:
                logger.error(f"Shutdown error: {e}")
