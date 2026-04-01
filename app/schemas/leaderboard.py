from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    user_name: str
    score: int
    accuracy: float
    total_time: int
    flagged: bool
