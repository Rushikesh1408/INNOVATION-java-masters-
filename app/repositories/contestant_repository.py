from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.response import Response
from app.models.result import Result
from app.models.session import Session as ExamSession
from app.models.user import User


class ContestantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, name: str, email: str) -> User:
        user = self.db.query(User).filter(User.email == email).first()
        if user:
            return user
        user = User(name=name, email=email)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_active_session(self, user_id: int, exam_id: int) -> ExamSession | None:
        return (
            self.db.query(ExamSession)
            .filter(ExamSession.user_id == user_id, ExamSession.exam_id == exam_id, ExamSession.status == "active")
            .first()
        )

    def create_session(self, user_id: int, exam_id: int, ip_address: str, device_info: str) -> ExamSession:
        exam_session = ExamSession(
            user_id=user_id,
            exam_id=exam_id,
            ip_address=ip_address,
            device_info=device_info,
        )
        try:
            self.db.add(exam_session)
            self.db.commit()
            self.db.refresh(exam_session)
            return exam_session
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Active session already exists") from exc

    def get_session(self, session_id) -> ExamSession | None:
        return self.db.query(ExamSession).filter(ExamSession.id == session_id).first()

    def get_session_for_update(self, session_id) -> ExamSession | None:
        return (
            self.db.query(ExamSession)
            .filter(ExamSession.id == session_id)
            .with_for_update()
            .first()
        )

    def save_response(self, session_id, question_id: int, selected_option: int, time_taken: int) -> Response:
        response = (
            self.db.query(Response)
            .filter(Response.session_id == session_id, Response.question_id == question_id)
            .first()
        )
        if response:
            response.selected_option = selected_option
            response.time_taken = time_taken
        else:
            response = Response(
                session_id=session_id,
                question_id=question_id,
                selected_option=selected_option,
                time_taken=time_taken,
            )
            self.db.add(response)

        self.db.commit()
        self.db.refresh(response)
        return response

    def list_responses(self, session_id) -> list[Response]:
        return self.db.query(Response).filter(Response.session_id == session_id).all()

    def upsert_result(self, user_id: int, exam_id: int, score: int, accuracy: float, total_time: int, flagged: bool) -> Result:
        result = self.db.query(Result).filter(Result.user_id == user_id, Result.exam_id == exam_id).first()
        if result:
            result.score = score
            result.accuracy = accuracy
            result.total_time = total_time
            result.flagged = flagged
        else:
            result = Result(
                user_id=user_id,
                exam_id=exam_id,
                score=score,
                accuracy=accuracy,
                total_time=total_time,
                flagged=flagged,
            )
            self.db.add(result)

        self.db.commit()
        self.db.refresh(result)
        return result

    def list_exam_results(self, exam_id: int) -> list[Result]:
        return (
            self.db.query(Result)
            .filter(Result.exam_id == exam_id)
            .order_by(Result.accuracy.desc(), Result.total_time.asc())
            .all()
        )
