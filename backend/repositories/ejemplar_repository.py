"""Repositorio de acceso a datos para la entidad Ejemplar."""
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from models.ejemplar import Ejemplar
from models.libro import Libro
from repositories.base import BaseRepository


class EjemplarRepository(BaseRepository[Ejemplar]):
    def __init__(self, session: Session):
        super().__init__(session, Ejemplar)

    def _query_with_details(self):
        return (
            select(Ejemplar, Libro.titulo)
            .join(Libro, Ejemplar.id_libro == Libro.id_libro)
            .where(Ejemplar.is_deleted == False)  # noqa: E712
        )

    def count(self, *, id_libro: Optional[int] = None, estado: Optional[str] = None) -> int:
        conditions = [Ejemplar.is_deleted == False]  # noqa: E712
        if id_libro:
            conditions.append(Ejemplar.id_libro == id_libro)
        if estado:
            conditions.append(Ejemplar.estado == estado)
        stmt = select(func.count(Ejemplar.id_ejemplar)).where(*conditions)
        return self.session.execute(stmt).scalar_one()

    def get_paginated_with_details(
        self, offset: int, per_page: int, *, id_libro: Optional[int] = None, estado: Optional[str] = None
    ) -> List:
        conditions = [Ejemplar.is_deleted == False]  # noqa: E712
        if id_libro:
            conditions.append(Ejemplar.id_libro == id_libro)
        if estado:
            conditions.append(Ejemplar.estado == estado)
        stmt = (
            self._query_with_details()
            .where(*conditions)
            .order_by(Ejemplar.codigo_ejemplar)
            .offset(offset)
            .limit(per_page)
        )
        return list(self.session.execute(stmt).all())

    def get_by_libro(self, id_libro: int) -> List[Ejemplar]:
        stmt = (
            select(Ejemplar)
            .where(Ejemplar.is_deleted == False, Ejemplar.id_libro == id_libro)  # noqa: E712
            .order_by(Ejemplar.codigo_ejemplar)
        )
        return list(self.session.exec(stmt))

    def get_by_codigo(self, codigo: str) -> Optional[Ejemplar]:
        stmt = (
            select(Ejemplar)
            .where(Ejemplar.is_deleted == False, func.upper(Ejemplar.codigo_ejemplar) == codigo.upper())  # noqa: E712
            .limit(1)
        )
        return self.session.exec(stmt).first()

    def get_primer_disponible(self, id_libro: int) -> Optional[Ejemplar]:
        stmt = (
            select(Ejemplar)
            .where(
                Ejemplar.is_deleted == False,  # noqa: E712
                Ejemplar.id_libro == id_libro,
                Ejemplar.estado == "DISPONIBLE",
            )
            .order_by(Ejemplar.codigo_ejemplar)
            .limit(1)
        )
        return self.session.exec(stmt).first()

    def count_estado(self, id_libro: int, estado: str) -> int:
        stmt = select(func.count(Ejemplar.id_ejemplar)).where(
            Ejemplar.is_deleted == False,  # noqa: E712
            Ejemplar.id_libro == id_libro,
            Ejemplar.estado == estado,
        )
        return self.session.execute(stmt).scalar_one()

    def get_estados(self) -> List[str]:
        stmt = (
            select(Ejemplar.estado)
            .where(Ejemplar.is_deleted == False)  # noqa: E712
            .distinct()
            .order_by(Ejemplar.estado)
        )
        return [row[0] for row in self.session.execute(stmt).all()]