# Guia de Contribuição

Obrigado pelo seu interesse em contribuir para o FuelTune Streamlit! Este documento fornece diretrizes e informações para contribuir com o projeto.

## Índice

- [Código de Conduta](#código-de-conduta)
- [Como Contribuir](#como-contribuir)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Padrões de Código](#padrões-de-código)
- [Processo de Desenvolvimento](#processo-de-desenvolvimento)
- [Testes](#testes)
- [Documentação](#documentação)
- [Pull Requests](#pull-requests)
- [Issues e Bugs](#issues-e-bugs)
- [Solicitação de Recursos](#solicitação-de-recursos)

## Código de Conduta

Este projeto adere ao código de conduta. Ao participar, você deve manter este código. Relate comportamentos inaceitáveis para [dev@fueltune.com](mailto:dev@fueltune.com).

### Nossas Promessas

- Manter um ambiente acolhedor e inclusivo
- Ser respeitoso com diferentes pontos de vista
- Aceitar críticas construtivas graciosamente
- Focar no que é melhor para a comunidade
- Mostrar empatia com outros membros da comunidade

## Como Contribuir

Existem várias maneiras de contribuir:

### 🐛 Reportar Bugs
- Use o template de issue para bugs
- Inclua steps para reproduzir
- Forneça informações do ambiente
- Adicione logs relevantes

### 💡 Sugerir Melhorias
- Use o template de feature request
- Explique o caso de uso
- Considere implementações alternativas
- Discuta o impacto na compatibilidade

### 📝 Melhorar Documentação
- Corrija erros de digitação
- Adicione exemplos
- Melhore explicações
- Traduza conteúdo

### 🚀 Implementar Recursos
- Comece com issues marcadas como "good first issue"
- Discuta grandes mudanças primeiro
- Siga os padrões de código
- Inclua testes

## Configuração do Ambiente

### Pré-requisitos

- Python 3.8+ (recomendado 3.11+)
- Git
- Editor com suporte a Python (VS Code recomendado)

### Setup Inicial

1. **Fork e Clone**
```bash
git clone https://github.com/SEU_USUARIO/fueltune-streamlit.git
cd fueltune-streamlit
```

2. **Setup Automático**
```bash
# Setup completo com ambiente virtual
./scripts/setup.sh --full

# Ou setup de desenvolvimento
./scripts/setup.sh --dev
```

3. **Verificar Instalação**
```bash
# Health check
python main.py --health-check

# Testes básicos
./scripts/test.sh --unit
```

### Configuração Manual

Se preferir configuração manual:

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Configurar pre-commit
pre-commit install

# 4. Criar arquivo .env
cp .env.example .env
```

## Padrões de Código

### Estilo de Código

Utilizamos as seguintes ferramentas:

- **Black**: Formatação automática
- **isort**: Ordenação de imports
- **flake8**: Linting
- **mypy**: Type checking

```bash
# Aplicar formatação
black src/ tests/
isort src/ tests/

# Verificar linting
flake8 src/ tests/

# Type checking
mypy src/
```

### Convenções

#### Nomenclatura
```python
# Classes: PascalCase
class DataProcessor:
    pass

# Funções e variáveis: snake_case
def process_data():
    user_name = "example"

# Constantes: UPPER_SNAKE_CASE
MAX_RECORDS = 1000

# Privados: prefixo _
def _internal_method():
    pass
```

#### Docstrings
Usamos o formato Google:

```python
def process_fueltech_data(file_path: str, validate: bool = True) -> ProcessingResult:
    """
    Process FuelTech CSV data with validation and normalization.
    
    Args:
        file_path: Path to the CSV file to process
        validate: Whether to run data validation
        
    Returns:
        ProcessingResult containing processed data and metadata
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValidationError: If data validation fails
        
    Example:
        >>> result = process_fueltech_data("data.csv")
        >>> print(f"Processed {result.record_count} records")
    """
    pass
```

#### Type Hints
Sempre use type hints:

```python
from typing import Dict, List, Optional, Union
from pathlib import Path

def analyze_session(
    session_id: str,
    fields: Optional[List[str]] = None,
    time_range: Optional[tuple[float, float]] = None
) -> Dict[str, Union[float, str]]:
    """Analyze session with optional filtering."""
    pass
```

### Estrutura de Arquivos

```python
# src/module/feature.py
"""
Module for specific feature.

This module provides functionality for...
"""

import logging
from typing import Any, Dict

# Módulos padrão primeiro
import json
import os
from pathlib import Path

# Dependências terceiros
import pandas as pd
import streamlit as st

# Imports locais
from ..utils.logger import get_logger
from .models import FeatureModel

logger = get_logger(__name__)

# Constantes no topo
DEFAULT_CONFIG = {...}

# Classes e funções
class FeatureClass:
    """Class description."""
    pass

def feature_function() -> Any:
    """Function description."""
    pass
```

## Processo de Desenvolvimento

### Workflow Git

1. **Crie um branch para sua feature**
```bash
git checkout -b feature/nome-da-feature
# ou
git checkout -b bugfix/nome-do-bug
```

2. **Faça commits pequenos e focados**
```bash
git add .
git commit -m "feat: adicionar validação de dados FuelTech"
git commit -m "docs: atualizar README com novos exemplos"
```

3. **Use commits convencionais**
- `feat:` nova funcionalidade
- `fix:` correção de bug  
- `docs:` documentação
- `style:` formatação
- `refactor:` refatoração
- `test:` testes
- `chore:` manutenção

4. **Mantenha o branch atualizado**
```bash
git fetch origin
git rebase origin/main
```

### Desenvolvimento de Features

1. **Planeje a implementação**
   - Discuta em issues grandes mudanças
   - Considere compatibilidade retroativa
   - Pense em testes desde o início

2. **Implemente incrementalmente**
   - Comece com testes
   - Implemente funcionalidade básica
   - Adicione casos edge
   - Otimize performance

3. **Teste completamente**
   - Testes unitários
   - Testes de integração
   - Testes manuais
   - Health checks

## Testes

### Estratégia de Testes

- **Cobertura mínima**: 75%
- **Testes unitários**: Para lógica de negócio
- **Testes de integração**: Para fluxos completos
- **Testes de UI**: Para componentes Streamlit

### Executando Testes

```bash
# Todos os testes
./scripts/test.sh --all

# Apenas unitários
./scripts/test.sh --unit

# Com cobertura
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/unit/test_csv_parser.py -v
```

### Escrevendo Testes

```python
# tests/unit/test_feature.py
import pytest
from unittest.mock import Mock, patch

from src.module.feature import FeatureClass, feature_function


class TestFeatureClass:
    """Test suite for FeatureClass."""
    
    def test_initialization(self):
        """Test FeatureClass initialization."""
        feature = FeatureClass()
        assert feature is not None
    
    def test_process_valid_data(self):
        """Test processing with valid data."""
        feature = FeatureClass()
        result = feature.process({"valid": "data"})
        assert result.success is True
    
    def test_process_invalid_data(self):
        """Test processing with invalid data."""
        feature = FeatureClass()
        with pytest.raises(ValueError):
            feature.process({"invalid": None})


@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"field1": "value1", "field2": "value2"}


def test_feature_function(sample_data):
    """Test feature_function with sample data."""
    result = feature_function(sample_data)
    assert result is not None
```

### Fixtures e Mocks

```python
# tests/fixtures/data.py
import pytest
import pandas as pd

@pytest.fixture
def fueltech_data():
    """Sample FuelTech data for testing."""
    return pd.DataFrame({
        'time': [0.0, 0.1, 0.2],
        'rpm': [800, 1000, 1200],
        'throttle_position': [0, 10, 20]
    })

@pytest.fixture
def mock_database():
    """Mock database for testing."""
    with patch('src.data.database.get_database') as mock:
        mock.return_value.get_sessions.return_value = []
        yield mock
```

## Documentação

### Tipos de Documentação

1. **API Documentation**: Gerada automaticamente do código
2. **User Guide**: Documentação para usuários finais
3. **Developer Guide**: Documentação para desenvolvedores
4. **Tutorials**: Tutoriais passo a passo

### Atualizando Documentação

```bash
# Gerar documentação
python main.py --docs

# Ou usando Sphinx diretamente
cd docs
make html

# Visualizar localmente
open docs/_build/html/index.html
```

### Escrevendo Documentação

```markdown
# Título da Seção

Breve introdução sobre o tópico.

## Subsecção

Explicação detalhada com exemplos:

```python
# Exemplo de código
from src.analysis import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
result = analyzer.analyze(data)
```

### Dicas Importantes

- Use markdown para formatação
- Inclua exemplos práticos
- Mantenha atualizado com o código
- Use screenshots quando apropriado
```

## Pull Requests

### Antes de Submeter

1. **Execute todos os testes**
```bash
./scripts/test.sh --all
```

2. **Verifique formatação**
```bash
black src/ tests/ --check
isort src/ tests/ --check-only
flake8 src/ tests/
```

3. **Execute type checking**
```bash
mypy src/
```

4. **Atualize documentação**
5. **Teste manualmente**

### Template de PR

Ao criar um Pull Request, inclua:

```markdown
## Descrição
Breve descrição das mudanças

## Tipo de Mudança
- [ ] Bug fix
- [ ] Nova feature
- [ ] Breaking change
- [ ] Documentação

## Como Testar
1. Passos para testar
2. Dados de teste necessários
3. Comportamento esperado

## Checklist
- [ ] Testes passam
- [ ] Documentação atualizada
- [ ] Changelog atualizado (se aplicável)
- [ ] Type hints adicionadas
- [ ] Compatibilidade retroativa mantida
```

### Processo de Review

1. **Automated Checks**: CI/CD deve passar
2. **Code Review**: Pelo menos 1 aprovação
3. **Manual Testing**: Para features críticas
4. **Documentation Review**: Para mudanças visíveis ao usuário

## Issues e Bugs

### Reportando Bugs

Use o template de issue:

```markdown
**Descrição do Bug**
Descrição clara e concisa do problema.

**Para Reproduzir**
Passos para reproduzir:
1. Vá para '...'
2. Clique em '....'
3. Veja o erro

**Comportamento Esperado**
O que deveria acontecer.

**Screenshots**
Se aplicável, adicione screenshots.

**Ambiente:**
 - OS: [e.g. Ubuntu 20.04]
 - Python: [e.g. 3.11]
 - Versão: [e.g. 1.0.0]

**Informações Adicionais**
Qualquer contexto adicional.
```

### Triagem de Issues

Issues são triadas com labels:

- **Priority**: `low`, `medium`, `high`, `critical`
- **Type**: `bug`, `enhancement`, `question`, `documentation`
- **Status**: `needs-investigation`, `needs-reproduction`, `confirmed`
- **Difficulty**: `good-first-issue`, `intermediate`, `advanced`

## Solicitação de Recursos

### Template de Feature Request

```markdown
**Funcionalidade Solicitada**
Descrição clara da funcionalidade desejada.

**Problema que Resolve**
Qual problema esta funcionalidade resolve?

**Solução Proposta**
Descrição da solução que você gostaria de ver.

**Alternativas Consideradas**
Outras soluções que você considerou.

**Informações Adicionais**
Qualquer contexto adicional.
```

### Processo de Avaliação

1. **Discussão**: Comunidade discute a proposta
2. **Planejamento**: Core team avalia viabilidade
3. **Priorização**: Adicionado ao roadmap
4. **Implementação**: Desenvolvido por contributor

## Comunidade e Suporte

### Canais de Comunicação

- **GitHub Issues**: Bugs e feature requests
- **Email**: [dev@fueltune.com](mailto:dev@fueltune.com)
- **Discussions**: Para perguntas gerais

### Reconhecimento

Contribuidores são reconhecidos:

- **AUTHORS.md**: Lista de todos os contribuidores
- **Release Notes**: Menção em releases importantes
- **Hall of Fame**: Contribuidores especiais

### Mentoria

Para novos contribuidores:

- **Good First Issues**: Issues ideais para começar
- **Pair Programming**: Sessões de programação em par
- **Code Review**: Feedback construtivo
- **Documentation**: Guias detalhados

## Recursos Adicionais

### Ferramentas Recomendadas

- **IDE**: VS Code com extensões Python
- **Git Client**: GitKraken, SourceTree, ou CLI
- **Database**: DB Browser para SQLite
- **API Testing**: Postman ou httpie

### Extensões VS Code

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "ms-toolsai.jupyter",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-json"
  ]
}
```

### Configuração do Git

```bash
# Configurar informações básicas
git config user.name "Seu Nome"
git config user.email "seu.email@example.com"

# Configurar merge/rebase
git config pull.rebase true
git config rebase.autoStash true

# Aliases úteis
git config alias.co checkout
git config alias.br branch
git config alias.ci commit
git config alias.st status
```

## Obrigado!

Obrigado por contribuir para o FuelTune Streamlit! Suas contribuições tornam este projeto melhor para toda a comunidade.

Para dúvidas sobre este guia, abra uma issue ou entre em contato conosco.

---

**Happy Coding!** 🚗💨