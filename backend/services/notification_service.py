"""Notification service for ClawBook collaboration features."""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.websocket import handlers as ws_handlers

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and WebSocket events."""

    @staticmethod
    async def notify_comment_new(db: Session, post_id: str, comment_id: str, author_id: str,
                                  content: str) -> None:
        """Notify all post viewers about a new comment."""
        try:
            await ws_handlers.emit_comment_new(post_id, comment_id, author_id, content)
            logger.info(f"Notified viewers of post {post_id} about new comment {comment_id}")
        except Exception as e:
            logger.error(f"Failed to notify comment:new event: {e}")

    @staticmethod
    async def notify_comment_updated(db: Session, post_id: str, comment_id: str, content: str,
                                     updated_at: Optional[datetime] = None) -> None:
        """Notify all post viewers about a comment update."""
        try:
            await ws_handlers.emit_comment_updated(post_id, comment_id, content, updated_at)
            logger.info(f"Notified viewers of post {post_id} about updated comment {comment_id}")
        except Exception as e:
            logger.error(f"Failed to notify comment:updated event: {e}")

    @staticmethod
    async def notify_comment_deleted(db: Session, post_id: str, comment_id: str) -> None:
        """Notify all post viewers about a deleted comment."""
        try:
            await ws_handlers.emit_comment_deleted(post_id, comment_id)
            logger.info(f"Notified viewers of post {post_id} about deleted comment {comment_id}")
        except Exception as e:
            logger.error(f"Failed to notify comment:deleted event: {e}")

    @staticmethod
    async def notify_post_shared(db: Session, share_id: str, post_id: str, sharer_id: str,
                                 recipient_id: str, message: Optional[str] = None) -> None:
        """Notify recipient about a shared post."""
        try:
            await ws_handlers.emit_share_notification(share_id, post_id, sharer_id, recipient_id, message)
            logger.info(f"Notified user {recipient_id} about shared post {post_id}")
        except Exception as e:
            logger.error(f"Failed to notify share:notification event: {e}")

    @staticmethod
    async def log_activity(db: Session, group_id: str, action: str, resource_id: str,
                          resource_type: str, actor_id: str, message: Optional[str] = None) -> None:
        """Log and broadcast activity to a group."""
        try:
            await ws_handlers.emit_activity_log(group_id, action, resource_id, resource_type, actor_id, message)
            logger.debug(f"Logged activity '{action}' for group {group_id}")
        except Exception as e:
            logger.error(f"Failed to emit activity:log event: {e}")

    @staticmethod
    async def notify_user_online(db: Session, group_id: str, user_id: str, online_users: list) -> None:
        """Broadcast user online event."""
        try:
            await ws_handlers.broadcast_user_online(group_id, user_id, online_users)
            logger.debug(f"Broadcast user {user_id} online in group {group_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast user:online event: {e}")

    @staticmethod
    async def notify_user_offline(db: Session, group_id: str, user_id: str, remaining_users: list) -> None:
        """Broadcast user offline event."""
        try:
            await ws_handlers.broadcast_user_offline(group_id, user_id, remaining_users)
            logger.debug(f"Broadcast user {user_id} offline in group {group_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast user:offline event: {e}")
