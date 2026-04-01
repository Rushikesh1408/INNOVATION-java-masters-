from datetime import UTC, datetime
import logging

from sqlalchemy.orm import Session, selectinload

from app.models.question import Question
from app.models.response import Response
from app.models.session import Session as ExamSession
from app.schemas.monitoring import MonitoringSnapshotResponse, ParticipantMonitoringItem

FAST_ANSWER_THRESHOLD_MS = 2000
WARNING_SUSPICIOUS_THRESHOLD = 2
logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_snapshot(self) -> MonitoringSnapshotResponse:
        active_sessions = (
            self.db.query(ExamSession)
            .options(selectinload(ExamSession.user), selectinload(ExamSession.exam))
            .filter(ExamSession.status == "active")
            .all()
        )

        session_ids = [session.id for session in active_sessions]
        responses = []
        if session_ids:
            responses = (
                self.db.query(Response)
                .filter(Response.session_id.in_(session_ids))
                .order_by(Response.answered_at.asc())
                .all()
            )

        responses_by_session: dict = {}
        for response in responses:
            responses_by_session.setdefault(response.session_id, []).append(response)

        exam_ids = list({session.exam_id for session in active_sessions})
        question_counts: dict[int, int] = {}
        if exam_ids:
            question_rows = (
                self.db.query(Question.exam_id)
                .filter(Question.exam_id.in_(exam_ids))
                .all()
            )
            for row in question_rows:
                question_counts[row.exam_id] = question_counts.get(row.exam_id, 0) + 1

        participant_rows: list[ParticipantMonitoringItem] = []
        for exam_session in active_sessions:
            if not exam_session.user or not exam_session.exam:
                logger.warning(
                    "Skipping monitoring payload for session %s due to missing user/exam relationship",
                    exam_session.id,
                )
                continue

            session_responses = responses_by_session.get(exam_session.id, [])
            answered_count = len([item for item in session_responses if item.selected_option is not None])
            total_questions = question_counts.get(exam_session.exam_id, 0)

            current_question = None
            if total_questions > 0:
                current_question = min(answered_count + 1, total_questions)

            time_per_question = {
                item.question_id: item.time_taken
                for item in session_responses
                if item.time_taken is not None
            }
            total_time = sum(time_per_question.values())
            has_fast_answers = any(
                item.time_taken is not None and item.time_taken < FAST_ANSWER_THRESHOLD_MS
                for item in session_responses
            )
            suspicious = (
                exam_session.flagged
                or exam_session.warning_count >= WARNING_SUSPICIOUS_THRESHOLD
                or has_fast_answers
            )

            last_activity_at = exam_session.start_time
            if session_responses:
                last_activity_at = max(item.answered_at for item in session_responses)

            participant_rows.append(
                ParticipantMonitoringItem(
                    session_id=exam_session.id,
                    user_id=exam_session.user_id,
                    user_name=exam_session.user.name,
                    user_email=exam_session.user.email,
                    exam_id=exam_session.exam_id,
                    exam_title=exam_session.exam.title,
                    current_question=current_question,
                    answered_count=answered_count,
                    total_questions=total_questions,
                    warning_count=exam_session.warning_count,
                    flagged=exam_session.flagged,
                    suspicious=suspicious,
                    time_per_question_ms=time_per_question,
                    total_time_ms=total_time,
                    last_activity_at=last_activity_at,
                )
            )

        participant_rows.sort(key=lambda item: item.last_activity_at, reverse=True)

        return MonitoringSnapshotResponse(
            generated_at=datetime.now(UTC),
            active_count=len(participant_rows),
            participants=participant_rows,
        )
