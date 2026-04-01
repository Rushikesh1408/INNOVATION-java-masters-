from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_admin_access_token, verify_password
from app.repositories.admin_repository import AdminRepository


class AuthService:
    def __init__(self, db: Session):
        self.repo = AdminRepository(db)

    def admin_login(self, username: str, password: str) -> tuple[str, int]:
        admin = self.repo.get_by_username(username)
        if not admin or not verify_password(password, admin.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return create_admin_access_token(username)
