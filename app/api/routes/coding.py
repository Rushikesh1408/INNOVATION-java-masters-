import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import bearer, get_current_admin
from app.core.security import decode_token
from app.db.session import get_db
from app.models.admin import Admin
from app.models.exam import Exam
from app.models.user import User
from app.repositories.coding_repository import (
    CodingProblemRepository,
    SubmissionRepository,
)
from app.services.coding_service import CodingService

router = APIRouter(prefix="/coding", tags=["coding"])
logger = logging.getLogger(__name__)
MAX_LEADERBOARD_LIMIT = 100


# Schemas
class TestCaseSchema(BaseModel):
    input: str
    expected: str


class CreateCodingProblemRequest(BaseModel):
    title: str
    description: str
    difficulty: str = "medium"
    time_limit_seconds: int = 2
    memory_limit_mb: int = 256
    starter_code: Optional[str] = None
    visible_test_cases: list[TestCaseSchema]
    hidden_test_cases: list[TestCaseSchema]


class CodeSubmissionRequest(BaseModel):
    code: str = Field(..., min_length=1)


class CodingProblemResponse(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    time_limit_seconds: int
    memory_limit_mb: int
    starter_code: Optional[str]
    visible_test_cases: list

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    problem_id: int
    status: str
    score: int
    passed_visible: int
    passed_hidden: int
    total_visible: int
    total_hidden: int
    execution_time_ms: Optional[int]
    submitted_at: str
    evaluated_at: Optional[str]

    class Config:
        from_attributes = True


class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: int
    name: str
    total_score: int
    submissions: int


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id_raw = payload.get("user_id") or payload.get("sub")
    if user_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Admin: Create coding problem
@router.post("/problems/{exam_id}", response_model=CodingProblemResponse)
def create_coding_problem(
    exam_id: int,
    payload: CreateCodingProblemRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new coding problem for an exam (admin only)"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    repo = CodingProblemRepository(db)

    visible_tests = [
        {"input": tc.input, "expected": tc.expected}
        for tc in payload.visible_test_cases
    ]
    hidden_tests = [
        {"input": tc.input, "expected": tc.expected}
        for tc in payload.hidden_test_cases
    ]

    problem = repo.create(
        exam_id=exam_id,
        title=payload.title,
        description=payload.description,
        difficulty=payload.difficulty,
        time_limit_seconds=payload.time_limit_seconds,
        memory_limit_mb=payload.memory_limit_mb,
        starter_code=payload.starter_code or "",
        visible_test_cases=visible_tests,
        hidden_test_cases=hidden_tests,
    )

    return problem


# Get coding problems for exam
@router.get("/problems/{exam_id}", response_model=list[CodingProblemResponse])
def get_coding_problems(
    exam_id: int,
    db: Session = Depends(get_db),
):
    """Get all coding problems for an exam (visible tests only)"""
    repo = CodingProblemRepository(db)
    problems = repo.get_by_exam(exam_id)
    return problems


# Get single coding problem
@router.get("/problems/{exam_id}/{problem_id}", response_model=CodingProblemResponse)
def get_coding_problem(
    exam_id: int,
    problem_id: int,
    db: Session = Depends(get_db),
):
    """Get a single coding problem with visible test cases"""
    repo = CodingProblemRepository(db)
    problem: Any = repo.get_by_id(problem_id)

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if int(problem.exam_id) != exam_id:
        raise HTTPException(status_code=404, detail="Problem not found")

    return problem


# Submit code
@router.post("/submit/{problem_id}", response_model=dict)
def submit_code(
    problem_id: int,
    payload: CodeSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit Java code for async evaluation"""
    from app.workers.tasks import evaluate_submission_task

    try:
        service = CodingService(db)
        result = service.submit_code(current_user.id, problem_id, payload.code)
        
        # Trigger async evaluation via Celery
        submission_id = result["submission_id"]
        evaluate_submission_task.delay(submission_id)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Unexpected error while submitting code")
        raise HTTPException(status_code=500, detail="Internal server error")


# Get submission status
@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get submission status and results"""
    repo = SubmissionRepository(db)
    submission: Any = repo.get_by_id(submission_id)

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if int(submission.user_id) != int(current_user.id):
        raise HTTPException(status_code=403, detail="Forbidden")

    return submission


# Get best submission for problem
@router.get("/best/{problem_id}", response_model=SubmissionResponse)
def get_best_submission(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get best submission for a problem (current user)"""
    repo = SubmissionRepository(db)
    submission = repo.get_latest_by_user_problem(current_user.id, problem_id)

    if not submission:
        raise HTTPException(status_code=404, detail="No submissions found")

    return submission


# Get coding leaderboard
@router.get("/leaderboard/{exam_id}", response_model=list[LeaderboardEntryResponse])
def get_coding_leaderboard(
    exam_id: int,
    limit: int = Query(50, ge=1, le=MAX_LEADERBOARD_LIMIT),
    db: Session = Depends(get_db),
):
    """Get coding round leaderboard for an exam"""
    service = CodingService(db)
    leaderboard = service.get_coding_leaderboard(exam_id, limit)
    return leaderboard


# Evaluate submission (can be called by Celery task or admin)
@router.post("/evaluate/{submission_id}", response_model=dict)
def evaluate_submission(
    submission_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Manually trigger evaluation (normally done async by Celery)"""
    _ = admin
    try:
        service = CodingService(db)
        result = service.evaluate_submission(submission_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Unexpected error while evaluating submission")
        raise HTTPException(status_code=500, detail="Internal server error")
