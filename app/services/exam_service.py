from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.exam_repository import ExamRepository


class ExamService:
    def __init__(self, db: Session):
        self.repo = ExamRepository(db)

    def create_exam(
        self,
        title: str,
        time_limit: int,
        rules: str | None,
        admin_id: int,
    ):
        return self.repo.create_exam(title, time_limit, rules, admin_id)

    def list_exams(self):
        return self.repo.list_exams()

    def add_question(
        self,
        exam_id: int,
        question_text: str,
        option_1: str,
        option_2: str,
        option_3: str,
        option_4: str,
        correct_option: int,
    ):
        if not isinstance(correct_option, int) or correct_option not in {1, 2, 3, 4}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="correct_option must be between 1 and 4",
            )

        exam = self.repo.get_exam(exam_id)
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found",
            )
        return self.repo.add_question(
            exam_id=exam_id,
            question_text=question_text,
            option_1=option_1,
            option_2=option_2,
            option_3=option_3,
            option_4=option_4,
            correct_option=correct_option,
        )

    def list_questions(self, exam_id: int):
        exam = self.repo.get_exam(exam_id)
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found",
            )
        return self.repo.list_questions(exam_id)
