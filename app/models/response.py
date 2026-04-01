import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Response(Base):
    __tablename__ = "responses"
    __table_args__ = (
        Index(
            "ix_responses_session_question",
            "session_id",
            "question_id",
            unique=True,
        ),
        CheckConstraint(
            "selected_option BETWEEN 1 AND 4",
            name="ck_responses_selected_option_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected_option: Mapped[int] = mapped_column(Integer, nullable=False)
    time_taken: Mapped[int] = mapped_column(Integer, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    session = relationship("Session", back_populates="responses")
    question = relationship("Question", back_populates="responses")
