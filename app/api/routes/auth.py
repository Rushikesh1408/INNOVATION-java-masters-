from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.auth import AdminLoginRequest, AdminProfileResponse, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    token, expires_in = AuthService(db).admin_login(payload.username, payload.password)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/admin/me", response_model=AdminProfileResponse)
def admin_me(admin: Admin = Depends(get_current_admin)):
    return AdminProfileResponse(id=admin.id, username=admin.username)
