from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ContestantRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr


class ContestantResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class StartExamRequest(BaseModel):
    exam_id: int
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr


class SessionQuestionOption(BaseModel):
    option_id: int = Field(ge=1, le=4)
    text: str


class SessionQuestion(BaseModel):
    question_id: int
    question_text: str
    options: list[SessionQuestionOption]


class StartExamResponse(BaseModel):
    session_id: UUID
    exam_id: int
    time_limit: int
    questions: list[SessionQuestion]


class ResumeExamRequest(BaseModel):
    exam_id: int
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr


class ResumeExamResponse(BaseModel):
    session_id: UUID
    exam_id: int
    status: str
    answered: dict[str, dict]


class AnswerSubmitRequest(BaseModel):
    session_id: UUID
    question_id: int
    selected_option: int | None = Field(default=None, ge=1, le=4)
    time_taken: int = Field(ge=0, le=3600000)


class MonitoringEventRequest(BaseModel):
    session_id: UUID
    event_type: str
    event_meta: dict | None = None


class ResultResponse(BaseModel):
    score: int
    accuracy: float
    total_time: int
    flagged: bool
