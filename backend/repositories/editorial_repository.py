"""Repositorio de acceso a datos para la entidad Editorial."""
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from models.editorial import Editorial
from models.libro import Libro
from repositories.base import BaseRepository


class EditorialRepository(BaseRepository[Editorial]):
    def __init__(self, session: Session):
        super().__init__(session, Editorial)

    def get_all(self) -> List[Editorial]:
        stmt = select(Editorial).where(Editorial.is_deleted == False).order_by(Editorial.nombre)  # noqa: E712
        return list(self.session.exec(stmt))

    def get_by_nombre(self, nombre: str) -> Optional[Editorial]:
        """Búsqueda case-insensitive entre las editoriales no borradas."""
        stmt = select(Editorial).where(
            Editorial.is_deleted == False,  # noqa: E712
            func.upper(Editorial.nombre) == nombre.strip().upper(),
        )
        return self.session.exec(stmt).first()

    def count_libros(self, id_editorial: int) -> int:
        stmt = select(func.count(Libro.id_libro)).where(
            Libro.id_editorial == id_editorial,
            Libro.is_deleted == False,  # noqa: E712
        )
        return self.session.execute(stmt).scalar_one()
