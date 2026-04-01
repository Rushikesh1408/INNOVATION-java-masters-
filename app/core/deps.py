from collections.abc import Mapping

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
<<<<<<< HEAD
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    if not payload or not isinstance(payload, Mapping):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

=======
        message = str(exc)
        detail = "Token has expired" if message == "Token expired" else "Invalid token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

>>>>>>> 055f788b5d01bc147a13a62a8fdbb51aea169464
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

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
