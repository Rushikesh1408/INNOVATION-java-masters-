from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.java_executor import JavaExecutor
from app.models.coding_problem import CodingProblem, Submission
from app.models.user import User
from app.repositories.coding_repository import (
    CodingProblemRepository,
    SubmissionRepository,
)
from app.services.log_service import LogService


class CodingService:
    """Service for handling coding submissions and evaluation"""

    MAX_LEADERBOARD_LIMIT = 100

    def __init__(self, db: Session):
        self.db = db
        self.problem_repo = CodingProblemRepository(db)
        self.submission_repo = SubmissionRepository(db)
        self.log_service = LogService(db)

    def submit_code(self, user_id: int, problem_id: int, code: str) -> dict:
        """
        Handle code submission.
        Returns submission ID and initial response.
        """
        problem = self.problem_repo.get_by_id(problem_id)
        if not problem:
            raise ValueError(f"Problem {problem_id} not found")

        # Create submission record
        submission = self.submission_repo.create(
            user_id=user_id,
            problem_id=problem_id,
            code=code,
            language="java"
        )

        # Log submission
        self.log_service.write(
            user_id=user_id,
            action="CODE_SUBMISSION",
            context=f"problem_id={problem_id}, submission_id={submission.id}"
        )

        return {
            "submission_id": submission.id,
            "status": "submitted",
            "message": "Code submitted for evaluation"
        }

    def evaluate_submission(self, submission_id: int) -> dict:
        """
        Evaluate a code submission against test cases.
        This is typically called async via Celery.
        """
        submission = self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")
        submission_record: Any = submission

        problem = self.problem_repo.get_by_id(int(submission_record.problem_id))
        if not problem:
            raise ValueError(f"Problem {submission_record.problem_id} not found")
        problem_record: Any = problem

        # Initialize executor
        executor = JavaExecutor(
            timeout_seconds=int(problem_record.time_limit_seconds),
            memory_limit_mb=int(problem_record.memory_limit_mb)
        )

        try:
            # Evaluate all tests
            eval_result = executor.evaluate_all_test_cases(
                code=submission_record.code,
                visible_tests=problem_record.visible_test_cases,
                hidden_tests=problem_record.hidden_test_cases
            )

            # Calculate score
            score = self._calculate_score(eval_result, int(problem_record.time_limit_seconds))

            # Update submission with results
            updated = self.submission_repo.update_evaluation_result(
                submission_id=submission_id,
                status=eval_result["status"],
                passed_visible=eval_result["passed_visible"],
                passed_hidden=eval_result["passed_hidden"],
                total_visible=eval_result["total_visible"],
                total_hidden=eval_result["total_hidden"],
                execution_time_ms=eval_result.get("max_time_ms", 0),
                score=score,
                test_case_results=eval_result.get("visible_results", []),
                error_message=eval_result.get("error", "")
            )

            # Log evaluation
            self.log_service.write(
                user_id=int(submission_record.user_id),
                action="CODE_EVALUATION",
                context=f"problem_id={problem_record.id}, submission_id={submission_id}, status={eval_result['status']}, score={score}"
            )

            return {
                "submission_id": submission_id,
                "status": eval_result["status"],
                "score": score,
                "passed_visible": eval_result["passed_visible"],
                "passed_hidden": eval_result["passed_hidden"],
                "total_visible": eval_result["total_visible"],
                "total_hidden": eval_result["total_hidden"],
                "execution_time_ms": eval_result.get("max_time_ms", 0),
                "error": eval_result.get("error", "")
            }

        finally:
            executor.cleanup()

    def _calculate_score(self, eval_result: dict, time_limit_seconds: int) -> int:
        """
        Calculate score based on evaluation results.
        
        Scoring breakdown:
        - 70% correctness (all tests passed)
        - 20% time efficiency (execution time < 50% of limit)
        - 10% code quality (optional - always 10 for now)
        """
        if eval_result["status"] == "compile_error":
            return 0

        if eval_result["status"] == "timeout":
            return int(eval_result["passed_visible"] * 10 + eval_result["passed_hidden"] * 10)

        # If not all visible tests passed, 0 score
        if eval_result["passed_visible"] < eval_result["total_visible"]:
            return 0

        # Correctness: 70 points
        correctness_ratio = (
            eval_result["passed_hidden"] / eval_result["total_hidden"]
            if eval_result["total_hidden"] > 0
            else 0
        )
        correctness_score = correctness_ratio * 70

        # Time efficiency: 20 points
        safe_limit_seconds = max(float(time_limit_seconds), 0.001)
        actual_time_s = eval_result.get("max_time_ms", 0) / 1000
        fraction = actual_time_s / safe_limit_seconds
        time_score = 20 if fraction < 0.5 else max(0, 20 * (1 - fraction))

        # Code quality: 10 points (always awarded for now)
        quality_score = 10

        total_score = int(correctness_score + time_score + quality_score)
        return min(100, max(0, total_score))

    def get_best_submission(self, user_id: int, problem_id: int) -> dict | None:
        """Get the best submission from user for a problem"""
        submissions = self.submission_repo.get_by_user_problem(user_id, problem_id)
        if not submissions:
            return None

        scored_submissions = [s for s in submissions if s.score is not None]
        if not scored_submissions:
            return None

        best = max(scored_submissions, key=lambda x: x.score)
        return self._submission_to_dict(best)

    def get_coding_leaderboard(self, exam_id: int, limit: int = 50) -> list[dict]:
        """
        Get coding round leaderboard for an exam.
        Ranks users by total score across all problems.
        """
        safe_limit = max(1, min(limit, self.MAX_LEADERBOARD_LIMIT))

        # Keep only each user's best score per problem, then aggregate by user.
        best_scores = (
            self.db.query(
                Submission.user_id.label("user_id"),
                Submission.problem_id.label("problem_id"),
                func.max(Submission.score).label("best_score"),
            )
            .join(CodingProblem, Submission.problem_id == CodingProblem.id)
            .filter(CodingProblem.exam_id == exam_id, Submission.score.is_not(None))
            .group_by(Submission.user_id, Submission.problem_id)
            .subquery()
        )

        users_data = (
            self.db.query(
                best_scores.c.user_id,
                func.sum(best_scores.c.best_score).label("total_score"),
                func.count(best_scores.c.problem_id).label("problems_attempted"),
            )
            .group_by(best_scores.c.user_id)
            .order_by(func.sum(best_scores.c.best_score).desc())
            .limit(safe_limit)
            .all()
        )

        result = []
        for rank, (user_id, total_score, problems_attempted) in enumerate(users_data, 1):
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                result.append({
                    "rank": rank,
                    "user_id": user_id,
                    "name": user.name,
                    "total_score": int(total_score or 0),
                    "submissions": int(problems_attempted or 0),
                })

        return result

    def _submission_to_dict(self, submission) -> dict:
        """Convert submission model to dict"""
        return {
            "id": submission.id,
            "user_id": submission.user_id,
            "problem_id": submission.problem_id,
            "status": submission.status,
            "score": submission.score,
            "passed_visible": submission.passed_visible,
            "passed_hidden": submission.passed_hidden,
            "total_visible": submission.total_visible,
            "total_hidden": submission.total_hidden,
            "execution_time_ms": submission.execution_time_ms,
            "submitted_at": submission.submitted_at,
            "evaluated_at": submission.evaluated_at,
        }
