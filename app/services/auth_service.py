from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_admin_access_token, verify_password
from app.repositories.admin_repository import AdminRepository
from app.services.log_service import LogService

DUMMY_PASSWORD_HASH = (
    "$2b$12$27BQYLGjqmVvzyff6kK3HeYQ95f9w4zVj40MmCj2wDTH95P6m5Tru"
)


class AuthService:
    def __init__(self, db: Session):
        self.repo = AdminRepository(db)
        self.log_service = LogService(db)

    def admin_login(self, username: str, password: str) -> tuple[str, int]:
        normalized_username = username.strip()
        admin = self.repo.get_by_username(normalized_username)
        password_hash = admin.password_hash if admin else DUMMY_PASSWORD_HASH
        password_valid = verify_password(password, password_hash)

        if not admin or not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        self.log_service.write(
            action="ADMIN_LOGIN",
            context=f"username={admin.username}",
        )
        return create_admin_access_token(admin.username)
