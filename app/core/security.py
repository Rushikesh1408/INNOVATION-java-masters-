from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_admin_access_token(subject: str) -> tuple[str, int]:
    expire_at = datetime.now(UTC) + timedelta(minutes=settings.admin_jwt_expire_minutes)
    payload = {"sub": subject, "role": "admin", "exp": expire_at}
    token = jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm)
    return token, settings.admin_jwt_expire_minutes * 60


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.admin_jwt_secret, algorithms=[settings.admin_jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise ValueError("Token expired") from exc
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
