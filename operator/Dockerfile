# Multi-stage non-root container configuration for KubeChain Operator
# Base image: Official Python 3.12 slim-bookworm

FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY core/ ./core/
COPY api/ ./api/
COPY operator/ ./operator/

# Install application and production dependencies into virtual environment
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install .

# ==============================================================================
# Production Runtime Stage
# ==============================================================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root system user and group (UID 10001)
RUN groupadd -g 10001 kubechain && \
    useradd -u 10001 -g kubechain -s /bin/false -m kubechain

COPY --from=builder /opt/venv /opt/venv
COPY core/ /app/core/
COPY api/ /app/api/
COPY operator/ /app/operator/

# Restrict permissions and run as non-root
RUN chown -R kubechain:kubechain /app
USER 10001

# Entrypoint for Kopf operator
ENTRYPOINT ["kopf", "run", "--all-namespaces", "-m", "operator"]
