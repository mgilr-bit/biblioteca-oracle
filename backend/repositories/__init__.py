from .base import BaseRepository
from .libro_repository import LibroRepository
from .prestamo_repository import PrestamoRepository
from .usuario_repository import UsuarioRepository

__all__ = [
    "BaseRepository",
    "LibroRepository",
    "PrestamoRepository",
    "UsuarioRepository",
]
