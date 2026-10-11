# CloudSentinel Fault Injection System

## 1. Overview & Safety Guarantee

The CloudSentinel Fault Injection module allows operators and academic reviewers to simulate realistic cloud failure modes on demand without jeopardizing the physical host operating system.

> **CRITICAL SAFETY CONSTRAINT**:
> All fault injection requests validate target node IDs against a strict whitelist of containerized demo nodes (`cs-node-web`, `cs-node-api`, `cs-node-worker`, `cs-node-auth`, `cs-node-storage`). Requests targeting host processes or invalid IDs are rejected with HTTP 400 Bad Request.

---

## 2. Supported Fault Types

### 1. CPU Stress (`POST /api/faults/cpu`)
- **Mechanism**: Spawns worker threads inside the demo container executing tight SHA-256 hash operations.
- **Parameters**: `duration` (seconds), `intensity` (0.1 to 1.0).
- **Observed Behavior**: Node CPU spikes to 95%+, Health Score degrades, classifier flags `OVERLOADED`.

### 2. Memory Leak (`POST /api/faults/memory`)
- **Mechanism**: Allocates controlled 10MB bytearray segments inside container memory.
- **Parameters**: `mb` (MB to allocate), `duration` (seconds).
- **Observed Behavior**: Memory usage reaches cgroup limit, triggers `MEMORY_EXHAUSTION` diagnosis.

### 3. Application Crash (`POST /api/faults/application`)
- **Mechanism**: Sets internal `IS_HEALTHY = False` flag on target node, causing `GET /health` to return HTTP 500.
- **Observed Behavior**: Container process remains active on Docker socket, but application layer fails. Proves application-level failure detection. Triggers Tier 1 Application Restart.

### 4. Container Death (`POST /api/faults/container`)
- **Mechanism**: Stops the target Docker container via Docker SDK (`container.stop()`).
- **Observed Behavior**: Heartbeat drops immediately, socket connection fails, classifier marks `DEAD`. Triggers Tier 2 Container Restart.

### 5. Network Latency (`POST /api/faults/network`)
- **Mechanism**: Injects artificial delay into response handlers.
- **Parameters**: `delay_ms` (ms to sleep), `duration` (seconds).
- **Observed Behavior**: Response latency breaches 2500ms, triggering `PERFORMANCE_DEGRADATION` warning.

### 6. Disk Pressure (`POST /api/faults/disk`)
- **Mechanism**: Writes temporary buffer chunks to `/tmp/cs_disk_<node_id>/`.
- **Parameters**: `size_mb` (MB to write), `duration` (seconds).
- **Observed Behavior**: Disk usage hits 95%+, triggers `DISK_EXHAUSTION_RISK`. Auto-cleans on reset.

### 7. Reset All Faults (`POST /api/faults/reset`)
- **Mechanism**: Stops all stress threads, deletes temporary files, clears memory buffers, and restarts any stopped demo containers.
