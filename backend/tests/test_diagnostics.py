import pytest
from app.models.node import NodeModel, NodeStatus
from app.diagnostics.rule_engine import DiagnosticEngine


def test_diagnose_application_failure():
    engine = DiagnosticEngine()
    node = NodeModel(
        node_id="test-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.RUNNING,
        application_healthy=False,
        heartbeat=True,
        health_score=40.0
    )
    diag = engine.diagnose(node)
    assert diag is not None
    assert diag["cause"] == "APPLICATION_FAILURE"
    assert diag["confidence"] >= 0.90
    assert diag["recommended_action"] == "RESTART_APPLICATION"


def test_diagnose_memory_exhaustion():
    engine = DiagnosticEngine()
    node = NodeModel(
        node_id="test-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.RUNNING,
        memory_percent=94.5,
        response_time_ms=850.0,
        application_healthy=True,
        heartbeat=True,
        health_score=35.0
    )
    diag = engine.diagnose(node)
    assert diag is not None
    assert diag["cause"] == "MEMORY_EXHAUSTION"
    assert "Memory utilization at 94.5%" in diag["evidence"][0]


def test_diagnose_container_stopped():
    engine = DiagnosticEngine()
    node = NodeModel(
        node_id="test-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.STOPPED,
        application_healthy=False,
        heartbeat=False,
        health_score=0.0
    )
    diag = engine.diagnose(node)
    assert diag is not None
    assert diag["cause"] == "CONTAINER_STOPPED"
    assert diag["confidence"] >= 0.98
