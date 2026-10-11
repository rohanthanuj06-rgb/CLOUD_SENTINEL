import time
from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.config import settings
from app.schemas.node_schemas import SystemStatusResponse, ThresholdUpdateRequest, NodeUpdateWeightRequest
from app.monitoring.docker_monitor import docker_monitor
from app.monitoring.health_scoring import health_score_engine
from app.firebase.firebase_service import firebase_service
from app.firebase.local_fallback import local_store
from app.core.security import require_role, CurrentUser
from app.models.audit import UserRole, AuditLogEntry
from app.core.events import event_bus

router = APIRouter(prefix="/api/system", tags=["System Controller"])
START_TIME = time.time()


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    nodes = local_store.get_all_nodes()
    alerts = local_store.get_alerts()
    recoveries = local_store.get_all_recoveries()

    return SystemStatusResponse(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="OPERATIONAL",
        uptime_seconds=round(time.time() - START_TIME, 1),
        docker_connected=docker_monitor.is_docker_available,
        docker_engine_mode="Live Docker Daemon" if docker_monitor.is_docker_available else "High-Fidelity Virtual Simulator",
        firebase_connected=firebase_service.is_connected,
        demo_mode=settings.DEMO_MODE,
        monitored_nodes_count=len(nodes),
        active_alerts_count=sum(1 for a in alerts if a.status.value == "ACTIVE"),
        active_recoveries_count=sum(1 for r in recoveries if r.result.value == "IN_PROGRESS"),
        auto_recovery_enabled=settings.AUTO_RECOVERY_ENABLED
    )


@router.get("/config")
async def get_system_config():
    return {
        "weights": {
            "cpu": health_score_engine.w_cpu,
            "ram": health_score_engine.w_ram,
            "network": health_score_engine.w_net,
            "response_time": health_score_engine.w_res,
            "heartbeat": health_score_engine.w_hb,
            "application": health_score_engine.w_app,
        },
        "thresholds": {
            "cpu_warning": settings.CPU_WARNING_THRESHOLD,
            "cpu_critical": settings.CPU_CRITICAL_THRESHOLD,
            "ram_warning": settings.MEMORY_WARNING_THRESHOLD,
            "ram_critical": settings.MEMORY_CRITICAL_THRESHOLD,
            "response_warning_ms": settings.RESPONSE_TIME_WARNING_MS,
            "response_critical_ms": settings.RESPONSE_TIME_CRITICAL_MS,
            "idle_threshold": settings.IDLE_CPU_THRESHOLD,
            "idle_duration": settings.IDLE_DURATION_SECONDS,
        },
        "auto_recovery_enabled": settings.AUTO_RECOVERY_ENABLED,
        "health_interval": settings.HEALTH_INTERVAL,
    }


@router.post("/config/weights")
async def update_weights(req: NodeUpdateWeightRequest, user: CurrentUser = Depends(require_role(UserRole.ADMIN))):
    health_score_engine.update_weights(
        w_cpu=req.weight_cpu,
        w_ram=req.weight_ram,
        w_net=req.weight_network,
        w_res=req.weight_response_time,
        w_hb=req.weight_heartbeat,
        w_app=req.weight_application
    )

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node="SYSTEM",
        event_type="SYSTEM_CONFIG",
        action="Updated multi-factor health scoring weights",
        result="SUCCESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())

    return {"message": "Health scoring weights updated", "new_weights": await get_system_config()}


@router.post("/config/thresholds")
async def update_thresholds(req: ThresholdUpdateRequest, user: CurrentUser = Depends(require_role(UserRole.ADMIN))):
    if req.cpu_warning is not None: settings.CPU_WARNING_THRESHOLD = req.cpu_warning
    if req.cpu_critical is not None: settings.CPU_CRITICAL_THRESHOLD = req.cpu_critical
    if req.ram_warning is not None: settings.MEMORY_WARNING_THRESHOLD = req.ram_warning
    if req.ram_critical is not None: settings.MEMORY_CRITICAL_THRESHOLD = req.ram_critical
    if req.response_warning_ms is not None: settings.RESPONSE_TIME_WARNING_MS = req.response_warning_ms
    if req.response_critical_ms is not None: settings.RESPONSE_TIME_CRITICAL_MS = req.response_critical_ms
    if req.idle_threshold is not None: settings.IDLE_CPU_THRESHOLD = req.idle_threshold
    if req.idle_duration is not None: settings.IDLE_DURATION_SECONDS = req.idle_duration

    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node="SYSTEM",
        event_type="SYSTEM_CONFIG",
        action="Updated health classification thresholds",
        result="SUCCESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())

    return {"message": "Thresholds updated", "new_thresholds": await get_system_config()}


@router.post("/config/auto-recovery/toggle")
async def toggle_auto_recovery(enabled: bool, user: CurrentUser = Depends(require_role(UserRole.ADMIN))):
    settings.AUTO_RECOVERY_ENABLED = enabled
    audit = AuditLogEntry(
        actor=user.email,
        role=user.role,
        target_node="SYSTEM",
        event_type="SYSTEM_CONFIG",
        action=f"Auto-recovery self-healing toggled to {enabled}",
        result="SUCCESS"
    )
    local_store.add_audit_log(audit)
    await event_bus.publish("audit_logged", audit.model_dump())
    return {"auto_recovery_enabled": settings.AUTO_RECOVERY_ENABLED}
