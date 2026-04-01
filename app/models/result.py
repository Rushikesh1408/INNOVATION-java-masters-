from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        Index(
            "ix_results_exam_accuracy_time",
            "exam_id",
            "accuracy",
            "total_time",
        ),
        Index("ux_results_user_exam", "user_id", "exam_id", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id"),
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    total_time: Mapped[int] = mapped_column(Integer, nullable=False)
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="results")
    exam = relationship("Exam", back_populates="results")
