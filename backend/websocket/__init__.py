"""WebSocket module for real-time collaboration features in ClawBook."""
from backend.websocket.manager import WebSocketManager
from backend.websocket.handlers import setup_event_handlers

__all__ = ["WebSocketManager", "setup_event_handlers"]
