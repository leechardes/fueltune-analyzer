# FIX-IMPORT-DUPLICATES Agent

## MISSÃO
Corrigir erro de importação de CSV que ocorre devido a constraint check de g_accel_range e implementar verificação de sessão duplicada com opção de sobrescrever.

## CONTEXTO
- **Erro atual:** `CHECK constraint failed: chk_g_accel_range` ao importar CSV
- **Problema:** Valores de g_force_accel fora do range permitido (-6.5542 está fora do limite)
- **Necessidade:** Verificar se sessão já existe e permitir sobrescrever
- **Arquivo de teste:** `/home/lee/Log 3_20250829_1806_log.csv`

## ANÁLISE DO ERRO

### Constraint Violada
```sql
CHECK constraint failed: chk_g_accel_range
```

### Valores Problemáticos no Log
- `g_force_accel`: -6.5542, -6.5478, -6.5438, -6.5386, -6.5374
- Esses valores estão ligeiramente abaixo do limite mínimo esperado (-6.5)

## TAREFAS

### 1. Verificar e Ajustar Constraints do Banco
- [ ] Localizar definição da constraint `chk_g_accel_range` em `models.py`
- [ ] Verificar limites atuais (provavelmente -6.5 a 6.5)
- [ ] Ajustar para acomodar valores reais dos logs (-7.0 a 7.0)

### 2. Implementar Verificação de Sessão Duplicada
- [ ] Adicionar método `check_existing_session()` em `database.py`
- [ ] Implementar diálogo de confirmação no upload
- [ ] Adicionar opção `force_reimport=True` na interface

### 3. Melhorar Tratamento de Erros
- [ ] Capturar erros de constraint específicos
- [ ] Fornecer mensagens claras ao usuário
- [ ] Implementar validação prévia dos dados

### 4. Atualizar Interface de Upload
- [ ] Adicionar checkbox "Sobrescrever se existir"
- [ ] Mostrar preview dos dados antes de importar
- [ ] Exibir validação de ranges dos campos

## IMPLEMENTAÇÃO

### Passo 1: Ajustar Models.py
```python
# Em models.py - ajustar constraint
g_force_accel = Column(Float, CheckConstraint('g_force_accel >= -7.0 AND g_force_accel <= 7.0'))
g_force_lateral = Column(Float, CheckConstraint('g_force_lateral >= -7.0 AND g_force_lateral <= 7.0'))
```

### Passo 2: Melhorar database.py
```python
def check_existing_session(self, file_hash: str) -> Optional[DataSession]:
    """Check if session with same file hash exists."""
    return self.db_manager.get_session_by_hash(file_hash)

def delete_existing_session(self, session_id: str) -> bool:
    """Delete existing session and all related data."""
    with self.get_session() as session:
        # Delete cascade will handle related data
        session.query(DataSession).filter_by(id=session_id).delete()
        session.commit()
    return True
```

### Passo 3: Atualizar upload.py
```python
# Adicionar na interface
force_reimport = st.checkbox(
    "Sobrescrever dados existentes",
    help="Se marcado, dados existentes serão substituídos"
)

# No processamento
if existing_session and not force_reimport:
    st.warning(f"Arquivo já importado como '{existing_session.session_name}'")
    if st.button("Sobrescrever mesmo assim"):
        force_reimport = True
```

### Passo 4: Validação Prévia
```python
def validate_g_force_ranges(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate g-force values are within acceptable ranges."""
    issues = []
    
    if 'g_force_accel' in df.columns:
        min_val = df['g_force_accel'].min()
        max_val = df['g_force_accel'].max()
        if min_val < -7.0 or max_val > 7.0:
            issues.append(f"g_force_accel fora do range: [{min_val:.2f}, {max_val:.2f}]")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues
    }
```

## TESTES

### Teste 1: Importação com Valores Extremos
```bash
# Usar arquivo de teste
python -c "
from src.data.database import FuelTechDatabase
db = FuelTechDatabase()
result = db.import_csv_file('/home/lee/Log 3_20250829_1806_log.csv', force_reimport=True)
print(result)
"
```

### Teste 2: Verificação de Duplicatas
```bash
# Importar duas vezes o mesmo arquivo
# Primeira vez deve funcionar
# Segunda vez deve detectar duplicata
```

### Teste 3: Sobrescrever Sessão
```bash
# Importar com force_reimport=True
# Deve deletar sessão anterior e reimportar
```

## ARQUIVOS A MODIFICAR

1. **src/data/models.py**
   - Ajustar constraints de g_force_accel e g_force_lateral
   - Expandir ranges para -7.0 a 7.0

2. **src/data/database.py**
   - Melhorar método `import_csv_file()`
   - Adicionar tratamento específico para constraint errors
   - Implementar validação prévia

3. **src/ui/pages/upload.py**
   - Adicionar checkbox para força reimportação
   - Melhorar feedback de erros
   - Mostrar preview de validação

4. **src/data/validators.py**
   - Adicionar validação específica para g-force ranges
   - Retornar warnings para valores próximos aos limites

## VALIDAÇÃO

### Critérios de Sucesso
- [ ] Importação do arquivo de teste sem erros
- [ ] Detecção correta de sessões duplicadas
- [ ] Opção funcional de sobrescrever
- [ ] Mensagens de erro claras e acionáveis
- [ ] Validação prévia previne erros de constraint

### Métricas
- Zero erros de constraint após ajustes
- Tempo de importação < 5s para arquivo de teste
- Interface intuitiva com feedback claro

## PADRÕES A SEGUIR
- Referência: `/home/lee/projects/fueltune-streamlit/docs/PYTHON-CODE-STANDARDS.md`
- **ZERO emojis** em interfaces de produção
- Type hints em todas as funções
- Docstrings Google Style
- Tratamento robusto de erros com logging

## STATUS
**PENDENTE** - Aguardando execução

---
*Agente criado para resolver problema crítico de importação*