# KubeChain Local Development Setup Guide

This guide describes how to configure, develop, and test the KubeChain platform locally.

---

## 1. Prerequisites

Verify that the following development tools are installed on your workstation:

| Tool | Minimum Version | Installation Reference |
| :--- | :--- | :--- |
| **Python** | 3.12+ | `brew install python@3.12` or pyenv |
| **Docker** | 24.0+ | [Docker Desktop](https://www.docker.com/products/docker-desktop/) or OrbStack |
| **kubectl** | 1.30+ | `brew install kubectl` |
| **kind** | 0.22+ | `brew install kind` (Required for Phase 1) |
| **Helm** | 3.14+ | `brew install helm` (Required for Phase 8) |
| **Make** | Any standard version | Standard macOS / Linux utility |

---

## 2. Quickstart via Makefile

The repository includes a comprehensive `Makefile` automating common development workflows.

### A. Environment Initialization
```bash
# Clone the repository
git clone https://github.com/aniruddhajadhav7/kubechain.git
cd kubechain

# Initialize virtual environment, install dev dependencies, and seed .env
make install
```

### B. Code Quality & Formatting
```bash
# Run Ruff linting
make lint

# Run Ruff formatting check
make format-check

# Auto-format codebase
make format

# Run Mypy static type checking
make typecheck
```

### C. Running Automated Tests
```bash
# Run full automated test suite
make test

# Run unit tests only
make test-unit

# Run tests with coverage reporting
make test-cov
```

### D. Managing Local Supporting Services
```bash
# Start local Redis container
make up

# Inspect running services
docker compose ps

# Stop local Redis container
make down
```

---

## 3. Configuration Management

Local environment settings are loaded from `.env` (copied from `.env.example`).

To customize gateway ports, chain IDs, or Redis connections, edit `.env`:
```bash
# Example overrides
CHAIN_ID=31337
GATEWAY_PORT=8000
REDIS_HOST=localhost
REDIS_PORT=6379
```

All environment variables are validated by Pydantic Settings in `core/config.py`.

---

## 4. Building Container Images

Both the Operator and Gateway include multi-stage Dockerfiles configured to run as unprivileged user `UID 10001`:

```bash
# Build both container images
make docker-build

# Verify built images
docker images | grep kubechain
```

---

## 5. Development Invariants

1. **No Direct Infrastructure Mutations in Gateway**: The Gateway (`gateway/`) possesses zero write access to Kubernetes resources.
2. **Deterministic Caching**: All cache keys are canonicalized with SHA-256 in `core/` and `gateway/`. Unfinalized blocks are never cached immutably.
3. **Structured Observability**: Metric labels adhere to strictly bounded cardinality; wallet addresses, API keys, and transaction hashes must never be used as metric labels.
