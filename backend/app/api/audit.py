from fastapi import APIRouter, Query
from typing import List, Optional
from app.models.audit import AuditLogEntry
from app.firebase.local_fallback import local_store

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogEntry])
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    node_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None)
):
    logs = local_store.get_audit_logs(limit=limit)
    if node_id:
        logs = [l for l in logs if l.target_node == node_id]
    if event_type:
        logs = [l for l in logs if l.event_type == event_type]
    return logs
