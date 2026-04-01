from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.admin_reports import router as admin_reports_router
from app.api.routes.contestants import router as contestant_router
from app.api.routes.exams import router as exams_router
from app.api.routes.monitoring import router as monitoring_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(admin_reports_router)
api_router.include_router(exams_router)
api_router.include_router(contestant_router)
api_router.include_router(monitoring_router)
