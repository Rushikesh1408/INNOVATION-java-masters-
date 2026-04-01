from pydantic import BaseModel, Field, model_validator


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


class QuestionAdminResponse(QuestionResponse):
    correct_option: int


class QuestionUpdateRequest(BaseModel):
    question_text: str | None = Field(default=None, min_length=5)
    option_1: str | None = Field(default=None, min_length=1, max_length=500)
    option_2: str | None = Field(default=None, min_length=1, max_length=500)
    option_3: str | None = Field(default=None, min_length=1, max_length=500)
    option_4: str | None = Field(default=None, min_length=1, max_length=500)
    correct_option: int | None = Field(default=None, ge=1, le=4)

    @model_validator(mode="after")
    def validate_non_empty_payload(self):
        if not any(
            [
                self.question_text,
                self.option_1,
                self.option_2,
                self.option_3,
                self.option_4,
                self.correct_option is not None,
            ]
        ):
            raise ValueError("At least one field must be provided for update")
        return self
