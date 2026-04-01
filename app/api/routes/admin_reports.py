from io import StringIO
import csv

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.log import LogResponse
from app.services.contestant_service import ContestantService
from app.services.log_service import LogService

router = APIRouter(prefix="/admin", tags=["admin-reports"])


@router.get("/audit-logs", response_model=list[LogResponse])
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    _ = admin
    return LogService(db).list_latest(limit=limit)


@router.get("/results/{exam_id}/export")
def export_results_csv(
    exam_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    _ = admin
    entries = ContestantService(db).leaderboard(exam_id)

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["rank", "user_id", "user_name", "score", "accuracy", "total_time", "flagged"])
    for item in entries:
        writer.writerow(
            [
                item["rank"],
                item["user_id"],
                item["user_name"],
                item["score"],
                item["accuracy"],
                item["total_time"],
                item["flagged"],
            ]
        )

    buffer.seek(0)
    filename = f"exam_{exam_id}_results.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
