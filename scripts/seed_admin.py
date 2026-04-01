import os

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.init_db import create_tables
from app.db.session import SessionLocal
from app.repositories.admin_repository import AdminRepository


def seed_admin(
    username: str,
    password: str,
    force_password_update: bool = False,
) -> None:
    create_tables()
    normalized_username = username.strip()
    db: Session = SessionLocal()
    try:
        repo = AdminRepository(db)
        existing = repo.get_by_username(normalized_username)
        if existing:
            if force_password_update:
                repo.update_password(existing, hash_password(password))
                print("Admin password updated")
                return
            print("Admin already exists")
            return

        repo.create(
            username=normalized_username,
            password_hash=hash_password(password),
        )
        print("Admin created")
    finally:
        db.close()


if __name__ == "__main__":
    # Configure admin seed credentials via environment variables.
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
    should_force_password_update = (
        os.getenv("ADMIN_FORCE_UPDATE", "0").strip().lower()
        in {
            "1",
            "true",
            "yes",
        }
    )

    if not admin_password:
        raise SystemExit(
            "ADMIN_PASSWORD environment variable is required and cannot be "
            "empty."
        )

    seed_admin(
        admin_username,
        admin_password,
        force_password_update=should_force_password_update,
    )
