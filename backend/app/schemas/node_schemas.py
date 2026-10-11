from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.node import NodeModel, NodeSummary, InfrastructureState


class NodeUpdateWeightRequest(BaseModel):
    weight_cpu: Optional[float] = None
    weight_ram: Optional[float] = None
    weight_network: Optional[float] = None
    weight_response_time: Optional[float] = None
    weight_heartbeat: Optional[float] = None
    weight_application: Optional[float] = None


class ThresholdUpdateRequest(BaseModel):
    cpu_warning: Optional[float] = None
    cpu_critical: Optional[float] = None
    ram_warning: Optional[float] = None
    ram_critical: Optional[float] = None
    response_warning_ms: Optional[float] = None
    response_critical_ms: Optional[float] = None
    idle_threshold: Optional[float] = None
    idle_duration: Optional[float] = None


class NodeManualActionRequest(BaseModel):
    action: str = Field(..., description="restart, recreate, health_check, failover")
    reason: Optional[str] = "Manual operator dispatch"


class SystemStatusResponse(BaseModel):
    app_name: str
    version: str
    status: str
    uptime_seconds: float
    docker_connected: bool
    docker_engine_mode: str
    firebase_connected: bool
    demo_mode: bool
    monitored_nodes_count: int
    active_alerts_count: int
    active_recoveries_count: int
    auto_recovery_enabled: bool
