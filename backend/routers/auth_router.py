"""Router de autenticación: login/registro emiten cookie de sesión + CSRF."""
import logging

from fastapi import APIRouter, Depends, Request, Response
from fastapi.concurrency import run_in_threadpool

from config.database import get_session
from core.config import settings
from core.rate_limit import limiter
from core.sessions import create_session, derive_csrf_token, revoke_session
from dependencies.auth import get_current_user
from models.usuario import Usuario
from schemas.auth import LoginRequest, LoginResponse, RegisterRequest, SessionUserResponse
from schemas.common import MessageResponse
from services.auth_service import AuthService

router = APIRouter()
logger = logging.getLogger(__name__)


def _do_login(email: str, password: str) -> Usuario:
    """Bloqueante (Oracle) — se corre en threadpool, no en el event loop."""
    with get_session() as session:
        usuario = AuthService(session).login(email, password)
        session.expunge(usuario)  # desprende la entidad de la sesión que está por cerrarse
        return usuario


def _do_register(nombre: str, email: str, password: str) -> dict:
    with get_session() as session:
        return AuthService(session).register(nombre, email, password)


def _set_session_cookies(response: Response, sid: str) -> None:
    csrf_token = derive_csrf_token(sid)
    common = dict(
        max_age=settings.SESSION_IDLE_TTL_SECONDS,
        secure=settings.is_production,
        samesite=settings.cookie_samesite,
    )
    # `sid` va con Path=/api: solo el backend la necesita (httpOnly), y así
    # el navegador solo la manda hacia /api/*.
    # `XSRF-TOKEN` va con Path=/ (no puede ser /api): el frontend es una SPA
    # en un origen aparte cuyas rutas (/libros, /prestamos, ...) no caen
    # bajo /api, y `document.cookie` solo expone una cookie cuando el Path
    # de la cookie es prefijo de la página actual — con Path=/api nunca
    # sería legible desde ninguna ruta del SPA.
    response.set_cookie(settings.SESSION_COOKIE_NAME, sid, httponly=True, path="/api", **common)
    response.set_cookie(settings.CSRF_COOKIE_NAME, csrf_token, httponly=False, path="/", **common)


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/api")
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")


@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(request: Request, response: Response, body: LoginRequest):
    usuario = await run_in_threadpool(_do_login, body.email, body.password)

    sid = await create_session(
        user_id=usuario.id_usuario,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=usuario.rol,
        ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )
    _set_session_cookies(response, sid)

    user_response = SessionUserResponse(
        id=usuario.id_usuario, nombre=usuario.nombre, email=usuario.email, rol=usuario.rol
    )
    return LoginResponse(success=True, user=user_response, message="Login exitoso")


@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(request: Request, body: RegisterRequest):
    return await run_in_threadpool(_do_register, body.nombre, body.email, body.password)


@router.get("/me", response_model=SessionUserResponse)
async def me(user=Depends(get_current_user)):
    return SessionUserResponse(id=user.id, nombre=user.nombre, email=user.email, rol=user.rol)


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response, user=Depends(get_current_user)):
    await revoke_session(user.sid, user.id, reason="logout")
    _clear_session_cookies(response)
    return {"success": True, "message": "Sesión cerrada"}
