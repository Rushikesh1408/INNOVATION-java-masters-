from datetime import UTC, datetime

from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class CodingProblem(Base):
    """Coding problem for competitive round"""
    __tablename__ = "coding_problems"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    time_limit_seconds = Column(Integer, default=2)  # seconds
    memory_limit_mb = Column(Integer, default=256)  # MB
    starter_code = Column(Text, nullable=True)  # Java template code
    visible_test_cases = Column(JSON, default=list)  # [{"input": "...", "expected": "..."}]
    hidden_test_cases = Column(JSON, default=list)  # [{"input": "...", "expected": "..."}]
    created_at = Column(String, default=lambda: datetime.now(UTC).isoformat())

    # Relationships
    exam = relationship("Exam", back_populates="coding_problems")
    submissions = relationship("Submission", back_populates="problem", cascade="all, delete-orphan")


class Submission(Base):
    """Code submission to a coding problem"""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("coding_problems.id"), nullable=False)
    code = Column(Text, nullable=False)  # Java source code
    language = Column(String(20), default="java")
    status = Column(String(50), default="pending")  # pending, compiling, running, accepted, wrong_answer, tle, mle, ce
    passed_visible = Column(Integer, default=0)
    passed_hidden = Column(Integer, default=0)
    total_visible = Column(Integer, default=0)
    total_hidden = Column(Integer, default=0)
    execution_time_ms = Column(Integer, nullable=True)
    memory_used_mb = Column(Integer, nullable=True)
    score = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)
    test_case_results = Column(JSON, default=list)  # [{"test": 1, "passed": True, "output": "...", "expected": "..."}]
    submitted_at = Column(String, default=lambda: datetime.now(UTC).isoformat())
    evaluated_at = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="submissions")
    problem = relationship("CodingProblem", back_populates="submissions")
