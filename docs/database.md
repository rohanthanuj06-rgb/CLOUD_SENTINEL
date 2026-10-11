# CloudSentinel Database & Storage Schema

## 1. Storage Architecture

CloudSentinel uses a hybrid persistence design:
1. **High-Frequency In-Memory Ring Buffer (`LocalDataStore`)**: Holds 1-second telemetry, recent metrics history (up to 500 points per node), active alerts, and session audit logs. Ensures sub-millisecond response times for dashboard charts without incurring cloud I/O costs.
2. **Aggregated Firestore Batches**: Background aggregator bundles local snapshots every 30-60 seconds into aggregated records (`avg_cpu`, `max_cpu`, `avg_mem`, `avg_latency`) to prevent excessive write costs on Firestore.
3. **Local Demo Mode Fallback**: When Firebase credentials are not provided in `.env`, the system automatically activates Local Demo Mode without error.

---

## 2. Data Models & Schemas

### `nodes` Collection
```json
{
  "node_id": "cs-node-web",
  "container_name": "cs-node-web",
  "container_id": "c1a2b3c4d5e6",
  "service_name": "web",
  "status": "running",
  "cpu_percent": 18.2,
  "memory_percent": 34.5,
  "disk_percent": 25.0,
  "response_time_ms": 42.0,
  "heartbeat": true,
  "application_healthy": true,
  "health_score": 93.5,
  "classification": "HEALTHY",
  "uptime_seconds": 3600.0,
  "restart_count": 0,
  "last_seen": "2026-10-08T09:40:00Z"
}
```

### `metrics` (Aggregated Telemetry)
```json
{
  "node_id": "cs-node-api",
  "window_start": "2026-10-08T09:40:00Z",
  "window_end": "2026-10-08T09:40:30Z",
  "avg_cpu": 22.4,
  "max_cpu": 38.1,
  "avg_memory": 45.2,
  "max_memory": 46.0,
  "avg_response_time": 45.6,
  "avg_health_score": 91.2,
  "sample_count": 10
}
```

### `alerts`
```json
{
  "id": "alt-9a1b2c",
  "node_id": "cs-node-storage",
  "alert_type": "DISK_PRESSURE",
  "severity": "WARNING",
  "status": "ACTIVE",
  "timestamp": "2026-10-08T09:42:00Z",
  "title": "Disk Pressure Injected on cs-node-storage",
  "description": "Storage buffer utilization exceeds 90%",
  "evidence": ["Volume space at 95%"],
  "recommended_action": "CLEAR_TEMP_BUFFERS"
}
```

### `recovery_actions`
```json
{
  "recovery_id": "rec-1a2b3c4d",
  "node_id": "cs-node-api",
  "failure_type": "APPLICATION_FAILURE",
  "action_tier": "RESTART_APPLICATION",
  "action_name": "RESTART_APPLICATION",
  "confidence_score": 0.95,
  "started_at": "2026-10-08T09:45:00Z",
  "completed_at": "2026-10-08T09:45:03Z",
  "result": "SUCCESS",
  "health_before": 22.0,
  "health_after": 94.0,
  "verification_passed": true
}
```

### `audit_logs`
```json
{
  "id": "aud-8f7e6d",
  "timestamp": "2026-10-08T09:45:03Z",
  "actor": "SYSTEM_SELF_HEALING",
  "role": "ADMIN",
  "target_node": "cs-node-api",
  "event_type": "SELF_HEALING",
  "action": "Self-recovery executed: RESTART_APPLICATION for APPLICATION_FAILURE",
  "result": "SUCCESS"
}
```
