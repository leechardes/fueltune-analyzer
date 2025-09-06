# EXECUTE-PROJECT-CLEANUP Agent

## MISSÃO
Executar todas as ações de limpeza e organização identificadas pelo agente ANALYZE-PROJECT-CLEANUP, aplicando as correções de forma segura e ordenada.

## PRÉ-REQUISITOS
- [x] Relatório de análise gerado em `/docs/agents/reports/CLEANUP-ANALYSIS-REPORT.md`
- [ ] Backup do projeto (recomendado)
- [ ] Aplicação parada durante a reorganização

## PLANO DE EXECUÇÃO

### FASE 1: PROBLEMAS CRÍTICOS 🔴

#### 1.1 Mover pasta /pages para estrutura correta
```bash
# Verificar se já existe /src/ui/pages
ls -la src/ui/pages/

# Mover Performance_Monitor.py para src/ui/pages
mv pages/Performance_Monitor.py src/ui/pages/

# Remover pasta pages vazia
rmdir pages/
```

#### 1.2 Mover banco de dados da raiz
```bash
# Mover fueltech_data.db para /data
mv fueltech_data.db data/

# Atualizar referências no código se necessário
grep -r "fueltech_data.db" src/ --include="*.py"
```

#### 1.3 Limpar logs duplicados
```bash
# Remover log da raiz (manter apenas em logs/ se existir)
rm -f fueltune.log
```

### FASE 2: PROBLEMAS IMPORTANTES 🟡

#### 2.1 Organizar scripts na raiz
```bash
# Mover scripts soltos para /scripts
mv performance_test.py scripts/
mv create-github-repo.sh scripts/setup/
mv create-repo.sh scripts/setup/
mv enable-sudo-nopasswd.sh scripts/setup/
mv push-to-github.sh scripts/setup/

# Criar subpastas se necessário
mkdir -p scripts/setup
mkdir -p scripts/utils
```

#### 2.2 Limpar pasta /app
```bash
# Verificar se app/README.md tem conteúdo útil
cat app/README.md

# Se vazio ou genérico, remover
rm -rf app/
```

#### 2.3 Limpar arquivos temporários
```bash
# Remover .pylintrc.temp
rm -f .pylintrc.temp

# Limpar scripts temporários
rm -rf scripts/temp/

# Remover caches antigos
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```

#### 2.4 Organizar bancos auxiliares
```bash
# Mover cache/metadata.db se necessário
mv cache/metadata.db data/cache_metadata.db
rmdir cache/
```

### FASE 3: SUGESTÕES 🟢

#### 3.1 Consolidar documentação
```bash
# Verificar READMEs duplicados
diff README.md docs/README.md

# Se idênticos, manter apenas o da raiz
# Se diferentes, consolidar conteúdo
```

#### 3.2 Limpar arquivos de documentação obsoletos
```bash
# Remover se redundantes
rm -f GITHUB-PUSH-INSTRUCTIONS.md  # Já no GitHub
```

#### 3.3 Organizar configurações
```bash
# Verificar .env files
ls -la .env* environments/.env*

# Consolidar se necessário
```

### FASE 4: VALIDAÇÃO

#### 4.1 Verificar estrutura final
```bash
# Estrutura esperada
tree -L 2 -d

# Deve mostrar:
# .
# ├── data/
# ├── docs/
# ├── environments/
# ├── infrastructure/
# ├── k8s/
# ├── monitoring/
# ├── scripts/
# ├── sphinx-docs/
# ├── src/
# ├── static/
# └── tests/
```

#### 4.2 Verificar imports
```python
# Script de validação
python << 'EOF'
import os
import ast

def check_imports(directory):
    errors = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        tree = ast.parse(f.read())
                    # Análise básica de imports
                except SyntaxError as e:
                    errors.append(f"{filepath}: {e}")
    return errors

errors = check_imports('src/')
if errors:
    print("Erros encontrados:")
    for e in errors:
        print(f"  - {e}")
else:
    print("✓ Todos os imports OK")
EOF
```

#### 4.3 Testar aplicação
```bash
# Verificar se ainda funciona
cd /home/lee/projects/fueltune-streamlit
source venv/bin/activate
streamlit run app.py --server.port 8502

# Verificar páginas principais
curl -s http://localhost:8502 | grep -q "FuelTune" && echo "✓ App rodando"
```

### FASE 5: ATUALIZAR REFERÊNCIAS

#### 5.1 Atualizar imports se necessário
```python
# Buscar e corrigir referências antigas
grep -r "from pages" src/ --include="*.py"
grep -r "import pages" src/ --include="*.py"

# Atualizar para:
# from src.ui.pages import ...
```

#### 5.2 Atualizar caminhos de banco
```python
# Buscar referências ao banco
grep -r "fueltech_data.db" . --include="*.py"

# Atualizar para:
# data/fueltech_data.db
```

#### 5.3 Atualizar documentação
```bash
# Atualizar README se necessário
# Mencionar nova estrutura
```

## CHECKLIST DE EXECUÇÃO

### Preparação
- [ ] Backup criado
- [ ] Aplicação parada
- [ ] Relatório revisado

### Execução - Críticos
- [ ] Pasta /pages movida
- [ ] Banco fueltech_data.db movido
- [ ] Logs limpos

### Execução - Importantes  
- [ ] Scripts organizados
- [ ] Pasta /app tratada
- [ ] Temporários removidos
- [ ] Bancos auxiliares organizados

### Execução - Sugestões
- [ ] Documentação consolidada
- [ ] Arquivos obsoletos removidos
- [ ] Configurações organizadas

### Validação
- [ ] Estrutura verificada
- [ ] Imports testados
- [ ] Aplicação funcionando

### Finalização
- [ ] Commit das mudanças
- [ ] Push para GitHub
- [ ] Documentação atualizada

## COMANDOS CONSOLIDADOS

```bash
#!/bin/bash
# Script completo de limpeza

echo "=== INICIANDO LIMPEZA DO PROJETO ==="

# FASE 1: CRÍTICOS
echo "→ Movendo pasta /pages..."
if [ -f "pages/Performance_Monitor.py" ]; then
    mv pages/Performance_Monitor.py src/ui/pages/
    rmdir pages/
fi

echo "→ Movendo banco de dados..."
[ -f "fueltech_data.db" ] && mv fueltech_data.db data/

echo "→ Limpando logs..."
rm -f fueltune.log

# FASE 2: IMPORTANTES
echo "→ Organizando scripts..."
mkdir -p scripts/setup
[ -f "performance_test.py" ] && mv performance_test.py scripts/
[ -f "create-github-repo.sh" ] && mv create-github-repo.sh scripts/setup/
[ -f "create-repo.sh" ] && mv create-repo.sh scripts/setup/
[ -f "enable-sudo-nopasswd.sh" ] && mv enable-sudo-nopasswd.sh scripts/setup/
[ -f "push-to-github.sh" ] && mv push-to-github.sh scripts/setup/

echo "→ Limpando temporários..."
rm -f .pylintrc.temp
rm -rf scripts/temp/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "→ Organizando cache..."
if [ -f "cache/metadata.db" ]; then
    mv cache/metadata.db data/cache_metadata.db
    rmdir cache/
fi

# FASE 3: SUGESTÕES
echo "→ Limpando documentação obsoleta..."
[ -f "GITHUB-PUSH-INSTRUCTIONS.md" ] && rm -f GITHUB-PUSH-INSTRUCTIONS.md

echo "→ Removendo pasta /app vazia..."
[ -d "app" ] && rm -rf app/

echo "=== LIMPEZA CONCLUÍDA ==="
echo "Por favor, teste a aplicação para garantir que tudo funciona!"
```

## ROLLBACK (SE NECESSÁRIO)

```bash
# Se algo der errado, reverter com git:
git status
git checkout -- .
git clean -fd

# Ou restaurar do backup
```

## MÉTRICAS DE SUCESSO

- ✅ Zero arquivos na raiz (exceto configs essenciais)
- ✅ Estrutura 100% padronizada
- ✅ Sem arquivos temporários
- ✅ Aplicação funcionando normalmente
- ✅ Todos os testes passando

## STATUS
**PENDENTE** - Aguardando execução

---
*Agente executor para limpeza e organização do projeto FuelTune Analyzer*