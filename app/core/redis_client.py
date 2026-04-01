import json
import logging

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def safe_get_json(key: str):
    try:
        raw = redis_client.get(key)
        if not raw:
            return None
        return json.loads(raw)
    except (RedisError, json.JSONDecodeError):
        logger.warning("Failed to read cache key: %s", key, exc_info=True)
        return None


def safe_set_json(key: str, payload, ttl_seconds: int) -> None:
    try:
        redis_client.setex(key, ttl_seconds, json.dumps(payload))
    except (RedisError, TypeError):
        logger.warning("Failed to write cache key: %s", key, exc_info=True)
