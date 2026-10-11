import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from app.config import settings
from app.monitoring.docker_monitor import docker_monitor, DEFAULT_NODES
from app.monitoring.health_scoring import health_score_engine
from app.monitoring.heartbeat import heartbeat_tracker
from app.diagnostics.classifier import classifier
from app.diagnostics.rule_engine import diagnostic_engine
from app.recovery.orchestrator import recovery_orchestrator
from app.firebase.local_fallback import local_store
from app.firebase.firebase_service import firebase_service
from app.core.events import event_bus
from app.models.node import NodeModel, NodeStatus, InfrastructureState
from app.models.metric import MetricSnapshot
from app.models.alert import AlertModel, AlertSeverity, AlertStatus

logger = logging.getLogger("cloudsentinel.collector")


class TelemetryCollector:
    def __init__(self):
        self._running = False
        self._task = None
        self._aggregation_counter = 0

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info(f"Telemetry Collector started (interval: {settings.HEALTH_INTERVAL}s).")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Telemetry Collector stopped.")

    async def _collection_loop(self):
        while self._running:
            try:
                await self.poll_all_nodes()
                self._aggregation_counter += 1
                if self._aggregation_counter >= 10:  # Every ~30s, aggregate for Firestore
                    self._aggregation_counter = 0
                    await self._aggregate_and_sync()
            except Exception as e:
                logger.error(f"Error in telemetry collection cycle: {e}", exc_info=True)

            await asyncio.sleep(settings.HEALTH_INTERVAL)

    async def poll_all_nodes(self):
        updated_nodes: List[Dict[str, Any]] = []

        for node_def in DEFAULT_NODES:
            try:
                node_id = node_def["node_id"]
                raw_telem = await docker_monitor.get_node_telemetry(node_def)

                # Heartbeat tracking
                if raw_telem["heartbeat"]:
                    heartbeat_tracker.record_heartbeat_received(node_id)
                else:
                    heartbeat_tracker.record_heartbeat_missed(node_id)

                missed_hb = heartbeat_tracker.get_missed_count(node_id)
                is_alive = heartbeat_tracker.is_alive(node_id)

                # Health score calculation
                scores = health_score_engine.calculate(
                    cpu_percent=raw_telem["cpu_percent"],
                    memory_percent=raw_telem["memory_percent"],
                    network_rx_rate_kb=raw_telem["network_rx_rate_kb"],
                    response_time_ms=raw_telem["response_time_ms"],
                    heartbeat=is_alive,
                    application_healthy=raw_telem["application_healthy"],
                    container_running=raw_telem["status"] == NodeStatus.RUNNING
                )

                # Build or update NodeModel
                node = NodeModel(
                    node_id=node_id,
                    container_name=raw_telem["container_name"],
                    container_id=raw_telem.get("container_id"),
                    service_name=raw_telem["service_name"],
                    port=raw_telem["port"],
                    status=raw_telem["status"],
                    cpu_percent=raw_telem["cpu_percent"],
                    memory_percent=raw_telem["memory_percent"],
                    memory_used_mb=raw_telem["memory_used_mb"],
                    memory_limit_mb=raw_telem["memory_limit_mb"],
                    disk_percent=raw_telem["disk_percent"],
                    network_rx_bytes=raw_telem["network_rx_bytes"],
                    network_tx_bytes=raw_telem["network_tx_bytes"],
                    network_rx_rate_kb=raw_telem["network_rx_rate_kb"],
                    network_tx_rate_kb=raw_telem["network_tx_rate_kb"],
                    response_time_ms=raw_telem["response_time_ms"],
                    heartbeat=is_alive,
                    missed_heartbeats=missed_hb,
                    application_healthy=raw_telem["application_healthy"],
                    restart_count=raw_telem["restart_count"],
                    uptime_seconds=raw_telem["uptime_seconds"],
                    last_seen=datetime.utcnow().isoformat(),
                    health_score=scores["health_score"],
                    active_faults=raw_telem.get("active_faults", []),
                    is_simulated=raw_telem.get("is_simulated", False)
                )

                # Classify Infrastructure State
                classification = classifier.classify(node)
                node.classification = classification

                # Diagnose potential failure
                diagnosis = diagnostic_engine.diagnose(node)
                node.latest_diagnosis = diagnosis

                local_store.update_node(node)

                # Record Telemetry Time Series Point
                snapshot = MetricSnapshot(
                    node_id=node_id,
                    cpu_percent=node.cpu_percent,
                    memory_percent=node.memory_percent,
                    memory_used_mb=node.memory_used_mb,
                    disk_percent=node.disk_percent,
                    network_rx_bytes=node.network_rx_bytes,
                    network_tx_bytes=node.network_tx_bytes,
                    network_rx_rate_kb=node.network_rx_rate_kb,
                    network_tx_rate_kb=node.network_tx_rate_kb,
                    response_time_ms=node.response_time_ms,
                    heartbeat=node.heartbeat,
                    application_healthy=node.application_healthy,
                    health_score=node.health_score,
                    classification=node.classification.value
                )
                local_store.record_metric(snapshot)

                # Automatic Self-Healing Trigger
                if settings.AUTO_RECOVERY_ENABLED and diagnosis and diagnosis.get("confidence", 0) >= 0.85:
                    cause = diagnosis["cause"]
                    if cause in ("APPLICATION_FAILURE", "CONTAINER_STOPPED", "CONTAINER_NETWORK_FAILURE", "MEMORY_EXHAUSTION"):
                        asyncio.create_task(
                            recovery_orchestrator.initiate_self_healing(
                                node_id=node_id,
                                failure_type=cause,
                                confidence=diagnosis["confidence"],
                                operator_initiated=False
                            )
                        )

                # Alert creation if critical condition detected
                if node.classification in (InfrastructureState.CRITICAL, InfrastructureState.DEAD, InfrastructureState.UNRESPONSIVE):
                    existing = [a for a in local_store.get_alerts(status=AlertStatus.ACTIVE) if a.node_id == node_id]
                    if not existing:
                        alert = AlertModel(
                            node_id=node_id,
                            container_name=node.container_name,
                            alert_type=diagnosis["cause"] if diagnosis else "CRITICAL_STATE",
                            severity=AlertSeverity.CRITICAL,
                            title=f"Critical Health Alert on {node.container_name}",
                            description=diagnosis["summary"] if diagnosis else "Node health has collapsed below safe threshold.",
                            evidence=diagnosis["evidence"] if diagnosis else ["Health score below 30%"],
                            recommended_action=diagnosis["recommended_action"] if diagnosis else "RESTART_CONTAINER"
                        )
                        local_store.add_alert(alert)
                        await event_bus.publish("alert_created", alert.model_dump())

                updated_nodes.append(node.model_dump())

            except Exception as e:
                logger.error(f"Error polling node {node_def['node_id']}: {e}")

        # Broadcast telemetry update to WebSocket subscribers
        if updated_nodes:
            await event_bus.publish("telemetry_cycle", {
                "timestamp": datetime.utcnow().isoformat(),
                "nodes": updated_nodes
            })

    async def _aggregate_and_sync(self):
        """Aggregates local snapshots into 30s/1m summaries for Firestore."""
        if not local_store.unaggregated_snapshots or not firebase_service.is_connected:
            return

        snapshots = list(local_store.unaggregated_snapshots)
        local_store.unaggregated_snapshots.clear()

        # Group by node_id
        grouped: Dict[str, List[MetricSnapshot]] = {}
        for s in snapshots:
            grouped.setdefault(s.node_id, []).append(s)

        aggregated = []
        for nid, group in grouped.items():
            if not group:
                continue
            rec = {
                "node_id": nid,
                "window_start": group[0].timestamp,
                "window_end": group[-1].timestamp,
                "avg_cpu": round(sum(g.cpu_percent for g in group) / len(group), 2),
                "max_cpu": round(max(g.cpu_percent for g in group), 2),
                "avg_memory": round(sum(g.memory_percent for g in group) / len(group), 2),
                "max_memory": round(max(g.memory_percent for g in group), 2),
                "avg_response_time": round(sum(g.response_time_ms for g in group) / len(group), 2),
                "avg_health_score": round(sum(g.health_score for g in group) / len(group), 2),
                "sample_count": len(group)
            }
            aggregated.append(rec)

        await firebase_service.save_aggregated_metrics(aggregated)


telemetry_collector = TelemetryCollector()
