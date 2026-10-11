from typing import Dict, Any
from datetime import datetime
import time
from app.config import settings
import logging

logger = logging.getLogger("cloudsentinel.heartbeat")


class HeartbeatTracker:
    def __init__(self):
        # node_id -> {"last_heartbeat": float, "missed_count": int, "is_alive": bool}
        self._nodes_hb: Dict[str, Dict[str, Any]] = {}

    def register_node(self, node_id: str):
        if node_id not in self._nodes_hb:
            self._nodes_hb[node_id] = {
                "last_heartbeat": time.time(),
                "missed_count": 0,
                "is_alive": True,
                "last_heartbeat_iso": datetime.utcnow().isoformat()
            }

    def record_heartbeat_received(self, node_id: str):
        now = time.time()
        self._nodes_hb[node_id] = {
            "last_heartbeat": now,
            "missed_count": 0,
            "is_alive": True,
            "last_heartbeat_iso": datetime.utcnow().isoformat()
        }

    def record_heartbeat_missed(self, node_id: str) -> int:
        if node_id not in self._nodes_hb:
            self.register_node(node_id)

        info = self._nodes_hb[node_id]
        info["missed_count"] += 1
        if info["missed_count"] >= settings.MISSED_HEARTBEATS_THRESHOLD:
            info["is_alive"] = False
        return info["missed_count"]

    def is_alive(self, node_id: str) -> bool:
        info = self._nodes_hb.get(node_id)
        if not info:
            return False
        return info["is_alive"]

    def get_missed_count(self, node_id: str) -> int:
        info = self._nodes_hb.get(node_id)
        return info["missed_count"] if info else 0

    def get_status(self, node_id: str) -> Dict[str, Any]:
        return self._nodes_hb.get(node_id, {
            "last_heartbeat": 0,
            "missed_count": 0,
            "is_alive": False,
            "last_heartbeat_iso": None
        })


heartbeat_tracker = HeartbeatTracker()
