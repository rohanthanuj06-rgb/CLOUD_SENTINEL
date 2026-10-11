import asyncio
import logging
from typing import Dict, Any
from app.monitoring.docker_monitor import docker_monitor, DEFAULT_NODES
from app.monitoring.health_scoring import health_score_engine

logger = logging.getLogger("cloudsentinel.recovery_verifier")


class RecoveryVerifier:
    async def verify_node_recovery(self, node_id: str, delay_seconds: float = 2.0) -> Dict[str, Any]:
        """
        Post-recovery verification workflow:
        1. Wait stabilization period
        2. Probe container state & HTTP /health endpoint
        3. Measure response latency
        4. Recalculate health score
        5. Verify recovery efficacy
        """
        logger.info(f"Initiating recovery verification for {node_id} (delay: {delay_seconds}s)...")
        await asyncio.sleep(delay_seconds)

        node_def = next((n for n in DEFAULT_NODES if n["node_id"] == node_id), None)
        if not node_def:
            return {"passed": False, "health_score": 0.0, "reason": "Node definition not found"}

        # Collect fresh telemetry post-recovery
        telemetry = await docker_monitor.get_node_telemetry(node_def)
        
        scores = health_score_engine.calculate(
            cpu_percent=telemetry["cpu_percent"],
            memory_percent=telemetry["memory_percent"],
            network_rx_rate_kb=telemetry["network_rx_rate_kb"],
            response_time_ms=telemetry["response_time_ms"],
            heartbeat=telemetry["heartbeat"],
            application_healthy=telemetry["application_healthy"],
            container_running=telemetry["status"].value == "running"
        )

        health_after = scores["health_score"]
        is_healthy = telemetry["application_healthy"] and telemetry["heartbeat"] and (health_after >= 65.0)

        return {
            "passed": is_healthy,
            "health_score": health_after,
            "status": "HEALTHY" if is_healthy else "DEGRADED",
            "application_healthy": telemetry["application_healthy"],
            "heartbeat": telemetry["heartbeat"],
            "response_time_ms": telemetry["response_time_ms"],
            "cpu_percent": telemetry["cpu_percent"],
            "memory_percent": telemetry["memory_percent"],
            "sub_scores": scores
        }


recovery_verifier = RecoveryVerifier()
