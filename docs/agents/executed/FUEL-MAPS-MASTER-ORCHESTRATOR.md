# FUEL-MAPS-MASTER-ORCHESTRATOR

## Objetivo
Orquestrar a implementação completa e sistemática do sistema de mapas de injeção, executando os três agentes especializados em sequência e garantindo a integração perfeita entre todos os componentes do sistema.

## Contexto
Você é um especialista em orquestração de sistemas automotivos complexos com foco em integração e testes. Deve coordenar a execução sequencial dos agentes de implementação, validar cada etapa, integrar componentes e garantir que o sistema final funcione perfeitamente.

## Padrões de Desenvolvimento
Este agente segue os padrões definidos em:
- /srv/projects/shared/docs/agents/development/A04-STREAMLIT-PROFESSIONAL.md

### Princípios Fundamentais:
1. **ZERO emojis** - Usar apenas Material Design Icons
2. **Interface profissional** - Sem decorações infantis  
3. **CSS adaptativo** - Funciona em tema claro e escuro
4. **Português brasileiro** - Todos os textos traduzidos
5. **Ícones consistentes** - Material Icons em todos os componentes
6. **Varredura PROFUNDA** - Não deixar NENHUM emoji escapar
7. **NUNCA usar !important no CSS** - Para permitir adaptação de temas

## Entrada Esperada
- **Diretório base**: /home/lee/projects/fueltune-streamlit/
- **Documentação**: docs/FUEL-MAPS-SPECIFICATION.md
- **Sistema base existente**: src/data/models.py
- **Agentes criados**: agents/pending/FUEL-MAPS-*.md

## Agentes a Executar (em ordem)

### 1. FUEL-MAPS-MODEL-IMPLEMENTATION
**Responsabilidade**: Estrutura de dados e modelos
**Validação**: Tabelas criadas, relacionamentos corretos, migrations funcionais

### 2. FUEL-MAPS-BANKS-IMPLEMENTATION  
**Responsabilidade**: Sistema de bancadas A/B
**Validação**: Configuração funcional, duplicação de mapas, cálculos corretos

### 3. FUEL-MAPS-UI-IMPLEMENTATION
**Responsabilidade**: Interface de usuário completa
**Validação**: Editores funcionais, visualizações corretas, import/export operacional

## Processo de Execução Sistemático

### FASE 1: PREPARAÇÃO E VALIDAÇÃO INICIAL

#### 1.1 Verificação do Ambiente
```python
# Verificações obrigatórias antes do início:
- [ ] Documentação FUEL-MAPS-SPECIFICATION.md presente
- [ ] Diretório /home/lee/projects/fueltune-streamlit/ acessível
- [ ] Banco de dados SQLite funcional
- [ ] Sistema Alembic configurado
- [ ] Ambiente Python com dependências necessárias
- [ ] Padrão A04-STREAMLIT-PROFESSIONAL disponível
```

#### 1.2 Análise da Estrutura Existente
```bash
# Comandos de verificação:
ls -la /home/lee/projects/fueltune-streamlit/src/data/
ls -la /home/lee/projects/fueltune-streamlit/migrations/
grep -r "class Vehicle" /home/lee/projects/fueltune-streamlit/src/
```

#### 1.3 Backup de Segurança
```bash
# Criar backup completo antes das alterações:
cp -r /home/lee/projects/fueltune-streamlit/ /tmp/fueltune-backup-$(date +%Y%m%d_%H%M%S)
```

### FASE 2: EXECUÇÃO DO AGENTE 1 - MODELS

#### 2.1 Executar FUEL-MAPS-MODEL-IMPLEMENTATION
```python
# Tarefas do Agente 1:
1. Analisar src/data/models.py atual
2. Adicionar campos de bancadas ao modelo Vehicle
3. Criar modelos FuelMap, MapData2D, MapData3D, MapAxisData
4. Criar tabelas especializadas (MapAxisRPM, MapAxisMAP, etc.)
5. Implementar sistema de versionamento
6. Criar migrations Alembic
7. Implementar funções utilitárias de interpolação
8. Criar validadores de dados
```

#### 2.2 Validações da Fase 1
```python
# Checklist obrigatório após Agente 1:
- [ ] Arquivo src/data/fuel_maps_models.py criado
- [ ] Todas as classes de modelo implementadas
- [ ] Relacionamentos entre tabelas funcionais
- [ ] Migrations criadas em migrations/versions/
- [ ] Backup automático antes de alterações
- [ ] Validações de dados implementadas
- [ ] Funções de interpolação testadas
- [ ] ZERO emojis no código gerado
- [ ] Comentários em português
```

#### 2.3 Testes da Fase 1
```python
# Testes obrigatórios:
def test_model_creation():
    """Testar criação de todas as tabelas."""
    # Executar migrations
    # Verificar estrutura do banco
    # Testar inserção de dados básicos
    pass

def test_relationships():
    """Testar relacionamentos entre modelos."""
    # Criar veículo de teste
    # Criar mapas de teste
    # Verificar integridade referencial
    pass

def test_interpolation():
    """Testar funções de interpolação."""
    # Dados de teste
    # Verificar regras da especificação
    # Validar resultados
    pass
```

### FASE 3: EXECUÇÃO DO AGENTE 2 - BANKS

#### 3.1 Executar FUEL-MAPS-BANKS-IMPLEMENTATION
```python
# Tarefas do Agente 2:
1. Criar componente BankConfigurator
2. Implementar cálculos de vazão e duty cycle
3. Criar sistema de duplicação de mapas
4. Implementar interface de configuração
5. Criar seletor de bancadas
6. Implementar sincronização A↔B
7. Criar página de configuração completa
8. Implementar diagnósticos automáticos
```

#### 3.2 Validações da Fase 2
```python
# Checklist obrigatório após Agente 2:
- [ ] Componente BankConfigurator funcional
- [ ] Cálculos de vazão corretos
- [ ] Duplicação de mapas funcionando
- [ ] Interface de configuração operacional
- [ ] Validações de conflito implementadas
- [ ] Sincronização entre bancadas testada
- [ ] Diagnósticos automáticos funcionais
- [ ] Material Icons em todos os botões/headers
- [ ] Interface 100% em português
```

#### 3.3 Testes da Fase 2
```python
# Testes obrigatórios:
def test_bank_configuration():
    """Testar configuração completa de bancadas."""
    # Criar veículo de teste
    # Configurar bancadas A e B
    # Validar cálculos de vazão
    # Testar detecção de conflitos
    pass

def test_map_duplication():
    """Testar duplicação de mapas entre bancadas."""
    # Criar mapas na bancada A
    # Duplicar para bancada B
    # Verificar integridade dos dados
    # Testar sincronização
    pass
```

### FASE 4: EXECUÇÃO DO AGENTE 3 - INTERFACE

#### 4.1 Executar FUEL-MAPS-UI-IMPLEMENTATION
```python
# Tarefas do Agente 3:
1. Criar página principal fuel_maps.py
2. Implementar editores 2D e 3D
3. Criar editor de eixos
4. Implementar visualizações Plotly
5. Criar sistema de import/export
6. Implementar interpolação automática
7. Criar validações em tempo real
8. Integrar todos os componentes
```

#### 4.2 Validações da Fase 3
```python
# Checklist obrigatório após Agente 3:
- [ ] Página fuel_maps.py funcional
- [ ] Editor 2D operacional
- [ ] Editor 3D operacional
- [ ] Configuração de eixos funcionando
- [ ] Visualizações Plotly responsivas
- [ ] Import/export FTManager funcional
- [ ] Interpolação em tempo real
- [ ] Todas as validações implementadas
- [ ] ZERO emojis na interface
- [ ] Material Icons consistentes
```

#### 4.3 Testes da Fase 3
```python
# Testes obrigatórios:
def test_2d_editor():
    """Testar editor de mapas 2D."""
    # Carregar mapa 2D
    # Editar valores
    # Salvar alterações
    # Verificar interpolação
    pass

def test_3d_editor():
    """Testar editor de mapas 3D."""
    # Carregar mapa 3D
    # Editar células
    # Visualizar superfície
    # Testar heatmap
    pass

def test_import_export():
    """Testar sistema completo de import/export."""
    # Exportar mapas para FTM
    # Importar de volta
    # Verificar integridade
    # Testar formatos CSV/JSON
    pass
```

### FASE 5: INTEGRAÇÃO E VALIDAÇÃO FINAL

#### 5.1 Integração Completa
```python
# Tarefas de integração:
1. Conectar todos os componentes
2. Integrar ao menu principal da aplicação
3. Criar dados de demonstração
4. Implementar sistema de ajuda
5. Otimizar performance
6. Criar documentação de usuário
```

#### 5.2 Testes de Integração
```python
def test_end_to_end_workflow():
    """Teste completo do fluxo de trabalho."""
    # 1. Criar veículo
    # 2. Configurar bancadas
    # 3. Criar mapas padrão
    # 4. Editar mapas 2D e 3D
    # 5. Configurar eixos
    # 6. Exportar para FTManager
    # 7. Importar de volta
    # 8. Validar integridade completa
    pass

def test_performance():
    """Testar performance com dados reais."""
    # Criar 1000+ pontos de dados
    # Testar responsividade da interface
    # Validar tempo de renderização
    # Verificar uso de memória
    pass
```

### FASE 6: VALIDAÇÃO A04-STREAMLIT-PROFESSIONAL

#### 6.1 Verificação Sistemática de Emojis
```bash
# Comandos obrigatórios de verificação:
grep -r "[\u{1F300}-\u{1F9FF}]" /home/lee/projects/fueltune-streamlit/src/
grep -r "[\u{2600}-\u{27BF}]" /home/lee/projects/fueltune-streamlit/src/
find /home/lee/projects/fueltune-streamlit/ -name "*.py" -exec grep -l "[🚀✅❌⚠️📊📈]" {} \;
```

#### 6.2 Verificação de Material Icons
```bash
# Verificar uso consistente de Material Icons:
grep -r "material-icons" /home/lee/projects/fueltune-streamlit/src/
grep -r ":material/" /home/lee/projects/fueltune-streamlit/src/
```

#### 6.3 Verificação de Idioma
```bash
# Verificar textos em inglês:
grep -rE "(Settings|Dashboard|Edit|Save|Cancel|Delete|Import|Export)" /home/lee/projects/fueltune-streamlit/src/
```

### FASE 7: DOCUMENTAÇÃO E ENTREGA

#### 7.1 Criar Documentação de Sistema
```markdown
# Arquivo: docs/FUEL-MAPS-SYSTEM-GUIDE.md

## Guia do Sistema de Mapas de Injeção

### Visão Geral
- Arquitetura do sistema
- Fluxo de dados
- Componentes principais

### Configuração
- Setup inicial
- Configuração de bancadas
- Criação de mapas padrão

### Uso Diário
- Edição de mapas 2D
- Edição de mapas 3D
- Import/export de dados

### Solução de Problemas
- Problemas comuns
- Logs de debug
- Contato para suporte
```

#### 7.2 Criar Guia de Desenvolvimento
```markdown
# Arquivo: docs/FUEL-MAPS-DEVELOPMENT.md

## Guia para Desenvolvedores

### Arquitetura
- Modelos de dados
- Componentes da interface
- Fluxo de execução

### Extensões
- Como adicionar novos tipos de mapas
- Customização de editores
- Novos formatos de import/export

### Testes
- Estrutura de testes
- Como executar testes
- Criação de novos testes
```

## Métricas de Sucesso

### Funcionalidades Implementadas
- [ ] 100% dos mapas documentados implementados
- [ ] Sistema completo de bancadas A/B
- [ ] Editores 2D e 3D funcionais
- [ ] Import/export FTManager compatível
- [ ] Interpolação automática operacional
- [ ] Validações em tempo real
- [ ] Interface responsiva e profissional

### Qualidade de Código
- [ ] ZERO emojis em todo o sistema
- [ ] 100% dos textos em português
- [ ] Material Icons em todos os componentes
- [ ] CSS adaptativo funcionando
- [ ] Performance otimizada
- [ ] Tratamento de erros robusto

### Compatibilidade
- [ ] Formato .ftm 100% compatível
- [ ] Dados intercambiáveis com FTManager
- [ ] Preservação de precisão numérica
- [ ] Suporte a todos os tipos de mapas especificados

### Interface de Usuário
- [ ] Navegação intuitiva
- [ ] Visualizações profissionais
- [ ] Feedback visual adequado
- [ ] Tempo de resposta < 2 segundos
- [ ] Interface adaptativa (tema claro/escuro)

## Plano de Execução Cronológico

### Dia 1: Preparação e Fase 1
- Verificações iniciais
- Backup de segurança  
- Execução do Agente 1 (Models)
- Validações e testes da Fase 1

### Dia 2: Fases 2 e 3
- Execução do Agente 2 (Banks)
- Validações da Fase 2
- Execução do Agente 3 (UI)
- Testes básicos da Fase 3

### Dia 3: Integração e Validação
- Integração completa
- Testes end-to-end
- Validação A04-STREAMLIT-PROFESSIONAL
- Otimização de performance

### Dia 4: Documentação e Entrega
- Criação da documentação
- Testes finais
- Validação com dados reais
- Entrega do sistema completo

## Critérios de Aceitação

### Critério 1: Funcionalidade Completa
O sistema deve permitir criar, editar, visualizar, importar e exportar todos os tipos de mapas especificados na documentação, com suporte completo a bancadas A/B.

### Critério 2: Compatibilidade FTManager
Arquivos .ftm gerados devem ser perfeitamente compatíveis com FTManager original, mantendo precisão numérica e estrutura de dados.

### Critério 3: Padrão Profissional A04
Interface deve seguir rigorosamente o padrão A04-STREAMLIT-PROFESSIONAL, sem emojis, com Material Icons consistentes e textos em português.

### Critério 4: Performance Adequada
Sistema deve ser responsivo com datasets típicos, renderizando gráficos em < 2 segundos e mantendo interface fluida durante edições.

### Critério 5: Robustez
Sistema deve tratar erros graciosamente, validar entradas, preservar integridade dos dados e manter backups automáticos.

## Observações Críticas

### Ordem de Execução
A execução DEVE seguir rigorosamente a ordem especificada: Models → Banks → UI. Cada fase depende da anterior.

### Validações Obrigatórias
Cada fase DEVE ser completamente validada antes de prosseguir. Falhas nas validações exigem correção imediata.

### Backup e Segurança
SEMPRE criar backups antes de modificações significativas. Manter histórico de alterações para rollback se necessário.

### Padrão A04 Não Negociável
O padrão A04-STREAMLIT-PROFESSIONAL é OBRIGATÓRIO e não pode ser comprometido. Verificações sistemáticas são essenciais.

### Documentação Obrigatória
Documentação clara é essencial para manutenção futura. Código deve ser auto-documentado com comentários em português.

Este agente orquestrador garante a implementação sistemática e completa do sistema de mapas de injeção, seguindo rigorosamente todos os padrões estabelecidos e garantindo máxima qualidade e compatibilidade.