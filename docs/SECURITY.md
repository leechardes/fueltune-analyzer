# Política de Segurança

## Versões Suportadas

Nós fornecemos atualizações de segurança para as seguintes versões do FuelTune Streamlit:

| Versão | Suportada          |
| ------- | ------------------ |
| 1.0.x   | ✅ |
| < 1.0   | ❌ |

## Reportando uma Vulnerabilidade

A segurança do FuelTune Streamlit é levada a sério. Se você descobrir uma vulnerabilidade de segurança, por favor siga estas diretrizes:

### 🔒 Divulgação Responsável

**NÃO** abra uma issue pública para vulnerabilidades de segurança. Em vez disso:

1. **Envie um email para**: [security@fueltune.com](mailto:security@fueltune.com)
2. **Use o assunto**: `[SECURITY] Vulnerabilidade em FuelTune Streamlit`
3. **Inclua detalhes**:
   - Descrição da vulnerabilidade
   - Steps para reproduzir
   - Impacto potencial
   - Versão afetada
   - Sua informação de contato

### ⏱️ Processo de Resposta

Nosso processo de resposta a vulnerabilidades:

1. **Confirmação**: Respondemos em até **24 horas**
2. **Investigação**: Avaliamos em até **72 horas**
3. **Correção**: Desenvolva patch em **7-14 dias**
4. **Release**: Publique correção em **14-30 dias**
5. **Divulgação**: Divulgação coordenada após correção

### 🏆 Reconhecimento

Contribuidores de segurança são reconhecidos em:

- **Hall of Fame de Segurança**
- **Release notes** (com permissão)
- **Página de agradecimentos**

## Boas Práticas de Segurança

### Para Usuários

#### Instalação Segura
```bash
# Sempre use ambientes virtuais
python -m venv venv
source venv/bin/activate

# Instale de fontes confiáveis
pip install fueltune-streamlit

# Verifique integridade
pip check
```

#### Configuração Segura
```bash
# Use .env para configurações sensíveis
echo "DATABASE_URL=sqlite:///secure_db.db" > .env
chmod 600 .env

# Não committe credenciais
echo ".env" >> .gitignore
```

#### Execução Segura
```bash
# Execute em ambiente controlado
./scripts/run.sh --prod

# Use HTTPS em produção
export STREAMLIT_SERVER_ENABLE_HTTPS=true
```

### Para Desenvolvedores

#### Desenvolvimento Seguro
```python
# Use type hints para prevenir erros
def process_user_input(data: str) -> ProcessedData:
    # Valide sempre os inputs
    if not isinstance(data, str):
        raise ValueError("Input deve ser string")
    
    # Sanitize dados
    clean_data = sanitize_input(data)
    return process_data(clean_data)

# Trate secrets apropriadamente
import os
from typing import Optional

def get_secret(key: str) -> Optional[str]:
    """Recupera secret de forma segura."""
    return os.environ.get(key)
```

#### Code Review de Segurança
- ✅ Validação de input
- ✅ Sanitização de dados
- ✅ Tratamento de erros
- ✅ Logging de segurança
- ✅ Gestão de secrets
- ✅ Autenticação/Autorização

## Checklist de Segurança

### 🔍 Análise Estática

Usamos as seguintes ferramentas:

```bash
# Bandit - Análise de segurança
bandit -r src/ -f json -o security-report.json

# Safety - Vulnerabilidades conhecidas
pip install safety
safety check

# Semgrep - Análise de código
semgrep --config=auto src/
```

### 🛡️ Controles de Segurança

#### Validação de Input
```python
from pandera import DataFrameSchema, Column
import pandera as pa

# Schema para validação FuelTech
fueltech_schema = DataFrameSchema({
    "time": Column(pa.Float, checks=pa.Check.ge(0)),
    "rpm": Column(pa.Int, checks=[
        pa.Check.ge(0),
        pa.Check.le(15000)  # RPM máximo razoável
    ]),
    "throttle_position": Column(pa.Float, checks=[
        pa.Check.ge(0),
        pa.Check.le(100)
    ])
})

def validate_fueltech_data(df: pd.DataFrame) -> pd.DataFrame:
    """Valida dados FuelTech contra schema."""
    try:
        return fueltech_schema.validate(df)
    except pa.errors.SchemaError as e:
        logger.error(f"Validação falhou: {e}")
        raise ValueError("Dados inválidos") from e
```

#### Sanitização
```python
import re
from pathlib import Path

def sanitize_filename(filename: str) -> str:
    """Sanitiza nome de arquivo."""
    # Remove caracteres perigosos
    safe_filename = re.sub(r'[^\w\-_\.]', '', filename)
    
    # Previne path traversal
    safe_filename = Path(safe_filename).name
    
    # Limite de tamanho
    if len(safe_filename) > 255:
        safe_filename = safe_filename[:255]
    
    return safe_filename

def sanitize_sql_input(input_str: str) -> str:
    """Sanitiza input SQL."""
    # Use parametrização em vez de sanitização manual
    # Este é apenas um exemplo
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/"]
    clean_str = input_str
    
    for char in dangerous_chars:
        clean_str = clean_str.replace(char, "")
    
    return clean_str
```

#### Logging de Segurança
```python
import logging
from typing import Dict, Any

security_logger = logging.getLogger("security")

def log_security_event(
    event_type: str,
    user_id: str,
    details: Dict[str, Any],
    success: bool = True
) -> None:
    """Log eventos de segurança."""
    log_entry = {
        "event_type": event_type,
        "user_id": user_id,
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }
    
    if success:
        security_logger.info(f"Security event: {log_entry}")
    else:
        security_logger.warning(f"Security failure: {log_entry}")

# Uso
log_security_event(
    "file_upload",
    "user123", 
    {"filename": "data.csv", "size": 1024},
    success=True
)
```

### 🔐 Autenticação e Autorização

#### Configuração para Produção
```python
# config/production.py
import os
from typing import Optional

class SecurityConfig:
    """Configurações de segurança para produção."""
    
    # Autenticação
    REQUIRE_AUTH: bool = True
    AUTH_METHOD: str = "oauth2"  # oauth2, basic, custom
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # File uploads
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set = {".csv", ".txt"}
    
    # Database
    DB_ENCRYPTION: bool = True
    DB_BACKUP_ENCRYPTION: bool = True
    
    # Logging
    LOG_SENSITIVE_DATA: bool = False
    AUDIT_LOG_RETENTION: int = 90  # days
    
    @classmethod
    def get_secret_key(cls) -> str:
        """Recupera chave secreta."""
        key = os.environ.get("SECRET_KEY")
        if not key:
            raise ValueError("SECRET_KEY não configurada")
        return key
```

### 🚨 Monitoramento de Segurança

#### Métricas de Segurança
```python
from prometheus_client import Counter, Histogram

# Métricas de segurança
security_events = Counter(
    'security_events_total',
    'Total security events',
    ['event_type', 'success']
)

failed_logins = Counter(
    'failed_logins_total', 
    'Total failed login attempts',
    ['user_id', 'ip_address']
)

file_upload_size = Histogram(
    'file_upload_size_bytes',
    'Size of uploaded files'
)

# Uso
def track_security_event(event_type: str, success: bool):
    security_events.labels(
        event_type=event_type,
        success=str(success).lower()
    ).inc()
```

#### Alertas Automáticos
```yaml
# monitoring/alerts.yml
groups:
  - name: security
    rules:
      - alert: HighFailedLoginRate
        expr: rate(failed_logins_total[5m]) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High failed login rate detected"
          
      - alert: LargeFileUpload
        expr: file_upload_size_bytes > 50000000  # 50MB
        for: 0s
        labels:
          severity: info
        annotations:
          summary: "Large file upload detected"
          
      - alert: SecurityEventSpike
        expr: rate(security_events_total{success="false"}[5m]) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Spike in security failures"
```

## Configurações de Produção

### Environment Variables
```bash
# Segurança
export SECRET_KEY="sua-chave-super-secreta-aqui"
export ENCRYPT_DATABASE=true
export REQUIRE_HTTPS=true

# Rate limiting
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_REQUESTS=100

# File uploads
export MAX_FILE_SIZE=104857600  # 100MB
export ALLOWED_EXTENSIONS=".csv,.txt"

# Logging
export LOG_LEVEL=INFO
export LOG_SENSITIVE_DATA=false
export AUDIT_LOG_ENABLED=true
```

### Nginx Configuration
```nginx
# /etc/nginx/sites-available/fueltune
server {
    listen 443 ssl http2;
    server_name fueltune.example.com;
    
    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # File Upload Limits
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Security
```dockerfile
# Dockerfile - Produção Segura
FROM python:3.11-slim

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Definir permissões
RUN chown -R appuser:appuser /app
USER appuser

# Configurações de segurança
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/health')"

# Expor porta
EXPOSE 8501

# Comando de inicialização
CMD ["python", "main.py", "--prod"]
```

## Compliance e Auditoria

### GDPR Compliance
```python
# Data protection utilities
class GDPRCompliance:
    """Utilitários para compliance com GDPR."""
    
    @staticmethod
    def anonymize_data(df: pd.DataFrame) -> pd.DataFrame:
        """Anonimiza dados pessoais."""
        # Remove colunas identificáveis
        sensitive_columns = ['user_id', 'license_plate', 'location']
        return df.drop(columns=sensitive_columns, errors='ignore')
    
    @staticmethod
    def hash_identifier(identifier: str) -> str:
        """Hash identificadores para pseudônimos."""
        import hashlib
        return hashlib.sha256(identifier.encode()).hexdigest()
    
    @staticmethod
    def log_data_access(user_id: str, data_type: str):
        """Log acesso a dados pessoais."""
        log_security_event(
            "data_access",
            user_id,
            {"data_type": data_type}
        )
```

### Audit Trail
```python
class AuditTrail:
    """Sistema de auditoria."""
    
    def __init__(self):
        self.audit_logger = logging.getLogger("audit")
    
    def log_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Dict[str, Any] = None
    ):
        """Log ação do usuário."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {},
            "ip_address": self._get_client_ip(),
            "user_agent": self._get_user_agent()
        }
        
        self.audit_logger.info(json.dumps(audit_entry))
```

## Contatos de Segurança

### Equipe de Segurança
- **Email Principal**: [security@fueltune.com](mailto:security@fueltune.com)
- **PGP Key ID**: `ABCD1234EFGH5678`
- **Resposta**: 24 horas (dias úteis)

### Emergências
Para vulnerabilidades críticas:
- **Email**: [security-urgent@fueltune.com](mailto:security-urgent@fueltune.com)
- **Telefone**: +55 (11) 9999-9999
- **Resposta**: 2-4 horas (24/7)

### Bug Bounty
Atualmente não temos um programa formal de bug bounty, mas reconhecemos contribuições de segurança através de:
- Menção em release notes
- Hall of fame de segurança
- Possível recompensa simbólica

---

## Recursos Adicionais

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Guide](https://python-security.readthedocs.io/)
- [Streamlit Security](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso)
- [Docker Security](https://docs.docker.com/engine/security/)

**Obrigado por ajudar a manter o FuelTune Streamlit seguro!** 🔒