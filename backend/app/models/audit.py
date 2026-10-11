from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class AuditLogEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"aud-{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    actor: str = Field(..., description="SYSTEM (automated) or user email / ID")
    role: UserRole = Field(default=UserRole.ADMIN)
    target_node: Optional[str] = None
    event_type: str = Field(..., description="FAULT_INJECTION, SELF_HEALING, RECOVERY_VERIFIED, MANUAL_RECOVERY, SYSTEM_CONFIG, ALERT_RESOLVED")
    action: str = Field(..., description="Human-readable description of executed action")
    result: str = Field("SUCCESS", description="SUCCESS, FAILED, WARNING, PENDING")
    details: Dict[str, Any] = Field(default_factory=dict)
