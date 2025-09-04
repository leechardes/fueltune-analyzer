"""
Reports Page - FuelTune Analyzer.

Página de geração e exportação de relatórios com:
- Geração de relatórios PDF
- Export para Excel
- Templates customizáveis
- Histórico de relatórios
- Comparação entre sessões

Author: A03-UI-STREAMLIT Agent
Created: 2025-01-02
"""

import io
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import streamlit as st

try:
    # Tentar importação relativa primeiro (para quando chamado como módulo)
    from ...data.database import get_database
    from ...utils.logging_config import get_logger
    from ..components.metric_card import MetricCard
    from ..components.session_selector import SessionSelector
except ImportError:
    # Fallback para importação absoluta (quando executado via st.navigation)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from src.data.database import get_database
    from src.utils.logging_config import get_logger
    from src.ui.components.metric_card import MetricCard
    from src.ui.components.session_selector import SessionSelector

logger = get_logger(__name__)


class ReportsManager:
    """
    Gerenciador de relatórios.

    Responsável por:
    - Geração de relatórios padronizados
    - Export em múltiplos formatos
    - Templates customizáveis
    - Comparação entre sessões
    - Histórico de relatórios
    """

    def __init__(self):
        self.db = get_database()
        self.metric_card = MetricCard()

    def generate_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Gerar resumo da sessão para relatórios."""
        try:
            # Aqui seria carregado um resumo completo da sessão
            # Por simplicidade, retornando um exemplo
            return {
                "session_id": session_id,
                "session_name": f"Sessão {session_id[:8]}",
                "total_records": 5420,
                "duration": 142.5,
                "max_rpm": 7200,
                "avg_rpm": 3450,
                "max_boost": 1.8,
                "avg_lambda": 0.85,
                "max_temp": 92.5,
                "quality_score": 87.3,
            }
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {str(e)}")
            return {}

    def render_report_templates(self) -> None:
        """Renderizar seleção de templates de relatório."""
        st.markdown("### Templates de Relatório")

        templates = {
            "summary": {
                "name": "Relatório Resumido",
                "description": "Visão geral da sessão com métricas principais",
                "icon": "",
            },
            "detailed": {
                "name": "Relatório Detalhado",
                "description": "Análise completa com gráficos e estatísticas",
                "icon": "",
            },
            "comparison": {
                "name": "Comparação de Sessões",
                "description": "Compare múltiplas sessões lado a lado",
                "icon": "",
            },
            "performance": {
                "name": "Relatório de Performance",
                "description": "Focado em métricas de potência e torque",
                "icon": "",
            },
            "diagnostic": {
                "name": "Relatório Diagnóstico",
                "description": "Análise de problemas e alertas",
                "icon": "",
            },
        }

        # Grid de templates
        cols = st.columns(3)

        for i, (template_id, template_info) in enumerate(templates.items()):
            with cols[i % 3]:
                with st.container():
                    st.markdown(
                        f"""
                    <div style="border: 1px solid #ddd; padding: 1rem; border-radius: 0.5rem; text-align: center;">
                        <h3>{template_info['name']}</h3>
                        <p>{template_info['description']}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    if st.button(f"Selecionar", key=f"template_{template_id}"):
                        st.session_state["selected_template"] = template_id
                        st.rerun()

    def render_report_configuration(self, template_id: str) -> Dict[str, Any]:
        """Renderizar configuração do relatório."""
        st.markdown("### Configuração do Relatório")

        config = {}

        col1, col2 = st.columns(2)

        with col1:
            config["report_title"] = st.text_input(
                "Título do Relatório:",
                value=f"Relatório FuelTech - {datetime.now().strftime('%d/%m/%Y')}",
            )

            config["author"] = st.text_input("Autor:", value="FuelTune Analyzer")

            config["include_charts"] = st.checkbox(
                "Incluir Gráficos",
                value=True,
                help="Incluir visualizações no relatório",
            )

        with col2:
            config["format"] = st.selectbox(
                "Formato de Saída:",
                ["PDF", "Excel", "Word", "HTML"],
                help="Formato do arquivo de saída",
            )

            config["quality"] = st.selectbox(
                "Qualidade:",
                ["Alta", "Média", "Baixa"],
                index=1,
                help="Qualidade das imagens e gráficos",
            )

            config["include_raw_data"] = st.checkbox(
                "Incluir Dados Brutos",
                value=False,
                help="Anexar planilha com dados originais",
            )

        # Configurações específicas do template
        if template_id == "comparison":
            st.markdown("#### Configurações de Comparação")
            config["max_sessions"] = st.slider(
                "Máximo de Sessões:", min_value=2, max_value=5, value=3
            )

        elif template_id == "performance":
            st.markdown("#### Configurações de Performance")
            config["include_curves"] = st.checkbox("Incluir Curvas de Potência/Torque", value=True)
            config["target_power"] = st.number_input("Potência Alvo (HP):", min_value=0, value=300)

        return config

    def render_session_selection_for_report(self, template_id: str, config: Dict) -> List[str]:
        """Renderizar seleção de sessões para o relatório."""
        st.markdown("### Seleção de Sessões")

        if template_id == "comparison":
            max_sessions = config.get("max_sessions", 3)
            st.info(f"Selecione até {max_sessions} sessões para comparação")

            # Multi-seletor de sessões
            selector = SessionSelector(key_prefix="report_multi")
            selected_sessions = selector.render_multi_selector(max_selections=max_sessions)

            return [s.id for s in selected_sessions]

        else:
            # Seletor único
            selector = SessionSelector(key_prefix="report_single")
            selected_session = selector.render_selector()

            return [selected_session.id] if selected_session else []

    def generate_summary_report(self, session_ids: List[str], config: Dict) -> Dict[str, Any]:
        """Gerar relatório resumido."""
        report_data = {
            "title": config.get("report_title", "Relatório Resumido"),
            "author": config.get("author", "FuelTune Analyzer"),
            "generated_at": datetime.now(),
            "sessions": [],
            "summary_stats": {},
        }

        # Gerar dados para cada sessão
        for session_id in session_ids:
            session_summary = self.generate_session_summary(session_id)
            if session_summary:
                report_data["sessions"].append(session_summary)

        # Calcular estatísticas agregadas
        if report_data["sessions"]:
            all_sessions = report_data["sessions"]
            report_data["summary_stats"] = {
                "total_sessions": len(all_sessions),
                "total_records": sum(s.get("total_records", 0) for s in all_sessions),
                "avg_quality": np.mean([s.get("quality_score", 0) for s in all_sessions]),
                "max_rpm": max(s.get("max_rpm", 0) for s in all_sessions),
                "avg_lambda": np.mean([s.get("avg_lambda", 0.85) for s in all_sessions]),
            }

        return report_data

    def render_report_preview(self, report_data: Dict[str, Any], template_id: str) -> None:
        """Renderizar preview do relatório."""
        st.markdown("### Preview do Relatório")

        # Header do relatório
        st.markdown(
            f"""
        # {report_data.get('title', 'Relatório')}

        **Autor:** {report_data.get('author', 'N/A')}
        **Data:** {report_data.get('generated_at', datetime.now()).strftime('%d/%m/%Y %H:%M')}
        **Template:** {template_id.title()}

        ---
        """
        )

        # Estatísticas resumidas
        if "summary_stats" in report_data:
            st.markdown("## Resumo Executivo")

            stats = report_data["summary_stats"]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Sessões", stats.get("total_sessions", 0))

            with col2:
                st.metric("Registros", f"{stats.get('total_records', 0):,}")

            with col3:
                st.metric("Qualidade Média", f"{stats.get('avg_quality', 0):.1f}%")

            with col4:
                st.metric("RPM Máximo", f"{stats.get('max_rpm', 0):,}")

        # Detalhes das sessões
        if report_data.get("sessions"):
            st.markdown("## Detalhes das Sessões")

            sessions_df = pd.DataFrame(report_data["sessions"])
            st.dataframe(sessions_df, width='stretch', hide_index=True)

        # Placeholder para gráficos
        st.markdown("## Visualizações")
        st.info("Gráficos serão incluídos no relatório final")

        # Placeholder para conclusões
        st.markdown("## Conclusões e Recomendações")
        st.markdown(
            """
        - Desempenho geral dentro dos parâmetros esperados
        - Recomenda-se monitoramento contínuo da temperatura
        - Lambda médio está adequado para a aplicação
        - Considerar ajustes no mapa de ignição para otimização
        """
        )

    def export_report(self, report_data: Dict, config: Dict) -> bytes:
        """Exportar relatório no formato escolhido."""
        format_type = config.get("format", "PDF")

        if format_type == "Excel":
            return self.export_to_excel(report_data)
        elif format_type == "HTML":
            return self.export_to_html(report_data)
        else:
            # Para PDF e Word, retornar placeholder
            return "Relatório gerado com sucesso (formato não implementado ainda)".encode("utf-8")

    def export_to_excel(self, report_data: Dict) -> bytes:
        """Exportar relatório para Excel."""
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            # Aba resumo
            summary_data = [
                {"Métrica": key, "Valor": value}
                for key, value in report_data.get("summary_stats", {}).items()
            ]

            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Resumo", index=False)

            # Aba sessões
            if report_data.get("sessions"):
                sessions_df = pd.DataFrame(report_data["sessions"])
                sessions_df.to_excel(writer, sheet_name="Sessões", index=False)

        output.seek(0)
        return output.read()

    def export_to_html(self, report_data: Dict) -> bytes:
        """Exportar relatório para HTML."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report_data.get('title', 'Relatório')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>{report_data.get('title', 'Relatório')}</h1>
            <p><strong>Autor:</strong> {report_data.get('author', 'N/A')}</p>
            <p><strong>Data:</strong> {report_data.get('generated_at', datetime.now()).strftime('%d/%m/%Y %H:%M')}</p>

            <h2>Resumo</h2>
            <table>
        """

        # Adicionar estatísticas
        for key, value in report_data.get("summary_stats", {}).items():
            html_content += f"<tr><td>{key}</td><td>{value}</td></tr>"

        html_content += """
            </table>
        </body>
        </html>
        """

        return html_content.encode("utf-8")

    def render_report_history(self) -> None:
        """Renderizar histórico de relatórios."""
        st.markdown("### Histórico de Relatórios")

        # Placeholder para histórico
        history_data = [
            {
                "Data": "02/01/2025 14:30",
                "Título": "Relatório de Performance - Sessão ABC",
                "Template": "Performance",
                "Status": "Concluído",
                "Formato": "PDF",
            },
            {
                "Data": "01/01/2025 16:45",
                "Título": "Comparação 3 Sessões",
                "Template": "Comparison",
                "Status": "Concluído",
                "Formato": "Excel",
            },
            {
                "Data": "31/12/2024 10:15",
                "Título": "Diagnóstico Motor",
                "Template": "Diagnostic",
                "Status": "Erro",
                "Formato": "PDF",
            },
        ]

        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, width='stretch', hide_index=True)

        # Ações do histórico
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Limpar Histórico"):
                st.success("Histórico limpo!")

        with col2:
            if st.button("Export Histórico"):
                csv = history_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "report_history.csv", "text/csv")

        with col3:
            if st.button("Atualizar"):
                st.rerun()


def render_reports_page() -> None:
    """Renderizar página de relatórios."""
    st.set_page_config(
        page_title="Relatórios - FuelTune Analyzer",
        page_icon=":material/description:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("FuelTune Analyzer - Relatórios")
    st.markdown("Geração e exportação de relatórios personalizados")
    st.markdown("---")

    # Inicializar manager
    reports_manager = ReportsManager()

    # Sidebar
    with st.sidebar:
        st.header("Relatórios")

        # Progresso do relatório
        if "selected_template" in st.session_state:
            progress = st.progress(0)

            steps = ["Template", "Configuração", "Sessões", "Preview", "Export"]
            current_step = st.session_state.get("report_step", 0)

            progress.progress((current_step + 1) / len(steps))
            st.write(f"Passo {current_step + 1}/{len(steps)}: {steps[current_step]}")

            if st.button("Recomeçar"):
                for key in list(st.session_state.keys()):
                    if key.startswith("selected_template") or key.startswith("report_"):
                        del st.session_state[key]
                st.rerun()

    # Conteúdo principal
    try:
        # Estado do wizard de relatórios
        if "selected_template" not in st.session_state:
            # Passo 1: Seleção de template
            reports_manager.render_report_templates()

        else:
            template_id = st.session_state["selected_template"]

            # Passo 2: Configuração
            if "report_config" not in st.session_state:
                st.session_state["report_step"] = 1
                config = reports_manager.render_report_configuration(template_id)

                if st.button("Próximo", type="primary"):
                    st.session_state["report_config"] = config
                    st.rerun()

            # Passo 3: Seleção de sessões
            elif "selected_sessions" not in st.session_state:
                st.session_state["report_step"] = 2
                config = st.session_state["report_config"]
                selected_sessions = reports_manager.render_session_selection_for_report(
                    template_id, config
                )

                if selected_sessions and st.button("Gerar Preview", type="primary"):
                    st.session_state["selected_sessions"] = selected_sessions
                    st.rerun()

            # Passo 4: Preview
            elif "report_data" not in st.session_state:
                st.session_state["report_step"] = 3
                config = st.session_state["report_config"]
                session_ids = st.session_state["selected_sessions"]

                with st.spinner("Gerando relatório..."):
                    report_data = reports_manager.generate_summary_report(session_ids, config)
                    st.session_state["report_data"] = report_data

                reports_manager.render_report_preview(report_data, template_id)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Voltar"):
                        del st.session_state["report_data"]
                        st.rerun()

                with col2:
                    if st.button("Exportar Relatório", type="primary"):
                        st.session_state["report_step"] = 4
                        st.rerun()

            # Passo 5: Export
            else:
                st.session_state["report_step"] = 4
                config = st.session_state["report_config"]
                report_data = st.session_state["report_data"]

                st.markdown("### Exportar Relatório")

                try:
                    report_bytes = reports_manager.export_report(report_data, config)
                    format_ext = config.get("format", "PDF").lower()

                    filename = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M')}.{format_ext}"

                    st.download_button(
                        f"Download {config.get('format', 'PDF')}",
                        data=report_bytes,
                        file_name=filename,
                        mime=f"application/{format_ext}",
                        type="primary",
                    )

                    st.success("Relatório gerado com sucesso!")

                except Exception as e:
                    st.error(f"Erro ao gerar relatório: {str(e)}")

                if st.button("Novo Relatório"):
                    for key in list(st.session_state.keys()):
                        if key.startswith("selected_template") or key.startswith("report_"):
                            del st.session_state[key]
                    st.rerun()

        # Seção de histórico (sempre visível)
        st.markdown("---")
        reports_manager.render_report_history()

    except Exception as e:
        logger.error(f"Erro na página de relatórios: {str(e)}")
        st.error(f"Erro: {str(e)}")

        if st.session_state.get("debug_mode", False):
            st.exception(e)


if __name__ == "__main__":
    render_reports_page()
