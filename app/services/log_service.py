from sqlalchemy.orm import Session

from app.repositories.log_repository import LogRepository


class LogService:
    def __init__(self, db: Session):
        self.repo = LogRepository(db)

    def write(self, action: str, user_id: int | None = None, context: str | None = None):
        return self.repo.create(action=action, user_id=user_id, context=context)

    def list_latest(self, limit: int = 100):
        return self.repo.list_latest(limit=limit)
