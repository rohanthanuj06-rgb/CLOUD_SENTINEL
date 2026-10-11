from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from app.models.recovery import RecoveryActionModel, RecoveryResult, RecoveryTier
from app.models.audit import UserRole, AuditLogEntry
from app.schemas.recovery_schemas import TriggerRecoveryRequest, ApproveRecoveryRequest, RecoverySummaryResponse
from app.firebase.local_fallback import local_store
from app.core.security import require_role, CurrentUser
from app.core.events import event_bus
from app.recovery.orchestrator import recovery_orchestrator

router = APIRouter(prefix="/api/recovery", tags=["Recovery"])


@router.get("", response_model=Dict[str, Any])
async def get_recovery_status():
    recoveries = local_store.get_all_recoveries(limit=100)
    total = len(recoveries)
    success = sum(1 for r in recoveries if r.result == RecoveryResult.SUCCESS)
    failed = sum(1 for r in recoveries if r.result == RecoveryResult.FAILED)
    escalated = sum(1 for r in recoveries if r.result == RecoveryResult.ESCALATED)
    in_progress = sum(1 for r in recoveries if r.result == RecoveryResult.IN_PROGRESS)
    requires_approval = sum(1 for r in recoveries if r.result == RecoveryResult.REQUIRES_APPROVAL)

    rate = round((success / total * 100.0), 1) if total > 0 else 100.0

    return {
        "summary": {
            "total_recoveries": total,
            "successful_recoveries": success,
            "failed_recoveries": failed,
            "escalated_recoveries": escalated,
            "in_progress_recoveries": in_progress,
            "requires_approval_count": requires_approval,
            "success_rate_percent": rate,
            "average_recovery_duration_seconds": 4.2
        },
        "recoveries": [r.model_dump() for r in recoveries]
    }


@router.get("/{recovery_id}")
async def get_recovery_detail(recovery_id: str):
    rec = local_store.get_recovery(recovery_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recovery record not found")
    return rec.model_dump()


@router.post("/trigger")
async def trigger_recovery(req: TriggerRecoveryRequest, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    node = local_store.get_node(req.node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {req.node_id} not found")

    rec = await recovery_orchestrator.initiate_self_healing(
        node_id=req.node_id,
        failure_type=req.reason or "MANUAL_OPERATOR_TRIGGER",
        confidence=1.0,
        forced_tier=req.forced_tier or RecoveryTier.TIER_2_RESTART_CONTAINER,
        operator_initiated=True
    )

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=req.node_id,
        event_type="MANUAL_RECOVERY",
        action=f"Manual recovery triggered: {rec.action_name}",
        result="IN_PROGRESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())

    return rec.model_dump()


@router.post("/{recovery_id}/approve")
async def approve_recovery(recovery_id: str, req: ApproveRecoveryRequest, user: CurrentUser = Depends(require_role(UserRole.ADMIN))):
    rec = local_store.get_recovery(recovery_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recovery not found")

    if rec.result != RecoveryResult.REQUIRES_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Recovery is in state {rec.result.value}, does not require approval")

    rec.approved_by = user.email
    if req.approved:
        rec.result = RecoveryResult.IN_PROGRESS
        import asyncio
        asyncio.create_task(recovery_orchestrator._execute_recovery_hierarchy(rec, RecoveryTier.TIER_2_RESTART_CONTAINER))
    else:
        rec.result = RecoveryResult.FAILED
        rec.steps_log.append({"step": "REJECTED", "detail": f"Rejected by admin {user.email}: {req.operator_notes}"})

    local_store.record_recovery(rec)
    return rec.model_dump()
