from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.admin import Admin

bearer = HTTPBearer(auto_error=True)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> Admin:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        message = str(exc)
        detail = "Token has expired" if message == "Token expired" else "Invalid token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    username = payload.get("sub")
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin


def get_client_metadata(
    user_agent: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
):
    return {
        "device_info": user_agent or "unknown",
        "forwarded_for": x_forwarded_for,
    }
