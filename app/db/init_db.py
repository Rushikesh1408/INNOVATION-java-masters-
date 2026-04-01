from app.db.base import Base
from app.db.session import engine
from app.models import admin, exam, question, response, result, session, user  # noqa: F401


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
