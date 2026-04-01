from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(
            "correct_option BETWEEN 1 AND 4",
            name="ck_questions_correct_option_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    option_1: Mapped[str] = mapped_column(String(500), nullable=False)
    option_2: Mapped[str] = mapped_column(String(500), nullable=False)
    option_3: Mapped[str] = mapped_column(String(500), nullable=False)
    option_4: Mapped[str] = mapped_column(String(500), nullable=False)
    correct_option: Mapped[int] = mapped_column(Integer, nullable=False)

    exam = relationship("Exam", back_populates="questions")
    responses = relationship("Response", back_populates="question")
