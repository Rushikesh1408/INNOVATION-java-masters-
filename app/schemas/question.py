from pydantic import BaseModel, Field


class QuestionCreateRequest(BaseModel):
    question_text: str = Field(min_length=5)
    option_1: str = Field(min_length=1, max_length=500)
    option_2: str = Field(min_length=1, max_length=500)
    option_3: str = Field(min_length=1, max_length=500)
    option_4: str = Field(min_length=1, max_length=500)
    correct_option: int = Field(ge=1, le=4)


class QuestionResponse(BaseModel):
    id: int
    exam_id: int
    question_text: str
    option_1: str
    option_2: str
    option_3: str
    option_4: str

    class Config:
        from_attributes = True
