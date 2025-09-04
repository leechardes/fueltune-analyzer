# AGENT-DOCUMENTATION-SPECIALIST

**Versão do Agente:** 2.1.0  
**Tipo:** Contínuo  
**Última Atualização do Template:** 2025-09-01
**Modelo Recomendado:** Claude 3.5 Sonnet (mais recente disponível)

## 🎯 Objetivo

Analisar COMPLETAMENTE a estrutura e código do projeto para criar e manter documentação atualizada, verificando TODOS os arquivos e atualizando TODA a documentação padrão.

## 📚 Padrões de Código Obrigatórios
Este agente segue RIGOROSAMENTE os padrões definidos em:
- **`/docs/PYTHON-CODE-STANDARDS.md`**
- Seções específicas aplicáveis:
  - [Professional UI Standards] - Interface sem emojis
  - [CSS Adaptativo] - Temas claro/escuro  
  - [Type Hints] - Type safety completo
  - [Error Handling] - Tratamento robusto
  - [Performance] - Otimização obrigatória
  - [Documentation Standards] - Documentação completa

### Requisitos Específicos:
- ❌ ZERO emojis na interface (usar Material Icons)
- ❌ ZERO cores hardcoded (#ffffff, #000000)
- ❌ ZERO uso de !important no CSS
- ✅ Variáveis CSS adaptativas obrigatórias
- ✅ Type hints 100% coverage
- ✅ Docstrings Google Style
- ✅ Performance < 1s para operações típicas
- ✅ Documentação completa e atualizada

## 🤖 CONFIGURAÇÃO DE MODELO IA

**RECOMENDAÇÃO:** Para melhor análise e documentação:
- **Usar preferencialmente:** Claude 3.5 Sonnet (versão mais recente)
- **Benefícios:** Melhor compreensão de código, análise mais profunda, documentação mais rica
- **Se indisponível:** Usar o modelo mais avançado disponível

## ⚠️ REQUISITOS OBRIGATÓRIOS

**IMPORTANTE:** Este agente DEVE completar 100% das tarefas abaixo. NÃO PODE pular etapas ou deixar arquivos sem verificar.

### Checklist Obrigatória:
- [ ] ✅ TODOS os arquivos do JSON devem ser marcados como `"verified": true`
- [ ] ✅ README.md deve ter conteúdo específico do projeto
- [ ] ✅ ARCHITECTURE.md deve descrever a arquitetura real
- [ ] ✅ INSTALLATION.md deve ter instruções detalhadas
- [ ] ✅ USAGE.md deve ter exemplos práticos de uso
- [ ] ✅ CHANGELOG.md deve registrar a análise
- [ ] ✅ VERSION.md deve ser atualizado
- [ ] ✅ Se for API: criar API.md com TODOS os endpoints
- [ ] ✅ Se for Frontend: criar COMPONENTS.md
- [ ] ✅ Se for Mobile: criar SCREENS.md
- [ ] ✅ Relatório completo em agents/reports/

## 📋 INSTRUÇÕES DE EXECUÇÃO OBRIGATÓRIAS

### PASSO 1: Ler Status de Verificação

```bash
# Ler o arquivo de controle
cat ./docs/agents/.verification-status.json
```

**AÇÃO OBRIGATÓRIA:** Contar EXATAMENTE quantos arquivos existem no JSON. Este é seu TARGET.

### PASSO 2: Análise COMPLETA de Arquivos

**ESTRATÉGIA OBRIGATÓRIA DE ANÁLISE:**

1. **Primeira Passada - Arquivos Principais (10-15 arquivos):**
   - main.py, app.py, index.js, index.ts
   - package.json, requirements.txt, pom.xml, pubspec.yaml
   - README.md existente (se houver)
   - Arquivos de configuração (.env.example, config/)
   - Routes/Controllers principais

2. **Segunda Passada - Estrutura (10-15 arquivos):**
   - Models/Schemas/Entities
   - Services/Repositories
   - Utils/Helpers
   - Middlewares/Interceptors

3. **Terceira Passada - Específicos do Tipo:**
   - Se API: todos os arquivos em routes/, endpoints/, controllers/
   - Se Frontend: components/, pages/, views/
   - Se Mobile: screens/, widgets/
   - Se Service: handlers/, workers/

4. **Quarta Passada - Restantes:**
   - Tests/
   - Scripts/
   - Migrations/
   - Qualquer arquivo ainda não verificado

**IMPORTANTE:** Se houver mais de 50 arquivos, divida em lotes mas PROCESSE TODOS!

### PASSO 3: Criação OBRIGATÓRIA de Documentação

#### 3.1 - README.md (OBRIGATÓRIO - Conteúdo Específico)

```markdown
# [Nome do Projeto]

## 📌 Sobre o Projeto
[Descrição ESPECÍFICA do que este projeto faz, não genérica]

## 🚀 Tecnologias
[Lista REAL das tecnologias encontradas no projeto]

## 📁 Estrutura do Projeto
[Estrutura REAL com os diretórios que existem]

## 🔧 Instalação
[Comandos ESPECÍFICOS baseados no gerenciador de pacotes usado]

## 💻 Uso
[Exemplos REAIS de como executar/usar o projeto]

## 🔌 Integrações
[Integrações REAIS encontradas no código]

## 📊 Status
[Status REAL baseado na análise]
```

#### 3.2 - ARCHITECTURE.md (OBRIGATÓRIO - Arquitetura Real)

```markdown
# Arquitetura

## Visão Geral
[Descrição REAL da arquitetura identificada]

## Padrões Identificados
[Padrões REAIS encontrados no código]

## Estrutura de Pastas
[Estrutura REAL com explicação de cada pasta]

## Fluxo de Dados
[Fluxo REAL baseado no código analisado]

## Componentes Principais
[Componentes REAIS com suas responsabilidades]

## Banco de Dados
[Schema/Models REAIS encontrados]

## Diagrama
[Diagrama Mermaid baseado na estrutura REAL]
```

#### 3.3 - INSTALLATION.md (OBRIGATÓRIO - Instruções Detalhadas)

```markdown
# Instalação

## Requisitos do Sistema
[Requisitos REAIS baseados nas dependências]

## Dependências
[Lista COMPLETA de dependências do projeto]

## Passo a Passo
[Instruções ESPECÍFICAS para este projeto]

## Configuração
[Variáveis de ambiente REAIS necessárias]

## Verificação
[Como verificar se está funcionando]
```

#### 3.4 - USAGE.md (OBRIGATÓRIO - Exemplos Práticos)

```markdown
# Uso

## Execução Local
[Comandos REAIS para rodar o projeto]

## Exemplos de Uso
[Exemplos PRÁTICOS baseados no código]

## APIs/Endpoints Disponíveis
[Se aplicável, lista de endpoints]

## Scripts Disponíveis
[Scripts REAIS encontrados no projeto]
```

#### 3.5 - Documentação Específica por Tipo

**SE FOR API (verificar presença de routes/, endpoints/, controllers/):**
- Criar API.md com TODOS os endpoints encontrados
- Documentar CADA rota com método, path, parâmetros, resposta

**SE FOR FRONTEND (verificar presença de components/, pages/):**
- Criar COMPONENTS.md com lista de TODOS os componentes
- Documentar props e uso de cada componente principal

**SE FOR MOBILE (verificar presença de screens/, lib/screens/):**
- Criar SCREENS.md com TODAS as telas
- Documentar navegação entre telas

**SE FOR SERVICE (verificar workers/, handlers/):**
- Criar SERVICES.md com TODOS os serviços
- Documentar funções e responsabilidades

### PASSO 4: Atualização OBRIGATÓRIA do JSON

**CRÍTICO:** TODOS os arquivos DEVEM ser marcados como verificados!

```python
# PSEUDOCÓDIGO OBRIGATÓRIO
para CADA arquivo no JSON:
    marcar verified = true
    marcar verified_at = timestamp_atual
    
# Atualizar estatísticas
statistics.verified_files = total_files
statistics.pending_files = 0

# VALIDAÇÃO FINAL
if pending_files > 0:
    ERRO: "Ainda existem arquivos não verificados!"
    VOLTAR e verificar os faltantes
```

**PROCESSO DE ATUALIZAÇÃO:**

1. Ler o JSON completo
2. Para CADA arquivo (sem exceção):
   - Definir `"verified": true`
   - Definir `"verified_at": "timestamp_atual"`
3. Atualizar statistics:
   - `"verified_files": total_de_arquivos`
   - `"pending_files": 0`
4. Salvar JSON atualizado

### PASSO 5: Relatório OBRIGATÓRIO

Criar em `./agents/reports/analysis-YYYYMMDD.md`:

```markdown
# Relatório de Análise - [DATA]

## ✅ Validação de Completude
- [ ] Todos os [X] arquivos foram verificados
- [ ] README.md atualizado com conteúdo específico
- [ ] ARCHITECTURE.md criado com arquitetura real
- [ ] INSTALLATION.md com instruções completas
- [ ] USAGE.md com exemplos práticos
- [ ] Documentação específica do tipo criada
- [ ] JSON 100% atualizado

## 📊 Estatísticas Finais
- Total de arquivos: X
- Arquivos verificados: X (DEVE SER 100%)
- Documentos criados: Y
- Documentos atualizados: Z

## 🔍 Descobertas
[Descobertas técnicas detalhadas]

## 📁 Arquivos Analisados
[Lista COMPLETA de todos os arquivos verificados]
```

## 🚨 VALIDAÇÃO FINAL OBRIGATÓRIA

Antes de finalizar, VERIFIQUE:

1. **JSON está 100% atualizado?**
   ```bash
   grep -c '"verified": false' .verification-status.json
   # DEVE retornar 0
   ```

2. **Toda documentação foi criada?**
   ```bash
   ls -la docs/*.md
   # DEVE ter todos os arquivos com conteúdo específico
   ```

3. **Statistics está correto?**
   - pending_files DEVE ser 0
   - verified_files DEVE ser igual a total_files

## ⛔ CRITÉRIOS DE FALHA

O agente FALHOU se:
- ❌ Algum arquivo ficou com `"verified": false`
- ❌ Documentação tem conteúdo genérico como "[Descrição]"
- ❌ pending_files > 0
- ❌ Não criou documentação específica do tipo (API.md, etc)
- ❌ Relatório não lista todos os arquivos verificados

## 🎯 Meta Final

**100% dos arquivos verificados + 100% da documentação atualizada = SUCESSO**

Qualquer coisa menos que isso é FALHA e deve ser corrigida antes de prosseguir.

---

## 📌 Path do Projeto

```
[SERÁ PREENCHIDO AUTOMATICAMENTE PELO SCRIPT]
```

---

*Este agente faz parte do sistema automatizado de documentação da Inoveon.*  
*Versão 2.1.0 - Rigor Total na Execução + Modelo Sonnet Recomendado*
## 📌 Path do Projeto

```
/home/lee/projects/fueltune-streamlit
```
