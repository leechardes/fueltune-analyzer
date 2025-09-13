"""
Componente para configuração de bancadas de injeção A/B.
Permite configurar modo de injeção, saídas, vazão e dead time.

Padrão: A04-STREAMLIT-PROFESSIONAL (ZERO emojis, Material Icons)
"""

import json
from typing import List, Optional

import streamlit as st

from src.data.database import get_database
from src.data.models import Vehicle
from src.utils.bank_calculations import (
    calculate_injector_dead_time_compensation,
    calculate_total_flow,
    compare_bank_configurations,
    recommend_injector_size,
    validate_bank_configuration,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BankConfigurator:
    """Configurador de bancadas de injeção."""

    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.db = get_database()

    def render_bank_config(self) -> None:
        """Renderiza interface completa de configuração de bancadas."""

        st.markdown(
            '<div class="main-header">'
            '<span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">settings</span>'
            "Configuração de Bancadas de Injeção"
            "</div>",
            unsafe_allow_html=True,
        )

        # Carregar dados do veículo
        vehicle = self._load_vehicle_data()
        if not vehicle:
            st.error("Veículo não encontrado")
            return

        # Layout em duas colunas
        col1, col2 = st.columns(2)

        # Configuração Bancada A
        with col1:
            self._render_bank_a_config(vehicle)

        # Configuração Bancada B
        with col2:
            self._render_bank_b_config(vehicle)

        # Resumo e validações
        st.markdown("---")
        self._render_configuration_summary(vehicle)

        # Botões de ação
        self._render_action_buttons(vehicle)

    def _render_bank_a_config(self, vehicle: Vehicle) -> None:
        """Renderiza configuração da Bancada A."""

        st.markdown(
            '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">electrical_services</span>Bancada A (Principal)</h3>',
            unsafe_allow_html=True,
        )

        # Bancada A sempre ativa
        st.info("A Bancada A é sempre ativa (principal) e não pode ser desabilitada")

        # Modo de injeção
        bank_a_mode = st.selectbox(
            "Modo de Injeção A",
            options=["multiponto", "semissequencial", "sequencial"],
            index=self._get_mode_index(vehicle.bank_a_mode or "semissequencial"),
            key="bank_a_mode",
            help="Multiponto: todos injetores simultaneamente | Semissequencial: aos pares | Sequencial: individual sincronizado",
        )

        # Saídas disponíveis
        available_outputs = list(range(1, 9))  # Saídas 1 a 8
        bank_a_outputs = st.multiselect(
            "Saídas Utilizadas A",
            options=available_outputs,
            default=self._parse_outputs(vehicle.bank_a_outputs) or [1, 2, 3, 4],
            key="bank_a_outputs",
            help="Selecione as saídas da ECU conectadas aos injetores da Bancada A",
        )

        # Configuração dos injetores
        col_a1, col_a2 = st.columns(2)

        with col_a1:
            bank_a_flow = st.number_input(
                "Vazão por Injetor A (lb/h)",
                min_value=10.0,
                max_value=2000.0,
                value=float(vehicle.bank_a_injector_flow or 80.0),
                step=5.0,
                key="bank_a_flow",
                help="Vazão individual de cada injetor em libras por hora",
            )

        with col_a2:
            bank_a_count = st.number_input(
                "Quantidade de Injetores A",
                min_value=1,
                max_value=8,
                value=int(vehicle.bank_a_injector_count or len(bank_a_outputs or [4])),
                key="bank_a_count",
                help="Número total de injetores na Bancada A",
            )

        # Vazão total calculada
        total_flow_a = calculate_total_flow(bank_a_flow, bank_a_count)
        st.metric(
            "Vazão Total Bancada A",
            f"{total_flow_a:.1f} lb/h",
            help="Vazão total da bancada (vazão por injetor × quantidade)",
        )

        # Dead time
        bank_a_dead_time = st.number_input(
            "Dead Time Bancada A (ms)",
            min_value=0.1,
            max_value=10.0,
            value=float(vehicle.bank_a_dead_time or 1.0),
            step=0.1,
            key="bank_a_dead_time",
            help="Compensação de tempo de resposta dos injetores",
        )

        # Calculadora de dead time
        if st.button(":material/calculate: Calcular Dead Time Automático", key="calc_dead_time_a"):
            voltage = st.session_state.get("system_voltage", 12.0)
            auto_dead_time = calculate_injector_dead_time_compensation(voltage, "standard")
            st.session_state["bank_a_dead_time"] = auto_dead_time
            st.success(f"Dead time calculado: {auto_dead_time:.2f}ms")

        # Validações da bancada A
        bank_a_config = {
            "enabled": True,
            "mode": bank_a_mode,
            "outputs": bank_a_outputs,
            "injector_flow": bank_a_flow,
            "injector_count": bank_a_count,
            "dead_time": bank_a_dead_time,
        }

        validations_a = validate_bank_configuration(bank_a_config)

        with st.expander("Validações Bancada A"):
            for validation in validations_a:
                if validation["status"] == "OK":
                    st.success(f"✓ {validation['message']}")
                elif validation["status"] == "WARNING":
                    st.warning(f"⚠ {validation['message']}")
                elif validation["status"] == "ERROR":
                    st.error(f"✗ {validation['message']}")
                else:  # INFO
                    st.info(f"ⓘ {validation['message']}")

        # Salvar configurações da Bancada A
        if st.button(":material/save: Salvar Bancada A", key="save_bank_a"):
            self._save_bank_a_config(
                vehicle, bank_a_mode, bank_a_outputs, bank_a_flow, bank_a_count, bank_a_dead_time
            )

    def _render_bank_b_config(self, vehicle: Vehicle) -> None:
        """Renderiza configuração da Bancada B."""

        st.markdown(
            '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">power</span>Bancada B (Auxiliar)</h3>',
            unsafe_allow_html=True,
        )

        # Habilitar/Desabilitar Bancada B
        bank_b_enabled = st.checkbox(
            "Habilitar Bancada B",
            value=vehicle.bank_b_enabled or False,
            key="bank_b_enabled",
            help="Ativar bancada auxiliar para sistemas duplos de injeção",
        )

        if not bank_b_enabled:
            st.info("Bancada B desabilitada. Ative acima para configurar sistema duplo.")
            return

        # Configurações da Bancada B (similares à A)
        bank_b_mode = st.selectbox(
            "Modo de Injeção B",
            options=["multiponto", "semissequencial", "sequencial"],
            index=self._get_mode_index(vehicle.bank_b_mode or "semissequencial"),
            key="bank_b_mode",
            help="Modo de operação da bancada auxiliar",
        )

        # Saídas disponíveis (excluindo as já usadas pela Bancada A)
        bank_a_outputs = self._parse_outputs(vehicle.bank_a_outputs) or []
        available_for_b = [x for x in range(1, 9) if x not in bank_a_outputs]

        if not available_for_b:
            st.error("Nenhuma saída disponível para Bancada B. Revise configuração da Bancada A.")
            return

        bank_b_outputs = st.multiselect(
            "Saídas Utilizadas B",
            options=available_for_b,
            default=self._parse_outputs(vehicle.bank_b_outputs) or available_for_b[:2],
            key="bank_b_outputs",
            help="Saídas restantes não utilizadas pela Bancada A",
        )

        # Configuração dos injetores B
        col_b1, col_b2 = st.columns(2)

        with col_b1:
            bank_b_flow = st.number_input(
                "Vazão por Injetor B (lb/h)",
                min_value=10.0,
                max_value=2000.0,
                value=float(vehicle.bank_b_injector_flow or 80.0),
                step=5.0,
                key="bank_b_flow",
                help="Vazão individual de cada injetor da bancada B",
            )

        with col_b2:
            bank_b_count = st.number_input(
                "Quantidade de Injetores B",
                min_value=1,
                max_value=8,
                value=int(vehicle.bank_b_injector_count or len(bank_b_outputs or [2])),
                key="bank_b_count",
                help="Número total de injetores na Bancada B",
            )

        # Vazão total B
        total_flow_b = calculate_total_flow(bank_b_flow, bank_b_count)
        st.metric(
            "Vazão Total Bancada B",
            f"{total_flow_b:.1f} lb/h",
            help="Vazão total da bancada auxiliar",
        )

        # Dead time B
        bank_b_dead_time = st.number_input(
            "Dead Time Bancada B (ms)",
            min_value=0.1,
            max_value=10.0,
            value=float(vehicle.bank_b_dead_time or 1.0),
            step=0.1,
            key="bank_b_dead_time",
            help="Compensação de tempo de resposta dos injetores B",
        )

        # Configuração de staging (quando B entra em ação)
        st.markdown("**Configuração de Staging:**")

        col_staging1, col_staging2 = st.columns(2)

        with col_staging1:
            staging_tps = st.number_input(
                "TPS para ativar B (%)",
                min_value=0.0,
                max_value=100.0,
                value=50.0,
                step=5.0,
                key="staging_tps",
                help="Posição do acelerador para ativar bancada B",
            )

        with col_staging2:
            staging_map = st.number_input(
                "MAP para ativar B (bar)",
                min_value=-1.0,
                max_value=3.0,
                value=0.5,
                step=0.1,
                key="staging_map",
                help="Pressão MAP para ativar bancada B",
            )

        # Validações da bancada B
        bank_b_config = {
            "enabled": bank_b_enabled,
            "mode": bank_b_mode,
            "outputs": bank_b_outputs,
            "injector_flow": bank_b_flow,
            "injector_count": bank_b_count,
            "dead_time": bank_b_dead_time,
        }

        validations_b = validate_bank_configuration(bank_b_config)

        with st.expander("Validações Bancada B"):
            for validation in validations_b:
                if validation["status"] == "OK":
                    st.success(f"✓ {validation['message']}")
                elif validation["status"] == "WARNING":
                    st.warning(f"⚠ {validation['message']}")
                elif validation["status"] == "ERROR":
                    st.error(f"✗ {validation['message']}")
                else:  # INFO
                    st.info(f"ⓘ {validation['message']}")

        # Salvar Bancada B
        if st.button(":material/save: Salvar Bancada B", key="save_bank_b"):
            self._save_bank_b_config(
                vehicle,
                bank_b_enabled,
                bank_b_mode,
                bank_b_outputs,
                bank_b_flow,
                bank_b_count,
                bank_b_dead_time,
            )

    def _render_configuration_summary(self, vehicle: Vehicle) -> None:
        """Renderiza resumo da configuração atual."""

        st.markdown(
            '<h3><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">analytics</span>Resumo da Configuração</h3>',
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)

        # Métricas básicas
        with col1:
            outputs_a_count = len(self._parse_outputs(vehicle.bank_a_outputs) or [])
            st.metric("Saídas Bancada A", outputs_a_count)

        with col2:
            outputs_b_count = (
                len(self._parse_outputs(vehicle.bank_b_outputs) or [])
                if vehicle.bank_b_enabled
                else 0
            )
            st.metric("Saídas Bancada B", outputs_b_count)

        with col3:
            total_a = calculate_total_flow(
                vehicle.bank_a_injector_flow or 0, vehicle.bank_a_injector_count or 0
            )
            total_b = (
                calculate_total_flow(
                    vehicle.bank_b_injector_flow or 0, vehicle.bank_b_injector_count or 0
                )
                if vehicle.bank_b_enabled
                else 0
            )

            st.metric("Vazão Total Sistema", f"{total_a + total_b:.1f} lb/h")

        with col4:
            # Verificar conflitos de saídas
            conflicts = self._check_output_conflicts(vehicle)
            status_color = "red" if len(conflicts) > 0 else "green"
            st.markdown(
                f'<div style="text-align: center;">'
                f'<div style="font-size: 1.2rem; color: {status_color}; font-weight: bold;">'
                f'{"ERRO" if conflicts else "OK"}'
                f"</div>"
                f'<div style="font-size: 0.8rem; color: gray;">Conflitos</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Comparação entre bancadas
        if vehicle.bank_b_enabled:
            bank_a_config = {
                "enabled": True,
                "mode": vehicle.bank_a_mode,
                "outputs": self._parse_outputs(vehicle.bank_a_outputs),
                "injector_flow": vehicle.bank_a_injector_flow or 0,
                "injector_count": vehicle.bank_a_injector_count or 0,
                "dead_time": vehicle.bank_a_dead_time or 0,
            }

            bank_b_config = {
                "enabled": vehicle.bank_b_enabled,
                "mode": vehicle.bank_b_mode,
                "outputs": self._parse_outputs(vehicle.bank_b_outputs),
                "injector_flow": vehicle.bank_b_injector_flow or 0,
                "injector_count": vehicle.bank_b_injector_count or 0,
                "dead_time": vehicle.bank_b_dead_time or 0,
            }

            comparisons = compare_bank_configurations(bank_a_config, bank_b_config)

            st.markdown("**Comparação entre Bancadas:**")
            for comparison in comparisons:
                if comparison["status"] == "OK":
                    st.success(f"✓ {comparison['message']}")
                elif comparison["status"] == "WARNING":
                    st.warning(f"⚠ {comparison['message']}")
                elif comparison["status"] == "ERROR":
                    st.error(f"✗ {comparison['message']}")
                else:  # INFO
                    st.info(f"ⓘ {comparison['message']}")

        # Exibir conflitos se houver
        if conflicts:
            st.error(f"Conflitos detectados nas saídas: {', '.join(map(str, conflicts))}")

    def _render_action_buttons(self, vehicle: Vehicle) -> None:
        """Renderiza botões de ação."""

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(":material/content_copy: Duplicar Mapas", key="duplicate_maps"):
                self._duplicate_maps_for_banks(vehicle)

        with col2:
            if st.button(":material/sync: Sincronizar A→B", key="sync_a_to_b"):
                self._sync_bank_a_to_b(vehicle)

        with col3:
            if st.button(":material/refresh: Recalcular Vazões", key="recalculate"):
                self._recalculate_flows(vehicle)

        with col4:
            if st.button(
                ":material/settings_backup_restore: Configuração Padrão", key="restore_default"
            ):
                self._restore_default_config(vehicle)

        # Calculadora de injetores
        st.markdown("---")
        with st.expander(":material/calculate: Calculadora de Injetores"):
            self._render_injector_calculator()

    def _render_injector_calculator(self) -> None:
        """Renderiza calculadora de injetores."""

        st.markdown("**Calculadora de Tamanho de Injetores:**")

        col_calc1, col_calc2, col_calc3 = st.columns(3)

        with col_calc1:
            target_power = st.number_input(
                "Potência Alvo (HP)",
                min_value=50.0,
                max_value=2000.0,
                value=300.0,
                step=25.0,
                key="calc_target_power",
            )

        with col_calc2:
            cylinders = st.selectbox(
                "Número de Cilindros", options=[4, 6, 8, 10, 12], index=0, key="calc_cylinders"
            )

        with col_calc3:
            num_banks = st.selectbox(
                "Número de Bancadas", options=[1, 2], index=0, key="calc_num_banks"
            )

        if st.button(":material/calculate: Calcular Recomendação", key="calc_injector_size"):
            recommendation = recommend_injector_size(target_power, cylinders, num_banks=num_banks)

            if "error" not in recommendation:
                st.success("Recomendação calculada:")

                rec_col1, rec_col2 = st.columns(2)

                with rec_col1:
                    st.metric(
                        "Injetor Recomendado",
                        f"{recommendation['recommended_injector_size_lb_h']:.0f} lb/h",
                    )
                    st.metric("Injetores por Bancada", f"{recommendation['injectors_per_bank']}")
                    st.metric(
                        "Potência Máxima Real", f"{recommendation['actual_max_power_hp']:.0f} HP"
                    )

                with rec_col2:
                    st.metric("Vazão Total", f"{recommendation['actual_total_flow_lb_h']:.0f} lb/h")
                    st.metric(
                        "Margem de Segurança", f"{recommendation['safety_margin_percent']:.1f}%"
                    )
                    st.metric("Duty Cycle Máximo", f"{recommendation['max_duty_percent']:.0f}%")
            else:
                st.error(recommendation["error"])

    # Métodos auxiliares
    def _load_vehicle_data(self) -> Optional[Vehicle]:
        """Carrega dados do veículo."""
        db_session = self.db.get_session()
        try:
            return db_session.query(Vehicle).filter(Vehicle.id == self.vehicle_id).first()
        finally:
            db_session.close()

    def _get_mode_index(self, mode: str) -> int:
        """Retorna índice do modo na lista."""
        modes = ["multiponto", "semissequencial", "sequencial"]
        try:
            return modes.index(mode)
        except ValueError:
            return 1  # Padrão: semissequencial

    def _parse_outputs(self, outputs_json) -> List[int]:
        """Parseia JSON de saídas."""
        if not outputs_json:
            return []
        try:
            if isinstance(outputs_json, str):
                return json.loads(outputs_json)
            elif isinstance(outputs_json, list):
                return outputs_json
            else:
                return []
        except:
            return []

    def _check_output_conflicts(self, vehicle: Vehicle) -> List[int]:
        """Verifica conflitos entre saídas das bancadas."""
        outputs_a = set(self._parse_outputs(vehicle.bank_a_outputs) or [])
        outputs_b = set(self._parse_outputs(vehicle.bank_b_outputs) or [])

        if not vehicle.bank_b_enabled:
            return []

        return list(outputs_a.intersection(outputs_b))

    def _save_bank_a_config(
        self,
        vehicle: Vehicle,
        mode: str,
        outputs: List[int],
        flow: float,
        count: int,
        dead_time: float,
    ) -> None:
        """Salva configuração da Bancada A."""
        db_session = self.db.get_session()
        try:
            vehicle.bank_a_mode = mode
            vehicle.bank_a_outputs = json.dumps(outputs)
            vehicle.bank_a_injector_flow = flow
            vehicle.bank_a_injector_count = count
            vehicle.bank_a_total_flow = calculate_total_flow(flow, count)
            vehicle.bank_a_dead_time = dead_time

            # Atualizar timestamp
            vehicle.update_calculated_flows()

            db_session.commit()
            st.success("Configuração da Bancada A salva com sucesso!")

        except Exception as e:
            db_session.rollback()
            st.error(f"Erro ao salvar Bancada A: {str(e)}")
            logger.error(f"Erro ao salvar bancada A para veículo {self.vehicle_id}: {str(e)}")
        finally:
            db_session.close()

    def _save_bank_b_config(
        self,
        vehicle: Vehicle,
        enabled: bool,
        mode: str,
        outputs: List[int],
        flow: float,
        count: int,
        dead_time: float,
    ) -> None:
        """Salva configuração da Bancada B."""
        db_session = self.db.get_session()
        try:
            vehicle.bank_b_enabled = enabled
            vehicle.bank_b_mode = mode
            vehicle.bank_b_outputs = json.dumps(outputs)
            vehicle.bank_b_injector_flow = flow
            vehicle.bank_b_injector_count = count
            vehicle.bank_b_total_flow = calculate_total_flow(flow, count) if enabled else 0
            vehicle.bank_b_dead_time = dead_time

            # Atualizar vazões calculadas
            vehicle.update_calculated_flows()

            db_session.commit()
            st.success("Configuração da Bancada B salva com sucesso!")

        except Exception as e:
            db_session.rollback()
            st.error(f"Erro ao salvar Bancada B: {str(e)}")
            logger.error(f"Erro ao salvar bancada B para veículo {self.vehicle_id}: {str(e)}")
        finally:
            db_session.close()

    def _duplicate_maps_for_banks(self, vehicle: Vehicle) -> None:
        """Duplica mapas para ambas bancadas."""
        st.info("Funcionalidade de duplicação de mapas será implementada na próxima fase")

    def _sync_bank_a_to_b(self, vehicle: Vehicle) -> None:
        """Sincroniza configuração da bancada A para B."""
        if not vehicle.bank_b_enabled:
            st.warning("Bancada B não está habilitada")
            return

        db_session = self.db.get_session()
        try:
            # Copiar configurações da A para B (exceto saídas)
            vehicle.bank_b_mode = vehicle.bank_a_mode
            vehicle.bank_b_injector_flow = vehicle.bank_a_injector_flow
            vehicle.bank_b_injector_count = vehicle.bank_a_injector_count
            vehicle.bank_b_dead_time = vehicle.bank_a_dead_time

            # Recalcular vazão B
            vehicle.update_calculated_flows()

            db_session.commit()
            st.success("Configuração sincronizada de A → B!")
            st.rerun()

        except Exception as e:
            db_session.rollback()
            st.error(f"Erro na sincronização: {str(e)}")
        finally:
            db_session.close()

    def _recalculate_flows(self, vehicle: Vehicle) -> None:
        """Recalcula vazões das bancadas."""
        db_session = self.db.get_session()
        try:
            vehicle.update_calculated_flows()
            db_session.commit()
            st.success("Vazões recalculadas com sucesso!")
            st.rerun()

        except Exception as e:
            db_session.rollback()
            st.error(f"Erro no recálculo: {str(e)}")
        finally:
            db_session.close()

    def _restore_default_config(self, vehicle: Vehicle) -> None:
        """Restaura configuração padrão das bancadas."""
        if st.checkbox("Confirmar restauração (irá sobrescrever configurações atuais)"):
            db_session = self.db.get_session()
            try:
                # Configuração padrão bancada A
                vehicle.bank_a_enabled = True
                vehicle.bank_a_mode = "semissequencial"
                vehicle.bank_a_outputs = json.dumps([1, 2, 3, 4])
                vehicle.bank_a_injector_flow = 80.0
                vehicle.bank_a_injector_count = 4
                vehicle.bank_a_dead_time = 1.0

                # Configuração padrão bancada B (desabilitada)
                vehicle.bank_b_enabled = False
                vehicle.bank_b_mode = "semissequencial"
                vehicle.bank_b_outputs = json.dumps([5, 6])
                vehicle.bank_b_injector_flow = 80.0
                vehicle.bank_b_injector_count = 2
                vehicle.bank_b_dead_time = 1.0

                # Recalcular vazões
                vehicle.update_calculated_flows()

                db_session.commit()
                st.success("Configuração padrão restaurada!")
                st.rerun()

            except Exception as e:
                db_session.rollback()
                st.error(f"Erro na restauração: {str(e)}")
            finally:
                db_session.close()
