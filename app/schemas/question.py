from pydantic import BaseModel, Field, model_validator


class QuestionCreateRequest(BaseModel):
    question_text: str = Field(min_length=5)
    options: dict[str, str]
    correct_option: int = Field(ge=1, le=4)

    @model_validator(mode="after")
    def validate_options(self):
        required = {"1", "2", "3", "4"}
        if set(self.options.keys()) != required:
            raise ValueError("options must contain keys 1,2,3,4")
        return self


class QuestionResponse(BaseModel):
    id: int
    exam_id: int
    question_text: str
    options: dict[str, str]

    class Config:
        from_attributes = True
