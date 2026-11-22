# ADR-001: Kopf & Python AsyncIO for Kubernetes Operator

## Status
Accepted

## Context
KubeChain requires a custom Kubernetes Controller to manage the lifecycle of blockchain workloads (`BlockchainNode` Custom Resources). The controller must reconcile desired state (declarative CR spec) against live state (StatefulSets, Services, PVCs, PodDisruptionBudgets), detect drift, handle failures, and update status conditions.

Common ecosystem options include:
1. **Go (Kubebuilder / Operator SDK)**: The standard Kubernetes ecosystem choice.
2. **Python (Kopf - Kubernetes Operator Pythonic Framework)**: High-level Python operator framework with native support for handlers, timers, subresources, and async execution.
3. **Rust (kube-rs)**: High-performance typed controller runtime.

## Decision
We select **Python 3.12+ with Kopf and `kubernetes-asyncio`** as the operator implementation framework for KubeChain.

### Architectural Rationale
1. **Language & Domain Alignment**: The gateway, telemetry, and platform tooling are unified on modern Python. Utilizing Python across both data plane and control plane allows shared models (`pydantic`), shared validation logic, and streamlined developer operations.
2. **Declarative Reconciliation in Kopf**: Kopf provides built-in reconciliation loops, automatic diff computation, event filtering, exponential backoff retries, and native status subresource updates.
3. **Async IO**: Using `kubernetes-asyncio` ensures non-blocking Kubernetes API communication and allows high-throughput handling of watch streams.

## Consequences
- **Positive**: Rapid development, unified Python code repository, shared Pydantic data schemas, robust built-in lifecycle handlers (`@kopf.on.create`, `@kopf.on.update`, `@kopf.on.timer`).
- **Negative**: Slightly higher memory footprint per controller replica than a statically compiled Go binary; requires careful handling of Kubernetes API pagination and watch stream reconnections.
