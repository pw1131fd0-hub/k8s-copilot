"""Repository layer for querying DiagnoseHistory records from the database."""
from sqlalchemy.orm import Session
from typing import List
from backend.models.orm_models import DiagnoseHistory
from backend.models.schemas import DiagnoseHistoryRecord


class DiagnoseRepository:
    """Data access layer for DiagnoseHistory persistence and retrieval."""

    def get_history(self, db: Session, limit: int = 50) -> List[DiagnoseHistoryRecord]:
        """Return the most recent diagnosis records, ordered by creation time descending."""
        records = db.query(DiagnoseHistory).order_by(DiagnoseHistory.created_at.desc()).limit(limit).all()
        return [DiagnoseHistoryRecord.model_validate(r) for r in records]

    def get_by_pod(self, db: Session, pod_name: str) -> List[DiagnoseHistoryRecord]:
        """Return all diagnosis records for a specific pod, newest first."""
        records = (db.query(DiagnoseHistory)
                   .filter(DiagnoseHistory.pod_name == pod_name)
                   .order_by(DiagnoseHistory.created_at.desc())
                   .all())
        return [DiagnoseHistoryRecord.model_validate(r) for r in records]
