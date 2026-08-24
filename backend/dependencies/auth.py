"""Dependencia de autenticación: resuelve la sesión desde la cookie `sid`."""
from fastapi import HTTPException, Request

from core.config import settings
from core.messages import AuthMessages
from core.sessions import SessionRevokedError, SessionUser, get_session


async def get_current_user(request: Request) -> SessionUser:
    sid = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not sid:
        raise HTTPException(status_code=401, detail=AuthMessages.TOKEN_REQUERIDO)

    try:
        user = await get_session(sid)
    except SessionRevokedError as error:
        raise HTTPException(
            status_code=401, detail=f"{AuthMessages.SESION_REVOCADA}: {error.reason}"
        ) from error

    if user is None:
        raise HTTPException(status_code=401, detail=AuthMessages.SESION_EXPIRADA)

    request.state.user = user
    request.state.sid = sid
    return user
