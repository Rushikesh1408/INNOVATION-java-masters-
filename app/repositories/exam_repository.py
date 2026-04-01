from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.question import Question


class ExamRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_exam(
        self,
        title: str,
        time_limit: int,
        rules: str | None,
        created_by: int,
    ) -> Exam:
        exam = Exam(
            title=title,
            time_limit=time_limit,
            rules=rules,
            created_by=created_by,
        )
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def list_exams(self) -> list[Exam]:
        return self.db.query(Exam).order_by(Exam.id.desc()).all()

    def get_exam(self, exam_id: int) -> Exam | None:
        return self.db.query(Exam).filter(Exam.id == exam_id).first()

    def add_question(
        self,
        exam_id: int,
        question_text: str,
        option_1: str,
        option_2: str,
        option_3: str,
        option_4: str,
        correct_option: int,
    ) -> Question:
        if not isinstance(correct_option, int) or correct_option not in {1, 2, 3, 4}:
            raise ValueError("correct_option must be an integer between 1 and 4")

        question = Question(
            exam_id=exam_id,
            question_text=question_text,
            option_1=option_1,
            option_2=option_2,
            option_3=option_3,
            option_4=option_4,
            correct_option=correct_option,
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def list_questions(self, exam_id: int) -> list[Question]:
        return (
            self.db.query(Question)
            .filter(Question.exam_id == exam_id)
            .order_by(Question.id.asc())
            .all()
        )
