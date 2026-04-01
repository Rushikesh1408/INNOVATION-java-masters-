import hashlib
import re
from sqlalchemy.orm import Session

from app.repositories.log_repository import LogRepository


class LogService:
    def __init__(self, db: Session):
        self.repo = LogRepository(db)

    @staticmethod
    def _sanitize_context(context: str | None) -> str | None:
        if context is None:
            return None

        cleaned = context.strip()
        cleaned = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted-email]", cleaned)
        cleaned = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b", "[redacted-phone]", cleaned)
        cleaned = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[redacted-ssn]", cleaned)
        if len(cleaned) > 512:
            cleaned = f"{cleaned[:512]}..."
        return cleaned

    @staticmethod
    def _pseudonymize_user_id(user_id: int | None) -> str | None:
        if user_id is None:
            return None
        return hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()[:16]

    def write(self, action: str, user_id: int | None = None, context: str | None = None):
        sanitized_context = self._sanitize_context(context)
        pseudonymous_id = self._pseudonymize_user_id(user_id)
        if pseudonymous_id:
            prefix = f"actor={pseudonymous_id}"
            sanitized_context = f"{prefix} {sanitized_context}" if sanitized_context else prefix
        return self.repo.create(action=action, user_id=None, context=sanitized_context)

    def list_latest(self, limit: int = 100):
        return self.repo.list_latest(limit=limit)
