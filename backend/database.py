"""Database engine and session management for Lobster K8s Copilot."""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lobster.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=not DATABASE_URL.startswith("sqlite"),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # pylint: disable=invalid-name


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """SQLAlchemy declarative base shared by all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, closing it when the request completes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables from SQLAlchemy ORM models."""
    # pylint: disable=import-outside-toplevel,unused-import
    from backend.models.orm_models import (  # noqa: F401 – side-effect: table registration
        Project,
        DiagnoseHistory,
        ClawBookPost,
        ClawBookComment,
        ClawBookLike,
        ClawBookImage,
        SlackConfig,
        AIDecisionPath,
    )
    Base.metadata.create_all(bind=engine)
