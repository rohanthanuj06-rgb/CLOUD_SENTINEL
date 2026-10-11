from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class InfrastructureState(str, Enum):
    HEALTHY = "HEALTHY"
    GOOD = "GOOD"
    WARNING = "WARNING"
    OVERLOADED = "OVERLOADED"
    POOR = "POOR"
    CRITICAL = "CRITICAL"
    UNRESPONSIVE = "UNRESPONSIVE"
    DEAD = "DEAD"
    IDLE = "IDLE"
    ZOMBIE = "ZOMBIE"
    RECOVERING = "RECOVERING"
    RECOVERY_FAILED = "RECOVERY_FAILED"


class NodeStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    RESTARTING = "restarting"
    PAUSED = "paused"
    DEAD = "dead"
    UNKNOWN = "unknown"


class NodeModel(BaseModel):
    node_id: str = Field(..., description="Unique node identifier (e.g. node-01 or cs-node-web)")
    container_name: str = Field(..., description="Docker container name")
    container_id: Optional[str] = Field(None, description="Docker container 64-char ID")
    service_name: str = Field(..., description="Service purpose: web, api, worker, auth, storage")
    port: int = Field(..., description="Service internal/mapped port")
    status: NodeStatus = Field(default=NodeStatus.RUNNING)
    
    # Telemetry metrics
    cpu_percent: float = Field(0.0, description="Instantaneous CPU utilization percentage")
    memory_percent: float = Field(0.0, description="RAM utilization percentage")
    memory_used_mb: float = Field(0.0, description="Memory used in megabytes")
    memory_limit_mb: float = Field(1024.0, description="Container memory limit in MB")
    disk_percent: float = Field(10.0, description="Disk volume utilization percentage")
    network_rx_bytes: int = Field(0, description="Cumulative network received bytes")
    network_tx_bytes: int = Field(0, description="Cumulative network transmitted bytes")
    network_rx_rate_kb: float = Field(0.0, description="Network ingress rate in KB/s")
    network_tx_rate_kb: float = Field(0.0, description="Network egress rate in KB/s")
    response_time_ms: float = Field(0.0, description="HTTP /health probe latency in milliseconds")
    
    # Health and State Flags
    heartbeat: bool = Field(True, description="True if latest heartbeat received")
    missed_heartbeats: int = Field(0, description="Consecutive missed heartbeats")
    application_healthy: bool = Field(True, description="True if HTTP /health returns 200")
    restart_count: int = Field(0, description="Cumulative container or app restart count")
    uptime_seconds: float = Field(0.0, description="Uptime in seconds since container start")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_seen: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Intelligent Scoring
    health_score: float = Field(100.0, description="Calculated composite health score [0 - 100]")
    classification: InfrastructureState = Field(default=InfrastructureState.HEALTHY)
    
    # Dynamic active faults & diagnosis
    active_faults: List[str] = Field(default_factory=list)
    latest_diagnosis: Optional[Dict[str, Any]] = None
    is_simulated: bool = Field(False, description="True if running via high-fidelity container simulator")


class NodeSummary(BaseModel):
    total_nodes: int
    healthy: int
    good: int
    warning: int
    overloaded: int
    poor: int
    critical: int
    unresponsive: int
    dead: int
    zombie: int
    recovering: int
    recovery_failed: int
    average_health_score: float
    recovery_success_rate: float
