from datetime import UTC, datetime, timedelta
from sqlalchemy.orm import Session

from app.models.log import Log


class LogRepository:
    RETENTION_DAYS = 90

    def __init__(self, db: Session):
        self.db = db

    def _prune_expired(self) -> None:
        cutoff = datetime.now(UTC) - timedelta(days=self.RETENTION_DAYS)
        self.db.query(Log).filter(Log.timestamp < cutoff).delete(synchronize_session=False)

    def create(self, action: str, user_id: int | None = None, context: str | None = None) -> Log:
        self._prune_expired()
        log_row = Log(user_id=user_id, action=action, context=context)
        self.db.add(log_row)
        self.db.commit()
        self.db.refresh(log_row)
        return log_row

    def list_latest(self, limit: int = 100) -> list[Log]:
        return self.db.query(Log).order_by(Log.timestamp.desc()).limit(limit).all()
