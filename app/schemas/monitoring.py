from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ParticipantMonitoringItem(BaseModel):
    session_id: UUID
    user_id: int
    user_name: str
    user_email: str
    exam_id: int
    exam_title: str
    current_question: int | None
    answered_count: int
    total_questions: int
    warning_count: int
    flagged: bool
    suspicious: bool
    time_per_question_ms: dict[int, int]
    total_time_ms: int
    last_activity_at: datetime


class MonitoringSnapshotResponse(BaseModel):
    generated_at: datetime
    active_count: int
    participants: list[ParticipantMonitoringItem]
