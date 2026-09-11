from .analytics_router import router as analytics_router
from .auditoria_router import router as auditoria_router
from .auth_router import router as auth_router
from .editorial_router import router as editorial_router
from .ejemplar_router import router as ejemplar_router
from .libro_router import router as libro_router
from .multa_router import router as multa_router
from .notificacion_router import router as notificacion_router
from .prestamo_router import router as prestamo_router
from .reserva_router import router as reserva_router
from .usuario_router import router as usuario_router

__all__ = [
    "analytics_router",
    "auditoria_router",
    "auth_router",
    "editorial_router",
    "ejemplar_router",
    "libro_router",
    "multa_router",
    "notificacion_router",
    "prestamo_router",
    "reserva_router",
    "usuario_router",
]
