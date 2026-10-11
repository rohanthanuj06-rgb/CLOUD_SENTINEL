from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
from app.models.alert import AlertModel, AlertStatus
from app.models.audit import UserRole, AuditLogEntry
from app.firebase.local_fallback import local_store
from app.core.security import require_role, CurrentUser
from app.core.events import event_bus

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertModel])
async def list_alerts(status: Optional[str] = Query(None)):
    status_filter = None
    if status:
        try:
            status_filter = AlertStatus(status.upper())
        except ValueError:
            pass
    return local_store.get_alerts(status=status_filter)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    alerts = local_store.alerts
    alert = alerts.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = AlertStatus.ACKNOWLEDGED
    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=alert.node_id,
        event_type="ALERT_ACKNOWLEDGED",
        action=f"Acknowledged alert {alert_id} ({alert.alert_type})",
        result="SUCCESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("alert_updated", alert.model_dump())
    return alert


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    alert = local_store.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=alert.node_id,
        event_type="ALERT_RESOLVED",
        action=f"Manually resolved alert {alert_id} ({alert.alert_type})",
        result="SUCCESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("alert_updated", alert.model_dump())
    return alert
