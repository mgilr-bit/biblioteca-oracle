"""Headers de seguridad tipo Helmet."""
from core.config import settings

_BASE_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-Download-Options": "noopen",
    "X-XSS-Protection": "0",
}

_DEFAULT_CSP = "default-src 'self'"

# Swagger UI (FastAPI /docs) y ReDoc (/redoc) cargan sus assets desde
# cdn.jsdelivr.net + un script inline — con el CSP por defecto quedan en
# blanco. Se afloja el CSP solo en estas rutas de documentación, igual al
# patrón `cspPerRoute` usado en wallet-api para su ruta de docs.
_DOCS_PATHS = {"/docs", "/redoc", "/docs/oauth2-redirect"}
_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "worker-src 'self' blob:; "
    "connect-src 'self'"
)


async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    for header, value in _BASE_HEADERS.items():
        response.headers[header] = value
    response.headers["Content-Security-Policy"] = (
        _DOCS_CSP if request.url.path in _DOCS_PATHS else _DEFAULT_CSP
    )
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response
