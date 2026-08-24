"""Rate limiting respaldado por Redis (slowapi)."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    strategy="fixed-window",
    headers_enabled=True,
)
