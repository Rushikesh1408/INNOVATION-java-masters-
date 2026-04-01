from app.db.base import Base
from app.db.session import engine
from app.models import admin, exam, log, question, response, result, session, user, coding_problem  # noqa: F401


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
