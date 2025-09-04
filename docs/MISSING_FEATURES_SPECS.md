# 📋 ESPECIFICAÇÕES TÉCNICAS - Funcionalidades Faltantes

## 1. 🗺️ EDITOR DE MAPAS 2D/3D

### Requisitos Funcionais Detalhados

#### Editor 2D de Tabelas
- **Tamanhos Suportados:** 8x8, 16x16, 20x20, 32x32 células
- **Tipos de Mapas:**
  - Fuel Map (correção de combustível %)
  - Ignition Map (avanço de ignição em graus)
  - Boost Map (pressão alvo em bar)
  - Custom Maps (definidos pelo usuário)

#### Operações de Edição
```python
class MapOperations:
    def increment_cell(value, step=1.0)
    def decrement_cell(value, step=1.0)
    def increment_region(cells, step=1.0)
    def smooth_region(cells, intensity=0.5)
    def interpolate_region(cells, method='linear')
    def copy_region(cells)
    def paste_region(cells, target)
    def undo(history_stack)
    def redo(history_stack)
```

#### Algoritmo de Suavização 3D
```python
def gaussian_smooth_3d(map_data, sigma=1.0, preserve_edges=True):
    """
    Aplica suavização Gaussian preservando bordas
    
    Parameters:
    - map_data: numpy array 2D com valores do mapa
    - sigma: intensidade da suavização (0.5 a 2.0)
    - preserve_edges: mantém valores extremos
    
    Returns:
    - smoothed_map: mapa suavizado
    """
    kernel = gaussian_kernel(size=5, sigma=sigma)
    smoothed = convolve2d(map_data, kernel, mode='same')
    
    if preserve_edges:
        # Preserva bordas usando weighted average
        edge_weight = detect_edges(map_data)
        smoothed = weighted_average(map_data, smoothed, edge_weight)
    
    return smoothed
```

### Requisitos Técnicos

#### Componente Frontend
```python
# Opção 1: Streamlit AG-Grid
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

def render_map_editor(map_data):
    gb = GridOptionsBuilder.from_dataframe(map_data)
    gb.configure_default_column(editable=True, type="number")
    gb.configure_grid_options(
        enableRangeSelection=True,
        clipboardDelimiter="\t"  # FTManager compatibility
    )
    
    response = AgGrid(
        map_data,
        gridOptions=gb.build(),
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        theme='alpine'
    )
    
    return response['data']

# Opção 2: Componente React Customizado
# Desenvolver em TypeScript/React e integrar via Streamlit Components
```

#### Visualização 3D
```python
import plotly.graph_objects as go

def render_3d_map(map_data, x_axis, y_axis, title):
    fig = go.Figure(data=[
        go.Surface(
            x=x_axis,  # RPM values
            y=y_axis,  # MAP/TPS values
            z=map_data,
            colorscale='Jet',
            showscale=True,
            hovertemplate='RPM: %{x}<br>MAP: %{y}<br>Value: %{z:.2f}'
        )
    ])
    
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='RPM',
            yaxis_title='MAP (bar)',
            zaxis_title='Correction (%)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ),
        height=600
    )
    
    return fig
```

### Persistência e Versionamento

```python
class MapSnapshot:
    """Sistema de versionamento de mapas"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def save_snapshot(self, map_data, metadata):
        snapshot = {
            'id': uuid.uuid4(),
            'timestamp': datetime.now(),
            'map_type': metadata['type'],
            'map_data': map_data.to_json(),
            'checksum': calculate_checksum(map_data),
            'notes': metadata.get('notes', ''),
            'parent_id': metadata.get('parent_id')
        }
        
        self.db.execute("""
            INSERT INTO map_snapshots 
            (id, timestamp, map_type, data, checksum, notes, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, snapshot.values())
        
        return snapshot['id']
    
    def compare_snapshots(self, snapshot_a, snapshot_b):
        """Compara dois snapshots e retorna diff"""
        map_a = self.load_snapshot(snapshot_a)
        map_b = self.load_snapshot(snapshot_b)
        
        diff = map_b - map_a
        changes = {
            'total_cells': diff.size,
            'changed_cells': (diff != 0).sum(),
            'max_increase': diff.max(),
            'max_decrease': diff.min(),
            'average_change': diff.mean()
        }
        
        return diff, changes
```

## 2. 📊 SISTEMA DE ANÁLISE INTELIGENTE

### Segmentação por Estados do Motor

```python
class EngineStateSegmentation:
    """Classifica dados em estados operacionais"""
    
    STATES = {
        'idle': {'rpm': (600, 1200), 'tps': (0, 5), 'map': (-0.8, -0.4)},
        'cruise_low': {'rpm': (1200, 2500), 'tps': (5, 30), 'map': (-0.4, 0)},
        'cruise_mid': {'rpm': (2500, 4000), 'tps': (30, 50), 'map': (0, 0.5)},
        'cruise_high': {'rpm': (4000, 6000), 'tps': (50, 70), 'map': (0.5, 1.0)},
        'wot': {'rpm': (2000, 8000), 'tps': (70, 100), 'map': (0.8, 2.0)},
        'decel': {'rpm': (1500, 8000), 'tps': (0, 5), 'delta_tps': (-100, -10)},
        'transient': {'delta_tps': (10, 100)},
        'cranking': {'rpm': (0, 600), 'engine_state': 'cranking'}
    }
    
    def segment(self, data_frame):
        segments = {}
        
        for state, conditions in self.STATES.items():
            mask = pd.Series([True] * len(data_frame))
            
            for param, (min_val, max_val) in conditions.items():
                if param in data_frame.columns:
                    mask &= (data_frame[param] >= min_val) & (data_frame[param] <= max_val)
            
            segments[state] = data_frame[mask]
        
        return segments
```

### Binning MAP×RPM Adaptativo

```python
class AdaptiveBinning:
    """Cria grade adaptativa baseada na densidade de dados"""
    
    def __init__(self, min_points=10):
        self.min_points = min_points
    
    def create_bins(self, data, rpm_col='rpm', map_col='map'):
        # Análise de densidade usando KDE
        kde = gaussian_kde(data[[rpm_col, map_col]].T)
        
        # Define grade inicial
        rpm_edges = np.percentile(data[rpm_col], np.linspace(0, 100, 20))
        map_edges = np.percentile(data[map_col], np.linspace(0, 100, 16))
        
        # Refina onde há mais dados
        for i in range(len(rpm_edges)-1):
            for j in range(len(map_edges)-1):
                cell_data = data[
                    (data[rpm_col] >= rpm_edges[i]) & 
                    (data[rpm_col] < rpm_edges[i+1]) &
                    (data[map_col] >= map_edges[j]) & 
                    (data[map_col] < map_edges[j+1])
                ]
                
                if len(cell_data) < self.min_points:
                    # Merge com célula adjacente
                    pass
                elif len(cell_data) > self.min_points * 5:
                    # Split célula em 4
                    pass
        
        return rpm_edges, map_edges
```

### Sistema de Sugestões com Confidence Score

```python
class SuggestionEngine:
    """Gera sugestões de ajuste com confidence score"""
    
    def calculate_suggestions(self, binned_data, target_afr=14.7):
        suggestions = []
        
        for cell_id, cell_data in binned_data.items():
            if len(cell_data) < 10:
                continue  # Skip células com poucos dados
            
            # Calcula estatísticas
            afr_median = cell_data['afr'].median()
            afr_std = cell_data['afr'].std()
            o2_correction = cell_data['o2_correction'].median()
            
            # Calcula correção necessária
            afr_error = (target_afr - afr_median) / target_afr
            correction = afr_error * 100  # Em percentual
            
            # Calcula confidence score
            confidence = self._calculate_confidence(
                n_points=len(cell_data),
                std_dev=afr_std,
                o2_consistency=o2_correction
            )
            
            # Limita correção por segurança
            correction = np.clip(correction, -15, 15)
            
            suggestion = {
                'cell_id': cell_id,
                'current_afr': afr_median,
                'target_afr': target_afr,
                'correction_percent': correction,
                'confidence': confidence,
                'priority': abs(correction) * confidence,
                'n_samples': len(cell_data)
            }
            
            suggestions.append(suggestion)
        
        # Ordena por prioridade
        suggestions.sort(key=lambda x: x['priority'], reverse=True)
        
        return suggestions
    
    def _calculate_confidence(self, n_points, std_dev, o2_consistency):
        """Calcula confidence score de 0 a 1"""
        
        # Mais pontos = mais confiança
        points_score = min(n_points / 100, 1.0)
        
        # Menos desvio = mais confiança
        std_score = max(0, 1 - (std_dev / 2.0))
        
        # O2 consistente = mais confiança
        o2_score = max(0, 1 - abs(o2_consistency / 10))
        
        # Média ponderada
        confidence = (points_score * 0.4 + std_score * 0.3 + o2_score * 0.3)
        
        return round(confidence, 2)
```

## 3. 🔄 INTEGRAÇÃO FTMANAGER

### Bridge de Comunicação

```python
class FTManagerBridge:
    """Interface de comunicação com FTManager"""
    
    def __init__(self):
        self.clipboard = pyperclip
    
    def import_from_clipboard(self):
        """Importa tabela do FTManager via clipboard"""
        try:
            clipboard_data = self.clipboard.paste()
            
            # Detecta formato FTManager
            if self._is_ftmanager_format(clipboard_data):
                # Parse formato tab-delimited
                lines = clipboard_data.strip().split('\n')
                data = []
                
                for line in lines:
                    row = line.split('\t')
                    data.append([float(x) for x in row])
                
                return pd.DataFrame(data)
            
        except Exception as e:
            st.error(f"Erro ao importar: {e}")
            return None
    
    def export_to_clipboard(self, map_data):
        """Exporta tabela para FTManager via clipboard"""
        try:
            # Formata para FTManager (tab-delimited, 2 decimais)
            output = ""
            
            for _, row in map_data.iterrows():
                row_str = '\t'.join([f"{x:.2f}" for x in row])
                output += row_str + '\n'
            
            self.clipboard.copy(output.strip())
            st.success("✅ Copiado para clipboard! Cole no FTManager com Ctrl+V")
            
        except Exception as e:
            st.error(f"Erro ao exportar: {e}")
    
    def _is_ftmanager_format(self, data):
        """Detecta se é formato FTManager"""
        lines = data.strip().split('\n')
        if len(lines) < 8:  # Mínimo 8x8
            return False
        
        # Verifica se é tab-delimited com números
        first_line = lines[0].split('\t')
        try:
            [float(x) for x in first_line]
            return True
        except:
            return False
```

## 4. 📈 SISTEMA DE COMPARAÇÃO A/B

```python
class SessionComparison:
    """Compara múltiplas sessões de log"""
    
    def compare_sessions(self, session_a, session_b, metrics=['afr', 'power', 'torque']):
        comparison = {}
        
        for metric in metrics:
            if metric not in session_a.columns or metric not in session_b.columns:
                continue
            
            comparison[metric] = {
                'a_mean': session_a[metric].mean(),
                'b_mean': session_b[metric].mean(),
                'improvement': self._calculate_improvement(
                    session_a[metric], 
                    session_b[metric]
                ),
                'correlation': session_a[metric].corr(session_b[metric])
            }
        
        # Detecta melhorias automáticas
        improvements = self._detect_improvements(comparison)
        
        return comparison, improvements
    
    def _calculate_improvement(self, before, after):
        """Calcula percentual de melhoria"""
        before_avg = before.mean()
        after_avg = after.mean()
        
        if before_avg == 0:
            return 0
        
        improvement = ((after_avg - before_avg) / before_avg) * 100
        return round(improvement, 2)
    
    def _detect_improvements(self, comparison):
        """Detecta melhorias significativas"""
        improvements = []
        
        for metric, data in comparison.items():
            if data['improvement'] > 5:
                improvements.append({
                    'metric': metric,
                    'improvement': data['improvement'],
                    'significance': 'high' if data['improvement'] > 10 else 'medium'
                })
        
        return improvements
```

## 5. 🎯 INTERFACE DE USUÁRIO APRIMORADA

### Atalhos de Teclado
```python
KEYBOARD_SHORTCUTS = {
    'ctrl+z': 'undo',
    'ctrl+y': 'redo', 
    'ctrl+s': 'save_snapshot',
    'ctrl+c': 'copy_cells',
    'ctrl+v': 'paste_cells',
    'ctrl+a': 'select_all',
    '+': 'increment_cell',
    '-': 'decrement_cell',
    'shift++': 'increment_region',
    'shift+-': 'decrement_region',
    'ctrl+shift+s': 'smooth_region',
    'ctrl+i': 'interpolate',
    'f1': 'help',
    'f5': 'refresh',
    'f11': 'fullscreen'
}
```

### Componente de Dashboard Customizável
```python
class CustomizableDashboard:
    """Dashboard com layout drag-and-drop"""
    
    def __init__(self):
        self.layout = self._load_layout()
    
    def render(self):
        # Grid layout customizável
        cols = st.columns(self.layout['columns'])
        
        for i, col in enumerate(cols):
            with col:
                for widget in self.layout['widgets'][i]:
                    self._render_widget(widget)
    
    def _render_widget(self, widget):
        if widget['type'] == 'gauge':
            self._render_gauge(widget)
        elif widget['type'] == 'chart':
            self._render_chart(widget)
        elif widget['type'] == 'table':
            self._render_table(widget)
```

---

*Estas especificações servem como guia técnico para implementação das funcionalidades faltantes.*