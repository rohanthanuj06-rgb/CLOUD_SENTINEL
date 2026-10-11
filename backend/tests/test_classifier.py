import pytest
from app.models.node import NodeModel, NodeStatus, InfrastructureState
from app.diagnostics.classifier import StateClassifier


def test_classify_healthy():
    classifier = StateClassifier()
    node = NodeModel(
        node_id="test-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.RUNNING,
        cpu_percent=25.0,
        memory_percent=35.0,
        health_score=92.0,
        heartbeat=True,
        application_healthy=True
    )
    assert classifier.classify(node) == InfrastructureState.HEALTHY


def test_classify_dead():
    classifier = StateClassifier()
    node = NodeModel(
        node_id="test-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.STOPPED,
        health_score=0.0
    )
    assert classifier.classify(node) == InfrastructureState.DEAD


def test_classify_unresponsive():
    classifier = StateClassifier()
    node = NodeModel(
        node_id="test-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.RUNNING,
        heartbeat=False,
        missed_heartbeats=5,
        health_score=20.0
    )
    assert classifier.classify(node) == InfrastructureState.UNRESPONSIVE


def test_classify_overloaded():
    classifier = StateClassifier()
    node = NodeModel(
        node_id="test-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.RUNNING,
        cpu_percent=96.0,
        health_score=45.0,
        heartbeat=True,
        application_healthy=True
    )
    assert classifier.classify(node) == InfrastructureState.OVERLOADED


def test_classify_zombie():
    classifier = StateClassifier()
    node = NodeModel(
        node_id="test-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.RUNNING,
        cpu_percent=1.2,
        network_rx_rate_kb=0.1,
        uptime_seconds=300.0,
        health_score=90.0,
        heartbeat=True,
        application_healthy=True
    )
    assert classifier.classify(node) == InfrastructureState.ZOMBIE
