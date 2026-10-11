from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.firebase.local_fallback import local_store
from app.diagnostics.rule_engine import diagnostic_engine

router = APIRouter(prefix="/api/diagnostics", tags=["Diagnostics"])


@router.get("", response_model=List[Dict[str, Any]])
async def get_all_diagnostics():
    nodes = local_store.get_all_nodes()
    reports = []
    for node in nodes:
        diag = diagnostic_engine.diagnose(node)
        reports.append({
            "node_id": node.node_id,
            "container_name": node.container_name,
            "service_name": node.service_name,
            "health_score": node.health_score,
            "classification": node.classification.value,
            "diagnosis": diag if diag else {
                "cause": "HEALTHY_NORMAL",
                "confidence": 0.98,
                "severity": "INFO",
                "evidence": ["All multi-metric parameters within optimal range"],
                "recommended_action": "NO_ACTION_REQUIRED",
                "summary": "Node operating under normal cloud operational baseline."
            }
        })
    return reports


@router.get("/{node_id}")
async def get_node_diagnostic(node_id: str):
    node = local_store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    diag = diagnostic_engine.diagnose(node)
    return {
        "node_id": node.node_id,
        "container_name": node.container_name,
        "health_score": node.health_score,
        "classification": node.classification.value,
        "diagnosis": diag
    }
