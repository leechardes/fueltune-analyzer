# Diretrizes do Repositório

## Estrutura do Projeto e Módulos
- Código-fonte: `src/` (principais pacotes: `analysis/`, `core/`, `ui/`, `utils/`, `maps/`, `performance/`, `components/`, `integration/`). A UI inicia em `main.py` (Streamlit).
- Testes: `tests/` (pytest). Dados em `data/` (criados por setup/Make), configs em `config/`, migrações em `migrations/` (incluindo `alembic.ini`), utilitários em `scripts/`, documentação em `docs/`.
- Scripts de database: `scripts/database/` (init_database.py, add_test_vehicles.py, check_db.py, etc.)
- Suporte na raiz: `Makefile`, `pyproject.toml`, `pytest.ini`, `.pre-commit-config.yaml`, `requirements-*.txt`, `app.py`, `main.py`, `config.py`.

## Comandos de Build, Teste e Desenvolvimento
- Setup: `make setup` (cria venv, instala deps de dev/test e habilita pre-commit).
- Executar localmente (Streamlit): `make dev` (hot-reload em http://localhost:8503) ou `make start` (modo produção).
- Qualidade: `make format` (autoflake+isort+black), `make lint` (flake8+pylint), `make type` (mypy), `make security` (bandit), `make quality` (format+lint+type).
- Testes: `make test`, `make test-unit`, `make test-integration`, `make test-cov` (relatório HTML em `htmlcov/`).
- Docker: `make docker-build` e `make docker-run` para execução conteinerizada.

## Estilo de Código e Convenções
- Python ≥ 3.8 (dev usa 3.12). Indentação de 4 espaços; limite de 100 colunas.
- Formatação: Black; Imports: isort (perfil "black"); Tipagem estática preferida (mypy estrito em `pyproject.toml`).
- Linters: flake8 e pylint; use nomes descritivos; evite variáveis de uma letra salvo idioms (`i`, `j`, `df`).
- Em `src/`: arquivos snake_case; classes em CapWords; funções/variáveis em snake_case.

## Diretrizes de Testes
- Framework: pytest com marcadores (`unit`, `integration`, `slow`, `api`). Nomeação: arquivos `test_*.py`, classes `Test*`, funções `test_*`.
- Cobertura: mínimo 80% (enforçado em `pytest.ini`). Gere com `make test-cov`.
- Priorize testes pequenos e determinísticos; marque `slow`/`integration` quando aplicável.

## Commits e Pull Requests
- Use Conventional Commits: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`. Títulos concisos; mantenha idioma consistente (pt-BR ou en).
- PRs: descrição clara, issues vinculadas e screenshots/GIFs para mudanças de UI. Garanta `make quality && make test` passando.
- Não versione segredos; baseie-se em `.env.example` (copie para `.env` local).

## Segurança e Configuração
- Rode `make security` periodicamente; não reduza thresholds de mypy/pylint sem discussão.
- Dados e arquivos SQLite ficam em `data/`; evite binários grandes no Git. Use `docker-compose*.yml` quando precisar de paridade de ambiente.

## Instruções para Agentes
- Agentes automatizados que interajam com este repositório devem sempre responder em português do Brasil (pt-BR).
- Respeite estas diretrizes ao criar/alterar arquivos e mensagens.

## 📁 Regras de Organização de Arquivos

### NUNCA criar na raiz do projeto:
- Scripts de utilidade ou teste Python → Coloque em `scripts/` ou subpastas apropriadas
- Scripts de database/migração → Coloque em `scripts/database/`
- Arquivos temporários ou de desenvolvimento → Use pastas apropriadas como `temp/` ou `.tmp/`
- Scripts de inicialização de dados → Coloque em `scripts/database/`

### Arquivos que DEVEM ficar na raiz:
- Entry points: `app.py` (Streamlit), `main.py` (CLI orquestrador), `config.py` (configurações)
- Documentação principal: `README.md`, `LICENSE`, `CHANGELOG.md`, `AGENTS.md`
- Configuração Python: `requirements.txt`, `setup.py`, `pyproject.toml`, `pytest.ini`, `tox.ini`
- Docker/Deploy: `Dockerfile`, `docker-compose.yml`, `Makefile`
- Versionamento: `VERSION`, `MANIFEST.in`

### Organização padrão:
- `scripts/database/` - Scripts relacionados a banco de dados
- `scripts/setup/` - Scripts de configuração inicial
- `migrations/` - Todas as migrações e `alembic.ini`
- `src/` - Código-fonte da aplicação
- `tests/` - Testes automatizados
- `docs/` - Documentação técnica
- `data/` - Dados e arquivos SQLite
