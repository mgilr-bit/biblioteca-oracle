from .base import BaseRepository
from .libro_repository import LibroRepository
from .multa_repository import MultaRepository
from .prestamo_repository import PrestamoRepository
from .usuario_repository import UsuarioRepository

__all__ = [
    "BaseRepository",
    "LibroRepository",
    "MultaRepository",
    "PrestamoRepository",
    "UsuarioRepository",
]
