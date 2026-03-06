from sqlalchemy.orm import Session
from typing import List
from backend.models.orm_models import DiagnoseHistory
from backend.models.schemas import DiagnoseHistoryRecord


class DiagnoseRepository:
    def get_history(self, db: Session, limit: int = 50) -> List[DiagnoseHistoryRecord]:
        records = db.query(DiagnoseHistory).order_by(DiagnoseHistory.created_at.desc()).limit(limit).all()
        return [DiagnoseHistoryRecord.model_validate(r) for r in records]

    def get_by_pod(self, db: Session, pod_name: str) -> List[DiagnoseHistoryRecord]:
        records = (db.query(DiagnoseHistory)
                   .filter(DiagnoseHistory.pod_name == pod_name)
                   .order_by(DiagnoseHistory.created_at.desc())
                   .all())
        return [DiagnoseHistoryRecord.model_validate(r) for r in records]
