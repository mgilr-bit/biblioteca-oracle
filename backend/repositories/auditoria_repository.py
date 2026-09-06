"""Repositorio de acceso a datos para la bitácora de auditoría."""
from typing import Optional

from sqlmodel import Session, func, select

from models.auditoria import Auditoria
from repositories.base import BaseRepository


class AuditoriaRepository(BaseRepository[Auditoria]):
    def __init__(self, session: Session):
        super().__init__(session, Auditoria)

    def _filtros(self, accion: Optional[str], recurso: Optional[str], id_usuario: Optional[int]):
        cond = []
        if accion:
            cond.append(Auditoria.accion == accion)
        if recurso:
            cond.append(Auditoria.recurso == recurso)
        if id_usuario:
            cond.append(Auditoria.id_usuario == id_usuario)
        return cond

    def search(
        self,
        offset: int,
        limit: int,
        accion: Optional[str] = None,
        recurso: Optional[str] = None,
        id_usuario: Optional[int] = None,
    ) -> list:
        stmt = (
            select(Auditoria)
            .where(*self._filtros(accion, recurso, id_usuario))
            .order_by(Auditoria.created_at.desc(), Auditoria.id_auditoria.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(stmt).all())

    def count(
        self,
        accion: Optional[str] = None,
        recurso: Optional[str] = None,
        id_usuario: Optional[int] = None,
    ) -> int:
        stmt = select(func.count(Auditoria.id_auditoria)).where(
            *self._filtros(accion, recurso, id_usuario)
        )
        total = self.session.exec(stmt).one()
        return int(total)