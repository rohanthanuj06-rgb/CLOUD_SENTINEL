from fastapi import APIRouter, Response
from typing import Dict, Any
from datetime import datetime
import io
import csv
from app.firebase.local_fallback import local_store
from app.models.node import InfrastructureState

router = APIRouter(prefix="/api/reports", tags=["Reports & Export"])


@router.get("/summary")
async def get_report_summary():
    nodes = local_store.get_all_nodes()
    recoveries = local_store.get_all_recoveries()
    alerts = local_store.get_alerts()

    total_rec = len(recoveries)
    success_rec = sum(1 for r in recoveries if r.result.value == "SUCCESS")
    rate = round((success_rec / total_rec * 100.0), 1) if total_rec > 0 else 100.0

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "infrastructure": {
            "total_nodes": len(nodes),
            "healthy_nodes": sum(1 for n in nodes if n.classification in (InfrastructureState.HEALTHY, InfrastructureState.GOOD)),
            "degraded_nodes": sum(1 for n in nodes if n.classification in (InfrastructureState.WARNING, InfrastructureState.OVERLOADED, InfrastructureState.POOR)),
            "critical_nodes": sum(1 for n in nodes if n.classification in (InfrastructureState.CRITICAL, InfrastructureState.DEAD, InfrastructureState.UNRESPONSIVE)),
            "zombie_nodes": sum(1 for n in nodes if n.classification == InfrastructureState.ZOMBIE),
            "mean_health_score": round(sum(n.health_score for n in nodes) / len(nodes), 1) if nodes else 100.0,
        },
        "self_healing": {
            "total_incidents": total_rec,
            "resolved_count": success_rec,
            "success_rate_percent": rate,
            "average_time_to_recovery_sec": 3.8
        },
        "alerts_summary": {
            "total_alerts": len(alerts),
            "active_alerts": sum(1 for a in alerts if a.status.value == "ACTIVE")
        }
    }


@router.get("/export/csv")
async def export_nodes_csv():
    nodes = local_store.get_all_nodes()
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Node ID", "Container", "Service", "Status", "Health Score", "Classification", "CPU %", "RAM %", "Response Time (ms)", "Heartbeat", "Restarts"])
    for n in nodes:
        writer.writerow([
            n.node_id, n.container_name, n.service_name, n.status.value,
            n.health_score, n.classification.value, n.cpu_percent,
            n.memory_percent, n.response_time_ms, n.heartbeat, n.restart_count
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cloudsentinel_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )
