from datetime import UTC, datetime
import logging
import random
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis_client import safe_get_json, safe_set_json
from app.models.user import User
from app.repositories.contestant_repository import ContestantRepository
from app.repositories.exam_repository import ExamRepository
from app.services.log_service import LogService

SUSPICIOUS_TIME_THRESHOLD_MS = 2000
AUTO_SUBMIT_WARNING_THRESHOLD = 2
FAST_ANSWER_FLAG_COUNT_THRESHOLD = 3
DEFAULT_SESSION_STATE_TTL_SECONDS = 3600
logger = logging.getLogger(__name__)


class ContestantService:
    def __init__(self, db: Session):
        self.repo = ContestantRepository(db)
        self.exam_repo = ExamRepository(db)
        self.log_service = LogService(db)
        self.settings = get_settings()

    def register(self, name: str, email: str):
        return self.repo.get_or_create_user(name, email)

    def _compute_session_ttl_seconds(self, time_limit) -> int:
        if isinstance(time_limit, (int, float)) and time_limit > 0:
            return max(int(time_limit) * 60, 60)

        logger.warning(
            "Invalid exam time_limit for session state TTL: %s. Using default TTL.",
            time_limit,
        )
        return DEFAULT_SESSION_STATE_TTL_SECONDS

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
        self.log_service.write(
            action="EXAM_STARTED",
            user_id=user.id,
            context=f"exam_id={exam_id} session_id={exam_session.id}",
        )
        ttl_seconds = self._compute_session_ttl_seconds(exam.time_limit)
        safe_set_json(
            key=f"session_state:{exam_session.id}",
            payload={
                "user_id": user.id,
                "exam_id": exam_id,
                "status": "active",
                "answered": {},
            },
            ttl_seconds=ttl_seconds,
        )
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

        if time_taken < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="time_taken must be non-negative",
            )

        if time_taken < SUSPICIOUS_TIME_THRESHOLD_MS:
            exam_session.flagged = True
            self.repo.db.flush()

        try:
            response = self.repo.save_response(
                session_id,
                question_id,
                selected_option,
                time_taken,
            )
            state_key = f"session_state:{session_id}"
            state = safe_get_json(state_key) or {
                "status": "active",
                "answered": {},
            }
            state.setdefault("answered", {})[str(question_id)] = {
                "selected_option": selected_option,
                "time_taken": time_taken,
            }
            exam = self.exam_repo.get_exam(exam_session.exam_id)
            ttl_seconds = self._compute_session_ttl_seconds(exam.time_limit if exam else None)
            safe_set_json(
                key=state_key,
                payload=state,
                ttl_seconds=ttl_seconds,
            )
            self.log_service.write(
                action="ANSWER_SUBMITTED",
                user_id=exam_session.user_id,
                context=(
                    f"session_id={session_id} question_id={question_id} "
                    f"time_taken={time_taken}"
                ),
            )
            return response
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

        self.log_service.write(
            action="MONITORING_EVENT",
            user_id=exam_session.user_id,
            context=f"session_id={session_id} event_type={event_type}",
        )

        self.repo.db.commit()
        self.repo.db.refresh(exam_session)
        return exam_session

    def resume_exam(self, name: str, email: str, exam_id: int):
        user = self.repo.get_or_create_user(name, email)
        active_session = self.repo.get_active_session(user.id, exam_id)
        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active session found to resume",
            )

        state = safe_get_json(f"session_state:{active_session.id}") or {
            "answered": {},
            "status": active_session.status,
        }
        return {
            "session_id": active_session.id,
            "exam_id": active_session.exam_id,
            "status": active_session.status,
            "answered": state.get("answered", {}),
        }

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
        exam = self.exam_repo.get_exam(exam_session.exam_id)
        question_map = {q.id: q for q in questions}

        correct = 0
        wrong = 0
        total_time = 0
        fast_answer_count = 0
        answered_count = 0
        for response in responses:
            total_time += response.time_taken
            if response.selected_option is not None:
                answered_count += 1
            if response.time_taken < SUSPICIOUS_TIME_THRESHOLD_MS:
                fast_answer_count += 1

            question = question_map.get(response.question_id)
            if (
                question
                and response.selected_option == question.correct_option
            ):
                correct += 1
            elif question and response.selected_option is not None:
                wrong += 1

        total_questions = max(len(questions), 1)
        positive_mark = exam.positive_mark if exam else 1.0
        negative_mark = exam.negative_mark if exam else 0.0
        computed_score = max(0.0, (correct * positive_mark) - (wrong * negative_mark))
        accuracy = (correct / total_questions) * 100
        suspicious_fast_pattern = (
            fast_answer_count >= FAST_ANSWER_FLAG_COUNT_THRESHOLD
        )
        suspicious_avg_speed = (
            answered_count > 0
            and (total_time / answered_count) < SUSPICIOUS_TIME_THRESHOLD_MS
        )
        skipped_all_questions = answered_count == 0
        flagged = (
            exam_session.flagged
            or suspicious_fast_pattern
            or suspicious_avg_speed
            or skipped_all_questions
        )

        exam_session.flagged = flagged
        result = self.repo.upsert_result(
            user_id=exam_session.user_id,
            exam_id=exam_session.exam_id,
            score=int(round(computed_score)),
            accuracy=accuracy,
            total_time=total_time,
            flagged=flagged,
        )

        self.repo.db.commit()
        self.log_service.write(
            action="EXAM_SUBMITTED",
            user_id=exam_session.user_id,
            context=f"session_id={session_id} score={result.score} flagged={flagged}",
        )
        return result

    def leaderboard(self, exam_id: int):
        cache_key = f"leaderboard:{exam_id}"
        cached = safe_get_json(cache_key)
        if cached is not None:
            return cached

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
        safe_set_json(
            key=cache_key,
            payload=entries,
            ttl_seconds=self.settings.leaderboard_cache_ttl_seconds,
        )
        return entries
