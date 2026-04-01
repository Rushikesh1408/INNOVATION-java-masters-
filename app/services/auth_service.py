from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_admin_access_token, verify_password
from app.repositories.admin_repository import AdminRepository

DUMMY_PASSWORD_HASH = (
    "$2b$12$27BQYLGjqmVvzyff6kK3HeYQ95f9w4zVj40MmCj2wDTH95P6m5Tru"
)


class AuthService:
    def __init__(self, db: Session):
        self.repo = AdminRepository(db)

    def admin_login(self, username: str, password: str) -> str:
        admin = self.repo.get_by_username(username)
        password_hash = admin.password_hash if admin else DUMMY_PASSWORD_HASH
        password_valid = verify_password(password, password_hash)

        if not admin or not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return create_admin_access_token(username)
