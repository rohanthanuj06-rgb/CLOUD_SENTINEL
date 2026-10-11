from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.recovery import RecoveryActionModel, RecoveryTier, RecoveryResult


class TriggerRecoveryRequest(BaseModel):
    node_id: str
    forced_tier: Optional[RecoveryTier] = None
    reason: Optional[str] = "Manual operator intervention"


class ApproveRecoveryRequest(BaseModel):
    recovery_id: str
    approved: bool = True
    operator_notes: Optional[str] = None


class RecoverySummaryResponse(BaseModel):
    total_recoveries: int
    successful_recoveries: int
    failed_recoveries: int
    escalated_recoveries: int
    success_rate_percent: float
    average_recovery_duration_seconds: float
    recent_recoveries: List[RecoveryActionModel]
