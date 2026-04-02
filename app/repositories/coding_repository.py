from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.coding_problem import CodingProblem, Submission


class CodingProblemRepository:
    """Repository for coding problems"""

    UPDATABLE_FIELDS = {
        "title",
        "description",
        "difficulty",
        "time_limit_seconds",
        "memory_limit_mb",
        "starter_code",
        "visible_test_cases",
        "hidden_test_cases",
    }

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        exam_id: int,
        title: str,
        description: str,
        difficulty: str,
        time_limit_seconds: int,
        memory_limit_mb: int,
        starter_code: str | None,
        visible_test_cases: list,
        hidden_test_cases: list,
    ) -> CodingProblem:
        """Create a new coding problem"""
        problem = CodingProblem(
            exam_id=exam_id,
            title=title,
            description=description,
            difficulty=difficulty,
            time_limit_seconds=time_limit_seconds,
            memory_limit_mb=memory_limit_mb,
            starter_code=starter_code,
            visible_test_cases=visible_test_cases,
            hidden_test_cases=hidden_test_cases,
        )
        self.db.add(problem)
        self.db.commit()
        self.db.refresh(problem)
        return problem

    def get_by_id(self, problem_id: int) -> CodingProblem | None:
        """Get problem by ID"""
        return self.db.query(CodingProblem).filter(CodingProblem.id == problem_id).first()

    def get_by_exam(self, exam_id: int) -> list[CodingProblem]:
        """Get all problems for an exam"""
        return self.db.query(CodingProblem).filter(CodingProblem.exam_id == exam_id).all()

    def update(self, problem_id: int, **kwargs) -> CodingProblem | None:
        """Update a coding problem"""
        problem = self.get_by_id(problem_id)
        if not problem:
            return None
        for key, value in kwargs.items():
            if key in self.UPDATABLE_FIELDS:
                setattr(problem, key, value)
        self.db.commit()
        self.db.refresh(problem)
        return problem

    def delete(self, problem_id: int) -> bool:
        """Delete a coding problem"""
        problem = self.get_by_id(problem_id)
        if not problem:
            return False
        self.db.delete(problem)
        self.db.commit()
        return True


class SubmissionRepository:
    """Repository for code submissions"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        problem_id: int,
        code: str,
        language: str = "java",
    ) -> Submission:
        """Create a new submission"""
        submission = Submission(
            user_id=user_id,
            problem_id=problem_id,
            code=code,
            language=language,
            status="pending",
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def get_by_id(self, submission_id: int) -> Submission | None:
        """Get submission by ID"""
        return self.db.query(Submission).filter(Submission.id == submission_id).first()

    def get_by_user_problem(self, user_id: int, problem_id: int) -> list[Submission]:
        """Get all submissions by user for a problem"""
        return (
            self.db.query(Submission)
            .filter(Submission.user_id == user_id, Submission.problem_id == problem_id)
            .order_by(Submission.submitted_at.desc())
            .all()
        )

    def get_latest_by_user_problem(self, user_id: int, problem_id: int) -> Submission | None:
        """Get latest submission from user for problem"""
        return (
            self.db.query(Submission)
            .filter(Submission.user_id == user_id, Submission.problem_id == problem_id)
            .order_by(Submission.submitted_at.desc())
            .first()
        )

    def get_best_by_user_problem(self, user_id: int, problem_id: int) -> Submission | None:
        """Get highest-scoring submission from user for problem.

        Falls back to most recent among ties.
        """
        return (
            self.db.query(Submission)
            .filter(
                Submission.user_id == user_id,
                Submission.problem_id == problem_id,
                Submission.score.is_not(None),
            )
            .order_by(Submission.score.desc(), Submission.submitted_at.desc())
            .first()
        )

    def get_by_user_exam(self, user_id: int, exam_id: int) -> list[Submission]:
        """Get all submissions by user for exam (across all problems in exam)"""
        return (
            self.db.query(Submission)
            .join(CodingProblem)
            .filter(
                Submission.user_id == user_id,
                CodingProblem.exam_id == exam_id
            )
            .order_by(Submission.submitted_at.desc())
            .all()
        )

    def update_evaluation_result(
        self,
        submission_id: int,
        status: str,
        passed_visible: int,
        passed_hidden: int,
        total_visible: int,
        total_hidden: int,
        execution_time_ms: float,
        score: int,
        test_case_results: list,
        error_message: str = "",
    ) -> Submission | None:
        """Update submission with evaluation results"""
        submission = self.get_by_id(submission_id)
        if not submission:
            return None

        submission_record: Any = submission
        submission_record.status = status
        submission_record.passed_visible = passed_visible
        submission_record.passed_hidden = passed_hidden
        submission_record.total_visible = total_visible
        submission_record.total_hidden = total_hidden
        submission_record.execution_time_ms = int(execution_time_ms)
        submission_record.score = score
        submission_record.test_case_results = test_case_results
        submission_record.error_message = error_message
        submission_record.evaluated_at = datetime.now(UTC).isoformat()

        self.db.commit()
        self.db.refresh(submission)
        return submission

    def get_best_score(self, user_id: int, problem_id: int) -> int:
        """Get best score from user for problem"""
        best_score = (
            self.db.query(func.coalesce(func.max(Submission.score), 0))
            .filter(Submission.user_id == user_id, Submission.problem_id == problem_id)
            .scalar()
        )
        return int(best_score or 0)

    def get_accepted_count(self, user_id: int, exam_id: int) -> int:
        """Count fully accepted submissions by user for exam"""
        return (
            self.db.query(Submission)
            .join(CodingProblem)
            .filter(
                Submission.user_id == user_id,
                CodingProblem.exam_id == exam_id,
                Submission.status == "accepted"
            )
            .count()
        )
