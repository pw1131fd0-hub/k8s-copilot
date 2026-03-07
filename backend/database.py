"""Database engine and session management for Lobster K8s Copilot."""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lobster.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base shared by all ORM models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, closing it when the request completes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables from SQLAlchemy ORM models."""
    from backend.models.orm_models import Project, DiagnoseHistory  # noqa: F401
    Base.metadata.create_all(bind=engine)
