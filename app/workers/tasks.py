from datetime import datetime
from pathlib import Path

from app.workers.celery_app import celery_app


@celery_app.task(name="backup.daily_database_placeholder")
def daily_database_backup_placeholder() -> str:
    backup_dir = Path("backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    marker = backup_dir / f"backup-marker-{datetime.utcnow().date()}.txt"
    marker.write_text("Replace with pg_dump command in deployment scheduler.\n", encoding="utf-8")
    return str(marker)
