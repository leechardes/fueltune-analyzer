# Documentação do Projeto

**Versão:** 1.0.0  
**Última Atualização:** 2024-08-31  
**Versão do Template:** v1.0

## 📁 Estrutura da Documentação

Este diretório contém toda a documentação do projeto seguindo os padrões de documentação da Inoveon.

### Documentos Principais

| Documento | Propósito | Status |
|-----------|-----------|--------|
| `README.md` | Este arquivo - Visão geral da documentação | ✅ Ativo |
| `CHANGELOG.md` | Histórico de versões e mudanças | 📝 Atualizado em releases |
| `VERSION.md` | Informações da versão atual | 📝 Atualizado em releases |
| `ARCHITECTURE.md` | Design e arquitetura do sistema | 📝 Conforme necessário |
| `API.md` | Endpoints e especificações da API | 📝 Conforme necessário |
| `INSTALLATION.md` | Guia de instalação e configuração | 📝 Conforme necessário |
| `USAGE.md` | Guia de uso e exemplos | 📝 Conforme necessário |

### 🤖 Sistema de Agentes

O diretório `agents/` contém agentes automatizados de documentação que ajudam a manter e atualizar a documentação.

- **Localização:** `./agents/`
- **Configuração:** Veja `./agents/README.md`
- **Relatórios:** Gerados em `./agents/reports/`

#### Pastas dos Agentes

- `agents/pending/` - Tarefas aguardando execução
- `agents/continuous/` - Tarefas recorrentes de documentação
- `agents/executed/` - Arquivo de tarefas concluídas
- `agents/reports/` - Análises e relatórios gerados

## 📋 Padrões de Documentação

### Nomenclatura de Arquivos
- Use MAIÚSCULAS para documentos padrão (README, CHANGELOG, etc.)
- Use minúsculas com hífens para documentos personalizados (guia-usuario.md)
- Nomes de arquivos em inglês para compatibilidade

### Diretrizes de Conteúdo
1. **Cabeçalhos Claros** - Use cabeçalhos descritivos nas seções
2. **Exemplos de Código** - Inclua exemplos práticos quando relevante
3. **Rastreamento de Versão** - Atualize VERSION.md e CHANGELOG.md
4. **Referências Cruzadas** - Faça links entre documentos relacionados
5. **Diagramas** - Use Mermaid ou ASCII art para visualizações

### Frequência de Atualização
- **README.md** - Em mudanças importantes
- **CHANGELOG.md** - A cada release
- **VERSION.md** - A cada release
- **API.md** - Em mudanças de endpoints
- **ARCHITECTURE.md** - Em mudanças de design

## 🔄 Automação

A documentação pode ser analisada e atualizada automaticamente usando agentes:

```bash
# Para analisar cobertura da documentação
cat ./agents/pending/ANALYZE-DOCS-$(date +%Y%m%d).md

# Para atualizar documentação
cat ./agents/pending/UPDATE-DOCS-$(date +%Y%m%d).md
```

## 📊 Métricas de Documentação

Acompanhe a saúde da documentação em `./agents/reports/`:
- Análise de cobertura
- Seções desatualizadas
- Documentação faltante
- Métricas de qualidade

## 🛠️ Manutenção

### Tarefas Regulares
1. Revisar agentes pendentes semanalmente
2. Atualizar CHANGELOG.md em releases
3. Verificar precisão da API.md mensalmente
4. Arquivar agentes executados antigos trimestralmente

### Comandos Rápidos

```bash
# Verificar status da documentação
ls -la ./

# Ver tarefas de documentação pendentes
ls ./agents/pending/

# Verificar últimos relatórios
ls -lt ./agents/reports/ | head -5
```

## 📚 Recursos Adicionais

- [Padrões de Documentação Inoveon](/srv/projects/shared/docs/DOCUMENTATION-STANDARDS.md)
- [Guia do Sistema de Agentes](/srv/projects/shared/docs/agents/README.md)
- [Repositório do Projeto](https://github.com/inoveon/[nome-do-projeto])

## 📝 Observações

Esta estrutura de documentação é mantida por agentes automatizados e atualizações manuais. Para dúvidas ou melhorias, crie uma tarefa em `./agents/pending/`.

---

*Este README faz parte do sistema padronizado de documentação da Inoveon.*  
*Template: /srv/projects/shared/scripts/docs-templates/docs-README.md*