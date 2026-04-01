from fastapi import APIRouter

router = APIRouter(prefix="/exams", tags=["exam-system"])


@router.get("/ping")
def exam_system_ping() -> dict[str, str]:
    return {"message": "Exam service is ready"}
