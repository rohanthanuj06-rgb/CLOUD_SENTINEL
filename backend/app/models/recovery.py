from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class RecoveryTier(str, Enum):
    TIER_1_RESTART_APPLICATION = "RESTART_APPLICATION"
    TIER_2_RESTART_CONTAINER = "RESTART_CONTAINER"
    TIER_3_RECREATE_CONTAINER = "RECREATE_CONTAINER"
    TIER_4_FAILOVER_WORKLOAD = "FAILOVER_WORKLOAD"
    TIER_5_ESCALATE_ADMIN = "ESCALATE_TO_ADMINISTRATOR"


class RecoveryResult(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


class RecoveryActionModel(BaseModel):
    recovery_id: str = Field(default_factory=lambda: f"rec-{uuid.uuid4().hex[:8]}")
    node_id: str
    container_name: str
    failure_type: str = Field(..., description="Root cause diagnosed (e.g. APPLICATION_FAILURE, CPU_OVERLOAD)")
    action_tier: RecoveryTier
    action_name: str
    confidence_score: float = Field(..., description="Calculated recovery confidence between 0.0 and 1.0")
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    result: RecoveryResult = Field(default=RecoveryResult.IN_PROGRESS)
    
    # Pre & post recovery health metrics
    health_before: float
    status_before: str
    health_after: Optional[float] = None
    status_after: Optional[str] = None
    
    # Step-by-step audit verification log
    steps_log: List[Dict[str, Any]] = Field(default_factory=list)
    verification_passed: Optional[bool] = None
    error_message: Optional[str] = None
    approved_by: Optional[str] = None
