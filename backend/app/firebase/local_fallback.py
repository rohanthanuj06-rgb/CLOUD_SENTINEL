from collections import deque
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
from app.models.node import NodeModel, InfrastructureState, NodeStatus
from app.models.metric import MetricSnapshot, MetricTimeseriesPoint
from app.models.alert import AlertModel, AlertStatus, AlertSeverity
from app.models.recovery import RecoveryActionModel, RecoveryResult
from app.models.audit import AuditLogEntry, UserRole


class LocalDataStore:
    """
    High-performance in-memory and local state store.
    Guarantees instant response times for dashboard, sub-second queries,
    and holds sliding windows for time-series metrics.
    """
    def __init__(self):
        self._lock = threading.RLock()
        
        # Nodes indexed by node_id
        self.nodes: Dict[str, NodeModel] = {}
        
        # Telemetry rolling history: node_id -> deque of MetricTimeseriesPoint
        self.metrics_history: Dict[str, deque] = {}
        
        # Alerts: alert_id -> AlertModel
        self.alerts: Dict[str, AlertModel] = {}
        
        # Recovery actions: recovery_id -> RecoveryActionModel
        self.recoveries: Dict[str, RecoveryActionModel] = {}
        
        # Audit logs: deque of AuditLogEntry (capped at 500)
        self.audit_logs: deque = deque(maxlen=500)
        
        # Predictions cache: node_id -> dict
        self.predictions: Dict[str, Any] = {}
        
        # Historical metric snapshots for aggregation
        self.unaggregated_snapshots: List[MetricSnapshot] = []

    def register_node(self, node: NodeModel):
        with self._lock:
            self.nodes[node.node_id] = node
            if node.node_id not in self.metrics_history:
                self.metrics_history[node.node_id] = deque(maxlen=500)

    def get_node(self, node_id: str) -> Optional[NodeModel]:
        with self._lock:
            return self.nodes.get(node_id)

    def get_all_nodes(self) -> List[NodeModel]:
        with self._lock:
            return list(self.nodes.values())

    def update_node(self, node: NodeModel):
        with self._lock:
            self.nodes[node.node_id] = node

    def record_metric(self, snapshot: MetricSnapshot):
        with self._lock:
            if snapshot.node_id not in self.metrics_history:
                self.metrics_history[snapshot.node_id] = deque(maxlen=500)
                
            point = MetricTimeseriesPoint(
                timestamp=snapshot.timestamp,
                cpu=snapshot.cpu_percent,
                memory=snapshot.memory_percent,
                disk=snapshot.disk_percent,
                network_rx_kb=round(snapshot.network_rx_rate_kb, 2),
                network_tx_kb=round(snapshot.network_tx_rate_kb, 2),
                response_time=snapshot.response_time_ms,
                health_score=snapshot.health_score
            )
            self.metrics_history[snapshot.node_id].append(point)
            self.unaggregated_snapshots.append(snapshot)

    def get_node_metrics(self, node_id: str, limit: int = 100) -> List[MetricTimeseriesPoint]:
        with self._lock:
            history = self.metrics_history.get(node_id, deque())
            items = list(history)
            return items[-limit:] if limit > 0 else items

    def add_alert(self, alert: AlertModel) -> AlertModel:
        with self._lock:
            self.alerts[alert.id] = alert
            return alert

    def get_alerts(self, status: Optional[AlertStatus] = None, limit: int = 50) -> List[AlertModel]:
        with self._lock:
            alerts = list(self.alerts.values())
            if status:
                alerts = [a for a in alerts if a.status == status]
            # Order newest first
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            return alerts[:limit]

    def resolve_alert(self, alert_id: str) -> Optional[AlertModel]:
        with self._lock:
            alert = self.alerts.get(alert_id)
            if alert:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow().isoformat()
            return alert

    def record_recovery(self, recovery: RecoveryActionModel):
        with self._lock:
            self.recoveries[recovery.recovery_id] = recovery

    def get_recovery(self, recovery_id: str) -> Optional[RecoveryActionModel]:
        with self._lock:
            return self.recoveries.get(recovery_id)

    def get_all_recoveries(self, limit: int = 50) -> List[RecoveryActionModel]:
        with self._lock:
            rec_list = list(self.recoveries.values())
            rec_list.sort(key=lambda x: x.started_at, reverse=True)
            return rec_list[:limit]

    def add_audit_log(self, entry: AuditLogEntry):
        with self._lock:
            self.audit_logs.appendleft(entry)

    def get_audit_logs(self, limit: int = 100) -> List[AuditLogEntry]:
        with self._lock:
            return list(self.audit_logs)[:limit]

    def set_prediction(self, node_id: str, data: Dict[str, Any]):
        with self._lock:
            self.predictions[node_id] = data

    def get_all_predictions(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.predictions)


local_store = LocalDataStore()
