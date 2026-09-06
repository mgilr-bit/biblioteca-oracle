"""FastAPI app factory — reemplaza app.py (Flask)."""
import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.casbin_enforcer import ensure_default_policies
from core.config import settings
from core.csrf import csrf_middleware
from core.messages import GenericMessages
from core.rate_limit import limiter
from core.request_limits import body_size_limit_middleware
from core.security_headers import security_headers_middleware
from routers import (
    auditoria_router,
    auth_router,
    editorial_router,
    ejemplar_router,
    libro_router,
    multa_router,
    notificacion_router,
    prestamo_router,
    reserva_router,
    usuario_router,
)
from services.exceptions import ServiceError

if not os.path.exists("logs"):
    os.mkdir("logs")

file_handler = RotatingFileHandler("logs/biblioteca.log", maxBytes=10_240_000, backupCount=10)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
)
logging.getLogger().addHandler(file_handler)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_default_policies()
    logger.info("Biblioteca API startup")
    yield


app = FastAPI(
    title="API Sistema de Gestión de Biblioteca",
    version="2.0",
    lifespan=lifespan,
    # El HTML de /redoc que trae FastAPI por defecto apunta a
    # cdn.jsdelivr.net/npm/redoc@next/... — ese dist-tag "next" está roto
    # (404) en jsdelivr ahora mismo. Se desactiva la ruta automática y se
    # registra una propia más abajo con una versión fija que sí existe.
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Orden importa: Starlette hace que el último middleware añadido sea el más
# externo. CORS va al final para que sea el más externo de todos — así
# también les añade los headers CORS a las respuestas tempranas (403 de
# CSRF, 401 de sesión, 429 de rate limit) que se generan antes de llegar al
# router; si quedara más interno, el navegador no podría ni leer esos errores.
app.middleware("http")(security_headers_middleware)
app.middleware("http")(csrf_middleware)
app.middleware("http")(body_size_limit_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", settings.CSRF_HEADER_NAME],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Mantiene el contrato `{"error": ...}` que ya espera el frontend
    # (FastAPI por defecto devolvería `{"detail": ...}`).
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail}, headers=exc.headers)


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc)})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception(f"Error no controlado en {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"error": GenericMessages.ERROR_INTERNO})


@app.get("/redoc", include_in_schema=False)
def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js",
    )


app.include_router(auth_router, prefix="/api/auth")
app.include_router(libro_router, prefix="/api/libros")
app.include_router(usuario_router, prefix="/api/usuarios")
app.include_router(prestamo_router, prefix="/api/prestamos")
app.include_router(editorial_router, prefix="/api/editoriales")
app.include_router(ejemplar_router, prefix="/api/ejemplares")
app.include_router(reserva_router, prefix="/api/reservas")
app.include_router(notificacion_router, prefix="/api/notificaciones")
app.include_router(multa_router, prefix="/api/multas")
app.include_router(auditoria_router, prefix="/api/auditoria")


@app.get("/")
def home():
    return {
        "message": "API Sistema de Gestión de Biblioteca",
        "version": "2.0",
        "endpoints": {
            "auth": "/api/auth",
            "libros": "/api/libros",
            "usuarios": "/api/usuarios",
            "prestamos": "/api/prestamos",
            "editoriales": "/api/editoriales",
            "ejemplares": "/api/ejemplares",
            "reservas": "/api/reservas",
            "notificaciones": "/api/notificaciones",
        },
    }


@app.get("/api/health")
def health():
    try:
        from config.database import check_connection

        check_connection()
        return {"status": "healthy", "database": "connected"}
    except Exception as error:
        return JSONResponse(status_code=500, content={"status": "unhealthy", "error": str(error)})
