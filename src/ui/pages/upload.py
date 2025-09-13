"""
Upload Data Page - FuelTune Analyzer.

Página de upload melhorada com drag & drop, preview dos dados,
validação visual com badges e progress bar para processamento.

Features:
- Drag & drop interface
- Preview dos dados CSV
- Validação em tempo real
- Progress bars detalhadas
- Suporte a múltiplos formatos
- Validação de qualidade

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

import hashlib
import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

try:
    # Tentar importação relativa primeiro (para quando chamado como módulo)
    from ...data.csv_parser import CSVParser
    from ...data.database import get_database
    from ...data.quality import DataQualityAssessor
    from ...data.validators import DataValidator
    from ...utils.logging_config import get_logger
    from ..components.chart_builder import ChartBuilder, ChartConfig
    from ..components.metric_card import MetricCard, MetricData
except ImportError:
    # Fallback para importação absoluta (quando executado via st.navigation)
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.data.csv_parser import CSVParser
    from src.data.database import get_database
    from src.data.quality import DataQualityAssessor
    from src.data.validators import DataValidator
    from src.ui.components.chart_builder import ChartBuilder, ChartConfig
    from src.ui.components.metric_card import MetricCard, MetricData
    from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class UploadManager:
    """
    Gerenciador de upload de arquivos CSV.

    Características:
    - Validação em tempo real
    - Preview visual dos dados
    - Progress tracking
    - Quality assessment
    - Error handling robusto
    """

    def __init__(self):
        self.db = get_database()
        self.csv_parser = CSVParser()
        self.validator = DataValidator()
        self.quality_checker = DataQualityAssessor()
        self.metric_card = MetricCard()

    def calculate_file_hash(self, content: bytes) -> str:
        """Calcular hash SHA-256 do arquivo para detecção de duplicatas."""
        return hashlib.sha256(content).hexdigest()

    def validate_file_format(self, uploaded_file) -> Tuple[bool, str]:
        """
        Validar formato do arquivo.

        Args:
            uploaded_file: Arquivo carregado

        Returns:
            Tuple (é_válido, mensagem)
        """
        # Verificar extensão
        if not uploaded_file.name.lower().endswith(".csv"):
            return False, "Apenas arquivos CSV são suportados"

        # Verificar tamanho (máximo 100MB)
        if uploaded_file.size > 100 * 1024 * 1024:
            return False, "Arquivo muito grande (máximo 100MB)"

        # Verificar se não está vazio
        if uploaded_file.size == 0:
            return False, "Arquivo vazio"

        return True, "Formato válido"

    def preview_csv_data(self, uploaded_file, num_rows: int = 100) -> Optional[pd.DataFrame]:
        """
        Fazer preview dos dados CSV.

        Args:
            uploaded_file: Arquivo carregado
            num_rows: Número de linhas para preview

        Returns:
            DataFrame com preview ou None se erro
        """
        try:
            # Reset file pointer
            uploaded_file.seek(0)

            # Ler com diferentes encodings
            encodings_to_try = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

            for encoding in encodings_to_try:
                try:
                    uploaded_file.seek(0)
                    content = uploaded_file.read().decode(encoding)

                    # Criar DataFrame
                    df = pd.read_csv(
                        io.StringIO(content),
                        nrows=num_rows,
                        na_values=["", " ", "N/A", "NULL", "null", "nan"],
                    )

                    logger.info(f"Preview carregado com encoding {encoding}")
                    return df

                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Erro com encoding {encoding}: {str(e)}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Erro no preview: {str(e)}")
            return None

    def analyze_csv_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analisar estrutura do CSV.

        Args:
            df: DataFrame para análise

        Returns:
            Dicionário com informações da estrutura
        """
        analysis = {
            "total_columns": len(df.columns),
            "total_rows": len(df),
            "columns_info": {},
            "missing_data_summary": {},
            "data_types": {},
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
            "potential_fields": [],
        }

        # Analisar cada coluna
        for col in df.columns:
            col_data = df[col]

            analysis["columns_info"][col] = {
                "dtype": str(col_data.dtype),
                "non_null_count": col_data.count(),
                "null_count": col_data.isnull().sum(),
                "null_percentage": (col_data.isnull().sum() / len(df)) * 100,
                "unique_values": col_data.nunique(),
                "sample_values": col_data.dropna().head(3).tolist(),
            }

            # Detectar possíveis campos FuelTech
            col_lower = col.lower().replace(" ", "_").replace(".", "_")
            if any(keyword in col_lower for keyword in ["time", "tempo"]):
                analysis["potential_fields"].append(("TIME", col))
            elif any(keyword in col_lower for keyword in ["rpm"]):
                analysis["potential_fields"].append(("RPM", col))
            elif any(keyword in col_lower for keyword in ["acelerador", "throttle", "tps"]):
                analysis["potential_fields"].append(("THROTTLE", col))
            elif any(keyword in col_lower for keyword in ["map", "pressure"]):
                analysis["potential_fields"].append(("MAP", col))
            elif any(keyword in col_lower for keyword in ["lambda", "sonda", "o2"]):
                analysis["potential_fields"].append(("LAMBDA", col))

        return analysis

    def render_file_uploader(self) -> Optional[Any]:
        """Renderizar interface de upload."""
        st.markdown("### Seleção de Arquivo")

        # Interface drag & drop
        uploaded_file = st.file_uploader(
            "Arraste seu arquivo CSV aqui ou clique para selecionar",
            type=["csv"],
            accept_multiple_files=False,
            help="Arquivos CSV do FuelTech ECU (máximo 100MB)",
        )

        if uploaded_file is None:
            # Mostrar informações sobre formatos suportados
            with st.expander("Formatos Suportados", expanded=True):
                st.markdown(
                    """
                **Formatos aceitos:**
                - Arquivos CSV do FuelTech ECU
                - Encoding: UTF-8, Latin-1, CP1252, ISO-8859-1
                - Tamanho máximo: 100MB
                - Separadores: vírgula (,) ou ponto e vírgula (;)

                **Campos esperados:**
                - TIME (obrigatório)
                - RPM (obrigatório)
                - Throttle Position, MAP, Lambda, etc.
                """
                )
            return None

        return uploaded_file

    def render_file_validation(self, uploaded_file) -> Tuple[bool, Dict[str, Any]]:
        """
        Renderizar validação do arquivo.

        Args:
            uploaded_file: Arquivo carregado

        Returns:
            Tuple (é_válido, informações_validação)
        """
        st.markdown("### Validação do Arquivo")

        validation_info = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "file_info": {},
        }

        # Informações básicas do arquivo
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Nome", uploaded_file.name)

        with col2:
            size_mb = uploaded_file.size / 1024 / 1024
            st.metric("Tamanho", f"{size_mb:.2f} MB")

        with col3:
            file_hash = self.calculate_file_hash(uploaded_file.read())
            uploaded_file.seek(0)  # Reset
            st.metric("Hash", file_hash[:8])
            validation_info["file_info"]["hash"] = file_hash

        with col4:
            timestamp = datetime.now()
            st.metric("Upload", timestamp.strftime("%H:%M:%S"))

        # Validação de formato
        is_format_valid, format_message = self.validate_file_format(uploaded_file)

        if is_format_valid:
            st.success(f"{format_message}")
        else:
            st.error(f"{format_message}")
            validation_info["is_valid"] = False
            validation_info["errors"].append(format_message)

        # Verificar duplicatas
        try:
            self.db.initialize_database()
            existing_session = self.db.db_manager.get_session_by_hash(file_hash)

            if existing_session:
                st.warning(f"Arquivo já foi importado em '{existing_session.session_name}'")
                validation_info["warnings"].append("Arquivo duplicado encontrado")
        except Exception as e:
            logger.error(f"Erro ao verificar duplicatas: {str(e)}")

        return validation_info["is_valid"], validation_info

    def render_data_preview(self, uploaded_file) -> Optional[Dict[str, Any]]:
        """Renderizar preview dos dados."""
        st.markdown("### Preview dos Dados")

        with st.spinner("Carregando preview..."):
            df = self.preview_csv_data(uploaded_file, num_rows=100)

        if df is None:
            st.error("Não foi possível ler o arquivo CSV")
            return None

        # Análise da estrutura
        analysis = self.analyze_csv_structure(df)

        # Métricas do dataset
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Colunas", analysis["total_columns"])

        with col2:
            st.metric("Linhas (preview)", analysis["total_rows"])

        with col3:
            st.metric("Memória", f"{analysis['memory_usage_mb']:.1f} MB")

        with col4:
            missing_pct = sum(
                info["null_percentage"] for info in analysis["columns_info"].values()
            ) / len(analysis["columns_info"])
            st.metric("Dados Faltantes", f"{missing_pct:.1f}%")

        # Tabs para diferentes views
        tab1, tab2, tab3 = st.tabs(["Dados", "Estrutura", "Qualidade"])

        with tab1:
            # Preview dos dados
            st.dataframe(df.head(50), width="stretch", hide_index=True)

        with tab2:
            # Informações das colunas
            columns_df = pd.DataFrame(
                [
                    {
                        "Coluna": col,
                        "Tipo": info["dtype"],
                        "Não-Nulos": info["non_null_count"],
                        "Nulos (%)": f"{info['null_percentage']:.1f}%",
                        "Únicos": info["unique_values"],
                        "Exemplo": str(info["sample_values"][:2]),
                    }
                    for col, info in analysis["columns_info"].items()
                ]
            )

            st.dataframe(columns_df, width="stretch", hide_index=True)

        with tab3:
            # Quality assessment
            self.render_quality_assessment(df, analysis)

        return analysis

    def render_quality_assessment(self, df: pd.DataFrame, analysis: Dict) -> None:
        """Renderizar avaliação de qualidade dos dados."""

        # Score de qualidade geral
        quality_score = self.calculate_quality_score(df, analysis)

        # Gauge de qualidade
        gauge_config = ChartConfig(title="Score de Qualidade", height=300)
        gauge_builder = ChartBuilder(gauge_config)

        color_ranges = [
            (0, 50, "red"),
            (50, 70, "orange"),
            (70, 90, "yellow"),
            (90, 100, "green"),
        ]

        gauge_builder.create_gauge_chart(
            value=quality_score, min_value=0, max_value=100, color_ranges=color_ranges
        )

        col1, col2 = st.columns([1, 2])

        with col1:
            gauge_builder.render(key="quality_gauge")

        with col2:
            # Métricas de qualidade detalhadas
            quality_metrics = self.get_quality_metrics(df, analysis)

            for metric in quality_metrics:
                self.metric_card.render_single(metric)

        # Problemas encontrados
        issues = self.identify_data_issues(df, analysis)
        if issues:
            st.markdown("#### Problemas Identificados")
            for issue in issues:
                if issue["severity"] == "error":
                    st.error(f"{issue['message']}")
                elif issue["severity"] == "warning":
                    st.warning(f"{issue['message']}")
                else:
                    st.info(f"{issue['message']}")

    def calculate_quality_score(self, df: pd.DataFrame, analysis: Dict) -> float:
        """Calcular score de qualidade dos dados."""
        score = 100.0

        # Penalizar dados faltantes
        avg_missing_pct = sum(
            info["null_percentage"] for info in analysis["columns_info"].values()
        ) / len(analysis["columns_info"])
        score -= avg_missing_pct * 0.5

        # Penalizar se não tem campos essenciais
        essential_fields = ["time", "rpm"]
        potential_field_names = [field[0].lower() for field in analysis["potential_fields"]]

        for essential in essential_fields:
            if essential not in potential_field_names:
                score -= 20

        # Bonus por ter muitos campos FuelTech reconhecidos
        recognized_fields = len(analysis["potential_fields"])
        if recognized_fields >= 10:
            score += 10
        elif recognized_fields >= 5:
            score += 5

        return max(0, min(100, score))

    def get_quality_metrics(self, df: pd.DataFrame, analysis: Dict) -> List[MetricData]:
        """Obter métricas de qualidade."""

        completeness = 100 - (
            sum(info["null_percentage"] for info in analysis["columns_info"].values())
            / len(analysis["columns_info"])
        )
        consistency = len(analysis["potential_fields"]) / max(len(df.columns), 1) * 100

        return [
            MetricData(
                value=completeness,
                label="Completude",
                unit="%",
                format=".1f",
                help_text="Percentual de dados não-faltantes",
            ),
            MetricData(
                value=consistency,
                label="Consistência",
                unit="%",
                format=".1f",
                help_text="Campos reconhecidos do FuelTech",
            ),
            MetricData(
                value=len(analysis["potential_fields"]),
                label="Campos FuelTech",
                format=".0f",
                help_text="Campos identificados do FuelTech",
            ),
        ]

    def identify_data_issues(self, df: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """Identificar problemas nos dados."""
        issues = []

        # Verificar campos essenciais
        potential_field_names = [field[0].lower() for field in analysis["potential_fields"]]

        if "time" not in potential_field_names:
            issues.append(
                {
                    "severity": "error",
                    "message": "Campo TIME não encontrado - obrigatório para importação",
                }
            )

        if "rpm" not in potential_field_names:
            issues.append(
                {
                    "severity": "error",
                    "message": "Campo RPM não encontrado - obrigatório para análise",
                }
            )

        # Verificar dados faltantes excessivos
        for col, info in analysis["columns_info"].items():
            if info["null_percentage"] > 80:
                issues.append(
                    {
                        "severity": "warning",
                        "message": f'Coluna "{col}" tem {info["null_percentage"]:.1f}% de dados faltantes',
                    }
                )

        # Verificar se tem poucos dados
        if len(df) < 10:
            issues.append(
                {
                    "severity": "warning",
                    "message": f"Dataset muito pequeno ({len(df)} linhas) - pode afetar análises",
                }
            )

        return issues

    def render_import_section(self, uploaded_file, analysis: Dict, validation_info: Dict) -> None:
        """Renderizar seção de importação."""
        st.markdown("### Importação")

        if not validation_info["is_valid"]:
            st.error("Corrija os erros de validação antes de importar")
            return

        # Configurações de importação
        col1, col2 = st.columns(2)

        with col1:
            session_name = st.text_input(
                "Nome da Sessão:",
                value=Path(uploaded_file.name).stem,
                help="Nome identificativo para esta sessão de dados",
            )

        with col2:
            format_version = st.selectbox(
                "Versão do Formato:",
                ["Auto-detectar", "v1.0 (37 campos)", "v2.0 (64 campos)"],
                help="Versão do formato FuelTech",
            )

        # Opções avançadas
        with st.expander("Opções Avançadas"):
            col1, col2 = st.columns(2)

            with col1:
                chunk_size = st.number_input(
                    "Tamanho do Chunk:",
                    min_value=1000,
                    max_value=50000,
                    value=10000,
                    step=1000,
                    help="Linhas processadas por vez",
                )

                force_reimport = st.checkbox(
                    "Sobrescrever se já existir",
                    value=False,
                    help="Se marcado, deletará a sessão anterior e reimportará o arquivo",
                )

            with col2:
                skip_validation = st.checkbox(
                    "Pular Validação Detalhada",
                    help="Acelera importação mas pode pular erros",
                )

        # Botão de importação
        if st.button("Iniciar Importação", type="primary", disabled=not session_name.strip()):
            self.process_import(
                uploaded_file,
                session_name,
                analysis,
                validation_info,
                chunk_size,
                skip_validation,
                force_reimport,
            )

    def process_import(
        self,
        uploaded_file,
        session_name: str,
        analysis: Dict,
        validation_info: Dict,
        chunk_size: int,
        skip_validation: bool,
        force_reimport: bool = False,
    ) -> None:
        """Processar importação do arquivo."""

        # Container para progress
        progress_container = st.empty()
        status_container = st.empty()

        try:
            with progress_container.container():
                st.markdown("#### Progresso da Importação")

                overall_progress = st.progress(0, text="Iniciando importação...")
                detail_progress = st.progress(0, text="")

                step_status = st.empty()

            # Passo 1: Preparar dados
            overall_progress.progress(10, text="Preparando dados...")
            step_status.info("Carregando arquivo completo...")

            uploaded_file.seek(0)
            full_df = pd.read_csv(uploaded_file)

            # Passo 2: Validação (se não pulada)
            if not skip_validation:
                overall_progress.progress(30, text="Validando dados...")
                step_status.info("Executando validação detalhada...")

                validation_results = self.run_detailed_validation(full_df)

                if validation_results["has_errors"]:
                    status_container.error("Validação falhou")
                    for error in validation_results["errors"]:
                        st.error(f"{error}")
                    return

            # Passo 3: Salvar arquivo temporário e importar usando a função completa
            overall_progress.progress(50, text="Processando arquivo...")
            step_status.info("Importando dados para o banco...")

            # Salvar arquivo temporário
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                uploaded_file.seek(0)
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name

            try:
                # Usar a função import_csv_file que já tem toda a lógica
                import_results = self.db.import_csv_file(
                    file_path=tmp_file_path,
                    session_name=session_name,
                    force_reimport=force_reimport,
                    validate_data=not skip_validation,
                    normalize_data=True,
                    assess_quality=True,
                )

                overall_progress.progress(100, text="Finalizando...")

                if import_results.get("status") == "completed":
                    step_status.success("Importação concluída!")
                    session_id = import_results.get("session_id")
                elif import_results.get("status") == "skipped":
                    step_status.warning(
                        "Arquivo já importado. Marque 'Sobrescrever' para reimportar."
                    )
                    session_id = import_results.get("session_id")
                else:
                    raise Exception("Falha na importação")

            finally:
                # Limpar arquivo temporário
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)

            # Mostrar resultado
            if import_results.get("status") == "completed":
                status_container.success(
                    f"""
                **Importação Concluída com Sucesso!**

                - **Sessão:** {session_name}
                - **Registros:** {import_results.get('total_records', 0):,}
                - **Colunas:** {import_results.get('field_count', 0)}
                - **Formato:** {import_results.get('format_version', 'N/A')}
                - **Qualidade:** {import_results.get('quality_results', {}).get('overall_score', 0):.1f}/100
                """
                )

                # Opções pós-importação
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Abrir Dashboard"):
                        st.session_state["selected_session_id"] = session_id
                        st.switch_page("pages/dashboard.py")

                with col2:
                    if st.button("Analisar Dados"):
                        st.session_state["selected_session_id"] = session_id
                        st.switch_page("pages/analysis.py")
            elif import_results.get("status") == "skipped":
                status_container.info(
                    f"""
                **Arquivo já foi importado anteriormente**
                
                - **Sessão existente:** {import_results.get('session_name', 'N/A')}
                - **ID:** {session_id}
                
                Para reimportar, marque a opção 'Sobrescrever se já existir' nas opções avançadas.
                """
                )

        except Exception as e:
            logger.error(f"Erro na importação: {str(e)}")
            status_container.error(f"Erro na importação: {str(e)}")

            # Cleanup em caso de erro
            try:
                if "session_record" in locals():
                    with self.db.get_session() as db:
                        db.query(DataSession).filter_by(id=session_record.id).delete()
                        db.commit()
            except:
                pass

    def run_detailed_validation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Executar validação detalhada dos dados."""
        results = {"has_errors": False, "errors": [], "warnings": []}

        # Implementar validações específicas
        # Por enquanto, retorna sem erros
        return results

    def prepare_chunk_for_db(self, chunk_df: pd.DataFrame) -> List[Dict]:
        """Preparar chunk de dados para inserção no banco."""
        records = []

        for _, row in chunk_df.iterrows():
            # Mapear colunas para campos do banco
            record = {}

            # Mapear campos conhecidos (simplificado)
            column_mapping = {
                "TIME": "time",
                "RPM": "rpm",
                "Posição_do_acelerador": "throttle_position",
                "MAP": "map",
                "Sonda_Geral": "o2_general",
                "Temp._do_motor": "engine_temp",
            }

            for csv_col, db_field in column_mapping.items():
                if csv_col in chunk_df.columns:
                    value = row[csv_col]
                    record[db_field] = None if pd.isna(value) else value

            records.append(record)

        return records


def render_upload_page() -> None:
    """
    Renderizar página de upload.

    Esta é a função principal que deve ser chamada para exibir a página de upload.
    """
    st.set_page_config(
        page_title="Upload - FuelTune Analyzer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Título da página
    st.title("FuelTune Analyzer - Upload de Dados")
    st.markdown("Carregue seus arquivos CSV do FuelTech ECU para análise")
    st.markdown("---")

    # Inicializar manager
    upload_manager = UploadManager()

    # Sidebar com informações
    with st.sidebar:
        st.header("Guia de Upload")

        with st.expander("Preparação", expanded=True):
            st.markdown(
                """
            **Antes do upload:**
            1. Certifique-se que o arquivo é um CSV válido
            2. Verifique se contém campos TIME e RPM
            3. Remova caracteres especiais do nome
            4. Confirme encoding UTF-8 se possível
            """
            )

        with st.expander("Limitações"):
            st.markdown(
                """
            **Limites atuais:**
            - Tamanho máximo: 100MB
            - Formato: CSV apenas
            - Campos obrigatórios: TIME, RPM
            - Encoding: UTF-8 preferencial
            """
            )

        with st.expander("Suporte"):
            st.markdown(
                """
            **Em caso de problemas:**
            - Verifique o formato do arquivo
            - Teste com arquivo menor primeiro
            - Consulte logs de erro
            - Contate suporte técnico
            """
            )

    # Conteúdo principal
    try:
        # Passo 1: Upload do arquivo
        uploaded_file = upload_manager.render_file_uploader()

        if uploaded_file is not None:
            st.markdown("---")

            # Passo 2: Validação
            is_valid, validation_info = upload_manager.render_file_validation(uploaded_file)

            if is_valid or st.session_state.get("force_preview", False):
                st.markdown("---")

                # Passo 3: Preview e análise
                analysis = upload_manager.render_data_preview(uploaded_file)

                if analysis is not None:
                    st.markdown("---")

                    # Passo 4: Importação
                    upload_manager.render_import_section(uploaded_file, analysis, validation_info)
            else:
                st.info("Corrija os problemas de validação para continuar")

                # Botão para forçar preview (debug)
                if st.checkbox("Forçar preview (debug)", help="Apenas para desenvolvimento"):
                    st.session_state["force_preview"] = True
                    st.rerun()

        else:
            # Mostrar estatísticas de uploads anteriores
            st.markdown("### Uploads Recentes")

            try:
                upload_manager.db.initialize_database()
                sessions = upload_manager.db.get_sessions()

                if sessions:
                    recent_sessions = sorted(sessions, key=lambda x: x["created_at"], reverse=True)[
                        :5
                    ]

                    for session in recent_sessions:
                        with st.expander(f"{session['name']}", expanded=False):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                records = session.get("records", 0)
                                records_value = records if records is not None else 0
                                st.metric("Registros", f"{records_value:,}")

                            with col2:
                                quality = session.get("quality_score", 0)
                                # Garantir que quality não seja None antes de formatar
                                quality_value = quality if quality is not None else 0
                                st.metric("Qualidade", f"{quality_value:.1f}%")

                            with col3:
                                status = (
                                    "Completo" if session["status"] == "completed" else "Aguardando"
                                )
                                st.metric(
                                    "Status",
                                    f"{status}",
                                )
                else:
                    st.info("Nenhum upload anterior encontrado. Carregue seu primeiro arquivo CSV!")

            except Exception as e:
                logger.error(f"Erro ao carregar uploads anteriores: {str(e)}")
                st.warning("Não foi possível carregar histórico de uploads")

    except Exception as e:
        logger.error(f"Erro na página de upload: {str(e)}")
        st.error(f"Erro inesperado: {str(e)}")

        if st.session_state.get("debug_mode", False):
            st.exception(e)


if __name__ == "__main__":
    # Executar página de upload diretamente
    render_upload_page()
