# ADR-002: Strict Data Plane and Control Plane Boundary Isolation

## Status
Accepted

## Context
A common architectural flaw in infrastructure-integrated proxy systems is coupling the request routing proxy directly to the infrastructure manager (e.g., having an RPC gateway create, scale, or delete Kubernetes pods in response to traffic).

Such tight coupling introduces severe failure modes:
1. Compromising the public-facing gateway would grant an attacker write access to the Kubernetes cluster API.
2. High inbound RPC traffic would flood the Kubernetes API server with read/write requests.
3. Network partitions or API server degradation would cascade into total RPC request failure.

## Decision
We enforce a **strict, unidirectional separation of concerns** between the Data Plane (Gateway) and Control Plane (Operator):

1. **The Gateway is Read-Only with respect to Infrastructure**:
   - The Gateway has zero Kubernetes write privileges (no RBAC permissions to create, update, or delete pods, services, or CRDs).
   - The Gateway discovers backend nodes via Kubernetes DNS (`<service>.<namespace>.svc`) or a localized, read-only cache of endpoints.
   - The Gateway never interacts with the Kubernetes API on the critical request path.
2. **The Operator is the Sole Infrastructure Mutator**:
   - Only the Kopf operator holds RBAC permissions to reconcile `BlockchainNode` resources and mutate StatefulSets, PVCs, and Services.
   - The Operator does not route or inspect JSON-RPC user traffic.

```
[ User Request ] ---> [ Data Plane: Gateway ] ---> [ StatefulSet: Anvil Pods ]
                             ^
                             | (DNS / Endpoints discovery only)
[ Kubernetes API ] <--- [ Control Plane: Operator ] ---> (Reconciles StatefulSet)
```

## Consequences
- **Positive**: Adheres to the principle of least privilege; insulates the Kubernetes API from external traffic surges; eliminates cascading failures; enables independent horizontal scaling of Gateway and Operator.
- **Negative**: Gateway cannot unilaterally command the cluster to auto-scale on a per-request basis; scaling must occur through metrics-based autoscaling (HPA) or operator-managed reconciliation.
