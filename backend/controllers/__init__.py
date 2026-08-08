from .auth_controller import auth_bp
from .libro_controller import libros_bp
from .prestamo_controller import prestamos_bp
from .usuario_controller import usuarios_bp

__all__ = ["auth_bp", "libros_bp", "prestamos_bp", "usuarios_bp"]
