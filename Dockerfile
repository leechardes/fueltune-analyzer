# =============================================
# FuelTune Streamlit - Multi-stage Dockerfile
# =============================================
# Optimized for production deployment
# Target size: < 500MB
# Build time: < 2 minutes

# =============================================
# Stage 1: Base Dependencies
# =============================================
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# =============================================
# Stage 2: Python Dependencies
# =============================================
FROM base as deps

# Create app directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt requirements-test.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt

# =============================================
# Stage 3: Application Build
# =============================================
FROM deps as builder

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p logs data cache && \
    chmod -R 755 logs data cache

# Remove development files
RUN rm -rf \
    venv/ \
    .git/ \
    .github/ \
    .mypy_cache/ \
    .pytest_cache/ \
    __pycache__/ \
    *.pyc \
    *.pyo \
    .coverage \
    htmlcov/ \
    tests/ \
    docs/

# =============================================
# Stage 4: Production Runtime
# =============================================
FROM python:3.12-slim as production

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8503 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_THEME_BASE=light \
    LOG_LEVEL=INFO

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r fueltune && useradd --no-log-init -r -g fueltune fueltune

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code from builder
COPY --from=builder --chown=fueltune:fueltune /app .

# Create required directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/cache && \
    chown -R fueltune:fueltune /app && \
    chmod -R 755 /app

# Switch to non-root user
USER fueltune

# Expose Streamlit port
EXPOSE 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8503/_stcore/health || exit 1

# Default command
CMD ["streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0", "--server.headless=true"]
