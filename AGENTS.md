# Diretrizes do Repositório

## Estrutura do Projeto e Módulos
- Código-fonte: `src/` (principais pacotes: `analysis/`, `core/`, `ui/`, `utils/`, `maps/`, `performance/`, `components/`, `integration/`). A UI inicia em `main.py` (Streamlit).
- Testes: `tests/` (pytest). Dados em `data/` (criados por setup/Make), configs em `config/`, migrações em `migrations/`, utilitários em `scripts/`, documentação em `docs/`.
- Suporte na raiz: `Makefile`, `pyproject.toml`, `pytest.ini`, `.pre-commit-config.yaml`, `requirements-*.txt`.

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
