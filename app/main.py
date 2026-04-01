from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging_middleware import RequestAuditMiddleware
from app.db.init_db import create_tables
from app.routes import exam_router

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

if "*" in settings.cors_origins:
    raise ValueError(
        "CORS origins cannot contain '*' when allow_credentials=True. "
        "Set explicit ALLOWED_ORIGINS.",
    )

app = FastAPI(title=settings.app_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestAuditMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_tables()


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(exam_router, prefix=settings.api_prefix)
