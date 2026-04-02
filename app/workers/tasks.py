from datetime import datetime
from pathlib import Path

from celery.signals import worker_process_shutdown
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.workers.celery_app import celery_app

settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


@worker_process_shutdown.connect
def _shutdown_worker_process(**_kwargs):
    engine.dispose()


@celery_app.task(name="backup.daily_database_placeholder")
def daily_database_backup_placeholder() -> str:
    backup_dir = Path("backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    marker = backup_dir / f"backup-marker-{datetime.utcnow().date()}.txt"
    marker.write_text("Replace with pg_dump command in deployment scheduler.\n", encoding="utf-8")
    return str(marker)


@celery_app.task(name="coding.evaluate_submission")
def evaluate_submission_task(submission_id: int) -> dict:
    """
    Async task to evaluate a code submission.
    Triggered after user submits code.
    """
    from app.services.coding_service import CodingService
    db = SessionLocal()

    try:
        service = CodingService(db)
        return service.evaluate_submission(submission_id)
    finally:
        db.close()

