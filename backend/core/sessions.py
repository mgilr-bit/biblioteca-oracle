"""Sesiones de usuario respaldadas por Redis (reemplaza JWT)."""
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from core.config import settings
from core.redis import redis_client

SESSION_KEY_PREFIX = "sess:"
USER_SESSIONS_KEY_PREFIX = "user_sessions:"


class SessionRevokedError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass
class SessionUser:
    sid: str
    id: int
    email: str
    nombre: str
    rol: str
    created_at: datetime


def _session_key(sid: str) -> str:
    return f"{SESSION_KEY_PREFIX}{sid}"


def _user_sessions_key(user_id: int) -> str:
    return f"{USER_SESSIONS_KEY_PREFIX}{user_id}"


def derive_csrf_token(sid: str) -> str:
    """Deriva el valor de XSRF-TOKEN a partir del sid, sin guardarlo aparte en Redis."""
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), sid.encode("utf-8"), hashlib.sha256).hexdigest()


async def create_session(*, user_id: int, email: str, nombre: str, rol: str, ip: str, user_agent: str) -> str:
    sid = secrets.token_urlsafe(32)
    blob = {
        "user_id": user_id,
        "email": email,
        "nombre": nombre,
        "rol": rol,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ip": ip,
        "user_agent": user_agent,
    }
    await redis_client.setex(_session_key(sid), settings.SESSION_IDLE_TTL_SECONDS, json.dumps(blob))
    await redis_client.sadd(_user_sessions_key(user_id), sid)
    return sid


async def get_session(sid: str) -> Optional[SessionUser]:
    raw = await redis_client.get(_session_key(sid))
    if raw is None:
        return None

    blob = json.loads(raw)

    if blob.get("revoked"):
        raise SessionRevokedError(blob.get("reason", "Sesión revocada"))

    created_at = datetime.fromisoformat(blob["created_at"])
    age_seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
    if age_seconds > settings.SESSION_ABSOLUTE_TTL_SECONDS:
        return None

    # Rolling: refresca el TTL de inactividad en cada uso válido.
    await redis_client.expire(_session_key(sid), settings.SESSION_IDLE_TTL_SECONDS)

    return SessionUser(
        sid=sid,
        id=blob["user_id"],
        email=blob["email"],
        nombre=blob.get("nombre", ""),
        rol=blob["rol"],
        created_at=created_at,
    )


async def revoke_session(sid: str, user_id: int, reason: str = "logout") -> None:
    tombstone = json.dumps({"revoked": True, "reason": reason})
    await redis_client.setex(_session_key(sid), settings.SESSION_REVOKED_TOMBSTONE_TTL_SECONDS, tombstone)
    await redis_client.srem(_user_sessions_key(user_id), sid)


async def revoke_all_sessions(user_id: int, *, except_sid: Optional[str] = None, reason: str = "revoked") -> None:
    sids = await redis_client.smembers(_user_sessions_key(user_id))
    for sid in sids:
        if sid == except_sid:
            continue
        await revoke_session(sid, user_id, reason)
