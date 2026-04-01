import logging
import time
import uuid

from fastapi import Request
from fastapi import Response
from fastapi.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.audit")


class RequestAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        started = time.perf_counter()
        response: Response | None = None

        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.error(
                "request_id=%s method=%s path=%s status=%s elapsed_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                exc.status_code,
                elapsed_ms,
                exc_info=True,
            )
            headers = dict(exc.headers or {})
            headers["X-Request-Id"] = request_id
            exc.headers = headers
            raise
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.error(
                "request_id=%s method=%s path=%s status=%s elapsed_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                500,
                elapsed_ms,
                exc_info=True,
            )
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            if response is not None:
                response.headers["X-Request-Id"] = request_id
                logger.info(
                    "request_id=%s method=%s path=%s status=%s elapsed_ms=%.2f",
                    request_id,
                    request.method,
                    request.url.path,
                    response.status_code,
                    elapsed_ms,
                )
