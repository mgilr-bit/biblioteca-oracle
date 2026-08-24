"""Middleware CSRF de doble-envío (double-submit cookie)."""
import hmac

from fastapi import Request
from fastapi.responses import JSONResponse

from core.config import settings
from core.messages import AuthMessages
from core.sessions import derive_csrf_token

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_EXEMPT_PATHS = {"/api/auth/login", "/api/auth/register"}


async def csrf_middleware(request: Request, call_next):
    if request.method in _SAFE_METHODS or request.url.path in _EXEMPT_PATHS:
        return await call_next(request)

    sid = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not sid:
        # Sin sesión: la dependencia de auth se encargará del 401.
        return await call_next(request)

    header_token = request.headers.get(settings.CSRF_HEADER_NAME, "")
    expected_token = derive_csrf_token(sid)

    # Comparación en tiempo constante (OWASP ASVS 6.2.4 / evitar side-channel
    # por timing), aunque el riesgo práctico en un token CSRF sea bajo.
    if not header_token or not hmac.compare_digest(header_token, expected_token):
        return JSONResponse(status_code=403, content={"error": AuthMessages.CSRF_INVALIDO})

    return await call_next(request)
