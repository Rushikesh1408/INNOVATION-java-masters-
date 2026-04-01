from pydantic import BaseModel, Field, field_validator

from app.schemas.question import QuestionAdminResponse


class ExamCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    time_limit: int = Field(gt=0, le=300)
    rules: str | None = Field(default=None, max_length=4000)

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "title must contain at least one non-whitespace character"
            )
        return value


class ExamResponse(BaseModel):
    id: int
    title: str
    time_limit: int
    rules: str | None

    class Config:
        from_attributes = True


class ExamWithQuestionsResponse(ExamResponse):
    questions: list[QuestionAdminResponse]
