from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.admin import Admin


class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> Admin | None:
        normalized = username.strip().lower()
        return (
            self.db.query(Admin)
            .filter(func.lower(Admin.username) == normalized)
            .first()
        )

    def create(self, username: str, password_hash: str) -> Admin:
        admin = Admin(username=username, password_hash=password_hash)
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def update_password(self, admin: Admin, password_hash: str) -> Admin:
        admin.password_hash = password_hash
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin
