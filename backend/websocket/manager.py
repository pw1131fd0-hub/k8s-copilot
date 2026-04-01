"""WebSocket connection manager for ClawBook real-time features."""
import logging
from typing import Dict, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections, rooms, and online users."""

    def __init__(self):
        """Initialize the WebSocket manager."""
        # sid -> {user_id, connected_at, rooms}
        self.active_connections: Dict[str, dict] = {}
        # group_id -> Set[sid]
        self.group_rooms: Dict[str, Set[str]] = {}
        # post_id -> Set[sid]
        self.post_rooms: Dict[str, Set[str]] = {}
        # user_id -> Set[sid] (for direct notifications)
        self.user_connections: Dict[str, Set[str]] = {}

    def register_connection(self, sid: str, user_id: str) -> None:
        """Register a new WebSocket connection."""
        self.active_connections[sid] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "rooms": set(),
        }
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(sid)
        logger.debug(f"WebSocket connection registered: {sid} for user {user_id}")

    def unregister_connection(self, sid: str) -> Optional[str]:
        """Unregister a WebSocket connection and clean up rooms."""
        if sid not in self.active_connections:
            return None

        conn = self.active_connections.pop(sid)
        user_id = conn["user_id"]

        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(sid)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Clean up room memberships
        for room_type, rooms in [("group", self.group_rooms), ("post", self.post_rooms)]:
            for room_id, sids in list(rooms.items()):
                if sid in sids:
                    sids.discard(sid)
                    if not sids:
                        del rooms[room_id]

        logger.debug(f"WebSocket connection unregistered: {sid} for user {user_id}")
        return user_id

    def join_group_room(self, sid: str, group_id: str) -> None:
        """Add connection to a group room."""
        if sid not in self.active_connections:
            return

        if group_id not in self.group_rooms:
            self.group_rooms[group_id] = set()

        self.group_rooms[group_id].add(sid)
        self.active_connections[sid]["rooms"].add(f"group:{group_id}")
        logger.debug(f"Connection {sid} joined group room: {group_id}")

    def leave_group_room(self, sid: str, group_id: str) -> None:
        """Remove connection from a group room."""
        if group_id in self.group_rooms:
            self.group_rooms[group_id].discard(sid)
            if not self.group_rooms[group_id]:
                del self.group_rooms[group_id]

        if sid in self.active_connections:
            self.active_connections[sid]["rooms"].discard(f"group:{group_id}")
        logger.debug(f"Connection {sid} left group room: {group_id}")

    def join_post_room(self, sid: str, post_id: str) -> None:
        """Add connection to a post room (for comment updates)."""
        if sid not in self.active_connections:
            return

        if post_id not in self.post_rooms:
            self.post_rooms[post_id] = set()

        self.post_rooms[post_id].add(sid)
        self.active_connections[sid]["rooms"].add(f"post:{post_id}")
        logger.debug(f"Connection {sid} joined post room: {post_id}")

    def leave_post_room(self, sid: str, post_id: str) -> None:
        """Remove connection from a post room."""
        if post_id in self.post_rooms:
            self.post_rooms[post_id].discard(sid)
            if not self.post_rooms[post_id]:
                del self.post_rooms[post_id]

        if sid in self.active_connections:
            self.active_connections[sid]["rooms"].discard(f"post:{post_id}")
        logger.debug(f"Connection {sid} left post room: {post_id}")

    def get_group_members(self, group_id: str) -> list[str]:
        """Get list of user IDs currently in a group room."""
        if group_id not in self.group_rooms:
            return []

        users = set()
        for sid in self.group_rooms[group_id]:
            if sid in self.active_connections:
                users.add(self.active_connections[sid]["user_id"])
        return list(users)

    def get_group_connections(self, group_id: str) -> Set[str]:
        """Get all connection SIDs in a group room."""
        return self.group_rooms.get(group_id, set())

    def get_post_connections(self, post_id: str) -> Set[str]:
        """Get all connection SIDs viewing a post."""
        return self.post_rooms.get(post_id, set())

    def get_user_connections(self, user_id: str) -> Set[str]:
        """Get all connection SIDs for a user."""
        return self.user_connections.get(user_id, set())

    def is_user_online(self, user_id: str) -> bool:
        """Check if a user has active connections."""
        return len(self.user_connections.get(user_id, set())) > 0

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)

    def get_stats(self) -> dict:
        """Get WebSocket manager statistics."""
        return {
            "total_connections": len(self.active_connections),
            "unique_users": len(self.user_connections),
            "group_rooms": len(self.group_rooms),
            "post_rooms": len(self.post_rooms),
        }
