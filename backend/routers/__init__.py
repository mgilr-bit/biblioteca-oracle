from .auth_router import router as auth_router
from .libro_router import router as libro_router
from .prestamo_router import router as prestamo_router
from .usuario_router import router as usuario_router

__all__ = ["auth_router", "libro_router", "prestamo_router", "usuario_router"]
