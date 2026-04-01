from asyncio import sleep, to_thread

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.core.security import decode_token
from app.db.session import SessionLocal, get_db
from app.models.admin import Admin
from app.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/admin/monitoring", tags=["admin-monitoring"])


@router.get("/active")
def active_participants(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    _ = admin
    return MonitoringService(db).get_active_snapshot()


def _verify_admin_token(token: str, db: Session) -> bool:
    try:
        payload = decode_token(token)
    except ValueError:
        return False

    if payload.get("role") != "admin":
        return False

    username = payload.get("sub")
    if not username:
        return False

    admin = db.query(Admin).filter(Admin.username == username).first()
    return admin is not None


def _get_snapshot_with_fresh_session():
    db = SessionLocal()
    try:
        return MonitoringService(db).get_active_snapshot()
    finally:
        db.close()


@router.websocket("/ws")
async def monitoring_stream(websocket: WebSocket, token: str = Query(default="")):
    await websocket.accept()

    auth_db = SessionLocal()
    try:
        if not token or not _verify_admin_token(token, auth_db):
            await websocket.close(code=1008, reason="Unauthorized")
            return
    finally:
        auth_db.close()

    try:
        while True:
            snapshot = await to_thread(_get_snapshot_with_fresh_session)
            await websocket.send_json(snapshot.model_dump(mode="json"))
            await sleep(3)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=1011, reason="Monitoring stream error")
