import httpx
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from app.schemas.fault_schemas import (
    CpuFaultRequest, MemoryFaultRequest, AppFailureRequest,
    ContainerStopRequest, NetworkFaultRequest, DiskFaultRequest, FaultResetRequest
)
from app.models.audit import UserRole, AuditLogEntry
from app.firebase.local_fallback import local_store
from app.core.security import require_role, CurrentUser
from app.core.events import event_bus
from app.monitoring.docker_monitor import docker_monitor, DEFAULT_NODES

logger = logging.getLogger("cloudsentinel.faults")
router = APIRouter(prefix="/api/faults", tags=["Fault Injection"])

VALID_NODE_IDS = {n["node_id"] for n in DEFAULT_NODES}


def validate_target_node(node_id: str):
    if node_id not in VALID_NODE_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Security constraint: Fault injection is strictly restricted to designated demo containers ({', '.join(sorted(VALID_NODE_IDS))})."
        )


async def send_fault_to_node(node_id: str, endpoint: str, payload: Dict[str, Any]):
    """Sends fault request to demo node HTTP port or applies to simulated state."""
    validate_target_node(node_id)
    node_def = next((n for n in DEFAULT_NODES if n["node_id"] == node_id), None)
    port = node_def["port"]

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(f"http://localhost:{port}{endpoint}", json=payload)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.debug(f"Direct fault injection HTTP error: {e}. Applying to simulator.")

    # Apply directly to simulator node
    sim = docker_monitor._simulated_nodes.get(node_id)
    if sim:
        if endpoint == "/fault/cpu":
            sim["active_faults"].add("CPU_STRESS")
        elif endpoint == "/fault/memory":
            sim["active_faults"].add("MEMORY_STRESS")
        elif endpoint == "/fault/app_failure":
            sim["active_faults"].add("APP_FAILURE")
        elif endpoint == "/fault/latency":
            sim["active_faults"].add("NETWORK_LATENCY")
        elif endpoint == "/fault/disk":
            sim["active_faults"].add("DISK_PRESSURE")
        elif endpoint == "/fault/reset":
            sim["active_faults"].clear()
            sim["status"] = "running"
        return {"action": f"FAULT_APPLIED_{endpoint}", "node_id": node_id, "status": "active"}

    return {"error": "Target node could not be reached"}


@router.post("/cpu")
async def inject_cpu_fault(req: CpuFaultRequest, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    validate_target_node(req.node_id)
    res = await send_fault_to_node(req.node_id, "/fault/cpu", {"duration": req.duration, "intensity": req.intensity})

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=req.node_id,
        event_type="FAULT_INJECTION",
        action=f"Injected CPU Stress ({int(req.intensity * 100)}% load for {req.duration}s)",
        result="ACTIVE",
        details=res
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())
    return {"status": "SUCCESS", "fault": "CPU_STRESS", "node_id": req.node_id, "detail": res}


@router.post("/memory")
async def inject_memory_fault(req: MemoryFaultRequest, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    validate_target_node(req.node_id)
    res = await send_fault_to_node(req.node_id, "/fault/memory", {"mb": req.mb, "duration": req.duration})

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=req.node_id,
        event_type="FAULT_INJECTION",
        action=f"Injected Memory Leak ({req.mb}MB allocation for {req.duration}s)",
        result="ACTIVE",
        details=res
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())
    return {"status": "SUCCESS", "fault": "MEMORY_STRESS", "node_id": req.node_id, "detail": res}


@router.post("/application")
async def inject_app_failure(req: AppFailureRequest, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    validate_target_node(req.node_id)
    res = await send_fault_to_node(req.node_id, "/fault/app_failure", {})

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=req.node_id,
        event_type="FAULT_INJECTION",
        action=f"Injected Application Crash (/health forced 500 error on {req.node_id})",
        result="ACTIVE",
        details=res
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())
    return {"status": "SUCCESS", "fault": "APP_FAILURE", "node_id": req.node_id, "detail": res}


@router.post("/container")
async def inject_container_stop(req: ContainerStopRequest, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    validate_target_node(req.node_id)
    res = await docker_monitor.execute_container_action(req.node_id, "stop")

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=req.node_id,
        event_type="FAULT_INJECTION",
        action=f"Stopped container {req.node_id} (simulating container crash/heartbeat drop)",
        result="ACTIVE",
        details=res
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())
    return {"status": "SUCCESS", "fault": "CONTAINER_STOP", "node_id": req.node_id, "detail": res}


@router.post("/network")
async def inject_network_fault(req: NetworkFaultRequest, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    validate_target_node(req.node_id)
    res = await send_fault_to_node(req.node_id, "/fault/latency", {"delay_ms": req.delay_ms, "duration": req.duration})

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=req.node_id,
        event_type="FAULT_INJECTION",
        action=f"Injected Network Latency (+{req.delay_ms}ms artificial delay on {req.node_id})",
        result="ACTIVE",
        details=res
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())
    return {"status": "SUCCESS", "fault": "NETWORK_LATENCY", "node_id": req.node_id, "detail": res}


@router.post("/disk")
async def inject_disk_fault(req: DiskFaultRequest, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    validate_target_node(req.node_id)
    res = await send_fault_to_node(req.node_id, "/fault/disk", {"size_mb": req.size_mb, "duration": req.duration})

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=req.node_id,
        event_type="FAULT_INJECTION",
        action=f"Injected Disk Pressure ({req.size_mb}MB buffer write on {req.node_id})",
        result="ACTIVE",
        details=res
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())
    return {"status": "SUCCESS", "fault": "DISK_PRESSURE", "node_id": req.node_id, "detail": res}


@router.post("/reset")
async def reset_faults(req: FaultResetRequest, user: CurrentUser = Depends(require_role(UserRole.OPERATOR))):
    target_nodes = [req.node_id] if req.node_id else list(VALID_NODE_IDS)
    results = {}
    for nid in target_nodes:
        # Reset faults on node
        res = await send_fault_to_node(nid, "/fault/reset", {})
        # Ensure container is running
        await docker_monitor.execute_container_action(nid, "start")
        results[nid] = res

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node=req.node_id or "ALL_NODES",
        event_type="FAULT_RESET",
        action=f"Reset all active faults for {req.node_id or 'all infrastructure nodes'}",
        result="SUCCESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())

    return {"status": "SUCCESS", "message": "All faults reset successfully", "results": results}
