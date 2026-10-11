import httpx
import logging
from typing import Dict, Any
from app.monitoring.docker_monitor import docker_monitor, DEFAULT_NODES

logger = logging.getLogger("cloudsentinel.recovery_actions")


class RecoveryActions:
    @staticmethod
    async def restart_application(node_id: str) -> Dict[str, Any]:
        """Tier 1: Restart application process via REST endpoint without cycling container."""
        node_def = next((n for n in DEFAULT_NODES if n["node_id"] == node_id), None)
        port = node_def["port"] if node_def else 8001
        url = f"http://localhost:{port}/restart_app"

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(url)
                if resp.status_code == 200:
                    return {"success": True, "action": "RESTART_APPLICATION", "detail": "Application state reset and restarted."}
        except Exception as e:
            logger.debug(f"Direct app restart endpoint error: {e}. Falling back to simulation.")

        # In simulation: reset node's active faults
        sim = docker_monitor._simulated_nodes.get(node_id)
        if sim:
            sim["active_faults"].clear()
            sim["restart_count"] += 1
            return {"success": True, "action": "RESTART_APPLICATION", "detail": "Simulated app restarted successfully."}

        return {"success": False, "error": f"Failed to reach node {node_id} application process."}

    @staticmethod
    async def restart_container(node_id: str) -> Dict[str, Any]:
        """Tier 2: Restart container using Docker SDK."""
        return await docker_monitor.execute_container_action(node_id, "restart")

    @staticmethod
    async def recreate_container(node_id: str) -> Dict[str, Any]:
        """Tier 3: Recreate container fresh from image."""
        return await docker_monitor.execute_container_action(node_id, "recreate")

    @staticmethod
    async def failover_workload(node_id: str, standby_node_id: str = "cs-node-worker") -> Dict[str, Any]:
        """Tier 4: Workload failover simulation."""
        return {
            "success": True,
            "action": "FAILOVER_WORKLOAD",
            "source_node": node_id,
            "target_node": standby_node_id,
            "detail": f"Active traffic for {node_id} redirected to secondary standby container {standby_node_id}."
        }
