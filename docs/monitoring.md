# CloudSentinel Monitoring & Multi-Factor Health Scoring

## 1. Multi-Factor Health Score Formulation

CloudSentinel uses a composite health score normalized between **0 and 100**:

$$\text{Health Score} = (S_{\text{CPU}} \times w_{\text{CPU}}) + (S_{\text{RAM}} \times w_{\text{RAM}}) + (S_{\text{Net}} \times w_{\text{Net}}) + (S_{\text{Resp}} \times w_{\text{Resp}}) + (S_{\text{HB}} \times w_{\text{HB}}) + (S_{\text{App}} \times w_{\text{App}})$$

### Default Weights:
- **CPU Score ($w_{\text{CPU}}$)**: `20%` (0.20)
- **RAM Score ($w_{\text{RAM}}$)**: `20%` (0.20)
- **Network Traffic ($w_{\text{Net}}$)**: `10%` (0.10)
- **Response Latency ($w_{\text{Resp}}$)**: `20%` (0.20)
- **Heartbeat Status ($w_{\text{HB}}$)**: `20%` (0.20)
- **Application Health ($w_{\text{App}}$)**: `10%` (0.10)

Weights can be dynamically tuned by an Administrator via `/api/system/config/weights`.

---

## 2. Infrastructure States

| State | Score Range | Description |
|---|---|---|
| **HEALTHY** | 86 - 100 | Normal operations; low CPU/RAM; fast response time; active heartbeat. |
| **GOOD** | 71 - 85 | Moderate workload; parameters well within nominal limits. |
| **WARNING** | 51 - 70 | Elevated utilization or response latency degradation. |
| **OVERLOADED** | Special | Sustained CPU > 90% or RAM > 90% leading to degraded throughput. |
| **POOR** | 31 - 50 | Multiple resource bottlenecks or degraded application endpoint. |
| **CRITICAL** | 0 - 30 | Severe multi-metric failure or collapsed application layer. |
| **UNRESPONSIVE**| Special | Consecutive missed heartbeats ($>= 3$) or socket probe timeout. |
| **DEAD** | Special | Docker container process terminated or crashed. |
| **IDLE** | Special | CPU < 5% and network < 1 KB/s during normal operations. |
| **ZOMBIE** | Special | Container running but prolonged zero activity ($> 120\text{s}$) with no active workload. |
| **RECOVERING** | Special | Autonomous self-healing action actively executing. |
| **RECOVERY_FAILED** | Special | Tiered recoveries attempted but post-verification health remains degraded. |

---

## 3. Heartbeat Surveillance

Every container node exposes `/heartbeat`:
- Backend probes `/heartbeat` every `HEALTH_INTERVAL` (3s).
- Tracks `last_heartbeat`, `missed_heartbeats`, and vitality flag.
- After 3 consecutive missed probes, the node is diagnosed with `CONTAINER_NETWORK_FAILURE` and passed to the recovery pipeline.
