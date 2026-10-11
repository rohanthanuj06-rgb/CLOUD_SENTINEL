import pytest
from app.monitoring.health_scoring import HealthScoreEngine


def test_perfect_health_score():
    engine = HealthScoreEngine()
    result = engine.calculate(
        cpu_percent=15.0,
        memory_percent=30.0,
        network_rx_rate_kb=100.0,
        response_time_ms=50.0,
        heartbeat=True,
        application_healthy=True,
        container_running=True
    )
    assert result["health_score"] >= 90.0
    assert result["cpu_score"] >= 90.0
    assert result["heartbeat_score"] == 100.0
    assert result["application_score"] == 100.0


def test_container_down_zero_score():
    engine = HealthScoreEngine()
    result = engine.calculate(
        cpu_percent=0.0,
        memory_percent=0.0,
        network_rx_rate_kb=0.0,
        response_time_ms=3000.0,
        heartbeat=False,
        application_healthy=False,
        container_running=False
    )
    assert result["health_score"] == 0.0


def test_cpu_overload_degrades_score():
    engine = HealthScoreEngine()
    result = engine.calculate(
        cpu_percent=98.0,
        memory_percent=40.0,
        network_rx_rate_kb=50.0,
        response_time_ms=800.0,
        heartbeat=True,
        application_healthy=True,
        container_running=True
    )
    assert result["health_score"] < 78.0
    assert result["cpu_score"] < 15.0


def test_custom_weights_normalization():
    engine = HealthScoreEngine()
    engine.update_weights(w_cpu=0.50, w_ram=0.50, w_net=0.0, w_res=0.0, w_hb=0.0, w_app=0.0)
    assert abs((engine.w_cpu + engine.w_ram) - 1.0) < 0.01
