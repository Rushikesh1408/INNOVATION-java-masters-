import os

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.init_db import create_tables
from app.db.session import SessionLocal
from app.repositories.admin_repository import AdminRepository


def seed_admin(username: str, password: str) -> None:
    create_tables()
    db: Session = SessionLocal()
    try:
        repo = AdminRepository(db)
        existing = repo.get_by_username(username)
        if existing:
            print("Admin already exists")
            return

        repo.create(username=username, password_hash=hash_password(password))
        print("Admin created")
    finally:
        db.close()


if __name__ == "__main__":
    # Configure admin seed credentials via environment variables.
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()

    if not admin_password:
        raise SystemExit(
            "ADMIN_PASSWORD environment variable is required and cannot be "
            "empty."
        )

    seed_admin(admin_username, admin_password)
