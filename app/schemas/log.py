from datetime import datetime

from pydantic import BaseModel


class LogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    context: str | None
    timestamp: datetime

    class Config:
        from_attributes = True
