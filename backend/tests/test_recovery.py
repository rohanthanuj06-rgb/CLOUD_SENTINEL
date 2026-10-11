import pytest
import asyncio
from app.recovery.orchestrator import RecoveryOrchestrator
from app.models.recovery import RecoveryTier, RecoveryResult
from app.firebase.local_fallback import local_store
from app.models.node import NodeModel, NodeStatus


@pytest.mark.asyncio
async def test_low_confidence_requires_approval():
    orchestrator = RecoveryOrchestrator()
    node = NodeModel(
        node_id="test-approval-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.RUNNING
    )
    local_store.register_node(node)

    # Trigger with low confidence (0.42 < 0.50 threshold)
    rec = await orchestrator.initiate_self_healing(
        node_id="test-approval-node",
        failure_type="UNKNOWN_ANOMALY",
        confidence=0.42,
        operator_initiated=False
    )

    assert rec.result == RecoveryResult.REQUIRES_APPROVAL
    assert rec.action_tier == RecoveryTier.TIER_5_ESCALATE_ADMIN


@pytest.mark.asyncio
async def test_high_confidence_auto_recovery():
    orchestrator = RecoveryOrchestrator()
    node = NodeModel(
        node_id="test-auto-node",
        container_name="cs-test",
        service_name="web",
        port=8001,
        status=NodeStatus.RUNNING,
        application_healthy=False
    )
    local_store.register_node(node)

    rec = await orchestrator.initiate_self_healing(
        node_id="test-auto-node",
        failure_type="APPLICATION_FAILURE",
        confidence=0.95,
        operator_initiated=False
    )

    assert rec is not None
    assert rec.action_tier == RecoveryTier.TIER_1_RESTART_APPLICATION
    # Allow background execution
    await asyncio.sleep(0.5)
    rec_updated = local_store.get_recovery(rec.recovery_id)
    assert rec_updated is not None
