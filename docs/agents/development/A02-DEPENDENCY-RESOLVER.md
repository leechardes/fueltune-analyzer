# A02 - DEPENDENCY RESOLVER

## 📋 Objetivo
Automatizar a identificação e instalação de dependências Python faltantes, executando a aplicação, detectando erros de importação e atualizando os arquivos de requirements.

## 🎯 Missão Específica
Este agente é responsável por:
1. **Executar a aplicação** e capturar erros de importação
2. **Identificar módulos faltantes** através de análise de logs
3. **Mapear pacotes corretos** para cada módulo
4. **Atualizar requirements.txt** com as dependências necessárias
5. **Instalar automaticamente** usando make install
6. **Repetir o processo** até que todos os erros sejam resolvidos

## 🔧 Contexto de Execução
- **Ambiente**: Diretório raiz do projeto Python/Streamlit
- **Pré-requisitos**: 
  - Makefile configurado com comandos `dev` e `install`
  - Ambiente virtual Python criado
  - requirements.txt existente
- **Timeout**: Máximo de 10 iterações para evitar loops infinitos

## 📋 Processo de Execução

### FASE 1 - Preparação
1. Verificar se o ambiente virtual existe
2. Verificar se o Makefile existe
3. Fazer backup do requirements.txt atual

### FASE 2 - Detecção de Erros
1. Executar `make dev` em background
2. Aguardar 10 segundos para capturar erros
3. Analisar logs em busca de `ModuleNotFoundError` ou `ImportError`
4. Extrair nome do módulo faltante

### FASE 3 - Mapeamento de Dependências
1. Mapear módulo para pacote PyPI correto
2. Verificar se já está no requirements.txt
3. Determinar versão apropriada

### FASE 4 - Atualização e Instalação
1. Adicionar dependência ao requirements.txt
2. Executar `make install`
3. Verificar se a instalação foi bem-sucedida

### FASE 5 - Validação
1. Executar novamente `make dev`
2. Verificar se o erro foi resolvido
3. Se houver novos erros, repetir o processo
4. Se não houver erros, finalizar com sucesso

## 📊 Mapeamento de Módulos Comuns

```python
MODULE_TO_PACKAGE = {
    # Streamlit Extensions
    'st_aggrid': 'streamlit-aggrid>=1.0.5',
    'streamlit_aggrid': 'streamlit-aggrid>=1.0.5',
    'streamlit_option_menu': 'streamlit-option-menu>=0.3.0',
    'streamlit_extras': 'streamlit-extras>=0.3.0',
    'streamlit_lottie': 'streamlit-lottie>=0.0.5',
    'streamlit_elements': 'streamlit-elements>=0.1.0',
    'streamlit_card': 'streamlit-card>=0.0.5',
    'streamlit_ace': 'streamlit-ace>=0.1.1',
    'streamlit_tags': 'streamlit-tags>=1.2.8',
    'streamlit_authenticator': 'streamlit-authenticator>=0.2.0',
    'streamlit_folium': 'streamlit-folium>=0.15.0',
    
    # Data Processing
    'yaml': 'pyyaml>=6.0',
    'cv2': 'opencv-python>=4.8.0',
    'PIL': 'Pillow>=10.0.0',
    'Image': 'Pillow>=10.0.0',
    'psycopg2': 'psycopg2-binary>=2.9.0',
    'pymongo': 'pymongo>=4.5.0',
    'redis': 'redis>=5.0.0',
    'kafka': 'kafka-python>=2.0.0',
    
    # Machine Learning
    'sklearn': 'scikit-learn>=1.3.0',
    'tensorflow': 'tensorflow>=2.14.0',
    'torch': 'torch>=2.1.0',
    'transformers': 'transformers>=4.35.0',
    'xgboost': 'xgboost>=2.0.0',
    'lightgbm': 'lightgbm>=4.1.0',
    
    # Visualization
    'plotly': 'plotly>=5.18.0',
    'altair': 'altair>=5.1.0',
    'bokeh': 'bokeh>=3.3.0',
    'holoviews': 'holoviews>=1.18.0',
    
    # Web/API
    'fastapi': 'fastapi>=0.104.0',
    'uvicorn': 'uvicorn>=0.24.0',
    'httpx': 'httpx>=0.25.0',
    'aiohttp': 'aiohttp>=3.9.0',
    'flask': 'flask>=3.0.0',
    
    # Database
    'alembic': 'alembic>=1.12.0',
    'sqlmodel': 'sqlmodel>=0.0.14',
    'peewee': 'peewee>=3.17.0',
    
    # Testing
    'pytest': 'pytest>=7.4.0',
    'pytest_cov': 'pytest-cov>=4.1.0',
    'pytest_mock': 'pytest-mock>=3.12.0',
    
    # Utilities
    'dotenv': 'python-dotenv>=1.0.0',
    'tqdm': 'tqdm>=4.66.0',
    'rich': 'rich>=13.7.0',
    'click': 'click>=8.1.0',
    'typer': 'typer>=0.9.0',
    'pydantic': 'pydantic>=2.5.0',
    'loguru': 'loguru>=0.7.0',
}
```

## 📝 Estrutura de Logs

```
[TIMESTAMP] 🚀 [A02-DEPENDENCY-RESOLVER] Iniciando resolução de dependências
[TIMESTAMP] 🔄 [A02-DEPENDENCY-RESOLVER] Executando make dev...
[TIMESTAMP] ❌ [A02-DEPENDENCY-RESOLVER] Erro detectado: ModuleNotFoundError: No module named 'st_aggrid'
[TIMESTAMP] 🔍 [A02-DEPENDENCY-RESOLVER] Mapeando módulo 'st_aggrid' para pacote 'streamlit-aggrid>=1.0.5'
[TIMESTAMP] ✏️ [A02-DEPENDENCY-RESOLVER] Adicionando ao requirements.txt
[TIMESTAMP] 📦 [A02-DEPENDENCY-RESOLVER] Instalando dependências com make install
[TIMESTAMP] ✅ [A02-DEPENDENCY-RESOLVER] Dependência instalada com sucesso
[TIMESTAMP] 🔄 [A02-DEPENDENCY-RESOLVER] Re-executando aplicação...
[TIMESTAMP] ✅ [A02-DEPENDENCY-RESOLVER] Todas as dependências resolvidas!
```

## 🚀 Como Executar

### Comando Manual
```bash
# Execute o agente no diretório do projeto
python -c "
import subprocess
import time
import re

# Executar o agente
resolver = DependencyResolver()
resolver.run()
"
```

### Comando via Task
```
Execute o agente A02-DEPENDENCY-RESOLVER no diretório do projeto.

O agente irá:
1. Executar make dev e capturar erros
2. Identificar módulos faltantes
3. Atualizar requirements.txt
4. Instalar dependências
5. Repetir até resolver todos os erros
```

## ⚠️ Regras Críticas
1. **SEMPRE** fazer backup do requirements.txt antes de modificar
2. **NUNCA** remover dependências existentes
3. **SEMPRE** verificar se o pacote já está listado antes de adicionar
4. **LIMITAR** a 10 iterações para evitar loops infinitos
5. **VALIDAR** que a instalação foi bem-sucedida antes de continuar

## 📊 Entrada Esperada
- Projeto Python/Streamlit com Makefile
- Comando `make dev` configurado
- Comando `make install` configurado
- requirements.txt existente

## 📈 Saída Esperada

### 1. Relatório de Análise
```
📊 ANÁLISE DE DEPENDÊNCIAS
- Total de erros encontrados: X
- Módulos faltantes identificados: Y
- Pacotes adicionados: Z
- Iterações necessárias: W
```

### 2. Requirements Atualizado
```
# Arquivo: requirements.txt
# Adicionadas automaticamente pelo A02-DEPENDENCY-RESOLVER
streamlit-aggrid>=1.0.5
streamlit-option-menu>=0.3.0
[...]
```

### 3. Log de Execução
```
Iteração 1:
- Erro: ModuleNotFoundError: No module named 'st_aggrid'
- Ação: Adicionado streamlit-aggrid>=1.0.5
- Status: Resolvido

Iteração 2:
- Erro: ModuleNotFoundError: No module named 'yaml'
- Ação: Adicionado pyyaml>=6.0
- Status: Resolvido
```

## 🔗 Dependências do Agente
- Python 3.7+
- subprocess (nativo)
- re (nativo)
- time (nativo)
- pathlib (nativo)

## 📊 Métricas de Sucesso
- [ ] Todos os erros de importação resolvidos
- [ ] requirements.txt atualizado corretamente
- [ ] Aplicação executando sem erros de módulos
- [ ] Backup do requirements.txt preservado
- [ ] Log detalhado de todas as ações

## 🆘 Tratamento de Erros

### Módulo não mapeado
Se um módulo não estiver no mapeamento:
1. Tentar buscar no PyPI com nome similar
2. Adicionar com nome do módulo como está
3. Registrar para revisão manual

### Falha na instalação
Se a instalação falhar:
1. Verificar se há conflitos de versão
2. Tentar sem especificar versão
3. Registrar erro para intervenção manual

### Loop infinito
Se passar de 10 iterações:
1. Parar execução
2. Listar todos os erros não resolvidos
3. Sugerir intervenção manual

---

**Versão:** 1.0
**Última atualização:** Janeiro 2025
**Tipo:** Automação de Dependências