import numpy as np
import logging
from typing import Dict, Any, List
from sklearn.ensemble import IsolationForest
from app.models.metric import MetricTimeseriesPoint

logger = logging.getLogger("cloudsentinel.anomaly_detector")


class AnomalyDetector:
    """
    Detects multivariate metric anomalies across CPU, RAM, Latency, and Network
    using Scikit-Learn IsolationForest and rolling Z-score baselines.
    """
    def analyze_node_metrics(self, node_id: str, metrics: List[MetricTimeseriesPoint]) -> Dict[str, Any]:
        if len(metrics) < 10:
            return {
                "node_id": node_id,
                "is_anomaly": False,
                "anomaly_score": 0.05,
                "severity": "NORMAL",
                "anomalous_features": [],
                "reason": "Insufficient historical metrics for baseline (< 10 samples)."
            }

        # Extract feature vectors: [CPU, RAM, ResponseTime, NetworkRx]
        X = np.array([[m.cpu, m.memory, m.response_time, m.network_rx_kb] for m in metrics])
        current_sample = X[-1].reshape(1, -1)

        # Statistical baseline (mean & std)
        means = np.mean(X, axis=0)
        stds = np.std(X, axis=0)
        stds[stds == 0] = 1.0  # Avoid division by zero

        z_scores = np.abs((current_sample[0] - means) / stds)
        feature_names = ["CPU Utilization", "Memory Usage", "Response Latency", "Network Traffic"]

        anomalous_features = []
        for i, z in enumerate(z_scores):
            if z > 2.5:
                anomalous_features.append({
                    "feature": feature_names[i],
                    "z_score": round(float(z), 2),
                    "current_val": round(float(current_sample[0][i]), 2),
                    "baseline_mean": round(float(means[i]), 2)
                })

        # Isolation Forest Anomaly Score
        anomaly_score = 0.1
        try:
            iso_forest = IsolationForest(contamination=0.1, random_state=42, n_estimators=50)
            iso_forest.fit(X)
            # decision_function gives negative for anomalies, positive for normal
            raw_score = iso_forest.decision_function(current_sample)[0]
            # Normalize to 0 (normal) to 1 (highly anomalous)
            anomaly_score = round(float(np.clip(0.5 - raw_score, 0.0, 1.0)), 3)
        except Exception as e:
            logger.debug(f"IsolationForest evaluation fallback: {e}")

        is_anomaly = anomaly_score > 0.65 or len(anomalous_features) > 0

        return {
            "node_id": node_id,
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "severity": "CRITICAL" if anomaly_score > 0.85 else ("WARNING" if is_anomaly else "NORMAL"),
            "anomalous_features": anomalous_features,
            "baseline_samples": len(metrics)
        }


anomaly_detector = AnomalyDetector()
