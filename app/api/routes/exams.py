from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.exam import ExamCreateRequest, ExamResponse
from app.schemas.question import QuestionCreateRequest, QuestionResponse
from app.services.exam_service import ExamService

router = APIRouter(prefix="/exams", tags=["exams"])


@router.post("", response_model=ExamResponse)
def create_exam(
    payload: ExamCreateRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return ExamService(db).create_exam(payload.title, payload.time_limit, payload.rules, admin.id)


@router.get("", response_model=list[ExamResponse])
def list_exams(db: Session = Depends(get_db)):
    return ExamService(db).list_exams()


@router.post("/{exam_id}/questions", response_model=QuestionResponse)
def add_question(
    exam_id: int,
    payload: QuestionCreateRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    _ = admin
    return ExamService(db).add_question(exam_id, payload.question_text, payload.options, payload.correct_option)


@router.get("/{exam_id}/questions", response_model=list[QuestionResponse])
def list_questions(exam_id: int, db: Session = Depends(get_db)):
    return ExamService(db).list_questions(exam_id)
