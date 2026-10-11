from fastapi import APIRouter
from typing import Dict, Any, List
from app.firebase.local_fallback import local_store
from app.prediction.anomaly_detector import anomaly_detector
from app.prediction.trend_analyzer import trend_analyzer

router = APIRouter(prefix="/api/predictions", tags=["Predictions & ML Analytics"])


@router.get("", response_model=List[Dict[str, Any]])
async def get_all_predictions():
    nodes = local_store.get_all_nodes()
    results = []

    for node in nodes:
        metrics = local_store.get_node_metrics(node.node_id, limit=40)
        
        # 1. Anomaly Detection via Isolation Forest & Z-scores
        anomaly_res = anomaly_detector.analyze_node_metrics(node.node_id, metrics)
        
        # 2. Linear Regression Trend Forecasting
        trend_res = trend_analyzer.predict_degradation(node.node_id, metrics, node.health_score)

        combined = {
            "node_id": node.node_id,
            "container_name": node.container_name,
            "service_name": node.service_name,
            "current_health_score": node.health_score,
            "classification": node.classification.value,
            "anomaly": anomaly_res,
            "trend": trend_res,
            "overall_risk_score": round(max(trend_res["failure_probability"], anomaly_res["anomaly_score"]) * 100, 1)
        }
        local_store.set_prediction(node.node_id, combined)
        results.append(combined)

    return results
