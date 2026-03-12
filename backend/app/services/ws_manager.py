"""
app/services/ws_manager.py — WebSocket connection manager.

Provides a module-level ``manager`` singleton used by both the scanner tasks
(to broadcast alerts) and the FastAPI WebSocket endpoint (to register clients).
"""
import json
import logging
from typing import List

from fastapi import WebSocket

log = logging.getLogger("ids.ws")


class ConnectionManager:
    """Fan-out broadcaster for all active WebSocket connections."""

    def __init__(self) -> None:
        self._active: List[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._active.append(ws)
        log.info("WS client connected  (total=%d)", len(self._active))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._active:
            self._active.remove(ws)
        log.info("WS client disconnected (total=%d)", len(self._active))

    async def broadcast(self, payload: dict) -> None:
        """Serialize *payload* to JSON and send to every live client."""
        message = json.dumps(payload)
        dead: List[WebSocket] = []
        for ws in list(self._active):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._active.remove(ws)

    @property
    def client_count(self) -> int:
        return len(self._active)


# Module-level singleton
manager = ConnectionManager()
