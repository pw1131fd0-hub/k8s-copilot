"""WebSocket event definitions for ClawBook real-time features."""
from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel


class EventType(str, Enum):
    """WebSocket event types."""

    # Comment events
    COMMENT_NEW = "comment:new"
    COMMENT_UPDATED = "comment:updated"
    COMMENT_DELETED = "comment:deleted"
    COMMENT_RESOLVED = "comment:resolved"

    # User presence events
    USER_ONLINE = "user:online"
    USER_OFFLINE = "user:offline"

    # Share notifications
    SHARE_NOTIFICATION = "share:notification"

    # Activity log events
    ACTIVITY_LOG = "activity:log"

    # System events
    CONNECTION_ACK = "connection:ack"
    PING = "ping"
    PONG = "pong"


class BaseEvent(BaseModel):
    """Base model for all WebSocket events."""

    event_type: EventType
    timestamp: datetime = None
    user_id: str = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class CommentEventPayload(BaseEvent):
    """Payload for comment-related events."""

    event_type: EventType
    post_id: str
    comment_id: str
    author_id: str
    content: str
    status: Optional[str] = None  # For resolved comments
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class UserPresencePayload(BaseEvent):
    """Payload for user presence events."""

    event_type: EventType
    user_id: str
    group_id: Optional[str] = None
    timestamp: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    class Config:
        use_enum_values = True


class ShareNotificationPayload(BaseEvent):
    """Payload for share notification events."""

    event_type: EventType
    share_id: str
    post_id: str
    sharer_id: str
    recipient_id: str
    message: Optional[str] = None
    timestamp: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    class Config:
        use_enum_values = True


class ActivityLogPayload(BaseEvent):
    """Payload for activity log events."""

    event_type: EventType
    action: str  # e.g., "post_created", "comment_added", "group_joined"
    resource_id: str
    resource_type: str  # e.g., "post", "comment", "group"
    actor_id: str
    message: Optional[str] = None
    timestamp: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    class Config:
        use_enum_values = True


class ConnectionAckPayload(BaseEvent):
    """Payload for connection acknowledgment."""

    event_type: EventType = EventType.CONNECTION_ACK
    user_id: str
    timestamp: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    class Config:
        use_enum_values = True


class PingPongPayload(BaseEvent):
    """Payload for ping/pong events."""

    event_type: EventType
    timestamp: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    class Config:
        use_enum_values = True


def create_event(event_type: EventType, **kwargs) -> dict:
    """Factory function to create event payloads."""
    payload_map = {
        EventType.COMMENT_NEW: CommentEventPayload,
        EventType.COMMENT_UPDATED: CommentEventPayload,
        EventType.COMMENT_DELETED: CommentEventPayload,
        EventType.COMMENT_RESOLVED: CommentEventPayload,
        EventType.USER_ONLINE: UserPresencePayload,
        EventType.USER_OFFLINE: UserPresencePayload,
        EventType.SHARE_NOTIFICATION: ShareNotificationPayload,
        EventType.ACTIVITY_LOG: ActivityLogPayload,
        EventType.CONNECTION_ACK: ConnectionAckPayload,
        EventType.PING: PingPongPayload,
        EventType.PONG: PingPongPayload,
    }

    payload_class = payload_map.get(event_type)
    if not payload_class:
        raise ValueError(f"Unknown event type: {event_type}")

    payload = payload_class(event_type=event_type, **kwargs)
    return payload.dict()
