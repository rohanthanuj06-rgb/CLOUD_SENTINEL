# CloudSentinel REST & WebSocket API Reference

The backend provides complete OpenAPI / Swagger documentation accessible at:
`http://localhost:8000/docs`

---

## 1. System Controller (`/api/system`)

- `GET /api/system/status`: Returns Docker engine connectivity, Firebase status, active node counts, and operational mode.
- `GET /api/system/config`: Returns active health scoring weights, warning/critical thresholds, and auto-recovery status.
- `POST /api/system/config/weights`: Admin endpoint to update multi-factor weights.
- `POST /api/system/config/thresholds`: Admin endpoint to update classification thresholds.
- `POST /api/system/config/auto-recovery/toggle?enabled={true|false}`: Admin toggle for autonomous self-healing.

---

## 2. Monitored Nodes (`/api/nodes`)

- `GET /api/nodes`: Lists all monitored container nodes with current health score, classification, and cluster summary.
- `GET /api/nodes/{node_id}`: Returns deep telemetry metrics, diagnosis, alerts, and recent logs for a specific node.
- `GET /api/nodes/{node_id}/metrics?range={5m|15m|1h|6h|24h}`: Returns historical time-series data for line charts.
- `GET /api/nodes/{node_id}/logs?tail={50}`: Returns container stdout/stderr log stream.
- `POST /api/nodes/{node_id}/restart`: Triggers manual container restart.
- `POST /api/nodes/{node_id}/recreate`: Triggers fresh container recreation from base image.
- `POST /api/nodes/{node_id}/scale`: Triggers simulated workload scale-out.

---

## 3. Alerts (`/api/alerts`)

- `GET /api/alerts?status={ACTIVE|ACKNOWLEDGED|RESOLVED}`: Returns alerts feed.
- `POST /api/alerts/{alert_id}/acknowledge`: Marks alert as acknowledged.
- `POST /api/alerts/{alert_id}/resolve`: Marks alert as resolved.

---

## 4. Recovery Operations (`/api/recovery`)

- `GET /api/recovery`: Returns recovery incident summary, success rate, and historical timeline.
- `POST /api/recovery/trigger`: Operator endpoint to manually initiate tiered self-healing on a node.
- `POST /api/recovery/{recovery_id}/approve`: Admin endpoint to approve or reject low-confidence recoveries.

---

## 5. Diagnostics & Predictions (`/api/diagnostics`, `/api/predictions`)

- `GET /api/diagnostics`: Returns root cause analysis, evidence list, and confidence scores across all nodes.
- `GET /api/predictions`: Computes Scikit-Learn linear regression degradation trajectories and Isolation Forest anomaly scores.

---

## 6. Fault Injection (`/api/faults`)

- `POST /api/faults/cpu`: Injects controlled CPU stress.
- `POST /api/faults/memory`: Injects controlled memory allocation.
- `POST /api/faults/application`: Injects application failure (HTTP 500 on /health).
- `POST /api/faults/container`: Stops target container.
- `POST /api/faults/network`: Injects artificial network latency.
- `POST /api/faults/disk`: Injects temporary disk pressure.
- `POST /api/faults/reset`: Resets all active faults.

---

## 7. Audit & Reports (`/api/audit`, `/api/reports`)

- `GET /api/audit`: Returns immutable audit logs with optional node and event filters.
- `GET /api/reports/summary`: Returns cluster reliability and self-healing executive summary.
- `GET /api/reports/export/csv`: Generates downloadable CSV export of infrastructure telemetry.

---

## 8. WebSocket Stream (`/ws`)

- WebSocket endpoint broadcasting:
  - `TELEMETRY_UPDATE` (every probe cycle)
  - `RECOVERY_STARTED` & `RECOVERY_COMPLETED`
  - `ALERT_CREATED` & `ALERT_UPDATED`
  - `AUDIT_LOGGED`
