"""Event handlers for emitting WebSocket events from REST API."""
import logging
from typing import Optional
from datetime import datetime
from socketio import AsyncServer

logger = logging.getLogger(__name__)

# Global reference to Socket.IO server (set in main.py)
sio: Optional[AsyncServer] = None


def set_sio_instance(socket_io: AsyncServer) -> None:
    """Set the global Socket.IO instance."""
    global sio
    sio = socket_io
    logger.info("Socket.IO instance set for event handlers")


async def emit_comment_new(post_id: str, comment_id: str, author_id: str, content: str) -> None:
    """Emit new comment event to all viewers of a post."""
    if not sio:
        logger.warning("Socket.IO not initialized, cannot emit comment:new event")
        return

    try:
        await sio.emit("comment:new", {
            "post_id": post_id,
            "comment_id": comment_id,
            "author_id": author_id,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }, to=f"post:{post_id}", namespace="/collaboration")
        logger.debug(f"Emitted comment:new for post {post_id}")
    except Exception as e:
        logger.error(f"Error emitting comment:new: {e}")


async def emit_comment_updated(post_id: str, comment_id: str, content: str, updated_at: datetime = None) -> None:
    """Emit comment updated event."""
    if not sio:
        logger.warning("Socket.IO not initialized, cannot emit comment:updated event")
        return

    try:
        await sio.emit("comment:updated", {
            "post_id": post_id,
            "comment_id": comment_id,
            "content": content,
            "updated_at": (updated_at or datetime.utcnow()).isoformat()
        }, to=f"post:{post_id}", namespace="/collaboration")
        logger.debug(f"Emitted comment:updated for comment {comment_id}")
    except Exception as e:
        logger.error(f"Error emitting comment:updated: {e}")


async def emit_comment_deleted(post_id: str, comment_id: str) -> None:
    """Emit comment deleted event."""
    if not sio:
        logger.warning("Socket.IO not initialized, cannot emit comment:deleted event")
        return

    try:
        await sio.emit("comment:deleted", {
            "post_id": post_id,
            "comment_id": comment_id,
            "timestamp": datetime.utcnow().isoformat()
        }, to=f"post:{post_id}", namespace="/collaboration")
        logger.debug(f"Emitted comment:deleted for comment {comment_id}")
    except Exception as e:
        logger.error(f"Error emitting comment:deleted: {e}")


async def emit_share_notification(share_id: str, post_id: str, sharer_id: str, recipient_id: str,
                                  message: Optional[str] = None) -> None:
    """Emit share notification to recipient."""
    if not sio:
        logger.warning("Socket.IO not initialized, cannot emit share:notification event")
        return

    try:
        await sio.emit("share:notification", {
            "share_id": share_id,
            "post_id": post_id,
            "sharer_id": sharer_id,
            "recipient_id": recipient_id,
            "message": message or "A post has been shared with you",
            "timestamp": datetime.utcnow().isoformat()
        }, to=f"user:{recipient_id}", namespace="/collaboration")
        logger.debug(f"Emitted share:notification for user {recipient_id}")
    except Exception as e:
        logger.error(f"Error emitting share:notification: {e}")


async def emit_activity_log(group_id: str, action: str, resource_id: str, resource_type: str,
                            actor_id: str, message: Optional[str] = None) -> None:
    """Emit activity log event to a group."""
    if not sio:
        logger.warning("Socket.IO not initialized, cannot emit activity:log event")
        return

    try:
        await sio.emit("activity:log", {
            "action": action,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "actor_id": actor_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }, to=f"group:{group_id}", namespace="/collaboration")
        logger.debug(f"Emitted activity:log for group {group_id}")
    except Exception as e:
        logger.error(f"Error emitting activity:log: {e}")


async def broadcast_user_online(group_id: str, user_id: str, online_users: list) -> None:
    """Broadcast user online event to a group."""
    if not sio:
        logger.warning("Socket.IO not initialized, cannot emit user:online event")
        return

    try:
        await sio.emit("user:online", {
            "user_id": user_id,
            "group_id": group_id,
            "online_users": online_users,
            "timestamp": datetime.utcnow().isoformat()
        }, to=f"group:{group_id}", namespace="/collaboration")
        logger.debug(f"Broadcast user:online for group {group_id}")
    except Exception as e:
        logger.error(f"Error broadcasting user:online: {e}")


async def broadcast_user_offline(group_id: str, user_id: str, remaining_users: list) -> None:
    """Broadcast user offline event to a group."""
    if not sio:
        logger.warning("Socket.IO not initialized, cannot emit user:offline event")
        return

    try:
        await sio.emit("user:offline", {
            "user_id": user_id,
            "group_id": group_id,
            "remaining_users": remaining_users,
            "timestamp": datetime.utcnow().isoformat()
        }, to=f"group:{group_id}", namespace="/collaboration")
        logger.debug(f"Broadcast user:offline for group {group_id}")
    except Exception as e:
        logger.error(f"Error broadcasting user:offline: {e}")
