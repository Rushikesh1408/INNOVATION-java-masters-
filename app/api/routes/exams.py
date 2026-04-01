from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.exam import (
    ExamCreateRequest,
    ExamResponse,
    ExamWithQuestionsResponse,
)
from app.schemas.question import (
    QuestionAdminResponse,
    QuestionCreateRequest,
    QuestionUpdateRequest,
)
from app.services.exam_service import ExamService

router = APIRouter(prefix="/exams", tags=["exams"])


@router.post("", response_model=ExamResponse)
def create_exam(
    payload: ExamCreateRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    return ExamService(db).create_exam(
        payload.title,
        payload.time_limit,
        payload.rules,
        admin.id,
    )


@router.get("", response_model=list[ExamResponse])
def list_exams(db: Session = Depends(get_db)):
    return ExamService(db).list_exams()


@router.get("/{exam_id}", response_model=ExamWithQuestionsResponse)
def get_exam_with_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    _ = admin
    return ExamService(db).get_exam_with_questions(exam_id)


@router.post("/{exam_id}/questions", response_model=QuestionAdminResponse)
def add_question(
    exam_id: int,
    payload: QuestionCreateRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    _ = admin
    return ExamService(db).add_question(
        exam_id=exam_id,
        question_text=payload.question_text,
        option_1=payload.option_1,
        option_2=payload.option_2,
        option_3=payload.option_3,
        option_4=payload.option_4,
        correct_option=payload.correct_option,
    )


@router.get("/{exam_id}/questions", response_model=list[QuestionAdminResponse])
def list_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    _ = admin
    return ExamService(db).list_questions(exam_id)


@router.put(
    "/{exam_id}/questions/{question_id}",
    response_model=QuestionAdminResponse,
)
def update_question(
    exam_id: int,
    question_id: int,
    payload: QuestionUpdateRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    _ = admin
    update_fields = payload.model_dump(exclude_none=True)
    return ExamService(db).update_question(exam_id, question_id, update_fields)


@router.delete(
    "/{exam_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_question(
    exam_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    _ = admin
    ExamService(db).delete_question(exam_id, question_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
