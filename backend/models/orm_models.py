"""SQLAlchemy ORM models for Lobster K8s Copilot persistent storage."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Index, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
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
