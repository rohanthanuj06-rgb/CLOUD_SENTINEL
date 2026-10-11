from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    ACKNOWLEDGED = "ACKNOWLEDGED"


class AlertModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    node_id: str
    container_name: str
    alert_type: str = Field(..., description="CPU_OVERLOAD, MEMORY_EXHAUSTION, HEARTBEAT_LOST, APPLICATION_FAILURE, DISK_PRESSURE, ZOMBIE_WORKLOAD, PREDICTION_WARNING, ANOMALY_DETECTED, RECOVERY_FAILED")
    severity: AlertSeverity
    status: AlertStatus = Field(default=AlertStatus.ACTIVE)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: Optional[str] = None
    title: str
    description: str
    evidence: List[str] = Field(default_factory=list)
    recommended_action: str
    recovery_id: Optional[str] = None
