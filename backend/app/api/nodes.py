from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from app.models.node import NodeModel, NodeSummary, InfrastructureState
from app.models.audit import UserRole, AuditLogEntry
from app.firebase.local_fallback import local_store
from app.monitoring.docker_monitor import docker_monitor, DEFAULT_NODES
from app.core.security import require_role, CurrentUser
from app.core.events import event_bus
from app.recovery.orchestrator import recovery_orchestrator
from app.models.recovery import RecoveryTier

router = APIRouter(prefix="/api/nodes", tags=["Nodes"])


@router.get("", response_model=Dict[str, Any])
async def get_nodes():
    nodes = local_store.get_all_nodes()
    
    # Calculate aggregate summary counts
    summary = {
        "total_nodes": len(nodes),
        "healthy": sum(1 for n in nodes if n.classification == InfrastructureState.HEALTHY),
        "good": sum(1 for n in nodes if n.classification == InfrastructureState.GOOD),
        "warning": sum(1 for n in nodes if n.classification == InfrastructureState.WARNING),
        "overloaded": sum(1 for n in nodes if n.classification == InfrastructureState.OVERLOADED),
        "poor": sum(1 for n in nodes if n.classification == InfrastructureState.POOR),
        "critical": sum(1 for n in nodes if n.classification == InfrastructureState.CRITICAL),
        "unresponsive": sum(1 for n in nodes if n.classification == InfrastructureState.UNRESPONSIVE),
        "dead": sum(1 for n in nodes if n.classification == InfrastructureState.DEAD),
        "idle": sum(1 for n in nodes if n.classification == InfrastructureState.IDLE),
        "zombie": sum(1 for n in nodes if n.classification == InfrastructureState.ZOMBIE),
        "recovering": sum(1 for n in nodes if n.classification == InfrastructureState.RECOVERING),
        "recovery_failed": sum(1 for n in nodes if n.classification == InfrastructureState.RECOVERY_FAILED),
        "average_health_score": round(sum(n.health_score for n in nodes) / len(nodes), 1) if nodes else 100.0,
    }

    # Calculate recovery success rate
    recoveries = local_store.get_all_recoveries(limit=100)
    total_rec = len(recoveries)
    success_rec = sum(1 for r in recoveries if r.result.value == "SUCCESS")
    summary["recovery_success_rate"] = round((success_rec / total_rec * 100.0), 1) if total_rec > 0 else 100.0

    return {
        "summary": summary,
        "nodes": [n.model_dump() for n in nodes]
    }


@router.get("/{node_id}")
async def get_node_detail(node_id: str):
    node = local_store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    metrics = local_store.get_node_metrics(node_id, limit=60)
    alerts = [a.model_dump() for a in local_store.get_alerts() if a.node_id == node_id]
    recoveries = [r.model_dump() for r in local_store.get_all_recoveries() if r.node_id == node_id]
    logs = await docker_monitor.get_container_logs(node_id, tail=40)

    return {
        "node": node.model_dump(),
        "recent_metrics": [m.model_dump() for m in metrics],
        "alerts": alerts,
        "recoveries": recoveries,
        "logs": logs
    }


@router.get("/{node_id}/metrics")
async def get_node_metrics_timeseries(node_id: str, range: str = Query("15m")):
    node = local_store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    limits = {
        "5m": 50,
        "15m": 150,
        "1h": 300,
        "6h": 500,
        "24h": 500
    }
    limit = limits.get(range, 150)
    metrics = local_store.get_node_metrics(node_id, limit=limit)
    return {
        "node_id": node_id,
        "range": range,
        "datapoints_count": len(metrics),
        "metrics": [m.model_dump() for m in metrics]
    }


@router.get("/{node_id}/logs")
async def get_node_logs(node_id: str, tail: int = Query(50)):
    logs = await docker_monitor.get_container_logs(node_id, tail=tail)
    return {"node_id": node_id, "tail": tail, "logs": logs}


@router.post("/{node_id}/restart")
async def restart_node(node_id: str, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    node = local_store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    # Trigger recovery orchestrator with forced Tier 2 container restart
    rec = await recovery_orchestrator.initiate_self_healing(
        node_id=node_id,
        failure_type="MANUAL_OPERATOR_RESTART",
        confidence=1.0,
        forced_tier=RecoveryTier.TIER_2_RESTART_CONTAINER,
        operator_initiated=True
    )

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=node_id,
        event_type="MANUAL_RECOVERY",
        action=f"Operator manually triggered container restart for {node_id}",
        result="IN_PROGRESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())

    return {"message": "Restart command dispatched", "recovery_id": rec.recovery_id if rec else None}


@router.post("/{node_id}/recreate")
async def recreate_node(node_id: str, user: CurrentUser = Depends(require_role(UserRole.ADMIN))):
    node = local_store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    rec = await recovery_orchestrator.initiate_self_healing(
        node_id=node_id,
        failure_type="MANUAL_OPERATOR_RECREATE",
        confidence=1.0,
        forced_tier=RecoveryTier.TIER_3_RECREATE_CONTAINER,
        operator_initiated=True
    )

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=node_id,
        event_type="MANUAL_RECOVERY",
        action=f"Administrator manually triggered container recreate for {node_id}",
        result="IN_PROGRESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())

    return {"message": "Recreate container dispatched", "recovery_id": rec.recovery_id if rec else None}


@router.post("/{node_id}/scale")
async def scale_node(node_id: str, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    """Simulates scale-out / failover of overloaded workload."""
    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=node_id,
        event_type="SCALE_WORKLOAD",
        action=f"Workload scale-out triggered: provisioned replica standby for {node_id}",
        result="SUCCESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())

    return {
        "status": "SCALED",
        "node_id": node_id,
        "message": f"Simulated workload scale-out dispatched for {node_id}. Replicas active."
    }
