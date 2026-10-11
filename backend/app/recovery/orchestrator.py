import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.models.recovery import RecoveryActionModel, RecoveryTier, RecoveryResult
from app.models.audit import AuditLogEntry, UserRole
from app.models.alert import AlertModel, AlertSeverity
from app.recovery.actions import RecoveryActions
from app.recovery.verifier import recovery_verifier
from app.firebase.local_fallback import local_store
from app.core.events import event_bus
from app.config import settings

logger = logging.getLogger("cloudsentinel.recovery_orchestrator")


class RecoveryOrchestrator:
    def __init__(self):
        self._in_progress_nodes = set()

    async def initiate_self_healing(
        self,
        node_id: str,
        failure_type: str,
        confidence: float,
        forced_tier: Optional[RecoveryTier] = None,
        operator_initiated: bool = False
    ) -> RecoveryActionModel:
        """
        Coordinates intelligent hierarchical recovery:
        Tier 1 (App Restart) -> Tier 2 (Container Restart) -> Tier 3 (Recreate) -> Tier 4 (Failover) -> Tier 5 (Escalate)
        """
        if node_id in self._in_progress_nodes and not operator_initiated:
            logger.info(f"Recovery already active for node {node_id}. Skipping redundant dispatch.")
            return

        self._in_progress_nodes.add(node_id)
        current_node = local_store.get_node(node_id)
        health_before = current_node.health_score if current_node else 20.0
        status_before = current_node.classification.value if current_node else "CRITICAL"

        # Check Confidence Gate
        if not operator_initiated and confidence < settings.MEDIUM_CONFIDENCE_THRESHOLD:
            # Low confidence: Suspend and require manual administrator approval
            rec_action = RecoveryActionModel(
                node_id=node_id,
                container_name=current_node.container_name if current_node else node_id,
                failure_type=failure_type,
                action_tier=RecoveryTier.TIER_5_ESCALATE_ADMIN,
                action_name="REQUIRE_APPROVAL",
                confidence_score=round(confidence, 2),
                result=RecoveryResult.REQUIRES_APPROVAL,
                health_before=health_before,
                status_before=status_before,
                steps_log=[{"step": "CONFIDENCE_GATE", "detail": f"Confidence {confidence:.2f} below threshold. Operator approval required."}]
            )
            local_store.record_recovery(rec_action)
            self._in_progress_nodes.discard(node_id)
            return rec_action

        # Determine starting tier based on failure type or forced parameter
        start_tier = forced_tier
        if not start_tier:
            if failure_type == "APPLICATION_FAILURE":
                start_tier = RecoveryTier.TIER_1_RESTART_APPLICATION
            elif failure_type in ("CONTAINER_STOPPED", "CONTAINER_NETWORK_FAILURE", "MEMORY_EXHAUSTION"):
                start_tier = RecoveryTier.TIER_2_RESTART_CONTAINER
            else:
                start_tier = RecoveryTier.TIER_2_RESTART_CONTAINER

        rec_action = RecoveryActionModel(
            node_id=node_id,
            container_name=current_node.container_name if current_node else node_id,
            failure_type=failure_type,
            action_tier=start_tier,
            action_name=start_tier.value,
            confidence_score=round(confidence, 2),
            result=RecoveryResult.IN_PROGRESS,
            health_before=health_before,
            status_before=status_before,
            steps_log=[{"step": "TRIGGER", "detail": f"Recovery initiated due to {failure_type}."}]
        )
        local_store.record_recovery(rec_action)

        # Notify via EventBus
        await event_bus.publish("recovery_started", rec_action.model_dump())

        # Execute recovery workflow asynchronously in background task
        asyncio.create_task(self._execute_recovery_hierarchy(rec_action, start_tier))
        return rec_action

    async def _execute_recovery_hierarchy(self, rec: RecoveryActionModel, initial_tier: RecoveryTier):
        node_id = rec.node_id
        hierarchy = [
            RecoveryTier.TIER_1_RESTART_APPLICATION,
            RecoveryTier.TIER_2_RESTART_CONTAINER,
            RecoveryTier.TIER_3_RECREATE_CONTAINER,
            RecoveryTier.TIER_4_FAILOVER_WORKLOAD,
            RecoveryTier.TIER_5_ESCALATE_ADMIN
        ]

        # Slice hierarchy starting from initial tier
        start_idx = hierarchy.index(initial_tier) if initial_tier in hierarchy else 0
        tiers_to_try = hierarchy[start_idx:]

        try:
            for current_tier in tiers_to_try:
                rec.action_tier = current_tier
                rec.action_name = current_tier.value
                rec.steps_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "step": current_tier.value,
                    "status": "EXECUTING"
                })

                if current_tier == RecoveryTier.TIER_1_RESTART_APPLICATION:
                    exec_res = await RecoveryActions.restart_application(node_id)
                elif current_tier == RecoveryTier.TIER_2_RESTART_CONTAINER:
                    exec_res = await RecoveryActions.restart_container(node_id)
                elif current_tier == RecoveryTier.TIER_3_RECREATE_CONTAINER:
                    exec_res = await RecoveryActions.recreate_container(node_id)
                elif current_tier == RecoveryTier.TIER_4_FAILOVER_WORKLOAD:
                    exec_res = await RecoveryActions.failover_workload(node_id)
                else:  # TIER_5_ESCALATE_ADMIN
                    rec.result = RecoveryResult.ESCALATED
                    rec.steps_log.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "step": "ADMIN_ESCALATION",
                        "status": "ESCALATED",
                        "detail": "Automated recovery tiers exhausted. Critical administrator alert created."
                    })
                    break

                # Post-Action Verification
                rec.steps_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "step": f"VERIFY_{current_tier.value}",
                    "status": "WAITING_VERIFICATION"
                })

                verification = await recovery_verifier.verify_node_recovery(node_id, delay_seconds=2.5)
                rec.health_after = verification["health_score"]
                rec.status_after = verification["status"]

                if verification["passed"]:
                    rec.result = RecoveryResult.SUCCESS
                    rec.verification_passed = True
                    rec.completed_at = datetime.utcnow().isoformat()
                    rec.steps_log.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "step": f"VERIFIED_{current_tier.value}",
                        "status": "SUCCESS",
                        "health_score": rec.health_after,
                        "detail": f"Health restored to {rec.health_after:.1f}% ({rec.status_after})"
                    })
                    break
                else:
                    rec.steps_log.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "step": f"VERIFY_FAILED_{current_tier.value}",
                        "status": "FAILED",
                        "health_score": rec.health_after,
                        "detail": f"Post-recovery health still degraded ({rec.health_after:.1f}%). Escalating to next tier."
                    })

            if rec.result != RecoveryResult.SUCCESS:
                rec.result = RecoveryResult.ESCALATED if rec.action_tier == RecoveryTier.TIER_5_ESCALATE_ADMIN else RecoveryResult.FAILED
                rec.verification_passed = False
                rec.completed_at = datetime.utcnow().isoformat()

            # Record final outcome
            local_store.record_recovery(rec)

            # Audit log entry
            audit_entry = AuditLogEntry(
                actor="SYSTEM_SELF_HEALING",
                role=UserRole.ADMIN,
                target_node=node_id,
                event_type="SELF_HEALING",
                action=f"Self-recovery executed: {rec.action_name} for {rec.failure_type}",
                result=rec.result.value,
                details={
                    "recovery_id": rec.recovery_id,
                    "confidence": rec.confidence_score,
                    "health_before": rec.health_before,
                    "health_after": rec.health_after,
                    "tier_used": rec.action_tier.value
                }
            )
            local_store.add_audit_log(audit_entry)

            # Publish event
            await event_bus.publish("recovery_completed", rec.model_dump())
            await event_bus.publish("audit_logged", audit_entry.model_dump())

        finally:
            self._in_progress_nodes.discard(node_id)


recovery_orchestrator = RecoveryOrchestrator()
