"""Repositorio de acceso a datos para la entidad Editorial."""
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from models.editorial import Editorial
from models.libro import Libro
from repositories.base import BaseRepository


class EditorialRepository(BaseRepository[Editorial]):
    def __init__(self, session: Session):
        super().__init__(session, Editorial)

    def count(self) -> int:
        stmt = select(func.count(Editorial.id_editorial)).where(Editorial.is_deleted == False)  # noqa: E712
        return self.session.execute(stmt).scalar_one()

    def get_paginated(self, offset: int, per_page: int) -> List[Editorial]:
        stmt = (
            select(Editorial)
            .where(Editorial.is_deleted == False)  # noqa: E712
            .order_by(Editorial.nombre)
            .offset(offset)
            .limit(per_page)
        )
        return list(self.session.exec(stmt))

    def get_ordered_by_nombre(self) -> List[Editorial]:
        stmt = (
            select(Editorial)
            .where(Editorial.is_deleted == False)  # noqa: E712
            .order_by(Editorial.nombre)
        )
        return list(self.session.exec(stmt))

    def contar_libros_por_editorial(self) -> Dict[int, int]:
        stmt = (
            select(Libro.id_editorial, func.count(Libro.id_libro))
            .where(Libro.is_deleted == False, Libro.id_editorial.is_not(None))  # noqa: E712
            .group_by(Libro.id_editorial)
        )
        return {id_editorial: total for id_editorial, total in self.session.execute(stmt).all()}

    def get_by_nombre(self, nombre: str) -> Optional[Editorial]:
        stmt = (
            select(Editorial)
            .where(
                Editorial.is_deleted == False,  # noqa: E712
                func.upper(Editorial.nombre) == nombre.upper(),
            )
            .limit(1)
        )
        return self.session.exec(stmt).first()