"""SQLAlchemy ORM models for Lobster K8s Copilot persistent storage."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Index, String, Text, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Project(Base):  # pylint: disable=too-few-public-methods
    """ORM model representing a monitored Kubernetes project/cluster context."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    k8s_context: Mapped[str] = mapped_column(String, nullable=False)


class DiagnoseHistory(Base):  # pylint: disable=too-few-public-methods
    """ORM model storing AI diagnosis results for auditing and history lookup."""

    __tablename__ = "diagnose_history"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pod_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String, nullable=False, default="default")
    error_type: Mapped[str] = mapped_column(String, nullable=True)
    ai_analysis: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    __table_args__ = (
        Index("ix_diagnose_history_pod_namespace", "pod_name", "namespace"),
    )


# ============================================================================
# ClawBook AI 日誌系統 Models
# ============================================================================


class ClawBookPost(Base):
    """ORM model for ClawBook diary posts."""

    __tablename__ = "clawbook_posts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mood: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "😊 好心情"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False, default="小龍蝦")
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    sentiment_score: Mapped[float] = mapped_column(Integer, nullable=True)  # 1-10 sentiment score
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    comments: Mapped[list["ClawBookComment"]] = relationship(
        "ClawBookComment", back_populates="post", cascade="all, delete-orphan"
    )
    likes: Mapped[list["ClawBookLike"]] = relationship(
        "ClawBookLike", back_populates="post", cascade="all, delete-orphan"
    )
    images: Mapped[list["ClawBookImage"]] = relationship(
        "ClawBookImage", back_populates="post", cascade="all, delete-orphan"
    )


class ClawBookComment(Base):
    """ORM model for comments on ClawBook posts."""

    __tablename__ = "clawbook_comments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(String, ForeignKey("clawbook_posts.id"), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String, nullable=False, default="我")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    post: Mapped["ClawBookPost"] = relationship("ClawBookPost", back_populates="comments")


class ClawBookLike(Base):
    """ORM model for likes on ClawBook posts."""

    __tablename__ = "clawbook_likes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(String, ForeignKey("clawbook_posts.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, default="default_user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    post: Mapped["ClawBookPost"] = relationship("ClawBookPost", back_populates="likes")

    __table_args__ = (
        Index("ix_clawbook_likes_post_user", "post_id", "user_id", unique=True),
    )


class ClawBookImage(Base):
    """ORM model for images attached to ClawBook posts."""

    __tablename__ = "clawbook_images"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(String, ForeignKey("clawbook_posts.id"), nullable=False, index=True)
    image_data: Mapped[str] = mapped_column(Text, nullable=False)  # Base64 encoded image
    filename: Mapped[str] = mapped_column(String, nullable=True)
    content_type: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    post: Mapped["ClawBookPost"] = relationship("ClawBookPost", back_populates="images")


class SlackConfig(Base):
    """ORM model for Slack webhook configuration."""

    __tablename__ = "slack_configs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_url: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_rules: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    summary_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    summary_time: Mapped[str] = mapped_column(String, default="09:00")  # HH:MM format
    high_mood_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    high_mood_threshold: Mapped[int] = mapped_column(Integer, default=4)
    milestone_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    include_full_content: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class AIDecisionPath(Base):
    """ORM model for AI decision path visualization - v1.4 feature."""

    __tablename__ = "ai_decision_paths"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(
        String, ForeignKey("clawbook_posts.id"), nullable=False, unique=True, index=True
    )

    # Decision path data stored as JSON
    reasoning_steps: Mapped[dict] = mapped_column(JSON, nullable=False)  # List[ReasoningStep]
    candidates: Mapped[dict] = mapped_column(JSON, nullable=False)  # List[DecisionCandidate]
    final_decision: Mapped[dict] = mapped_column(JSON, nullable=False)  # Final decision with confidence
    key_factors: Mapped[dict] = mapped_column(JSON, nullable=False)  # List[KeyFactor]

    # Metadata
    model_used: Mapped[str] = mapped_column(String, nullable=True)  # e.g., "ollama/llama2"
    decision_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)  # Milliseconds taken

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    post: Mapped["ClawBookPost"] = relationship("ClawBookPost")


# ============================================================================
# ClawBook v1.6 Collaboration Features - Models
# ============================================================================


class User(Base):
    """ORM model for user management - v1.6 feature."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    shares: Mapped[list["Share"]] = relationship("Share", back_populates="owner", foreign_keys="Share.owner_id")
    shares_with_me: Mapped[list["Share"]] = relationship(
        "Share", back_populates="shared_with_user", foreign_keys="Share.shared_with_id"
    )
    groups: Mapped[list["Group"]] = relationship(
        "Group", secondary="group_members", back_populates="members"
    )
    comments: Mapped[list["CollaborationComment"]] = relationship(
        "CollaborationComment", back_populates="author"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="actor"
    )


class Share(Base):
    """ORM model for post sharing - v1.6 feature."""

    __tablename__ = "shares"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(String, ForeignKey("clawbook_posts.id"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    shared_with_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=True, index=True)
    group_id: Mapped[str] = mapped_column(String, ForeignKey("groups.id"), nullable=True, index=True)

    permission: Mapped[str] = mapped_column(String(20), default="read")  # "read", "comment", "edit"
    status: Mapped[str] = mapped_column(String(20), default="pending")  # "pending", "accepted", "rejected"

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    accepted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    post: Mapped["ClawBookPost"] = relationship("ClawBookPost")
    owner: Mapped["User"] = relationship("User", back_populates="shares", foreign_keys=[owner_id])
    shared_with_user: Mapped["User"] = relationship(
        "User", back_populates="shares_with_me", foreign_keys=[shared_with_id]
    )
    group: Mapped["Group"] = relationship("Group", back_populates="shares")

    __table_args__ = (
        Index("ix_shares_post_owner", "post_id", "owner_id"),
        Index("ix_shares_shared_with", "shared_with_id"),
        Index("ix_shares_group", "group_id"),
    )


class Group(Base):
    """ORM model for collaboration groups - v1.6 feature."""

    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    creator_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    visibility: Mapped[str] = mapped_column(String(20), default="private")  # "private", "team", "public"
    icon: Mapped[str] = mapped_column(String(100), nullable=True)  # emoji or icon name

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    members: Mapped[list["User"]] = relationship(
        "User", secondary="group_members", back_populates="groups"
    )
    shares: Mapped[list["Share"]] = relationship("Share", back_populates="group")
    activity_logs: Mapped[list["ActivityLog"]] = relationship("ActivityLog", back_populates="group")


class GroupMember(Base):
    """ORM model for group membership - v1.6 feature."""

    __tablename__ = "group_members"

    group_id: Mapped[str] = mapped_column(String, ForeignKey("groups.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)

    role: Mapped[str] = mapped_column(String(20), default="member")  # "admin", "member"
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_group_members", "group_id", "user_id"),
    )


class CollaborationComment(Base):
    """ORM model for collaboration comments - v1.6 feature."""

    __tablename__ = "collaboration_comments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(String, ForeignKey("clawbook_posts.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_suggestion: Mapped[bool] = mapped_column(Boolean, default=False)  # "建議編輯" vs "評論"
    status: Mapped[str] = mapped_column(String(20), default="open")  # "open", "accepted", "rejected", "resolved"

    parent_id: Mapped[str] = mapped_column(String, ForeignKey("collaboration_comments.id"), nullable=True)  # 回覆關係

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    post: Mapped["ClawBookPost"] = relationship("ClawBookPost")
    author: Mapped["User"] = relationship("User", back_populates="comments")
    parent: Mapped["CollaborationComment"] = relationship(
        "CollaborationComment", remote_side=[id], backref="replies"
    )

    __table_args__ = (
        Index("ix_collaboration_comments_post", "post_id"),
        Index("ix_collaboration_comments_user", "user_id"),
    )


class ActivityLog(Base):
    """ORM model for collaboration activity logging - v1.6 feature."""

    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(String, ForeignKey("groups.id"), nullable=True, index=True)
    actor_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    action: Mapped[str] = mapped_column(String(50), nullable=False)  # "share_post", "comment", "accept_share", "create_group"
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "post", "comment", "user"
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)

    activity_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Additional context

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    group: Mapped["Group"] = relationship("Group", back_populates="activity_logs")
    actor: Mapped["User"] = relationship("User", back_populates="activity_logs")

    __table_args__ = (
        Index("ix_activity_group", "group_id", "created_at"),
    )

    @staticmethod
    def create_log(
        db,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: str,
        group_id: str = None,
        metadata: dict = None,
    ) -> "ActivityLog":
        """Create an activity log entry."""
        log = ActivityLog(
            id=str(uuid.uuid4()),
            group_id=group_id,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            activity_data=metadata,
        )
        db.add(log)
        db.commit()
        return log


class PsychologyProfile(Base):  # pylint: disable=too-few-public-methods
    """ORM model for AI personality profile assessment - v1.7 feature."""

    __tablename__ = "psychology_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Trait scores (stored as JSON: {"curiosity": 7, "emotional_maturity": 6, ...})
    traits_data: Mapped[str] = mapped_column(Text, nullable=False)

    # Personality archetype (e.g., "The Learner", "The Helper")
    archetype: Mapped[str] = mapped_column(String, nullable=False)

    # Confidence score (0-100%)
    confidence_score: Mapped[float] = mapped_column(Integer, nullable=False)

    # Insights (stored as JSON array)
    insights_data: Mapped[str] = mapped_column(Text, nullable=True)

    # Number of posts analyzed
    posts_analyzed_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_psychology_profiles_created_at", "created_at"),
    )
