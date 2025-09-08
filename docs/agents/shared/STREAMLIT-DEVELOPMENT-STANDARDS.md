# STREAMLIT DEVELOPMENT STANDARDS

## 📋 Objetivo
Este documento define os padrões de desenvolvimento para aplicações Streamlit profissionais, incluindo diretrizes de UI/UX, mapeamentos de ícones, traduções e boas práticas de CSS adaptativo.

## 🎯 Princípios Fundamentais

### 1. Interface Profissional
- **Substituir TODOS emojis por Material Design Icons** (remover só se impossível)
- **CSS adaptativo que funciona em tema claro E escuro automaticamente**
- **NUNCA usar !important no CSS** para permitir adaptação de temas
- **Usar variáveis CSS dinâmicas** que respondem ao tema do Streamlit

### 2. Consistência Visual
- Todos os headers devem ter Material Icons
- Todos os botões devem usar sintaxe `:material/icon:`
- Métricas devem usar `create_metric_card` com ícone à direita
- Interface 100% em português brasileiro

## ⚠️ ERROS CRÍTICOS - NUNCA COMETER

### ❌ PROIBIDO - Causará erros no Streamlit:
```python
# ERRO 1: st.success/error/warning/info NÃO suportam HTML
st.success("<span class='material-icons'>check</span> Texto", unsafe_allow_html=True)  # ERRO!
st.error("❌ Erro", unsafe_allow_html=True)  # ERRO!

# ERRO 2: st.metric não suporta HTML no label
st.metric(label="<span>CPU</span>", value="50%")  # ERRO!

# ERRO 3: Emojis Unicode em qualquer lugar
st.write("✅ Sucesso")  # PROIBIDO!

# ERRO 4: st.expander não suporta HTML
st.expander("<span class='material-icons'>add</span>Adicionar")  # ERRO!
```

### ✅ CORRETO - Maneiras apropriadas:
```python
# CORRETO 1: Mensagens de status sem HTML
st.success("Operação concluída com sucesso")
st.error("Erro ao processar")
st.warning("Atenção: limite atingido")
st.info("Processando...")

# CORRETO 2: Para usar ícones em mensagens, converter para markdown
st.markdown('<div style="padding: 0.5rem; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 0.25rem; color: #155724;"><span class="material-icons" style="vertical-align: middle;">check_circle</span> Sucesso</div>', unsafe_allow_html=True)

# CORRETO 3: Métricas com ícones via create_metric_card
from components.metrics import create_metric_card
create_metric_card("CPU", "50%", icon="memory")

# CORRETO 4: Botões com Material Icons nativos
st.button(":material/save: Salvar")

# CORRETO 5: Expander sem HTML
st.expander("Detalhes")
```

## 📊 MAPEAMENTO COMPLETO EMOJI → MATERIAL ICON

```python
EMOJI_TO_MATERIAL = {
    # === AÇÕES E CONTROLES ===
    '🔄': 'refresh',          # Atualizar/Recarregar
    '✅': 'check_circle',     # Sucesso/Completo
    '❌': 'cancel',           # Erro/Cancelar
    '🔴': 'error',            # Erro crítico/Parar
    '⚠️': 'warning',         # Aviso
    '⚠': 'warning',          # Aviso (sem variação)
    '⏰': 'alarm',            # Alarme/Timer
    '⏱️': 'timer',           # Cronômetro
    '⏱': 'timer',            # Cronômetro (sem variação)
    '▶️': 'play_arrow',      # Play/Iniciar
    '⏹️': 'stop',            # Parar
    '➕': 'add',              # Adicionar
    '➖': 'remove',           # Remover
    '⬇️': 'download',        # Download
    '♻️': 'recycling',       # Reciclar/Loop
    
    # === ARQUIVOS E DOCUMENTOS ===
    '📄': 'description',      # Arquivo/Documento
    '📋': 'assignment',       # Lista/Clipboard
    '📝': 'edit_note',        # Editar/Escrever
    '📖': 'menu_book',        # Documentação/Manual
    '📎': 'attach_file',      # Anexo/Attachment
    '📁': 'folder',           # Pasta
    '📂': 'folder_open',      # Pasta aberta
    '🗂️': 'folder_special',  # Pasta especial
    '📦': 'inventory_2',      # Pacote/Package
    '🗑️': 'delete',          # Lixeira/Deletar
    '🗑': 'delete',           # Lixeira (sem variação)
    '💾': 'save',             # Salvar
    '📤': 'upload',           # Upload/Exportar
    '📥': 'download',         # Download/Importar
    
    # === GRÁFICOS E ANÁLISE ===
    '📊': 'analytics',        # Dashboard/Analytics
    '📈': 'trending_up',      # Crescimento/Up
    '📉': 'trending_down',    # Queda/Down
    '🎯': 'target',           # Objetivo/Target
    '📍': 'place',            # Localização/Pin
    '🔝': 'vertical_align_top', # Topo/Top
    
    # === PESSOAS E SOCIAL ===
    '👤': 'person',           # Usuário individual
    '👥': 'people',           # Múltiplos usuários
    '🤖': 'smart_toy',        # Bot/Robot/AI
    '😴': 'bedtime',          # Dormindo/Inativo
    '🚨': 'emergency',        # Emergência/Alerta
    
    # === SISTEMA E CONFIGURAÇÕES ===
    '⚙️': 'settings',         # Configurações
    '⚙': 'settings',          # Configurações (sem variação)
    '🔧': 'build',            # Ferramentas/Build
    '🛠️': 'handyman',        # Ferramentas/Manutenção
    '🔌': 'power',            # Conexão/Plugin
    '🔒': 'lock',             # Bloqueado/Seguro
    '🔓': 'lock_open',        # Desbloqueado
    '⚡': 'bolt',             # Rápido/Lightning
    '🌍': 'public',           # Global/World
    
    # === INTERFACE E NAVEGAÇÃO ===
    '🏠': 'home',             # Home/Início
    '🔍': 'search',           # Buscar/Search
    '👈': 'arrow_back',       # Voltar/Back
    '→': 'arrow_forward',     # Avançar/Forward
    '🏢': 'business',         # Empresa/Building
    '🚫': 'block',            # Bloqueado/Proibido
    '●': 'circle',            # Ponto/Círculo
    '✓': 'check',            # Check simples
    
    # === DISPOSITIVOS ===
    '💻': 'computer',         # Computador
    '🖥️': 'desktop_windows', # Desktop
    '📱': 'smartphone',       # Mobile/Celular
    
    # === ATIVIDADES ===
    '🏃': 'directions_run',   # Executando/Running
    '🧹': 'cleaning_services',# Limpeza/Clean
    '🚀': 'rocket_launch',    # Lançar/Deploy
    
    # === TEMPO ===
    '🕐': 'schedule',         # Horário/Clock
    
    # === OUTROS ===
    '🥧': 'pie_chart',        # Gráfico pizza
    '💡': 'lightbulb',        # Ideia
    '🌟': 'star',             # Estrela/Favorito
    '✨': 'auto_awesome',     # Mágica/Especial
    'ℹ️': 'info',            # Informação
    '❓': 'help',             # Ajuda/Pergunta
    '🎨': 'palette',          # Design/Tema
    '🌐': 'language',         # Web/Internet
}
```

## 🌐 DICIONÁRIO DE TRADUÇÕES PT-BR

```python
TRANSLATIONS = {
    # === NAVEGAÇÃO ===
    'Settings': 'Configurações',
    'Dashboard': 'Painel',
    'System': 'Sistema',
    'Logs': 'Logs',
    'Documentation': 'Documentação',
    'Services': 'Serviços',
    'Repositories': 'Repositórios',
    'Projects': 'Projetos',
    
    # === AÇÕES ===
    'Save': 'Salvar',
    'Cancel': 'Cancelar',
    'Submit': 'Enviar',
    'Delete': 'Excluir',
    'Edit': 'Editar',
    'Add': 'Adicionar',
    'Update': 'Atualizar',
    'Refresh': 'Atualizar',
    'Search': 'Buscar',
    'Filter': 'Filtrar',
    'Download': 'Baixar',
    'Upload': 'Enviar',
    'Export': 'Exportar',
    'Import': 'Importar',
    'Copy': 'Copiar',
    'Paste': 'Colar',
    'Clear': 'Limpar',
    'Open': 'Abrir',
    'Close': 'Fechar',
    
    # === STATUS ===
    'Status': 'Status',
    'Actions': 'Ações',
    'Details': 'Detalhes',
    'Info': 'Informações',
    'Warning': 'Aviso',
    'Error': 'Erro',
    'Success': 'Sucesso',
    'Loading': 'Carregando',
    'Running': 'Em execução',
    'Stopped': 'Parado',
    'Online': 'Online',
    'Offline': 'Offline',
    'Active': 'Ativo',
    'Inactive': 'Inativo',
    'Enabled': 'Habilitado',
    'Disabled': 'Desabilitado',
    
    # === GERAIS ===
    'None': 'Nenhum',
    'All': 'Todos',
    'Selected': 'Selecionados',
    'Total': 'Total',
    'Available': 'Disponível',
    'Used': 'Usado',
    'Free': 'Livre',
    'Yes': 'Sim',
    'No': 'Não',
    'Start': 'Iniciar',
    'Stop': 'Parar',
    'Restart': 'Reiniciar',
    'Pull': 'Baixar',
    'Push': 'Enviar',
    'Remote': 'Remoto'
}
```

## 🎨 MAPEAMENTO DE ÍCONES PARA COMPONENTES

### Headers e Seções
```python
HEADER_ICONS = {
    # === PRINCIPAIS ===
    'Dashboard': 'dashboard',
    'Painel': 'dashboard',
    'System': 'desktop_windows',
    'Sistema': 'desktop_windows',
    'Documentation': 'description',
    'Documentação': 'description',
    'Settings': 'settings',
    'Configurações': 'settings',
    'Services': 'settings',
    'Serviços': 'settings',
    'Repositories': 'source',
    'Repositórios': 'source',
    'Projects': 'folder',
    'Projetos': 'folder',
    
    # === ANÁLISE ===
    'Estatísticas': 'analytics',
    'Statistics': 'analytics',
    'Métricas': 'insights',
    'Metrics': 'insights',
    'Analytics': 'analytics',
    
    # === VISUALIZAÇÃO ===
    'Explorador de Documentos': 'folder_open',
    'Visualização': 'visibility',
    'Visualizador de Logs': 'description',
    
    # === SISTEMA ===
    'Visão Geral do Sistema': 'desktop_windows',
    'System Overview': 'desktop_windows',
    'Informações de Hardware': 'build',
    'Hardware Information': 'build',
    'Processador': 'memory',
    'CPU': 'memory',
    'Memória': 'memory',
    'Memory': 'memory',
    'Armazenamento': 'storage',
    'Storage': 'storage',
    'Informações de Rede': 'public',
    'Network Information': 'public',
    'Informações de Processos': 'refresh',
    'Process Information': 'refresh',
    
    # === TECNOLOGIAS ===
    'APIs': 'api',
    'Web': 'public',
    'Mobile': 'smartphone',
    'Desktop': 'computer',
    'Libraries': 'library_books',
    'Bibliotecas': 'library_books',
    'Database': 'storage',
    'Network': 'public',
    'Security': 'security',
    'Monitoring': 'monitoring',
    'Git': 'source',
    'Claude Manager': 'smart_toy',
    
    # === OUTROS ===
    'Outros': 'inventory_2',
    'Others': 'inventory_2',
    'Dashboards': 'dashboard',
    'Painéis': 'dashboard',
    'Gerenciamento de Serviços': 'settings',
    'Gerenciador de Repositórios': 'source',
}
```

### Botões
```python
BUTTON_ICONS = {
    # === NAVEGAÇÃO ===
    'Explorador': 'folder_open',
    'Visualização': 'visibility',
    'Documentation': 'description',
    'Documentação': 'description',
    
    # === ESTATÍSTICAS ===
    'Estatísticas': 'analytics',
    'Statistics': 'analytics',
    'Métricas': 'insights',
    'Metrics': 'insights',
    'APIs': 'api',
    
    # === AÇÕES BÁSICAS ===
    'Save': 'save',
    'Salvar': 'save',
    'Cancel': 'cancel',
    'Cancelar': 'cancel',
    'Submit': 'send',
    'Enviar': 'send',
    'Delete': 'delete',
    'Excluir': 'delete',
    'Edit': 'edit',
    'Editar': 'edit',
    'Add': 'add',
    'Adicionar': 'add',
    'Update': 'update',
    'Atualizar': 'refresh',
    'Refresh': 'refresh',
    'Search': 'search',
    'Buscar': 'search',
    'Download': 'download',
    'Baixar': 'download',
    'Upload': 'upload',
    'Export': 'file_download',
    'Exportar': 'file_download',
    'Import': 'file_upload',
    'Importar': 'file_upload',
    'Open': 'open_in_new',
    'Abrir': 'open_in_new',
    'Close': 'close',
    'Fechar': 'close',
    'Run': 'play_arrow',
    'Executar': 'play_arrow',
    'Stop': 'stop',
    'Parar': 'stop',
    'Restart': 'restart_alt',
    'Reiniciar': 'restart_alt',
    'Clear': 'clear',
    'Limpar': 'clear',
    'Copy': 'content_copy',
    'Copiar': 'content_copy',
    'Paste': 'content_paste',
    'Colar': 'content_paste',
    'Settings': 'settings',
    'Configurações': 'settings',
    'Status': 'info',
    'Pull': 'cloud_download',
    'Push': 'cloud_upload',
    'Remote': 'cloud',
    'Atualizar Repositórios': 'refresh',
    'Atualizar Informações': 'refresh'
}
```

## 🎨 CSS ADAPTATIVO (CLARO/ESCURO)

### Material Design Icons
```html
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">
```

### Variáveis CSS Adaptativas
```css
/* SEMPRE usar variáveis do Streamlit */
:root {
    /* Cores que funcionam em ambos os temas */
    --primary: #3b82f6;      /* Azul que funciona em ambos */
    --success: #10b981;      /* Verde visível em ambos */
    --warning: #f59e0b;      /* Laranja adaptável */
    --danger: #ef4444;       /* Vermelho adaptável */
    
    /* Usar variáveis do Streamlit */
    --bg-primary: var(--background-color);
    --text-primary: var(--text-color);
    --bg-card: var(--secondary-background-color);
    
    /* Bordas e sombras adaptativas */
    --border: rgba(var(--text-color-rgb), 0.1);
    --shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

/* NUNCA usar !important */
/* NUNCA usar cores fixas como #ffffff ou #000000 */
/* SEMPRE usar variáveis para cores */
```

### Regras de CSS
1. **NUNCA** usar `!important`
2. **NUNCA** usar cores fixas (`#ffffff`, `#000000`)
3. **SEMPRE** usar variáveis CSS do Streamlit
4. **NUNCA** usar fallback branco em variáveis
5. **SEMPRE** testar em ambos os temas

## 📋 COMPONENTES STREAMLIT - REFERÊNCIA RÁPIDA

### Componentes que NÃO aceitam HTML
- `st.info()`, `st.success()`, `st.warning()`, `st.error()`
- `st.metric()`
- `st.button()`, `st.download_button()`
- `st.selectbox()`, `st.multiselect()` (nas opções)
- `st.radio()`, `st.checkbox()`
- `st.text_input()`, `st.text_area()` (nos labels)
- `st.slider()`, `st.number_input()`
- `st.expander()` (no label)
- `st.tabs()` (nos labels das tabs)
- `st.navigation()` (nos títulos)

### Componentes que aceitam HTML (com unsafe_allow_html=True)
- `st.markdown()`
- `st.write()`

## 📐 PADRÕES DE IMPLEMENTAÇÃO

### Headers Principais
```python
st.markdown('<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">icon_name</span>Texto do Header</div>', unsafe_allow_html=True)
```

### Subheaders com Ícones
```python
st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>icon_name</span>Título da Seção", unsafe_allow_html=True)
```

### Botões com Material Icons
```python
st.button(":material/icon_name: Texto do Botão")
```

### Métricas Profissionais
```python
from components.metrics import create_metric_card
create_metric_card("Label", "Valor", "icon_name")
```

## ✅ CHECKLIST DE VALIDAÇÃO

### Por Arquivo
- [ ] Header principal tem Material Icon
- [ ] Todos os subheaders têm Material Icon
- [ ] Todos os botões têm `:material/icon:`
- [ ] Todos os textos em português
- [ ] Métricas usando `create_metric_card`
- [ ] Nenhum emoji Unicode presente
- [ ] CSS sem `!important`
- [ ] Cores usando variáveis CSS
- [ ] HTML com `unsafe_allow_html=True`
- [ ] Sintaxe Python válida

### Global
- [ ] Testado em tema claro
- [ ] Testado em tema escuro
- [ ] Interface 100% em português
- [ ] Ícones consistentes
- [ ] Nenhum `<span class` visível na interface
- [ ] Performance mantida
- [ ] Funcionalidades preservadas

## 🚫 REGRAS ESPECIAIS

1. **NÃO** modificar `st.navigation()` - manter nomes de arquivos .py
2. **NÃO** traduzir nomes de arquivos Python ou variáveis
3. **NÃO** traduzir níveis de log técnicos (ERROR, WARN, INFO, DEBUG)
4. **NÃO** traduzir SQL ou código dentro de strings
5. **PRESERVAR** referências `adaptive_theme.css`
6. **MANTER** `--info-color` para ícones azuis nos headers
7. **PRESERVAR** Material Icons nativos do Streamlit (`:material/icon:`)
8. **NÃO** modificar URLs mesmo com emojis

## 🔧 FERRAMENTAS DE VALIDAÇÃO

### Buscar Emojis
```bash
# Regex para encontrar emojis Unicode
grep -rE "[\U0001F300-\U0001F9FF]" --include="*.py"
```

### Validar HTML sem unsafe_allow_html
```bash
grep -n '<span class' arquivo.py | grep -v unsafe_allow_html
```

### Validar Sintaxe Python
```bash
python3 -m py_compile arquivo.py
```

### Buscar Cores Hardcoded
```bash
grep -rE "color:\s*#[0-9a-fA-F]{3,6}" --include="*.py"
grep -rE "background[-color]*:\s*#[0-9a-fA-F]{3,6}" --include="*.py"
```

## 📚 REFERÊNCIAS

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Material Design Icons](https://fonts.google.com/icons)
- [Streamlit Theming](https://docs.streamlit.io/library/advanced-features/theming)

---

**Última atualização:** Janeiro 2025
**Versão:** 1.0