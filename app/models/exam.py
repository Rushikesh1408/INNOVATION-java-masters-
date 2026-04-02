from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    time_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    positive_mark: Mapped[float] = mapped_column(Float, default=1.0)
    negative_mark: Mapped[float] = mapped_column(Float, default=0.0)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("admins.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    admin = relationship("Admin", back_populates="exams")
    questions = relationship(
        "Question",
        back_populates="exam",
        cascade="all, delete-orphan",
    )
    coding_problems = relationship(
        "CodingProblem",
        back_populates="exam",
        cascade="all, delete-orphan",
    )
    sessions = relationship("Session", back_populates="exam")
    results = relationship("Result", back_populates="exam")
