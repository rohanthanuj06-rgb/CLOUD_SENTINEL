# CloudSentinel Hierarchical Recovery Engine

## 1. Overview

Blindly restarting containers or hosts whenever a failure occurs is dangerous and wasteful. **CloudSentinel** implements a tiered hierarchical recovery strategy:

```
FAILURE DETECTED
       │
       ▼
Tier 1: Restart Application Process (via REST /restart_app)
       │
   Passed? ──► YES ──► Verify Health ──► RECOVERY COMPLETED
       │
      NO
       ▼
Tier 2: Restart Container (via Docker SDK container.restart)
       │
   Passed? ──► YES ──► Verify Health ──► RECOVERY COMPLETED
       │
      NO
       ▼
Tier 3: Recreate Container Fresh (destroy & recreate clean image)
       │
   Passed? ──► YES ──► Verify Health ──► RECOVERY COMPLETED
       │
      NO
       ▼
Tier 4: Workload Failover (redirect traffic to healthy standby node)
       │
   Passed? ──► YES ──► Verify Health ──► RECOVERY COMPLETED
       │
      NO
       ▼
Tier 5: Administrator Escalation (CRITICAL Alert & Incident Audit)
```

---

## 2. Recovery Flow Mermaid Diagram

```mermaid
flowchart TD
    Start([Failure Diagnosed]) --> Gate{Recovery Confidence >= 50%?}
    Gate -- No --> Suspend[Status: REQUIRES_APPROVAL<br>Wait for Admin Review]
    Suspend --> AdminChoice{Admin Decision}
    AdminChoice -- Approved --> T1
    AdminChoice -- Rejected --> Terminate([Action Aborted])

    Gate -- Yes --> T1[Tier 1: Restart Application Layer]
    T1 --> V1{Verify Health<br>Delay: 2.5s}
    V1 -- Passed (Score >= 75%) --> Done([Recovery Successful])
    
    V1 -- Failed --> T2[Tier 2: Restart Docker Container]
    T2 --> V2{Verify Health<br>Delay: 2.5s}
    V2 -- Passed --> Done
    
    V2 -- Failed --> T3[Tier 3: Recreate Container From Image]
    T3 --> V3{Verify Health<br>Delay: 2.5s}
    V3 -- Passed --> Done
    
    V3 -- Failed --> T4[Tier 4: Workload Failover to Standby Node]
    T4 --> V4{Verify Health<br>Delay: 2.5s}
    V4 -- Passed --> Done
    
    V4 -- Failed --> T5[Tier 5: Escalate to Administrator]
    T5 --> Alert[Log Critical Alert & Incident Report]
    Alert --> End([Unresolved Failure Escalated])
```

---

## 3. Post-Recovery Health Verification

A recovery is never assumed successful simply because a command completed without exit code errors.

The `RecoveryVerifier` executes the following checks:
1. **Stabilization Delay**: Waits a configurable stabilization window (default 2.5 seconds).
2. **Container State**: Confirms Docker container status is `running`.
3. **Heartbeat Re-Probe**: Probes `/heartbeat` to ensure ping viability.
4. **Application Probe**: Queries HTTP `/health` expecting HTTP 200 OK.
5. **Latency Measurement**: Verifies response latency is sub-second.
6. **Health Score Delta**: Recalculates composite score and verifies `health_after >= 65.0`.
7. **Audit Logging**: Emits an immutable audit log with pre- and post-recovery health metrics.
