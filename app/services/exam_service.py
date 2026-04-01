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
        positive_mark: float,
        negative_mark: float,
        admin_id: int,
    ):
        if time_limit <= 0:
            raise ValueError("time_limit must be greater than 0")
        if positive_mark < 0:
            raise ValueError("positive_mark must be greater than or equal to 0")

        normalized_negative_mark = abs(negative_mark)
        return self.repo.create_exam(
            title,
            time_limit,
            rules,
            positive_mark,
            normalized_negative_mark,
            admin_id,
        )

    def list_exams(self):
        return self.repo.list_exams()

    def get_exam_with_questions(self, exam_id: int):
        exam = self.repo.get_exam_with_questions(exam_id)
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found",
            )
        return exam

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
        if (
            not isinstance(correct_option, int)
            or correct_option not in {1, 2, 3, 4}
        ):
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

    def update_question(self, exam_id: int, question_id: int, fields: dict):
        if "correct_option" in fields:
            correct_option = fields["correct_option"]
            if (
                type(correct_option) is not int
                or correct_option not in {1, 2, 3, 4}
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="correct_option must be between 1 and 4",
                )

        question = self.repo.get_question(exam_id, question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found for this exam",
            )

        return self.repo.update_question(question, fields)

    def delete_question(self, exam_id: int, question_id: int) -> None:
        question = self.repo.get_question(exam_id, question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found for this exam",
            )

        self.repo.delete_question(question)
