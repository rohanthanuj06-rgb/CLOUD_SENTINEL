import pytest
from app.models.metric import MetricTimeseriesPoint
from app.prediction.trend_analyzer import TrendAnalyzer
from app.prediction.anomaly_detector import AnomalyDetector


def test_trend_analyzer_detects_cpu_slope():
    analyzer = TrendAnalyzer()
    # Construct rising trend: 40, 43, 46... 85%
    metrics = []
    for i in range(20):
        metrics.append(MetricTimeseriesPoint(
            timestamp=f"2026-10-08T09:{i:02d}:00Z",
            cpu=40.0 + (i * 2.5),
            memory=30.0,
            disk=20.0,
            network_rx_kb=10.0,
            network_tx_kb=5.0,
            response_time=50.0,
            health_score=85.0 - (i * 2.0)
        ))

    pred = analyzer.predict_degradation("cs-node-web", metrics, 50.0)
    assert pred["cpu_trend_slope"] > 0
    assert pred["failure_probability"] > 0.40
    assert pred["time_to_cpu_breach_min"] is not None


def test_anomaly_detector_identifies_outlier():
    detector = AnomalyDetector()
    metrics = []
    # 20 normal samples
    for i in range(20):
        metrics.append(MetricTimeseriesPoint(
            timestamp=f"2026-10-08T09:{i:02d}:00Z",
            cpu=20.0 + (i % 3),
            memory=30.0,
            disk=20.0,
            network_rx_kb=10.0,
            network_tx_kb=5.0,
            response_time=40.0,
            health_score=95.0
        ))
    # Spike outlier sample
    metrics.append(MetricTimeseriesPoint(
        timestamp="2026-10-08T09:21:00Z",
        cpu=99.0,
        memory=98.0,
        disk=20.0,
        network_rx_kb=1000.0,
        network_tx_kb=500.0,
        response_time=2500.0,
        health_score=20.0
    ))

    result = detector.analyze_node_metrics("cs-node-web", metrics)
    assert result["is_anomaly"] is True
    assert len(result["anomalous_features"]) > 0
