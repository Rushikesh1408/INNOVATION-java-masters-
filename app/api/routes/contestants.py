from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.contestant import (
    AnswerSubmitRequest,
    ContestantRegisterRequest,
    ContestantResponse,
    MonitoringEventRequest,
    ResultResponse,
    StartExamRequest,
    StartExamResponse,
)
from app.schemas.leaderboard import LeaderboardEntry
from app.services.contestant_service import ContestantService

router = APIRouter(prefix="/contestants", tags=["contestants"])


@router.post("/register", response_model=ContestantResponse)
def register(payload: ContestantRegisterRequest, db: Session = Depends(get_db)):
    return ContestantService(db).register(payload.name, payload.email)


@router.post("/start-exam", response_model=StartExamResponse)
def start_exam(payload: StartExamRequest, request: Request, db: Session = Depends(get_db)):
    forwarded_for = request.headers.get("x-forwarded-for")
    ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    exam_session, exam = ContestantService(db).start_exam(payload.user_id, payload.exam_id, ip_address, user_agent)
    return StartExamResponse(session_id=exam_session.id, exam_id=exam.id, time_limit=exam.time_limit)


@router.post("/submit-answer")
def submit_answer(payload: AnswerSubmitRequest, db: Session = Depends(get_db)):
    ContestantService(db).submit_answer(
        payload.session_id,
        payload.question_id,
        payload.selected_option,
        payload.time_taken,
    )
    return {"status": "accepted"}


@router.post("/monitoring-event")
def monitoring_event(payload: MonitoringEventRequest, db: Session = Depends(get_db)):
    exam_session = ContestantService(db).ingest_monitoring_event(payload.session_id, payload.event_type)
    return {
        "status": exam_session.status,
        "warning_count": exam_session.warning_count,
        "flagged": exam_session.flagged,
    }


@router.post("/finish/{session_id}", response_model=ResultResponse)
def finish_exam(session_id: UUID, db: Session = Depends(get_db)):
    result = ContestantService(db).finalize_result(session_id)
    return ResultResponse(
        score=result.score,
        accuracy=result.accuracy,
        total_time=result.total_time,
        flagged=result.flagged,
    )


@router.get("/leaderboard/{exam_id}", response_model=list[LeaderboardEntry])
def leaderboard(exam_id: int, db: Session = Depends(get_db)):
    return ContestantService(db).leaderboard(exam_id)
