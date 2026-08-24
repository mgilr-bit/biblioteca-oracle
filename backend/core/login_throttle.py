"""Throttle de intentos fallidos de login por cuenta.

NIST SP 800-63B 5.2.2: el verificador debe limitar los intentos de
autenticación fallidos "por cuenta o por IP de origen". El rate-limit de
slowapi (ver core/rate_limit.py) ya cubre el caso por-IP; esto cierra el
otro caso — un atacante distribuido en muchas IPs no puede seguir
fuerza-bruteando UNA cuenta puntual, porque el contador es por email.
"""
from core.redis import redis_client

MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 15 * 60


def _key(email: str) -> str:
    return f"login_fail:{email.strip().lower()}"


async def is_locked(email: str) -> bool:
    count = await redis_client.get(_key(email))
    return count is not None and int(count) >= MAX_INTENTOS


async def register_failure(email: str) -> None:
    key = _key(email)
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, VENTANA_SEGUNDOS)


async def clear_failures(email: str) -> None:
    await redis_client.delete(_key(email))
