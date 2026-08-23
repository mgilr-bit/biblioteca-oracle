"""Cliente Redis (async) compartido por sesiones y rate limiting."""
from redis.asyncio import Redis, from_url

from core.config import settings

redis_client: Redis = from_url(settings.REDIS_URL, decode_responses=True)
