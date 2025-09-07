"""
Componente para seleção de bancada ativa na interface.
Permite alternar entre bancadas A/B nos editores de mapas.

Padrão: A04-STREAMLIT-PROFESSIONAL (ZERO emojis, Material Icons)
"""

import streamlit as st
from typing import Optional


class BankSelector:
    """Seletor de bancada para interface de mapas."""
    
    @staticmethod
    def render_bank_selector(vehicle_has_bank_b: bool, key_prefix: str = "") -> str:
        """
        Renderiza seletor de bancada.
        
        Args:
            vehicle_has_bank_b: Se veículo tem bancada B habilitada
            key_prefix: Prefixo para keys únicos
        
        Returns:
            Bancada selecionada ('A' ou 'B')
        """
        if not vehicle_has_bank_b:
            st.info("Veículo configurado apenas com Bancada A")
            return 'A'
        
        st.markdown(
            '<h4><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem;">electrical_services</span>Selecionar Bancada</h4>',
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        
        # Estado atual da seleção
        current_bank = st.session_state.get(f"{key_prefix}_selected_bank", 'A')
        
        with col1:
            bank_a_selected = st.button(
                ":material/electrical_services: Bancada A (Principal)",
                key=f"{key_prefix}_bank_a",
                use_container_width=True,
                type="primary" if current_bank == 'A' else "secondary",
                help="Selecionar bancada principal de injeção"
            )
        
        with col2:
            bank_b_selected = st.button(
                ":material/power: Bancada B (Auxiliar)",
                key=f"{key_prefix}_bank_b",
                use_container_width=True,
                type="primary" if current_bank == 'B' else "secondary",
                help="Selecionar bancada auxiliar de injeção"
            )
        
        # Atualizar seleção
        if bank_a_selected:
            st.session_state[f"{key_prefix}_selected_bank"] = 'A'
            current_bank = 'A'
        elif bank_b_selected:
            st.session_state[f"{key_prefix}_selected_bank"] = 'B'
            current_bank = 'B'
        
        # Indicador visual da bancada selecionada
        bank_info = {
            'A': {
                'name': 'Bancada A (Principal)',
                'description': 'Bancada principal sempre ativa',
                'color': '#1f77b4'
            },
            'B': {
                'name': 'Bancada B (Auxiliar)',
                'description': 'Bancada auxiliar para sistemas duplos',
                'color': '#ff7f0e'
            }
        }
        
        selected_info = bank_info[current_bank]
        
        st.markdown(
            f'<div style="'
            f'border-left: 4px solid {selected_info["color"]}; '
            f'padding: 10px; '
            f'background-color: var(--background-color); '
            f'margin: 10px 0; '
            f'border-radius: 0 5px 5px 0;'
            f'">'
            f'<strong style="color: {selected_info["color"]};">{selected_info["name"]}</strong><br>'
            f'<small style="color: var(--text-secondary);">{selected_info["description"]}</small>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        return current_bank
    
    @staticmethod
    def render_bank_tabs(vehicle_has_bank_b: bool, key_prefix: str = "") -> str:
        """
        Renderiza seletor de bancada em formato de tabs.
        
        Args:
            vehicle_has_bank_b: Se veículo tem bancada B habilitada
            key_prefix: Prefixo para keys únicos
        
        Returns:
            Bancada selecionada ('A' ou 'B')
        """
        if not vehicle_has_bank_b:
            st.info("Operando com Bancada A apenas")
            return 'A'
        
        # Criar tabs para as bancadas
        tab_names = ["Bancada A", "Bancada B"]
        tabs = st.tabs(tab_names)
        
        # Armazenar qual tab está ativa no session state
        selected_tab = st.session_state.get(f"{key_prefix}_active_tab", 0)
        
        # Determinar bancada baseada na tab ativa
        # Nota: Streamlit tabs não permite detectar qual está ativa programaticamente
        # então usamos o seletor de botões como fallback
        return BankSelector.render_bank_selector(vehicle_has_bank_b, key_prefix)
    
    @staticmethod
    def render_compact_selector(vehicle_has_bank_b: bool, key_prefix: str = "") -> str:
        """
        Renderiza seletor compacto de bancada para uso em sidebars.
        
        Args:
            vehicle_has_bank_b: Se veículo tem bancada B habilitada
            key_prefix: Prefixo para keys únicos
        
        Returns:
            Bancada selecionada ('A' ou 'B')
        """
        if not vehicle_has_bank_b:
            st.markdown("**Bancada:** A (única)")
            return 'A'
        
        selected_bank = st.radio(
            "Bancada Ativa:",
            options=['A', 'B'],
            index=0 if st.session_state.get(f"{key_prefix}_selected_bank", 'A') == 'A' else 1,
            key=f"{key_prefix}_compact_bank_selector",
            horizontal=True,
            help="Selecionar bancada para editar mapas"
        )
        
        # Sincronizar com o session state principal
        st.session_state[f"{key_prefix}_selected_bank"] = selected_bank
        
        # Mostrar informação da bancada selecionada
        if selected_bank == 'A':
            st.markdown("🔵 **Principal** - Sempre ativa")
        else:
            st.markdown("🟠 **Auxiliar** - Para sistemas duplos")
        
        return selected_bank
    
    @staticmethod
    def get_selected_bank(key_prefix: str = "") -> str:
        """
        Retorna bancada selecionada no session state.
        
        Args:
            key_prefix: Prefixo para keys únicos
            
        Returns:
            Bancada selecionada ('A' ou 'B')
        """
        return st.session_state.get(f"{key_prefix}_selected_bank", 'A')
    
    @staticmethod
    def set_selected_bank(bank_id: str, key_prefix: str = "") -> None:
        """
        Define bancada selecionada no session state.
        
        Args:
            bank_id: ID da bancada ('A' ou 'B')
            key_prefix: Prefixo para keys únicos
        """
        if bank_id in ['A', 'B']:
            st.session_state[f"{key_prefix}_selected_bank"] = bank_id
    
    @staticmethod
    def clear_selection(key_prefix: str = "") -> None:
        """
        Limpa seleção de bancada do session state.
        
        Args:
            key_prefix: Prefixo para keys únicos
        """
        if f"{key_prefix}_selected_bank" in st.session_state:
            del st.session_state[f"{key_prefix}_selected_bank"]
    
    @staticmethod
    def render_bank_status_indicator(vehicle_has_bank_b: bool, key_prefix: str = "") -> None:
        """
        Renderiza indicador de status das bancadas.
        
        Args:
            vehicle_has_bank_b: Se veículo tem bancada B habilitada
            key_prefix: Prefixo para keys únicos
        """
        selected_bank = BankSelector.get_selected_bank(key_prefix)
        
        st.markdown("#### Status das Bancadas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            status_a = "🟢 ATIVA" if selected_bank == 'A' else "⚪ DISPONÍVEL"
            st.markdown(f"**Bancada A (Principal):** {status_a}")
        
        with col2:
            if vehicle_has_bank_b:
                status_b = "🟢 ATIVA" if selected_bank == 'B' else "⚪ DISPONÍVEL" 
                st.markdown(f"**Bancada B (Auxiliar):** {status_b}")
            else:
                st.markdown("**Bancada B:** ❌ DESABILITADA")
    
    @staticmethod
    def render_bank_warning_if_needed(vehicle_has_bank_b: bool, selected_bank: str) -> None:
        """
        Renderiza avisos específicos baseados na bancada selecionada.
        
        Args:
            vehicle_has_bank_b: Se veículo tem bancada B habilitada
            selected_bank: Bancada atualmente selecionada
        """
        if selected_bank == 'B' and not vehicle_has_bank_b:
            st.error(
                "Bancada B selecionada mas não está habilitada no veículo. "
                "Verifique a configuração das bancadas primeiro."
            )
            return
        
        if selected_bank == 'B' and vehicle_has_bank_b:
            st.info(
                "Editando mapas da Bancada B (auxiliar). "
                "Certifique-se de que as configurações de staging estão corretas."
            )
        elif selected_bank == 'A':
            st.info(
                "Editando mapas da Bancada A (principal). "
                "Esta bancada está sempre ativa durante o funcionamento."
            )