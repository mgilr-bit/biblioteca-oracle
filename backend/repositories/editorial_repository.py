"""Repositorio de acceso a datos para la entidad Editorial."""
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from models.editorial import Editorial
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