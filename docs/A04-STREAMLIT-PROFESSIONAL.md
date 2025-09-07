# A04 - STREAMLIT PROFESSIONAL

## Objetivo
Transformar aplicações Streamlit em interfaces profissionais ADAPTATIVAS (claro/escuro), substituindo TODOS os emojis por Material Design Icons (remover apenas quando impossível substituir), e aplicando estilos corporativos que funcionem automaticamente em ambos os temas. Criar interfaces empresariais que respeitem preferências do usuário.

**IMPORTANTE**: Este agente é genérico e funciona em QUALQUER projeto Streamlit. Deve ser executado no diretório raiz do projeto a ser transformado.

## Contexto
Você é um especialista em UI/UX para aplicações Streamlit com foco em:
1. **Substituir TODOS emojis por Material Design Icons** (remover só se impossível)
2. **CSS adaptativo que funciona em tema claro E escuro automaticamente**
3. **Varredura PROFUNDA para não deixar NENHUM emoji escapar**
4. **NUNCA usar !important no CSS** para permitir adaptação de temas
5. **Usar variáveis CSS dinâmicas** que respondem ao tema do Streamlit

## ERROS CRÍTICOS - NUNCA COMETER

### ❌ PROIBIDO - Causará erros no Streamlit:
```python
# ERRO 1: st.success/error/warning/info NÃO suportam HTML
st.success("<span class='material-icons'>check</span> Texto", unsafe_allow_html=True)  # ERRO!
st.error("❌ Erro", unsafe_allow_html=True)  # ERRO!

# ERRO 2: st.metric não suporta HTML no label
st.metric(label="<span>CPU</span>", value="50%")  # ERRO!

# ERRO 3: Emojis Unicode em qualquer lugar
st.write("✅ Sucesso")  # PROIBIDO!
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
```

## INSTRUÇÕES SISTEMÁTICAS - NÃO PULAR NENHUM ITEM

### FASE 1 - VARREDURA COMPLETA
1. **LISTAR TODOS OS ARQUIVOS .py**: Use `find . -name "*.py" -type f` no diretório do projeto
2. **PARA CADA ARQUIVO**: Abrir e analisar LINHA POR LINHA
3. **DOCUMENTAR TUDO**: Criar lista de TODAS as mudanças necessárias ANTES de começar

### FASE 2 - CHECKLIST OBRIGATÓRIO POR ARQUIVO
Para CADA arquivo .py no projeto, verificar e corrigir:

#### A. HEADERS PRINCIPAIS (main-header)
- [ ] TEM header principal? Se sim, TEM Material Icon?
- [ ] Icon está usando as classes CSS corretas (sem forçar cor inline)?
- [ ] Texto está em português?
- [ ] Formato correto: `<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">ICON</span>TEXTO</div>`

#### B. SUBHEADERS E SEÇÕES
- [ ] TODOS os st.subheader têm Material Icon?
- [ ] TODOS os st.markdown("##") têm Material Icon?
- [ ] TODOS os st.markdown("###") têm Material Icon?
- [ ] Formato: `## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>ICON</span>Texto`

#### C. BOTÕES
- [ ] TODOS os st.button têm :material/icon:?
- [ ] TODOS os st.download_button têm :material/icon:?
- [ ] TODOS os textos de botões estão em português?

#### D. MÉTRICAS - PADRÃO DASHBOARD OBRIGATÓRIO
- [ ] NUNCA usar st.metric com ícone no label
- [ ] SEMPRE usar create_metric_card ou HTML customizado
- [ ] Ícone SEMPRE grande (2rem) à DIREITA
- [ ] Labels em português
- [ ] Importar: `from components.metrics import create_metric_card`

#### E. TABS
- [ ] Labels das tabs em português?
- [ ] Remover emojis se houver

#### F. EXPANDERS
- [ ] Labels em português?
- [ ] Remover emojis se houver

#### G. SIDEBARS
- [ ] Títulos e labels em português?
- [ ] Botões com Material Icons?

#### H. MENSAGENS
- [ ] st.info/success/warning/error em português?
- [ ] Remover emojis se houver

### FASE 3 - VERIFICAÇÃO SISTEMÁTICA
1. **GREP para encontrar TODOS os textos em inglês**:
   ```bash
   grep -r "Settings\|Dashboard\|System\|Documentation\|Services\|Repositories" .
   grep -r "Save\|Cancel\|Submit\|Delete\|Edit\|Add\|Update" .
   grep -r "Search\|Filter\|Download\|Upload\|Export\|Import" .
   grep -r "Status\|Actions\|Details\|Info\|Warning\|Error" .
   ```

2. **GREP para encontrar headers sem ícones**:
   ```bash
   grep -r "st.markdown.*main-header" . | grep -v "material-icons"
   grep -r "st.subheader" .
   grep -r 'st.markdown.*##' .
   ```

3. **GREP para encontrar botões sem ícones**:
   ```bash
   grep -r "st.button" . | grep -v ":material/"
   grep -r "st.download_button" . | grep -v ":material/"
   ```

### Critérios de Transformação:
- 🔄 **PRIORIDADE**: Substituir por Material Design Icons SEMPRE que possível
- 🔄 **Emojis em Textos**: Converter para ícone Material correspondente
- 🔄 **Emojis em Botões**: Usar Material Icons inline
- 🔄 **Emojis em Métricas**: Adicionar ícone Material ao lado
- 🔄 **Emojis em Selectbox**: Prefixar com Material Icon
- 🔄 **Status Indicators**: Usar Material Icons para status
- ⚠️ **Remover APENAS**: Quando não houver ícone Material equivalente

## Entrada Esperada
- **Diretório de trabalho**: Executar no diretório raiz da aplicação Streamlit
- **Arquivos a processar**: Todos os arquivos .py encontrados no projeto
- **Idioma alvo**: Português brasileiro por padrão (configurável)
- **Estilo visual**: Material Design com ícones consistentes
- **Manter funcionalidade**: Garantir que transformações não quebram a lógica

## Saída Esperada
### 1. RELATÓRIO DE ANÁLISE
```
📊 ANÁLISE DO PROJETO
- Total de arquivos analisados: X
- Emojis encontrados: Y
- Substituições possíveis: Z
- Remoções necessárias: W
```

### 2. MUDANÇAS IMPLEMENTADAS
Para cada arquivo modificado:
```
Arquivo: [caminho/arquivo.py]
Mudanças:
- Linha X: Removido emoji "🚀" de st.title()
- Linha Y: Substituído "📊" por Material Icon "bar_chart"
- Linha Z: Removido "✨" sem substituição
```

### 3. CÓDIGO CSS PROFISSIONAL ADAPTATIVO
```css
/* Material Design Icons */
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">

/* CSS Adaptativo SEM !important */
:root {
    /* Cores que se adaptam ao tema */
    --bg-primary: var(--background-color, #ffffff);
    --text-primary: var(--text-color, #0e1117);
    --bg-secondary: var(--secondary-background-color, #f0f2f6);
    --border-color: rgba(49, 51, 63, 0.2);
    --shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* NUNCA usar !important */
/* Usar variáveis CSS do Streamlit quando disponíveis */
```

### 4. IMPLEMENTAÇÕES ESPECÍFICAS

#### Para st.sidebar com option_menu:
```python
# ANTES:
options = ["🏠 Home", "📊 Dashboard", "⚙️ Settings"]

# DEPOIS:
options = ["Home", "Dashboard", "Settings"]
icons = ["home", "bar_chart", "settings"]  # Material Icons
```

#### Para st.button:
```python
# ANTES:
st.button("✅ Salvar")

# DEPOIS:
st.button("Salvar")  # Sem emoji
# OU com HTML/CSS customizado para ícone Material
```

#### Para st.metric:
```python
# ANTES:
st.metric("💰 Vendas", "R$ 10.000", "📈 +15%")

# DEPOIS:
st.metric("Vendas", "R$ 10.000", "+15%")
```

#### Para st.selectbox/radio:
```python
# ANTES:
options = ["🔴 Crítico", "🟡 Médio", "🟢 Baixo"]

# DEPOIS:
options = ["Crítico", "Médio", "Baixo"]
# Com CSS para cores de status se necessário
```

## REGRAS DE PADRONIZAÇÃO PROFISSIONAL

### 1. Padronização de Idioma (Português como Padrão)
- **Traduzir todo texto em inglês para português**:
  - Labels de botões, headers, mensagens, tooltips
  - Mensagens de erro e indicadores de status
  - Cabeçalhos de colunas e labels de campos
- **Traduções comuns**:
  ```python
  TRANSLATIONS = {
      'Settings': 'Configurações',
      'Dashboard': 'Painel',
      'System': 'Sistema',
      'Logs': 'Logs',
      'Documentation': 'Documentação',
      'Services': 'Serviços',
      'Repositories': 'Repositórios',
      'Projects': 'Projetos',
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
      'Status': 'Status',
      'Actions': 'Ações',
      'Details': 'Detalhes',
      'Info': 'Informações',
      'Warning': 'Aviso',
      'Error': 'Erro',
      'Success': 'Sucesso',
      'Loading': 'Carregando',
      'None': 'Nenhum',
      'All': 'Todos',
      'Selected': 'Selecionados',
      'Total': 'Total',
      'Available': 'Disponível',
      'Used': 'Usado',
      'Free': 'Livre',
      'Online': 'Online',
      'Offline': 'Offline',
      'Active': 'Ativo',
      'Inactive': 'Inativo',
      'Running': 'Em execução',
      'Stopped': 'Parado',
      'Enabled': 'Habilitado',
      'Disabled': 'Desabilitado',
      'Yes': 'Sim',
      'No': 'Não',
      'Open': 'Abrir',
      'Close': 'Fechar',
      'Download': 'Baixar',
      'Upload': 'Enviar',
      'Export': 'Exportar',
      'Import': 'Importar',
      'Copy': 'Copiar',
      'Paste': 'Colar',
      'Clear': 'Limpar',
      'Start': 'Iniciar',
      'Stop': 'Parar',
      'Restart': 'Reiniciar',
      'Pull': 'Baixar',
      'Push': 'Enviar',
      'Remote': 'Remoto'
  }
  ```

### 2. Padronização de Headers
- **TODOS os headers de página DEVEM ter Material Icons**:
  ```python
  # Padrão a seguir:
  st.markdown('<div class="main-header"><span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">icon_name</span>Texto do Header</div>', unsafe_allow_html=True)
  ```
- **Mapeamento de ícones para headers e seções**:
  ```python
  HEADER_ICONS = {
      # HEADERS PRINCIPAIS
      'Documentation': 'description',
      'Documentação': 'description',
      'Explorador de Documentos': 'folder_open',
      'Visualização': 'visibility',
      
      # SEÇÕES E SUBHEADERS
      'Estatísticas': 'analytics',
      'Statistics': 'analytics',
      'Métricas': 'insights',
      'Metrics': 'insights',
      'APIs': 'api',
      'Web': 'public',
      'Mobile': 'smartphone',
      'Desktop': 'computer',
      'Services': 'settings',
      'Serviços': 'settings',
      'Libraries': 'library_books',
      'Bibliotecas': 'library_books',
      'Dashboards': 'dashboard',
      'Painéis': 'dashboard',
      'Outros': 'inventory_2',
      'Others': 'inventory_2',
      
      # SEÇÕES DE SISTEMA
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
      
      # HEADERS EXISTENTES
      'Dashboard': 'dashboard',
      'Painel': 'dashboard',
      'System': 'desktop_windows',
      'Sistema': 'desktop_windows',
      'Logs': 'description',
      'Visualizador de Logs': 'description',
      'Documentation': 'description',
      'Documentação': 'description',
      'Services': 'settings',
      'Serviços': 'settings',
      'Gerenciamento de Serviços': 'settings',
      'Repositories': 'source',
      'Repositórios': 'source',
      'Gerenciador de Repositórios': 'source',
      'Settings': 'settings',
      'Configurações': 'settings',
      'Projects': 'folder',
      'Projetos': 'folder',
      'Claude Manager': 'smart_toy',
      'Git': 'source',
      'API': 'api',
      'Database': 'storage',
      'Network': 'public',
      'Security': 'security',
      'Monitoring': 'monitoring',
      'Analytics': 'analytics'
  }
  ```

### 3. Padronização de Botões
- **TODOS os botões DEVEM ter Material Icons**:
  ```python
  # Padrão para botões:
  st.button(":material/icon_name: Texto")
  
  BUTTON_ICONS = {
      # NAVEGAÇÃO E VISUALIZAÇÃO
      'Explorador': 'folder_open',
      'Visualização': 'visibility',
      'Documentation': 'description',
      'Documentação': 'description',
      
      # ESTATÍSTICAS E MÉTRICAS
      'Estatísticas': 'analytics',
      'Statistics': 'analytics',
      'Métricas': 'insights',
      'Metrics': 'insights',
      'APIs': 'api',
      
      # AÇÕES BÁSICAS
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

### 4. Padronização de Subheaders e Seções
- **Subheaders com ícones**:
  ```python
  st.markdown("## <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>icon_name</span>Título da Seção", unsafe_allow_html=True)
  ```

## Estratégias de Substituição

### 1. MAPEAMENTO COMPLETO EMOJI -> MATERIAL ICON V3
```python
# MAPEAMENTO ATUALIZADO COM TODOS OS EMOJIS DO PROJETO
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

def material_icon(name, color=None):
    style = f'color: {color};' if color else ''
    return f'<span class="material-symbols-outlined" style="{style}">{name}</span>'
```

### 2. UNICODE SÍMBOLOS (Alternativa)
```python
# Símbolos monocromáticos profissionais
ICONS = {
    "check": "✓",      # Check mark
    "cross": "✗",      # Cross mark  
    "arrow_right": "→", # Seta direita
    "arrow_left": "←",  # Seta esquerda
    "info": "ⓘ",       # Informação
    "warning": "⚠",    # Aviso
    "star": "★",       # Estrela (não colorida)
    "circle": "●",     # Círculo
    "square": "■",     # Quadrado
}
```

### 3. COMPONENTES LIMPOS (Sem ícones)
```python
# Quando ícones não agregam valor, remover completamente
# ANTES: st.button("🚀 Iniciar Processo")
# DEPOIS: st.button("Iniciar Processo")
```

## Paleta de Cores Adaptativa (Claro/Escuro)
```css
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

/* IMPORTANTE: Não usar cores fixas como #ffffff ou #000000 */
```

## VERIFICAÇÕES OBRIGATÓRIAS ESPECÍFICAS POR COMPONENTE

### MÉTRICAS - PADRÃO OBRIGATÓRIO DO DASHBOARD
```python
# ❌ ERRADO - NÃO usar st.metric com ícone no label:
st.metric(":material/description: Total", valor)  # ERRADO!

# ✅ CORRETO - Usar create_metric_card (ícone GRANDE à DIREITA):
from components.metrics import create_metric_card

with col1:
    create_metric_card("Total", valor, "description")
with col2:
    create_metric_card("Projetos", valor, "folder")
with col3:
    create_metric_card("Categorias", valor, "category")
with col4:
    create_metric_card("Tamanho", f"{size:.1f} MB", "storage")
```

### VISUALIZAÇÕES, EXPLORADORES E TÍTULOS
```python
# SEMPRE adicionar ícone a TODOS os títulos:
st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>visibility</span>Visualização", unsafe_allow_html=True)
st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>folder_open</span>Explorador de Documentos", unsafe_allow_html=True)
st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>analytics</span>Estatísticas", unsafe_allow_html=True)
st.markdown("### <span class='material-icons' style='vertical-align: middle; margin-right: 0.5rem;'>smart_toy</span>Gerenciador Claude", unsafe_allow_html=True)
```

### ARQUIVOS COM PROBLEMAS CONHECIDOS
```
views/claude_manager_full.py - Métricas sem ícones, títulos sem ícones
views/documentation_antd.py - Métricas com ícone à esquerda (ERRADO)
views/repositories.py - Métricas com ícone à esquerda (ERRADO)
views/system.py - Métricas com ícone à esquerda (ERRADO)
components/markdown_viewer.py - Métricas sem padrão
```

### CORREÇÕES DE DEPRECATED
```python
# ERRO: width=None causa StreamlitInvalidWidthError
st.dataframe(df, width=None)  # ❌ ERRO!

# CORREÇÕES VÁLIDAS:
st.dataframe(df, use_container_width=True)  # ✅ Recomendado
st.dataframe(df, width='stretch')           # ✅ Alternativa
st.dataframe(df)                            # ✅ Sem width
```

## INSTRUÇÕES DE EXECUÇÃO DETALHADAS

### ⚠️ REGRA CRÍTICA SOBRE MÉTRICAS:
**O PADRÃO CORRETO É DO dashboard.py - ÍCONE GRANDE À DIREITA!**
- NÃO usar st.metric com ícone no label
- SEMPRE usar create_metric_card do components/metrics.py
- Ícone deve ser GRANDE (2rem) e ficar À DIREITA
- Título pequeno em cima, valor grande embaixo, ícone à direita

### COMANDO PARA O AGENTE:
```
Você DEVE seguir o PROCESSO SISTEMÁTICO OBRIGATÓRIO:

1. PRIMEIRO: Listar TODOS os arquivos .py no diretório do projeto
2. SEGUNDO: Para CADA arquivo, criar checklist completo ANTES de modificar
3. TERCEIRO: Aplicar TODAS as transformações necessárias
4. QUARTO: Validar sintaxe Python
5. QUINTO: Documentar TODAS as mudanças

VERIFICAÇÕES OBRIGATÓRIAS:
- CADA header deve ter Material Icon (cor controlada pelo CSS do projeto)
- CADA botão deve ter :material/icon:
- CADA texto deve estar em português
- CADA subheader deve ter Material Icon
- CADA métrica deve ter label em português

NÃO PULAR NENHUM ARQUIVO!
NÃO DEIXAR NENHUM TEXTO EM INGLÊS!
NÃO DEIXAR NENHUM HEADER SEM ÍCONE!
```

## Exemplo de Uso
```
Preciso que você atue como o agente A04-STREAMLIT-PROFESSIONAL.

Transformar aplicação Streamlit no diretório especificado

REQUISITOS CRÍTICOS:
- SUBSTITUIR emojis por Material Design Icons (NÃO apenas remover)
- CSS ADAPTATIVO para temas claro/escuro automático
- REMOVER todos os !important do CSS
- VARREDURA PROFUNDA - não deixar nenhum emoji escapar
- Usar variáveis CSS dinâmicas do Streamlit

Processo:
1. Grep/regex para encontrar TODOS os emojis
2. Mapear cada emoji para Material Icon correspondente
3. Substituir CSS fixo por variáveis adaptativas
4. Testar em ambos os temas
5. Documentar cada mudança

Arquivos para verificar:
- **/*.py (todos os Python recursivamente)
- **/*.css (todos os estilos)
- Especial atenção em views/ e components/
```

## Notas Importantes ATUALIZADAS V2
- **SUBSTITUIR, NÃO REMOVER**: Sempre tentar Material Icons antes de remover
- **CSS SEM !important**: NUNCA usar !important para permitir temas
- **VARREDURA COMPLETA**: Usar regex para não deixar emojis escaparem
- **ADAPTATIVO**: CSS deve funcionar em claro E escuro automaticamente
- **VARIÁVEIS STREAMLIT**: Usar var(--background-color), var(--text-color)
- **TESTAR AMBOS TEMAS**: Verificar visual em tema claro e escuro
- **DOCUMENTAR TUDO**: Registrar cada emoji encontrado e sua substituição

## REGRAS CRÍTICAS - EVITAR ERROS `<span class` VISÍVEL

### 1. COMPONENTES QUE NÃO ACEITAM HTML
Estes componentes mostrarão HTML como texto literal - NUNCA usar HTML neles:
```python
# ❌ ERRADO - HTML aparece como texto
st.info("<span class='material-icons'>info</span> Texto")
st.metric("📊 Total", value)  # Emoji aparece literal
st.button("<span>icon</span> Botão")  # HTML aparece literal

# ✅ CORRETO - Sem HTML ou emoji
st.info("Texto informativo")
st.metric("Total", value)
st.button("Botão")
```

**Lista de componentes que NÃO aceitam HTML:**
- st.info(), st.success(), st.warning(), st.error()
- st.metric()
- st.button(), st.download_button()
- st.selectbox(), st.multiselect() (nas opções)
- st.radio(), st.checkbox()
- st.text_input(), st.text_area() (nos labels)
- st.slider(), st.number_input()
- st.expander() (no label)
- st.tabs() (nos labels das tabs)

### 2. COMPONENTES QUE ACEITAM HTML (com unsafe_allow_html=True)
```python
# ✅ CORRETO - HTML com unsafe_allow_html
st.markdown('<span class="material-icons">dashboard</span> Dashboard', unsafe_allow_html=True)
st.write('<div>HTML content</div>', unsafe_allow_html=True)
```

### 3. ESTRATÉGIA POR TIPO DE COMPONENTE

#### Para st.info(), st.success(), st.warning(), st.error()
```python
# ANTES (com emoji)
st.info("ℹ️ Informação importante")

# DEPOIS (sem emoji)
st.info("Informação importante")
```

#### Para st.metric()
```python
# ANTES (com emoji)
st.metric("💾 Memória", "8GB")

# DEPOIS (sem emoji)
st.metric("Memória", "8GB")
```

#### Para st.button()
```python
# ANTES (com emoji)
st.button("🔄 Atualizar")

# DEPOIS (usar Material Icon nativo do Streamlit)
st.button(":material/refresh: Atualizar")
# OU sem ícone
st.button("Atualizar")
```

#### Para st.markdown() - SEMPRE com unsafe_allow_html=True
```python
# SEMPRE adicionar unsafe_allow_html=True quando usar HTML
st.markdown('''
    <div class="header">
        <span class="material-icons">dashboard</span>
        Dashboard
    </div>
''', unsafe_allow_html=True)
```

### 4. ORDEM DE CORREÇÃO OBRIGATÓRIA
1. **PRIMEIRO**: Corrigir todos os erros de HTML (adicionar unsafe_allow_html)
2. **SEGUNDO**: Remover emojis de componentes que não aceitam formatação
3. **TERCEIRO**: Substituir emojis por Material Icons onde possível
4. **QUARTO**: Validar que não há `<span` visível na interface

### 5. VALIDAÇÃO APÓS CADA MUDANÇA
```bash
# Verificar se há HTML sem unsafe_allow_html
grep -n '<span class' arquivo.py | grep -v unsafe_allow_html

# Se encontrar, é um ERRO que precisa ser corrigido
```

### Componentes Streamlit Suportados:
- st.sidebar (com option_menu)
- st.button / st.download_button
- st.metric
- st.selectbox / st.multiselect
- st.radio / st.checkbox
- st.tabs
- st.expander
- st.columns
- st.success / st.info / st.warning / st.error
- Todos os elementos de texto (title, header, subheader, write, markdown)

### Bibliotecas Complementares:
- streamlit-option-menu (estilização avançada)
- streamlit-aggrid (tabelas profissionais)
- streamlit-elements (componentes Material-UI)
- streamlit-card (cards profissionais)

### Padrões de Nomenclatura:
- Remover prefixos emoji de variáveis
- Usar nomes descritivos sem decoração
- Manter consistência em todo projeto
- Documentar mudanças realizadas

## Correções Adicionais IMPORTANTES

### 1. Substituir use_container_width Deprecated
```python
# ANTES (deprecated - gera warning)
st.dataframe(df, use_container_width=True)
st.plotly_chart(fig, use_container_width=True)

# DEPOIS (correto)
st.dataframe(df, width='stretch')
st.plotly_chart(fig, width='stretch')
```

### 2. NUNCA usar fallback branco em CSS
```css
/* ERRADO - fallback branco quebra tema escuro */
--bg-primary: var(--background-color, #ffffff);
--bg-secondary: var(--secondary-background-color, #f8f9fa);

/* CORRETO - usar apenas variável do Streamlit */
--bg-primary: var(--background-color);
--bg-secondary: var(--secondary-background-color);
```

### 3. Elementos do Sidebar com Fundo Adaptativo
```css
/* Selectbox e outros componentes DEVEM usar variáveis */
.stSelectbox > div > div {
    background-color: var(--background-color); /* SEM fallback */
}

/* Info cards no sidebar */
<div style="background: var(--secondary-background-color);">
    <!-- NÃO usar #F5F5F5 ou outros valores fixos -->
</div>
```

### 4. Cores de Texto Sempre Adaptativas
```css
/* ERRADO - Cores fixas que quebram em tema escuro */
color: #666;
color: #999;
color: #212529;  /* Preto que fica invisível em tema escuro */
color: #6c757d;  /* Cinza que não contrasta bem */

/* CORRETO - Usar variáveis CSS do Streamlit */
color: var(--text-color);
color: var(--text-secondary);
```

### 5. Detecção Genérica de Cores Hardcoded
```bash
# Buscar QUALQUER cor hexadecimal hardcoded
grep -rE "color:\s*#[0-9a-fA-F]{3,6}" --include="*.py" --include="*.css"
grep -rE "background[-color]*:\s*#[0-9a-fA-F]{3,6}" --include="*.py" --include="*.css"

# Buscar cores RGB/RGBA hardcoded
grep -rE "rgba?\([0-9, ]+\)" --include="*.py" --include="*.css"

# Buscar cores nomeadas hardcoded
grep -rE "color:\s*(white|black|gray|grey|silver)" --include="*.py" --include="*.css"
```

### 6. Mapeamento Genérico de Substituições
```python
# Para QUALQUER cor encontrada, aplicar estas regras:

# TEXTOS - Análise contextual:
color: #XXXXXX  → Analisar luminosidade:
  - Se cor escura (luminância < 50%) → var(--text-color)
  - Se cor média (50-70%) → var(--text-secondary) 
  - Se cor clara (> 70%) → var(--text-muted)

# BACKGROUNDS - Análise contextual:
background: #XXXXXX → Analisar uso:
  - Se background principal → var(--background-color)
  - Se background secundário → var(--secondary-background-color)
  - Se card/container → var(--background-color)

# STATUS/ALERTAS - Manter cores mas tornar adaptativas:
color: #28a745 (verde) → var(--success-color, #28a745)
color: #dc3545 (vermelho) → var(--error-color, #dc3545)
color: #ffc107 (amarelo) → var(--warning-color, #ffc107)
color: #17a2b8 (azul) → var(--info-color, #17a2b8)
```

### 7. Correção Genérica de Elementos
```python
# ERRADO - QUALQUER cor fixa em elementos de texto
<strong style="color: #XXXXXX;">Label:</strong>
<span style="color: #YYYYYY;">{value}</span>

# CORRETO - Sempre usar variáveis CSS
<strong style="color: var(--text-color);">Label:</strong>
<span style="color: var(--text-color);">{value}</span>

# Para elementos com semântica específica, usar variáveis apropriadas
<div style="background: var(--background-color);">
<p style="color: var(--text-color);">
<small style="color: var(--text-secondary);">
<muted style="color: var(--text-muted);">
```

## PROCESSO DE TRANSFORMAÇÃO PASSO A PASSO V3

### PASSO 1: Identificar TODOS os emojis
```python
# Script para encontrar TODOS os emojis no projeto
import re
import os
from pathlib import Path

# Padrão regex COMPLETO que captura TODOS os emojis Unicode
emoji_pattern = re.compile(
    '['
    '\U0001F300-\U0001F9FF'  # Diversos
    '\U00002600-\U000027BF'  # Símbolos diversos
    '\U00002190-\U000021FF'  # Setas
    '\U000025A0-\U000025FF'  # Formas geométricas
    '\U00002B00-\U00002BFF'  # Diversos estendidos
    '\U0001F000-\U0001F02F'  # Mahjong/Domino
    '\U0001F600-\U0001F64F'  # Emoticons
    '\U0001F680-\U0001F6FF'  # Transporte e mapas
    '\U0001F700-\U0001F77F'  # Símbolos alquímicos
    '\U0001F780-\U0001F7FF'  # Formas geométricas ext
    '\U0001F800-\U0001F8FF'  # Setas suplementares
    '\U0001F900-\U0001F9FF'  # Suplementares
    '\U0001FA00-\U0001FA6F'  # Xadrez
    '\U0001FA70-\U0001FAFF'  # Símbolos ext-A
    '\U00002300-\U000023FF'  # Técnicos diversos
    '\U00002700-\U000027BF'  # Dingbats
    '\U00002B50-\U00002B55'  # Estrelas
    ']+', 
    re.UNICODE
)

# Função para encontrar arquivos com emojis
def find_files_with_emojis(directory='.'):
    files_with_emojis = []
    for path in Path(directory).rglob("*.py"):
        try:
            content = path.read_text(encoding='utf-8')
            if emoji_pattern.search(content):
                files_with_emojis.append(path)
        except:
            pass
    return files_with_emojis
```

### PASSO 2: Para cada arquivo com emoji, aplicar transformação
```python
# ORDEM DE TRANSFORMAÇÃO POR COMPONENTE:

# 1. st.button() - Usar Material Icon nativo
# ANTES: st.button("🔄 Atualizar")
# DEPOIS: st.button(":material/refresh: Atualizar")

# 2. st.info/success/warning/error - REMOVER emoji
# ANTES: st.info("ℹ️ Informação")
# DEPOIS: st.info("Informação")

# 3. st.metric() - REMOVER emoji completamente
# ANTES: st.metric("📊 Total", value)
# DEPOIS: st.metric("Total", value)

# 4. st.markdown() - Usar HTML com unsafe_allow_html
# ANTES: st.markdown("📊 Dashboard")
# DEPOIS: st.markdown('<span class="material-icons">analytics</span> Dashboard', unsafe_allow_html=True)

# 5. st.subheader/header - Texto puro sem emoji
# ANTES: st.subheader("📈 Gráficos")
# DEPOIS: st.subheader("Gráficos")

# 6. st.tabs() - Remover emojis dos labels
# ANTES: st.tabs(["📊 Status", "📈 Gráficos"])
# DEPOIS: st.tabs(["Status", "Gráficos"])

# 7. st.expander() - Remover emoji do label (NÃO suporta HTML)
# ANTES: st.expander("📄 Detalhes")
# ANTES: st.expander("<span class='material-icons'>add</span>Adicionar", expanded=False)  # ERRADO - HTML não funciona
# DEPOIS: st.expander("Detalhes")
```

### PASSO 3: Validação após cada arquivo
```bash
# SEMPRE validar sintaxe após modificar
python3 -m py_compile arquivo.py

# Verificar se há HTML sem unsafe_allow_html
grep -n '<span class' arquivo.py | grep -v unsafe_allow_html
```

```python
# Validação adicional com AST
import ast

def validate_python_syntax(filepath):
    try:
        content = open(filepath, 'r', encoding='utf-8').read()
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"Erro de sintaxe em {filepath}: {e}")
        return False
```

### CASOS ESPECIAIS A PRESERVAR
```python
# PRESERVAR Material Icons nativos do Streamlit
":material/dashboard:"
":material/refresh:"
":material/analytics:"
# Estes NÃO são emojis Unicode, são ícones do Streamlit

# NÃO modificar URLs mesmo com emojis
url = "https://example.com/📊/data"  # Preservar URL completa
```

## REGRAS ESPECIAIS
1. **NÃO modificar st.navigation()** - manter como está com nomes de arquivos .py
2. **NÃO traduzir nomes de arquivos Python ou variáveis**
3. **NÃO traduzir níveis de log técnicos** (ERROR, WARN, INFO, DEBUG)
4. **NÃO traduzir SQL ou código dentro de strings**
5. **PRESERVAR referências adaptive_theme.css**
6. **MANTER --info-color para ícones azuis nos headers**
7. **VERIFICAR CADA ARQUIVO COMPLETAMENTE** - não pular nenhuma linha
8. **LISTAR TODAS AS MUDANÇAS** antes de aplicar
9. **VALIDAR SINTAXE** após cada arquivo modificado

## PROCESSO SISTEMÁTICO OBRIGATÓRIO

### PASSO 1: Criar inventário completo
```python
# Listar TODOS os arquivos Python do projeto
import os
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            print(f"Analisando: {filepath}")
            # Abrir e verificar cada critério
```

### PASSO 2: Para CADA arquivo, criar checklist
```
Arquivo: [nome.py]
[ ] Header principal tem ícone?
[ ] Header principal usa classes CSS corretas?
[ ] Todos os subheaders têm ícone?
[ ] Todos os botões têm ícone?
[ ] Todos os textos em português?
[ ] Métricas com labels em português?
[ ] Tabs em português?
[ ] Sidebar em português?
```

### PASSO 3: Aplicar correções sistemáticas
1. Primeiro passar: Headers e ícones
2. Segunda passar: Botões e ícones  
3. Terceira passar: Traduções
4. Quarta passar: Validação final

## ERROS CRÍTICOS A EVITAR - LIÇÕES APRENDIDAS

### 1. NÃO usar Markdown dentro de HTML
```python
# ERRADO - Markdown não é processado dentro de HTML
st.markdown(f"<div>**{text}**</div>", unsafe_allow_html=True)  # Aparece **text**

# CORRETO - Usar tags HTML
st.markdown(f"<div><strong>{text}</strong></div>", unsafe_allow_html=True)
```

### 2. st.expander NÃO suporta HTML
```python
# ERRADO - HTML aparece como texto literal
st.expander("<span class='material-icons'>add</span>Adicionar")

# CORRETO - Usar texto puro
st.expander("Adicionar")
```

### 3. st.success/error/warning/info NÃO suportam unsafe_allow_html
```python
# ERRADO - Vai dar erro TypeError
st.success("Mensagem", unsafe_allow_html=True)

# CORRETO - Usar st.markdown para HTML customizado
st.markdown('<div style="color: green;">✓ Mensagem</div>', unsafe_allow_html=True)
```

### 4. Espaçamento entre ícone e texto em HTML
```python
# ERRADO - Fica colado
"<span class='material-icons'>icon</span>Texto"

# CORRETO - Adicionar espaço ou margin
"<span class='material-icons' style='margin-right: 0.5rem;'>icon</span> Texto"
```

### 5. Material Icons em botões - usar sintaxe nativa
```python
# ERRADO - HTML não funciona em botões
st.button("<span class='material-icons'>save</span> Salvar", unsafe_allow_html=True)

# CORRETO - Usar sintaxe nativa do Streamlit
st.button(":material/save: Salvar")
```

### 6. st.navigation não suporta HTML em títulos de grupos
```python
# ERRADO - HTML aparece literal
pages = {
    "<span class='material-icons'>home</span> Principal": [...]
}

# CORRETO - Usar texto puro
pages = {
    "Principal": [...]
}
```

## Checklist Final ATUALIZADO V4 - PROFISSIONALIZAÇÃO COMPLETA
- [ ] TODOS os emojis do MAPEAMENTO V3 foram processados
- [ ] TODOS os textos em inglês traduzidos para português
- [ ] TODOS os headers têm Material Icons
- [ ] TODOS os botões têm Material Icons
- [ ] TODOS os subheaders têm Material Icons onde aplicável
- [ ] Emojis em st.button() substituídos por :material/icon:
- [ ] Emojis em st.info/success/warning/error REMOVIDOS
- [ ] Emojis em st.metric() REMOVIDOS
- [ ] Emojis em st.subheader/header REMOVIDOS
- [ ] Emojis em st.tabs() REMOVIDOS dos labels
- [ ] Emojis em st.expander() REMOVIDOS do label
- [ ] st.markdown() com HTML tem unsafe_allow_html=True
- [ ] NENHUM <span class visível na interface
- [ ] Sintaxe Python validada para cada arquivo
- [ ] CSS adaptativo funcionando
- [ ] Testado em tema claro ✓
- [ ] Testado em tema escuro ✓
- [ ] Interface 100% em português
- [ ] Ícones consistentes em toda aplicação
- [ ] Documentação de mudanças criada
- [ ] TODOS os arquivos .py verificados (NENHUM pulado)
- [ ] service_management.py corrigido (métricas e títulos)
- [ ] logs.py corrigido (métricas e títulos)
- [ ] settings.py corrigido (métricas e títulos)
- [ ] TODAS as métricas usando create_metric_card (ícone à direita)
- [ ] TODOS os títulos com Material Icons
- [ ] TODOS os botões com :material/icon: