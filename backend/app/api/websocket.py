import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
from app.core.events import event_bus

logger = logging.getLogger("cloudsentinel.websocket")
router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        dead_connections = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.add(connection)

        for dead in dead_connections:
            self.active_connections.discard(dead)


manager = ConnectionManager()


# Register event listeners on the event_bus
async def on_telemetry(data):
    await manager.broadcast({"type": "TELEMETRY_UPDATE", "data": data})


async def on_recovery_started(data):
    await manager.broadcast({"type": "RECOVERY_STARTED", "data": data})


async def on_recovery_completed(data):
    await manager.broadcast({"type": "RECOVERY_COMPLETED", "data": data})


async def on_alert_created(data):
    await manager.broadcast({"type": "ALERT_CREATED", "data": data})


async def on_alert_updated(data):
    await manager.broadcast({"type": "ALERT_UPDATED", "data": data})


async def on_audit_logged(data):
    await manager.broadcast({"type": "AUDIT_LOGGED", "data": data})


event_bus.subscribe("telemetry_cycle", on_telemetry)
event_bus.subscribe("recovery_started", on_recovery_started)
event_bus.subscribe("recovery_completed", on_recovery_completed)
event_bus.subscribe("alert_created", on_alert_created)
event_bus.subscribe("alert_updated", on_alert_updated)
event_bus.subscribe("audit_logged", on_audit_logged)


@router.websocket("/ws")
@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open; receive ping or messages from client
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
        manager.disconnect(websocket)
