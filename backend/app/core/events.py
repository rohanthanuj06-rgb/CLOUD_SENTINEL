import asyncio
from typing import Callable, List, Dict, Any
import logging

logger = logging.getLogger("cloudsentinel.events")


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[Dict[str, Any]], Any]):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)

    async def publish(self, event_name: str, data: Dict[str, Any]):
        handlers = self._subscribers.get(event_name, []) + self._subscribers.get("*", [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(data))
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error executing event handler for {event_name}: {e}")


event_bus = EventBus()
