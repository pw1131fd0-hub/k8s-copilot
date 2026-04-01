"""Socket.IO namespace handlers for ClawBook collaboration."""
import logging
from typing import Optional
from socketio import AsyncNamespace, emit
from backend.websocket.manager import WebSocketManager
from backend.websocket.events import EventType, UserPresencePayload

logger = logging.getLogger(__name__)


class CollaborationNamespace(AsyncNamespace):
    """Socket.IO namespace for collaboration features."""

    def __init__(self, namespace: str, manager: WebSocketManager):
        super().__init__(namespace=namespace)
        self.manager = manager

    async def on_connect(self, sid: str, environ):
        """Handle client connection."""
        # Extract user_id from query params or connection data
        # In production, this would come from JWT token
        user_id = "default_user"  # Placeholder for single-user mode

        self.manager.register_connection(sid, user_id)
        logger.info(f"Client connected: {sid} as {user_id}")

        # Send acknowledgment
        emit("connection:ack", {
            "status": "connected",
            "user_id": user_id,
            "message": "Welcome to ClawBook collaboration"
        }, to=sid)

    async def on_disconnect(self, sid: str):
        """Handle client disconnection."""
        user_id = self.manager.unregister_connection(sid)
        if user_id:
            logger.info(f"Client disconnected: {sid} (user: {user_id})")

            # Broadcast user offline notification to all rooms the user was in
            for group_id in list(self.manager.group_rooms.keys()):
                if sid in self.manager.group_rooms[group_id]:
                    emit("user:offline", {
                        "user_id": user_id,
                        "group_id": group_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }, to=f"group:{group_id}")

    async def on_join_group(self, sid: str, data: dict):
        """Handle user joining a group room."""
        group_id = data.get("group_id")
        if not group_id:
            emit("error", {"message": "group_id required"}, to=sid)
            return

        conn = self.manager.active_connections.get(sid)
        if not conn:
            return

        user_id = conn["user_id"]
        self.manager.join_group_room(sid, group_id)

        # Notify others in the group that user is online
        group_members = self.manager.get_group_members(group_id)
        emit("user:online", {
            "user_id": user_id,
            "group_id": group_id,
            "online_users": group_members,
            "timestamp": datetime.utcnow().isoformat()
        }, to=f"group:{group_id}")

        logger.debug(f"User {user_id} joined group {group_id}")

    async def on_leave_group(self, sid: str, data: dict):
        """Handle user leaving a group room."""
        group_id = data.get("group_id")
        if not group_id:
            return

        conn = self.manager.active_connections.get(sid)
        if not conn:
            return

        user_id = conn["user_id"]
        self.manager.leave_group_room(sid, group_id)

        # Notify others that user is offline
        group_members = self.manager.get_group_members(group_id)
        emit("user:offline", {
            "user_id": user_id,
            "group_id": group_id,
            "remaining_users": group_members,
            "timestamp": datetime.utcnow().isoformat()
        }, to=f"group:{group_id}")

        logger.debug(f"User {user_id} left group {group_id}")

    async def on_join_post(self, sid: str, data: dict):
        """Handle user viewing a post (for comment updates)."""
        post_id = data.get("post_id")
        if not post_id:
            emit("error", {"message": "post_id required"}, to=sid)
            return

        self.manager.join_post_room(sid, post_id)
        logger.debug(f"Connection {sid} joined post {post_id}")

    async def on_leave_post(self, sid: str, data: dict):
        """Handle user leaving a post view."""
        post_id = data.get("post_id")
        if not post_id:
            return

        self.manager.leave_post_room(sid, post_id)
        logger.debug(f"Connection {sid} left post {post_id}")

    async def on_comment_new(self, sid: str, data: dict):
        """Handle new comment notification (will be called from REST API)."""
        post_id = data.get("post_id")
        if not post_id:
            return

        # Broadcast to all users viewing this post
        emit("comment:new", data, to=f"post:{post_id}")

    async def on_ping(self, sid: str):
        """Handle ping from client."""
        emit("pong", {"timestamp": datetime.utcnow().isoformat()}, to=sid)

    async def on_error(self, sid: str, data):
        """Handle errors from client."""
        logger.error(f"Client error from {sid}: {data}")


def create_collaboration_namespace(sio, manager: WebSocketManager):
    """Create and register the collaboration namespace."""
    namespace = CollaborationNamespace("/collaboration", manager)
    sio.register_namespace(namespace)
    logger.info("Collaboration namespace registered")
    return namespace


# Import datetime for isoformat usage
from datetime import datetime
