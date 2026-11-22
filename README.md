# KubeChain

> **Kubernetes-Native Blockchain Infrastructure Orchestration Platform**

KubeChain is an engineering platform for declaratively provisioning, managing, monitoring, and exposing EVM-compatible blockchain RPC infrastructure on Kubernetes.

---

## 1. Architectural Layers

KubeChain is engineered as three decoupled planes:

1. **Control Plane (`operator/`)**:
   - Kubernetes Custom Resource Definition (`BlockchainNode`).
   - Python Operator powered by [Kopf](https://kopf.readthedocs.io/) and `kubernetes-asyncio`.
   - Continuous reconciliation of StatefulSets, Headless Services, ClusterIP Services, PDBs, and PVCs.
   - Autonomous drift detection and self-healing.

2. **Data Plane (`gateway/`)**:
   - Asynchronous JSON-RPC 2.0 Gateway built on [FastAPI](https://fastapi.tiangolo.com/) and [HTTPX](https://www.python-httpx.org/).
   - Method-aware intelligent routing and strict retry semantics (idempotent reads retried; stateful writes un-retried).
   - Redis-backed sliding window rate limiter with Compute Unit (CU) method weighting.
   - Reorg-safe deterministic Redis caching with fail-open circuit breaking.

3. **Observability & Reliability (`observability/`, `chaos/`)**:
   - Prometheus metrics with strictly bounded cardinality.
   - OpenTelemetry distributed tracing across request lifecycles.
   - Chaos Mesh failure injection and k6 load verification.

---

## 2. Repository Layout

```
Kubechain/
├── api/                  # CRD definitions and Pydantic schema representations
├── operator/             # Kopf Kubernetes operator controller and reconcilers
├── gateway/              # FastAPI JSON-RPC 2.0 gateway and routing engine
├── node_manager/         # Node lifecycle and blockchain-specific health probes
├── deploy/               # Kubernetes manifests, Helm charts, RBAC, and local configs
├── observability/        # Prometheus rules, Grafana dashboards, OpenTelemetry specs
├── chaos/                # Chaos Mesh and failure recovery experiment definitions
├── infra/                # Terraform infrastructure modules (EKS / Cloud)
├── tests/                # Unit, integration, e2e, and load test suites
└── docs/                 # Architectural specifications, decisions (ADRs), and runbooks
```

---

## 3. Quickstart (Development Setup)

### Prerequisites
- Python 3.12+
- Docker
- `kubectl`
- `kind` (Kubernetes in Docker)
- `helm`

### Environment Setup
```bash
# Clone the repository and enter workspace
git clone <repo_url>
cd Kubechain

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
```

### Running Checks
```bash
# Linting & Formatting Check
ruff check .
ruff format --check .

# Type Verification
mypy .

# Unit Tests
pytest
```

---

## 4. Development Phases

- [x] **Phase 0**: Architecture, repository foundation, ADRs, and tooling configuration.
- [ ] **Phase 1**: Local Kubernetes (`kind`) and deterministic Anvil development backend.
- [ ] **Phase 2**: Custom Resource Definition (`BlockchainNode`) and Python Kopf Operator.
- [ ] **Phase 3**: High-performance async JSON-RPC 2.0 Gateway.
- [ ] **Phase 4**: Node health engine, block lag evaluator, and dynamic discovery.
- [ ] **Phase 5**: Security layer (API keys, Compute Unit rate limiting, deterministic Redis cache).
- [ ] **Phase 6**: Observability (Prometheus, OpenTelemetry, Grafana dashboards).
- [ ] **Phase 7**: Reliability and Chaos testing.
- [ ] **Phase 8**: Helm packaging and CI/CD pipelines.
- [ ] **Phase 9**: Terraform & AWS EKS production infrastructure.

---

## 5. Architectural Decision Records (ADRs)

- [ADR-001: Kopf and Python for Kubernetes Operator](file:///Users/aniruddhajadhav/Desktop/Kubechain/docs/decisions/ADR-001-operator-framework.md)
- [ADR-002: Strict Data Plane and Control Plane Boundary Isolation](file:///Users/aniruddhajadhav/Desktop/Kubechain/docs/decisions/ADR-002-data-plane-isolation.md)
- [ADR-003: Deterministic Caching & Safe Retry Semantics for JSON-RPC](file:///Users/aniruddhajadhav/Desktop/Kubechain/docs/decisions/ADR-003-rpc-caching-retry-semantics.md)
