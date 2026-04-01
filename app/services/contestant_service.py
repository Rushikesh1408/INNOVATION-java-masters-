from datetime import UTC, datetime
import random
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.contestant_repository import ContestantRepository
from app.repositories.exam_repository import ExamRepository

SUSPICIOUS_TIME_THRESHOLD_MS = 2000
AUTO_SUBMIT_WARNING_THRESHOLD = 2


class ContestantService:
    def __init__(self, db: Session):
        self.repo = ContestantRepository(db)
        self.exam_repo = ExamRepository(db)

    def register(self, name: str, email: str):
        return self.repo.get_or_create_user(name, email)

    def start_exam(
        self,
        name: str,
        email: str,
        exam_id: int,
        ip_address: str,
        device_info: str,
    ):
        user = self.repo.get_or_create_user(name, email)
        exam = self.exam_repo.get_exam(exam_id)
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found",
            )

        active_session = self.repo.get_active_session_for_user(user.id)
        if active_session:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active session already exists for this email",
            )

        try:
            exam_session = self.repo.create_session(
                user.id,
                exam_id,
                ip_address,
                device_info,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Active session already exists",
            ) from exc

        questions = self.exam_repo.list_questions(exam_id)
        randomized_questions = []
        for question in questions:
            options = [
                {"option_id": 1, "text": question.option_1},
                {"option_id": 2, "text": question.option_2},
                {"option_id": 3, "text": question.option_3},
                {"option_id": 4, "text": question.option_4},
            ]
            random.shuffle(options)
            randomized_questions.append(
                {
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "options": options,
                }
            )

        random.shuffle(randomized_questions)
        return exam_session, exam, randomized_questions

    def submit_answer(
        self,
        session_id: UUID,
        question_id: int,
        selected_option: int | None,
        time_taken: int,
    ):
        exam_session = self.repo.get_session(session_id)
        if not exam_session or exam_session.status != "active":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session unavailable",
            )

        question = self.exam_repo.get_question(
            exam_session.exam_id,
            question_id,
        )
        if not question or question.exam_id != exam_session.exam_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question does not belong to this exam session",
            )

        if selected_option is not None and selected_option not in {1, 2, 3, 4}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "selected_option must be between 1 and 4 "
                    "or null for skip"
                ),
            )

        if time_taken < SUSPICIOUS_TIME_THRESHOLD_MS:
            exam_session.flagged = True
            self.repo.db.flush()

        try:
            return self.repo.save_response(
                session_id,
                question_id,
                selected_option,
                time_taken,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

    def ingest_monitoring_event(self, session_id: UUID, event_type: str):
        exam_session = self.repo.get_session_for_update(session_id)
        if not exam_session or exam_session.status != "active":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session unavailable",
            )

        if event_type in {"TAB_SWITCH", "FULLSCREEN_EXIT"}:
            exam_session.warning_count += 1
            if exam_session.warning_count >= AUTO_SUBMIT_WARNING_THRESHOLD:
                exam_session.status = "submitted"
                exam_session.end_time = datetime.now(UTC)
                exam_session.flagged = True

        self.repo.db.commit()
        self.repo.db.refresh(exam_session)
        return exam_session

    def finalize_result(self, session_id: UUID):
        exam_session = self.repo.get_session(session_id)
        if not exam_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        if exam_session.status == "active":
            exam_session.status = "submitted"
            exam_session.end_time = datetime.now(UTC)

        responses = self.repo.list_responses(session_id)
        questions = self.exam_repo.list_questions(exam_session.exam_id)
        question_map = {q.id: q for q in questions}

        correct = 0
        total_time = 0
        for response in responses:
            total_time += response.time_taken
            question = question_map.get(response.question_id)
            if (
                question
                and response.selected_option == question.correct_option
            ):
                correct += 1

        total_questions = max(len(questions), 1)
        accuracy = (correct / total_questions) * 100
        result = self.repo.upsert_result(
            user_id=exam_session.user_id,
            exam_id=exam_session.exam_id,
            score=correct,
            accuracy=accuracy,
            total_time=total_time,
            flagged=exam_session.flagged,
        )

        self.repo.db.commit()
        return result

    def leaderboard(self, exam_id: int):
        results = self.repo.list_exam_results(exam_id)
        user_ids = [result.user_id for result in results]
        users = self.repo.db.query(User).filter(User.id.in_(user_ids)).all()
        user_map = {user.id: user for user in users}

        entries = []
        for idx, result in enumerate(results, start=1):
            user = user_map.get(result.user_id)
            entries.append(
                {
                    "rank": idx,
                    "user_id": result.user_id,
                    "user_name": user.name if user else "Unknown",
                    "score": result.score,
                    "accuracy": result.accuracy,
                    "total_time": result.total_time,
                    "flagged": result.flagged,
                }
            )
        return entries
