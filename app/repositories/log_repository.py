from sqlalchemy.orm import Session

from app.models.log import Log


class LogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, action: str, user_id: int | None = None, context: str | None = None) -> Log:
        log_row = Log(user_id=user_id, action=action, context=context)
        self.db.add(log_row)
        self.db.commit()
        self.db.refresh(log_row)
        return log_row

    def list_latest(self, limit: int = 100) -> list[Log]:
        return self.db.query(Log).order_by(Log.timestamp.desc()).limit(limit).all()
