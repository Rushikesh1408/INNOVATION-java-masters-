from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.exam_repository import ExamRepository


class ExamService:
    def __init__(self, db: Session):
        self.repo = ExamRepository(db)

    def create_exam(self, title: str, time_limit: int, rules: str | None, admin_id: int):
        return self.repo.create_exam(title, time_limit, rules, admin_id)

    def list_exams(self):
        return self.repo.list_exams()

    def add_question(self, exam_id: int, question_text: str, options: dict, correct_option: int):
        exam = self.repo.get_exam(exam_id)
        if not exam:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
        return self.repo.add_question(exam_id, question_text, options, correct_option)

    def list_questions(self, exam_id: int):
        return self.repo.list_questions(exam_id)
