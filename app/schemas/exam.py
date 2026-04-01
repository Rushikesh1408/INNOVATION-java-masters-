from pydantic import BaseModel, Field


class ExamCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    time_limit: int = Field(gt=0, le=300)
    rules: str | None = None


class ExamResponse(BaseModel):
    id: int
    title: str
    time_limit: int
    rules: str | None

    class Config:
        from_attributes = True
