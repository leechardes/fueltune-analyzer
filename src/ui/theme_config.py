"""
Configuração de Tema Profissional - FuelTune Analyzer
====================================================

Sistema de temas corporativo minimalista com Material Design Icons.
Desenvolvido pelo agente A04-STREAMLIT-PROFESSIONAL.

Author: A04-STREAMLIT-PROFESSIONAL Agent
Created: 2025-01-03
"""

from dataclasses import dataclass
from typing import Dict, Optional

import streamlit as st


@dataclass
class ThemeColors:
    """Definição das cores do tema corporativo."""
    
    # Primary Colors
    primary: str = "#1976D2"
    primary_light: str = "#42A5F5"
    primary_dark: str = "#1565C0"
    
    # Secondary Colors  
    secondary: str = "#37474F"
    secondary_light: str = "#546E7A"
    secondary_dark: str = "#263238"
    
    # Status Colors
    success: str = "#4CAF50"
    warning: str = "#FF9800"
    error: str = "#F44336"
    info: str = "#2196F3"
    
    # Neutral Colors
    gray_50: str = "#FAFAFA"
    gray_100: str = "#F5F5F5"
    gray_200: str = "#EEEEEE"
    gray_300: str = "#E0E0E0"
    gray_400: str = "#BDBDBD"
    gray_500: str = "#9E9E9E"
    gray_600: str = "#757575"
    gray_700: str = "#616161"
    gray_800: str = "#424242"
    gray_900: str = "#212121"
    
    # Text Colors
    text_primary: str = "#212529"
    text_secondary: str = "#6C757D"
    text_muted: str = "#ADB5BD"
    
    # Background Colors
    bg_primary: str = "#FFFFFF"
    bg_secondary: str = "#F8F9FA"
    bg_sidebar: str = "#FAFBFC"
    bg_card: str = "#FFFFFF"
    
    # Border and Shadows
    border_color: str = "#DEE2E6"
    shadow_sm: str = "0 2px 4px rgba(0,0,0,0.1)"
    shadow_md: str = "0 4px 6px rgba(0,0,0,0.1)"
    shadow_lg: str = "0 10px 15px rgba(0,0,0,0.1)"


class ProfessionalTheme:
    """Gerenciador de tema profissional corporativo."""
    
    def __init__(self, colors: Optional[ThemeColors] = None):
        self.colors = colors or ThemeColors()
        self.material_icons_loaded = False
    
    def inject_css(self) -> None:
        """Injetar CSS profissional na aplicação."""
        css = self._generate_professional_css()
        st.markdown(css, unsafe_allow_html=True)
        self.material_icons_loaded = True
    
    def _generate_professional_css(self) -> str:
        """Gerar CSS completo do tema profissional."""
        return f"""
        <!-- Material Design Icons -->
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        
        <style>
        :root {{
            --primary-color: {self.colors.primary};
            --primary-light: {self.colors.primary_light};
            --primary-dark: {self.colors.primary_dark};
            --secondary-color: {self.colors.secondary};
            --success-color: {self.colors.success};
            --warning-color: {self.colors.warning};
            --error-color: {self.colors.error};
            --info-color: {self.colors.info};
            --text-primary: {self.colors.text_primary};
            --text-secondary: {self.colors.text_secondary};
            --bg-primary: {self.colors.bg_primary};
            --bg-secondary: {self.colors.bg_secondary};
            --border-color: {self.colors.border_color};
            --shadow-sm: {self.colors.shadow_sm};
            --shadow-md: {self.colors.shadow_md};
        }}
        
        /* Material Icons */
        .material-icons {{
            font-family: 'Material Icons';
            font-weight: normal;
            font-style: normal;
            font-size: 24px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            vertical-align: middle;
        }}
        
        .material-icons-outlined {{
            font-family: 'Material Icons Outlined';
        }}
        
        /* Typography */
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            color: var(--text-primary);
            line-height: 1.4;
        }}
        
        /* Main Container */
        .main .block-container {{
            padding: 2rem 3rem;
            max-width: 1200px;
        }}
        
        /* Sidebar */
        .sidebar .sidebar-content {{
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
            box-shadow: var(--shadow-sm);
        }}
        
        .stButton > button:hover {{
            background-color: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }}
        
        .stButton > button:focus {{
            outline: none;
            box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.2);
        }}
        
        /* Alerts */
        div[data-testid="stAlert"] {{
            border-radius: 8px;
            border: none;
            box-shadow: var(--shadow-sm);
            padding: 1rem 1.5rem;
        }}
        
        div[data-testid="stAlert"][data-baseweb="notification"][kind="success"] {{
            background-color: #E8F5E8;
            border-left: 4px solid var(--success-color);
            color: #2E7D32;
        }}
        
        div[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {{
            background-color: #FFF3E0;
            border-left: 4px solid var(--warning-color);
            color: #F57C00;
        }}
        
        div[data-testid="stAlert"][data-baseweb="notification"][kind="error"] {{
            background-color: #FFEBEE;
            border-left: 4px solid var(--error-color);
            color: #C62828;
        }}
        
        div[data-testid="stAlert"][data-baseweb="notification"][kind="info"] {{
            background-color: #E3F2FD;
            border-left: 4px solid var(--info-color);
            color: #1565C0;
        }}
        
        /* Metrics */
        div[data-testid="metric-container"] {{
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: var(--shadow-sm);
            text-align: center;
        }}
        
        div[data-testid="metric-container"] > div:first-child {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}
        
        div[data-testid="metric-container"] > div:last-child {{
            color: var(--primary-dark);
            font-size: 2rem;
            font-weight: 700;
            line-height: 1;
        }}
        
        /* Expanders */
        .element-container div[data-testid="stExpander"] {{
            border: 1px solid var(--border-color);
            border-radius: 12px;
            box-shadow: var(--shadow-sm);
            background-color: var(--bg-primary);
            overflow: hidden;
        }}
        
        .element-container div[data-testid="stExpander"] > div:first-child {{
            background-color: var(--secondary-background-color);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 1.5rem;
        }}
        
        /* Input Fields */
        .stTextInput > div > div > input {{
            border: 1px solid {self.colors.gray_300};
            border-radius: 8px;
            padding: 0.75rem;
            transition: border-color 0.2s ease;
        }}
        
        .stTextInput > div > div > input:focus {{
            border-color: var(--primary-color);
            outline: none;
            box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
        }}
        
        /* Selectbox */
        .stSelectbox > div > div {{
            border: 1px solid {self.colors.gray_300};
            border-radius: 8px;
            background-color: var(--background-color);
        }}
        
        /* Progress Bar */
        .stProgress > div > div > div {{
            background-color: var(--primary-color);
            border-radius: 4px;
        }}
        
        /* Data Frames */
        div[data-testid="stDataFrame"] {{
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0;
            background-color: var(--secondary-background-color);
            border-radius: 12px;
            padding: 0.25rem;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            color: var(--text-secondary);
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: var(--background-color);
            color: var(--primary-color);
            box-shadow: var(--shadow-sm);
        }}
        
        /* Radio Buttons - for custom tab styling */
        .stRadio > div[role="radiogroup"] > label {{
            background-color: var(--secondary-background-color);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            margin: 0 0.25rem;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }}
        
        .stRadio > div[role="radiogroup"] > label[data-checked="true"] {{
            background-color: var(--primary-color);
            color: white;
            border-color: var(--primary-dark);
        }}
        
        /* Charts */
        .js-plotly-plot {{
            border-radius: 12px;
            box-shadow: var(--shadow-sm);
            overflow: hidden;
        }}
        
        /* Status Indicators */
        .status-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
        }}
        
        .status-success {{
            background-color: #E8F5E8;
            color: #2E7D32;
        }}
        
        .status-warning {{
            background-color: #FFF3E0;
            color: #F57C00;
        }}
        
        .status-error {{
            background-color: #FFEBEE;
            color: #C62828;
        }}
        
        .status-info {{
            background-color: #E3F2FD;
            color: #1565C0;
        }}
        
        /* Icon Buttons */
        .icon-button {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
        }}
        
        .icon-button:hover {{
            background-color: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }}
        
        .icon-button-secondary {{
            background-color: transparent;
            color: var(--primary-color);
            border: 1px solid var(--primary-color);
        }}
        
        .icon-button-secondary:hover {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .main .block-container {{
                padding: 1rem;
            }}
            
            .icon-button {{
                padding: 0.5rem 1rem;
                font-size: 0.875rem;
            }}
        }}
        
        /* Print Styles */
        @media print {{
            .sidebar,
            .stButton,
            .stDownloadButton {{
                display: none !important;
            }}
            
            .main .block-container {{
                padding: 0;
                max-width: none;
            }}
        }}
        </style>
        """
    
    def create_status_badge(self, status: str, text: str) -> str:
        """Criar badge de status com Material Icons."""
        icon_map = {
            "success": "check_circle",
            "warning": "warning", 
            "error": "error",
            "info": "info"
        }
        
        color_map = {
            "success": self.colors.success,
            "warning": self.colors.warning,
            "error": self.colors.error,
            "info": self.colors.info
        }
        
        icon = icon_map.get(status, "help")
        color = color_map.get(status, self.colors.gray_500)
        
        return f"""
        <div class="status-indicator status-{status}">
            <i class="material-icons" style="color: {color}; font-size: 1.1rem;">{icon}</i>
            <span>{text}</span>
        </div>
        """
    
    def create_icon_button(self, icon: str, text: str, secondary: bool = False) -> str:
        """Criar botão com Material Icon."""
        button_class = "icon-button-secondary" if secondary else "icon-button"
        
        return f"""
        <div class="{button_class}">
            <i class="material-icons">{icon}</i>
            <span>{text}</span>
        </div>
        """
    
    def create_section_header(self, icon: str, title: str, subtitle: str = "") -> str:
        """Criar cabeçalho de seção profissional."""
        subtitle_html = f'<p style="margin: 0.25rem 0 0 0; color: {self.colors.text_secondary};">{subtitle}</p>' if subtitle else ""
        
        return f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
            <i class="material-icons" style="font-size: 3rem; color: {self.colors.primary};">{icon}</i>
            <div>
                <h1 style="margin: 0; color: {self.colors.primary};">{title}</h1>
                {subtitle_html}
            </div>
        </div>
        """


# Instância global do tema
professional_theme = ProfessionalTheme()


def apply_professional_theme() -> None:
    """Aplicar tema profissional na aplicação atual."""
    professional_theme.inject_css()


def create_material_card(title: str, content: str, icon: str = "info") -> str:
    """Criar card profissional com Material Design."""
    return f"""
    <div style="
        background: var(--background-color); 
        border: 1px solid {professional_theme.colors.border_color}; 
        border-radius: 12px; 
        padding: 1.5rem; 
        box-shadow: {professional_theme.colors.shadow_sm};
        margin-bottom: 1rem;
    ">
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="material-icons" style="color: {professional_theme.colors.primary}; font-size: 1.5rem;">{icon}</i>
            <h3 style="margin: 0; color: {professional_theme.colors.primary};">{title}</h3>
        </div>
        <div style="color: {professional_theme.colors.text_primary};">
            {content}
        </div>
    </div>
    """