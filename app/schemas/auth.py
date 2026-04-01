from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128, repr=False)


class TokenResponse(BaseModel):
    access_token: str = Field(min_length=1)
    token_type: str = "bearer"
    expires_in: int


class AdminProfileResponse(BaseModel):
    id: int
    username: str
