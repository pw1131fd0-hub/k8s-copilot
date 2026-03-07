"""Repository layer for querying DiagnoseHistory records from the database."""
from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.models.orm_models import DiagnoseHistory
from backend.models.schemas import DiagnoseHistoryRecord


class DiagnoseRepository:
    """Data access layer for DiagnoseHistory persistence and retrieval."""

    def get_history(
        self,
        db: Session,
        limit: int = 50,
        search: str | None = None,
        namespace: str | None = None,
        error_type: str | None = None,
    ) -> list[DiagnoseHistoryRecord]:
        """Return the most recent diagnosis records, with optional filters."""
        query = db.query(DiagnoseHistory)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    DiagnoseHistory.pod_name.ilike(search_pattern),
                    DiagnoseHistory.ai_analysis.ilike(search_pattern),
                )
            )

        if namespace:
            query = query.filter(DiagnoseHistory.namespace == namespace)

        if error_type:
            query = query.filter(DiagnoseHistory.error_type == error_type)

        records = query.order_by(DiagnoseHistory.created_at.desc()).limit(limit).all()
        return [DiagnoseHistoryRecord.model_validate(r) for r in records]

    def get_by_pod(self, db: Session, pod_name: str) -> list[DiagnoseHistoryRecord]:
        """Return all diagnosis records for a specific pod, newest first."""
        records = (db.query(DiagnoseHistory)
                   .filter(DiagnoseHistory.pod_name == pod_name)
                   .order_by(DiagnoseHistory.created_at.desc())
                   .all())
        return [DiagnoseHistoryRecord.model_validate(r) for r in records]
