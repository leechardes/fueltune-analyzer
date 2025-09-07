# VEHICLE-INTEGRATION-IMPLEMENTATION

## Objetivo
Integrar o sistema de veículos com todas as páginas existentes do FuelTune, adicionando seletores de veículo, filtros por veículo e contexto global de veículo ativo.

## Padrões de Desenvolvimento
Este agente segue os padrões definidos em:
- /srv/projects/shared/docs/agents/development/A04-STREAMLIT-PROFESSIONAL.md

### Princípios Fundamentais:
1. **ZERO emojis** - Usar apenas Material Design Icons
2. **Interface profissional** - Sem decorações infantis  
3. **CSS adaptativo** - Funciona em tema claro e escuro
4. **Português brasileiro** - Todos os textos traduzidos
5. **Ícones consistentes** - Material Icons em todos os componentes

## Análise das Páginas Existentes

### Páginas Identificadas para Integração:
1. **app.py** - Sidebar com seletor global
2. **upload.py** - Associar sessões ao veículo
3. **dashboard.py** - Métricas filtradas por veículo
4. **analysis.py** - Análises contextualizadas
5. **performance.py** - Cálculos com dados reais do veículo
6. **consumption.py** - Análise de consumo por veículo
7. **imu.py** - Dados de aceleração por veículo
8. **reports.py** - Relatórios por veículo

## Implementação por Página

### 1. Modificar app.py - Contexto Global

#### 1.1 Adicionar Imports
```python
# Adicionar no topo do app.py
from src.ui.components.vehicle_selector import render_vehicle_selector, get_vehicle_context, set_vehicle_context
from src.data.database import get_vehicle_by_id
```

#### 1.2 Adicionar Seletor na Sidebar
```python
# Modificar a função main() em app.py
def main():
    """Função principal da aplicação."""
    
    # Configuração da página
    st.set_page_config(
        page_title="FuelTune",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Aplicar estilos
    apply_global_styles()
    
    # Sidebar com navegação e contexto de veículo
    with st.sidebar:
        st.markdown('''
            <div class="sidebar-header">
                <span class="material-icons" style="font-size: 2rem; margin-right: 0.5rem;">speed</span>
                <h1>FuelTune</h1>
            </div>
        ''', unsafe_allow_html=True)
        
        st.divider()
        
        # Seletor de Veículo Global
        st.markdown("### Contexto do Veículo")
        selected_vehicle_id = render_vehicle_selector(
            label="Veículo Ativo",
            key="global_vehicle_context",
            help_text="Todos os dados serão filtrados por este veículo"
        )
        
        # Atualizar contexto global
        if selected_vehicle_id:
            set_vehicle_context(selected_vehicle_id)
            
            # Mostrar informações resumidas do veículo
            vehicle = get_vehicle_by_id(selected_vehicle_id)
            if vehicle:
                st.info(f"📊 Analisando: **{vehicle.display_name}**")
        else:
            set_vehicle_context(None)
        
        st.divider()
        
        # Menu de navegação
        st.markdown("### Navegação")
        
        # Lista de páginas com ícones Material Design
        pages = {
            "Dashboard": {"icon": "dashboard", "emoji": None},
            "Upload de Dados": {"icon": "cloud_upload", "emoji": None},
            "Análise de Dados": {"icon": "analytics", "emoji": None},
            "Performance": {"icon": "speed", "emoji": None},
            "Consumo": {"icon": "local_gas_station", "emoji": None},
            "Dados IMU": {"icon": "accelerometer", "emoji": None},
            "Relatórios": {"icon": "assessment", "emoji": None},
            "Veículos": {"icon": "directions_car", "emoji": None},
            "Versionamento": {"icon": "history", "emoji": None}
        }
        
        # Renderizar menu
        for page_name, page_info in pages.items():
            icon = page_info["icon"]
            if st.button(
                f'{page_name}',
                key=f"nav_{page_name}",
                use_container_width=True
            ):
                st.session_state.current_page = page_name
        
        # Página atual
        current_page = st.session_state.get("current_page", "Dashboard")
        
        # Aviso se não há veículo selecionado
        if not selected_vehicle_id and current_page != "Veículos":
            st.warning("⚠️ Selecione um veículo para visualizar os dados")
    
    # Renderizar página selecionada
    render_selected_page(current_page, selected_vehicle_id)

def render_selected_page(page_name: str, vehicle_id: Optional[str]):
    """Renderiza a página selecionada com contexto do veículo."""
    
    if page_name == "Dashboard":
        from src.ui.pages.dashboard import show_dashboard
        show_dashboard(vehicle_id)
        
    elif page_name == "Upload de Dados":
        from src.ui.pages.upload import show_upload_page
        show_upload_page(vehicle_id)
        
    elif page_name == "Análise de Dados":
        from src.ui.pages.analysis import show_analysis_page
        show_analysis_page(vehicle_id)
        
    elif page_name == "Performance":
        from src.ui.pages.performance import show_performance_page
        show_performance_page(vehicle_id)
        
    elif page_name == "Consumo":
        from src.ui.pages.consumption import show_consumption_page
        show_consumption_page(vehicle_id)
        
    elif page_name == "Dados IMU":
        from src.ui.pages.imu import show_imu_page
        show_imu_page(vehicle_id)
        
    elif page_name == "Relatórios":
        from src.ui.pages.reports import show_reports_page
        show_reports_page(vehicle_id)
        
    elif page_name == "Veículos":
        from src.ui.pages.vehicles import show_vehicles_page
        show_vehicles_page()
        
    elif page_name == "Versionamento":
        from src.ui.pages.versioning import show_versioning_page
        show_versioning_page(vehicle_id)
```

### 2. Modificar src/ui/pages/upload.py

#### 2.1 Atualizar Função Principal
```python
# Modificar show_upload_page para aceitar vehicle_id
def show_upload_page(vehicle_id: Optional[str] = None):
    """Página de upload com seleção obrigatória de veículo."""
    
    st.markdown('''
        <div class="main-header">
            <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">
                cloud_upload
            </span>
            Upload de Dados de Telemetria
        </div>
    ''', unsafe_allow_html=True)
    
    # Verificar se há veículo selecionado
    if not vehicle_id:
        st.error("⚠️ Selecione um veículo na barra lateral antes de fazer upload de dados.")
        st.info("💡 Os dados de telemetria precisam ser associados a um veículo específico.")
        return
    
    # Mostrar informações do veículo
    vehicle = get_vehicle_by_id(vehicle_id)
    if vehicle:
        st.success(f"📊 Upload será associado ao veículo: **{vehicle.display_name}**")
        
        with st.expander("ℹ️ Informações do Veículo", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Motor:** {vehicle.technical_summary}")
                st.write(f"**Potência:** {vehicle.estimated_power} HP" if vehicle.estimated_power else "**Potência:** Não especificada")
            with col2:
                st.write(f"**Peso:** {vehicle.curb_weight} kg" if vehicle.curb_weight else "**Peso:** Não especificado")
                st.write(f"**Combustível:** {vehicle.fuel_type}" if vehicle.fuel_type else "**Combustível:** Não especificado")
    
    # Continuar com upload normal, mas passar vehicle_id
    show_upload_interface(vehicle_id)

def show_upload_interface(vehicle_id: str):
    """Interface de upload com vehicle_id."""
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV de telemetria",
        type=['csv'],
        help="Arquivo CSV com dados do FuelTech"
    )
    
    if uploaded_file is not None:
        try:
            # Processar arquivo
            df = pd.read_csv(uploaded_file)
            
            # Validar dados
            is_valid, validation_errors = validate_csv_data(df)
            
            if is_valid:
                st.success("✅ Arquivo válido! Dados prontos para importação.")
                
                # Mostrar preview
                show_data_preview(df)
                
                # Botão de importação
                if st.button("📥 Importar Dados", type="primary"):
                    import_data_with_vehicle(df, uploaded_file.name, vehicle_id)
            else:
                st.error("❌ Arquivo inválido:")
                for error in validation_errors:
                    st.error(f"• {error}")
                
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")

def import_data_with_vehicle(df: pd.DataFrame, filename: str, vehicle_id: str):
    """Importa dados associando ao veículo."""
    
    try:
        with st.spinner("Importando dados..."):
            # Criar sessão com vehicle_id
            session_data = {
                "filename": filename,
                "file_size": len(df),
                "vehicle_id": vehicle_id,  # Associar ao veículo
                "created_at": datetime.now(),
                "data_format_version": "2.0"
            }
            
            session_id = create_data_session(session_data)
            
            # Importar dados da sessão
            imported_count = import_session_data(session_id, df)
            
            st.success(f"✅ {imported_count} registros importados com sucesso!")
            st.balloons()
            
            # Mostrar estatísticas
            show_import_statistics(session_id, vehicle_id)
            
    except Exception as e:
        st.error(f"Erro na importação: {str(e)}")

def show_import_statistics(session_id: str, vehicle_id: str):
    """Mostra estatísticas da importação."""
    
    vehicle = get_vehicle_by_id(vehicle_id)
    stats = get_vehicle_statistics(vehicle_id)
    
    st.markdown("### 📊 Estatísticas da Importação")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Veículo", vehicle.name if vehicle else "N/A")
    
    with col2:
        st.metric("Total de Sessões", stats.get("session_count", 0))
    
    with col3:
        st.metric("Total de Registros", f"{stats.get('core_data_count', 0):,}")
    
    with col4:
        if stats.get("last_session_date"):
            st.metric("Última Sessão", stats["last_session_date"].strftime("%d/%m/%Y"))
```

### 3. Modificar src/ui/pages/dashboard.py

```python
# Modificar função principal para aceitar vehicle_id
def show_dashboard(vehicle_id: Optional[str] = None):
    """Dashboard principal com dados filtrados por veículo."""
    
    st.markdown('''
        <div class="main-header">
            <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">
                dashboard
            </span>
            Dashboard Principal
        </div>
    ''', unsafe_allow_html=True)
    
    if not vehicle_id:
        st.info("📋 Selecione um veículo na barra lateral para visualizar o dashboard.")
        return
    
    # Obter dados do veículo
    vehicle = get_vehicle_by_id(vehicle_id)
    if not vehicle:
        st.error("❌ Veículo não encontrado.")
        return
    
    # Header com informações do veículo
    show_vehicle_header(vehicle)
    
    # Métricas principais
    show_vehicle_metrics(vehicle_id)
    
    # Gráficos principais
    show_dashboard_charts(vehicle_id)
    
    # Sessões recentes
    show_recent_sessions(vehicle_id)

def show_vehicle_header(vehicle):
    """Header com informações do veículo ativo."""
    
    st.markdown(f'''
        <div class="vehicle-context-header">
            <div class="vehicle-info">
                <span class="material-icons" style="font-size: 1.5rem; margin-right: 0.5rem;">
                    directions_car
                </span>
                <div class="vehicle-details">
                    <h2>{vehicle.display_name}</h2>
                    <p>{vehicle.technical_summary}</p>
                </div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

def show_vehicle_metrics(vehicle_id: str):
    """Métricas específicas do veículo."""
    
    # Obter estatísticas do veículo
    stats = get_vehicle_statistics(vehicle_id)
    vehicle = get_vehicle_by_id(vehicle_id)
    
    # Obter dados de performance
    performance_data = get_vehicle_performance_summary(vehicle_id)
    
    st.markdown("### 📊 Métricas do Veículo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Sessões Registradas",
            stats.get("session_count", 0),
            help="Total de sessões de dados para este veículo"
        )
    
    with col2:
        st.metric(
            "Registros de Telemetria",
            f"{stats.get('core_data_count', 0):,}",
            help="Total de pontos de dados coletados"
        )
    
    with col3:
        max_power = performance_data.get("max_power", 0)
        estimated_power = vehicle.estimated_power if vehicle else 0
        power_diff = max_power - estimated_power if estimated_power else None
        
        st.metric(
            "Potência Máxima Registrada",
            f"{max_power:.1f} HP",
            delta=f"{power_diff:+.1f} HP" if power_diff else None,
            help="Máxima potência registrada vs estimada"
        )
    
    with col4:
        max_torque = performance_data.get("max_torque", 0)
        st.metric(
            "Torque Máximo",
            f"{max_torque:.1f} Nm",
            help="Máximo torque registrado"
        )

def show_dashboard_charts(vehicle_id: str):
    """Gráficos do dashboard filtrados por veículo."""
    
    # Obter dados do veículo
    recent_data = get_recent_vehicle_data(vehicle_id, limit=1000)
    
    if recent_data.empty:
        st.info("📈 Nenhum dado encontrado para este veículo. Faça upload de dados primeiro.")
        return
    
    st.markdown("### 📈 Gráficos de Análise")
    
    tab1, tab2, tab3 = st.tabs(["Performance", "Motor", "Sensores"])
    
    with tab1:
        show_performance_charts(recent_data)
    
    with tab2:
        show_engine_charts(recent_data)
    
    with tab3:
        show_sensor_charts(recent_data)

def show_recent_sessions(vehicle_id: str):
    """Lista das sessões recentes do veículo."""
    
    sessions = get_recent_vehicle_sessions(vehicle_id, limit=10)
    
    if not sessions:
        st.info("📋 Nenhuma sessão encontrada para este veículo.")
        return
    
    st.markdown("### 📋 Sessões Recentes")
    
    for session in sessions:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{session.filename}**")
                st.caption(f"Criado em: {session.created_at.strftime('%d/%m/%Y %H:%M')}")
            
            with col2:
                st.metric("Registros", f"{session.record_count:,}")
            
            with col3:
                st.metric("Duração", f"{session.duration_minutes:.1f} min")
            
            with col4:
                if st.button(f"📊 Analisar", key=f"analyze_{session.id}"):
                    st.switch_page("pages/analysis")
                    st.session_state.selected_session_id = session.id
```

### 4. Modificar Outras Páginas de Análise

#### 4.1 src/ui/pages/analysis.py
```python
def show_analysis_page(vehicle_id: Optional[str] = None):
    """Página de análise com contexto de veículo."""
    
    if not vehicle_id:
        st.info("🔍 Selecione um veículo para visualizar as análises.")
        return
    
    vehicle = get_vehicle_by_id(vehicle_id)
    
    st.markdown(f'''
        <div class="main-header">
            <span class="material-icons" style="vertical-align: middle; margin-right: 0.5rem; font-size: 2.5rem;">
                analytics
            </span>
            Análise de Dados - {vehicle.display_name if vehicle else 'Veículo Desconhecido'}
        </div>
    ''', unsafe_allow_html=True)
    
    # Filtrar dados por veículo
    sessions = get_vehicle_sessions(vehicle_id)
    
    if not sessions:
        st.info("📊 Nenhuma sessão encontrada para este veículo.")
        return
    
    # Seletor de sessão
    selected_session = st.selectbox(
        "Selecionar Sessão",
        sessions,
        format_func=lambda s: f"{s.filename} ({s.created_at.strftime('%d/%m/%Y')})"
    )
    
    if selected_session:
        show_session_analysis(selected_session, vehicle)
```

#### 4.2 src/ui/pages/performance.py
```python
def show_performance_page(vehicle_id: Optional[str] = None):
    """Página de performance com dados reais do veículo."""
    
    if not vehicle_id:
        st.info("🏎️ Selecione um veículo para análise de performance.")
        return
    
    vehicle = get_vehicle_by_id(vehicle_id)
    
    # Usar dados reais do veículo para cálculos
    vehicle_weight = vehicle.curb_weight if vehicle and vehicle.curb_weight else 1400
    estimated_power = vehicle.estimated_power if vehicle and vehicle.estimated_power else None
    
    # Cálculos de performance com dados reais
    performance_data = calculate_vehicle_performance(
        vehicle_id=vehicle_id,
        vehicle_weight=vehicle_weight,
        estimated_power=estimated_power
    )
    
    show_performance_analysis(performance_data, vehicle)
```

### 5. Criar Funções Auxiliares

#### 5.1 src/data/vehicle_queries.py
```python
"""
Queries específicas para dados filtrados por veículo.
"""

def get_vehicle_sessions(vehicle_id: str) -> List[DataSession]:
    """Obtém todas as sessões de um veículo."""
    try:
        with get_db_session() as session:
            return session.query(DataSession).filter(
                DataSession.vehicle_id == vehicle_id
            ).order_by(DataSession.created_at.desc()).all()
    except Exception as e:
        logger.error(f"Erro ao buscar sessões do veículo {vehicle_id}: {str(e)}")
        return []

def get_recent_vehicle_data(vehicle_id: str, limit: int = 1000) -> pd.DataFrame:
    """Obtém dados recentes de telemetria do veículo."""
    try:
        with get_db_session() as session:
            query = session.query(FuelTechCoreData).join(DataSession).filter(
                DataSession.vehicle_id == vehicle_id
            ).order_by(FuelTechCoreData.timestamp.desc()).limit(limit)
            
            return pd.read_sql(query.statement, session.bind)
    except Exception as e:
        logger.error(f"Erro ao buscar dados do veículo {vehicle_id}: {str(e)}")
        return pd.DataFrame()

def get_vehicle_performance_summary(vehicle_id: str) -> dict:
    """Calcula resumo de performance do veículo."""
    try:
        with get_db_session() as session:
            # Buscar máximos registrados
            query = session.query(
                func.max(FuelTechCoreData.engine_power).label('max_power'),
                func.max(FuelTechCoreData.engine_torque).label('max_torque'),
                func.max(FuelTechCoreData.engine_rpm).label('max_rpm'),
                func.max(FuelTechCoreData.map_pressure).label('max_boost'),
                func.avg(FuelTechCoreData.engine_temp).label('avg_temp')
            ).join(DataSession).filter(
                DataSession.vehicle_id == vehicle_id
            ).first()
            
            return {
                'max_power': query.max_power or 0,
                'max_torque': query.max_torque or 0,
                'max_rpm': query.max_rpm or 0,
                'max_boost': query.max_boost or 0,
                'avg_temp': query.avg_temp or 0
            }
    except Exception as e:
        logger.error(f"Erro ao calcular performance do veículo {vehicle_id}: {str(e)}")
        return {}

def calculate_vehicle_performance(vehicle_id: str, vehicle_weight: float, estimated_power: Optional[float] = None) -> dict:
    """Calcula métricas de performance com dados reais do veículo."""
    
    data = get_recent_vehicle_data(vehicle_id)
    
    if data.empty:
        return {}
    
    # Cálculos específicos com peso real
    power_to_weight = data['engine_power'] / vehicle_weight if vehicle_weight > 0 else 0
    
    # Comparação com potência estimada
    power_efficiency = data['engine_power'] / estimated_power if estimated_power else 1
    
    return {
        'max_power_to_weight': power_to_weight.max(),
        'avg_power_to_weight': power_to_weight.mean(),
        'power_efficiency': power_efficiency.mean(),
        'max_recorded_power': data['engine_power'].max(),
        'vehicle_weight': vehicle_weight,
        'estimated_power': estimated_power
    }
```

### 6. Atualizar Sistema de Cache

#### 6.1 Modificar src/data/cache.py
```python
# Adicionar suporte a cache por veículo

def get_cache_key_with_vehicle(base_key: str, vehicle_id: Optional[str] = None) -> str:
    """Gera chave de cache incluindo vehicle_id."""
    if vehicle_id:
        return f"{base_key}_vehicle_{vehicle_id}"
    return base_key

def get_cached_vehicle_data(vehicle_id: str, data_type: str) -> Optional[pd.DataFrame]:
    """Obtém dados cachados específicos do veículo."""
    cache_key = get_cache_key_with_vehicle(data_type, vehicle_id)
    return get_cached_data(cache_key)

def cache_vehicle_data(vehicle_id: str, data_type: str, data: pd.DataFrame, ttl: int = 3600):
    """Armazena dados em cache por veículo."""
    cache_key = get_cache_key_with_vehicle(data_type, vehicle_id)
    cache_data(cache_key, data, ttl)

def clear_vehicle_cache(vehicle_id: str):
    """Limpa cache de um veículo específico."""
    cache_keys = get_cache_keys()
    vehicle_keys = [key for key in cache_keys if f"_vehicle_{vehicle_id}" in key]
    
    for key in vehicle_keys:
        clear_cache_key(key)
    
    logger.info(f"Cache limpo para veículo {vehicle_id}: {len(vehicle_keys)} entradas removidas")
```

## Checklist de Integração

### Contexto Global
- [ ] Seletor de veículo adicionado na sidebar do app.py
- [ ] Contexto global de veículo implementado
- [ ] Função set_vehicle_context criada
- [ ] Função get_vehicle_context implementada

### Página Upload
- [ ] Upload agora exige seleção de veículo
- [ ] Dados são associados automaticamente ao veículo
- [ ] Validação de veículo antes da importação
- [ ] Estatísticas pós-importação por veículo

### Dashboard
- [ ] Métricas filtradas por veículo selecionado
- [ ] Header com informações do veículo ativo
- [ ] Gráficos contextualizado por veículo
- [ ] Lista de sessões recentes do veículo

### Páginas de Análise
- [ ] analysis.py aceita parâmetro vehicle_id
- [ ] performance.py usa dados reais do veículo
- [ ] consumption.py filtra por veículo
- [ ] imu.py contextualizado por veículo
- [ ] reports.py gera relatórios por veículo

### Queries e Performance
- [ ] Funções de query por veículo criadas
- [ ] Cache por veículo implementado
- [ ] Índices de performance verificados
- [ ] Queries otimizadas para filtros

### Interface e UX
- [ ] Avisos quando nenhum veículo selecionado
- [ ] Headers com informações do veículo ativo
- [ ] Material Design Icons consistentes
- [ ] Zero emojis na interface

## Testes de Integração

### 1. Teste de Fluxo Completo
```python
def test_complete_vehicle_workflow():
    """Testa fluxo completo: cadastro -> upload -> análise."""
    
    # 1. Cadastrar veículo
    vehicle_id = create_vehicle({
        "name": "Test Vehicle",
        "brand": "Honda",
        "year": 2020
    })
    
    # 2. Fazer upload associado
    test_data = create_test_telemetry_data()
    session_id = import_data_with_vehicle(test_data, "test.csv", vehicle_id)
    
    # 3. Verificar dados na dashboard
    stats = get_vehicle_statistics(vehicle_id)
    assert stats["session_count"] > 0
    assert stats["core_data_count"] > 0
    
    # 4. Verificar análises
    performance_data = get_vehicle_performance_summary(vehicle_id)
    assert performance_data["max_power"] > 0
```

### 2. Teste de Performance com Filtros
```python
def test_vehicle_filter_performance():
    """Testa performance das queries com filtro de veículo."""
    
    import time
    
    # Criar múltiplos veículos e dados
    vehicle_ids = []
    for i in range(5):
        vid = create_vehicle({"name": f"Vehicle {i}"})
        vehicle_ids.append(vid)
        
        # Adicionar dados para cada veículo
        for j in range(100):
            create_test_session(vid)
    
    # Testar performance da query filtrada
    start_time = time.time()
    
    for vid in vehicle_ids:
        sessions = get_vehicle_sessions(vid)
        assert len(sessions) == 100
    
    elapsed = time.time() - start_time
    assert elapsed < 2.0, f"Query muito lenta: {elapsed:.2f}s"
```

## Riscos e Mitigações

### Riscos Técnicos
1. **Performance**: Queries com JOIN podem ser lentas
2. **Cache**: Cache existente pode ficar inválido
3. **Estado**: Mudança de veículo pode causar inconsistências
4. **Dados Órfãos**: Sessões sem veículo podem quebrar a aplicação

### Mitigações
1. **Índices adequados** nas foreign keys
2. **Cache por veículo** implementado
3. **Limpeza de estado** ao trocar veículo
4. **Migração completa** antes da integração

## Próximos Passos

1. **Executar VEHICLE-MODEL-IMPLEMENTATION** primeiro
2. **Executar VEHICLE-MIGRATION-IMPLEMENTATION** para dados existentes
3. **Implementar esta integração** gradualmente por página
4. **Testar extensivamente** cada integração
5. **Otimizar performance** conforme necessário

---

**Prioridade:** Alta  
**Complexidade:** Alta  
**Tempo Estimado:** 2-3 dias  
**Dependências:** VEHICLE-MODEL-IMPLEMENTATION, VEHICLE-MIGRATION-IMPLEMENTATION  
**Bloqueia:** Utilização completa do sistema de veículos