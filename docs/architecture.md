# CloudSentinel System Architecture

## 1. Executive Summary

**CloudSentinel** (*An Intelligent Cloud-Based System for Virtual Machine/Container Failure Detection and Automated Recovery*) is an autonomous infrastructure health monitoring, fault diagnosis, and self-healing platform.

The system is designed to run entirely locally on a single physical machine using **Docker Desktop**, containerizing workloads to simulate a private cloud testbed without requiring paid cloud vendors or heavy VirtualBox/VMware virtual machines.

---

## 2. High-Level Architecture Diagram

```mermaid
graph TD
    User([Cloud Operator / Administrator]) -->|Interacts with| Dashboard[React Operations Dashboard]
    Dashboard -->|REST API / WebSocket| Controller[FastAPI Orchestration Controller]

    subgraph Controller_Subsystems [CloudSentinel Core Engine]
        Controller --> Monitor[Docker Monitoring Engine]
        Controller --> Score[Multi-Factor Health Scoring]
        Controller --> Diag[Rule-Based Diagnostic Engine]
        Controller --> Recovery[Hierarchical Self-Healing Orchestrator]
        Controller --> ML[Predictive Trend & Anomaly ML]
        Controller --> Storage[Local In-Memory Cache & Ring Buffer]
    end

    subgraph Infrastructure_Layer [Docker Containerized Infrastructure]
        Monitor -->|Docker SDK & Probes| Node1["Node 01: cs-node-web (Port 8001)"]
        Monitor -->|Docker SDK & Probes| Node2["Node 02: cs-node-api (Port 8002)"]
        Monitor -->|Docker SDK & Probes| Node3["Node 03: cs-node-worker (Port 8003)"]
        Monitor -->|Docker SDK & Probes| Node4["Node 04: cs-node-auth (Port 8004)"]
        Monitor -->|Docker SDK & Probes| Node5["Node 05: cs-node-storage (Port 8005)"]
    end

    subgraph Persistence_Layer [Persistence & Telemetry]
        Storage -->|Aggregated 30s/1m batches| Firestore[(Firebase Firestore Cloud Persistence)]
        Controller -->|Role Verification| FirebaseAuth[Firebase Auth / Demo RBAC]
    end
```

---

## 3. Telemetry and Data Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Node as Container Node (/health)
    participant Monitor as Telemetry Collector
    participant Engine as Health Scoring Engine
    participant Diag as Diagnostic Rule Engine
    participant Recovery as Recovery Orchestrator
    participant UI as React Dashboard (WebSocket)

    loop Every 3 Seconds (HEALTH_INTERVAL)
        Monitor->>Node: HTTP GET /health & GET /heartbeat
        Node-->>Monitor: Status, Latency (ms), Active Faults
        Monitor->>Monitor: Query Docker SDK Stats (CPU %, RAM %, Net RX/TX)
        Monitor->>Engine: Calculate Multi-Factor Health Score (0-100)
        Engine-->>Monitor: Health Score & 6 Sub-scores
        Monitor->>Diag: Classify State & Evaluate Root Causes
        
        alt Node Degraded / Failed (Confidence >= 80%)
            Diag->>Recovery: Trigger Autonomous Self-Healing
            Recovery->>Node: Execute Tier Action (App Restart / Container Restart)
            Recovery->>Monitor: Schedule Post-Recovery Verification
        end

        Monitor->>UI: Broadcast Live Telemetry via WebSocket (/ws)
    end
```

---

## 4. Architectural Boundaries and Security

1. **Host Isolation**: All fault injections (CPU stress, memory leakage, disk filling) execute strictly inside designated isolated demo containers. The host machine is never exposed to destructive operations.
2. **Docker Socket Access**: Only the backend Python controller communicates with `/var/run/docker.sock` via the official Docker SDK. The frontend has zero Docker socket access.
3. **Dual Operation Mode**:
   - **Live Docker Daemon**: Connects via Docker SDK when Docker Desktop is running.
   - **High-Fidelity Virtual Simulator**: Seamless fallback mode if Docker Desktop is offline, ensuring continuous system testing without crashes.
