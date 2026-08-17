"""Repositorio de acceso a datos para la entidad Libro."""
from typing import Dict, List

from sqlalchemy import and_, case, func
from sqlmodel import Session, select

from models.libro import Libro
from repositories.base import BaseRepository


class LibroRepository(BaseRepository[Libro]):
    def __init__(self, session: Session):
        super().__init__(session, Libro)

    def count(self) -> int:
        stmt = select(func.count(Libro.id_libro))
        return self.session.execute(stmt).scalar_one()

    def get_ordered_by_titulo(self) -> List[Libro]:
        stmt = select(Libro).order_by(Libro.titulo)
        return list(self.session.exec(stmt))

    def get_paginated(self, offset: int, per_page: int) -> List[Libro]:
        stmt = (
            select(Libro)
            .order_by(Libro.titulo)
            .offset(offset)
            .limit(per_page)
        )
        return list(self.session.exec(stmt))

    def get_first_n(self, limit: int) -> List[Libro]:
        stmt = select(Libro).order_by(Libro.titulo).limit(limit)
        return list(self.session.exec(stmt))

    def search(
        self,
        *,
        titulo: str = "",
        autor: str = "",
        isbn: str = "",
        genero: str = "",
        limit: int = 200,
    ) -> List[Libro]:
        conditions = []
        if titulo:
            conditions.append(func.upper(Libro.titulo).like(f"%{titulo.upper()}%"))
        if autor:
            conditions.append(func.upper(Libro.autor).like(f"%{autor.upper()}%"))
        if isbn:
            conditions.append(func.upper(Libro.isbn).like(f"%{isbn.upper()}%"))
        if genero:
            conditions.append(func.upper(Libro.genero).like(f"%{genero.upper()}%"))

        stmt = select(Libro).order_by(Libro.titulo).limit(limit)
        if conditions:
            stmt = stmt.where(*conditions)
        return list(self.session.exec(stmt))

    def get_generos(self) -> List[str]:
        stmt = (
            select(Libro.genero)
            .where(Libro.genero.is_not(None))
            .distinct()
            .order_by(Libro.genero)
        )
        return [row[0] for row in self.session.execute(stmt).all()]

    def get_bajo_stock(self) -> List[Libro]:
        stmt = (
            select(Libro)
            .where(Libro.copias_disponibles < 2)
            .order_by(Libro.copias_disponibles)
        )
        return list(self.session.exec(stmt))

    def get_estadisticas(self) -> Dict:
        stmt = select(
            func.count(Libro.id_libro).label("total_libros"),
            func.coalesce(func.sum(Libro.copias_disponibles), 0).label("total_disponibles"),
            func.coalesce(func.sum(Libro.numero_copias), 0).label("total_copias"),
            func.coalesce(
                func.sum(
                    case(
                        (and_(Libro.copias_disponibles <= 2, Libro.numero_copias > 0), 1),
                        else_=0,
                    )
                ),
                0,
            ).label("bajo_stock"),
        )
        row = self.session.execute(stmt).one()
        return dict(row._mapping)
