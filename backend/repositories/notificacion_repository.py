"""Repositorio de acceso a datos para la entidad Notificacion."""
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from models.notificacion import Notificacion
from repositories.base import BaseRepository


class NotificacionRepository(BaseRepository[Notificacion]):
    def __init__(self, session: Session):
        super().__init__(session, Notificacion)

    def get_by_usuario(self, id_usuario: int, limit: int = 200) -> List[Notificacion]:
        stmt = (
            select(Notificacion)
            .where(
                Notificacion.is_deleted == False,  # noqa: E712
                Notificacion.id_usuario == id_usuario,
            )
            .order_by(Notificacion.fecha_generacion.desc())
            .limit(limit)
        )
        return list(self.session.exec(stmt))

    def get_no_leidas_count(self, id_usuario: int) -> int:
        stmt = select(func.count(Notificacion.id_notificacion)).where(
            Notificacion.is_deleted == False,  # noqa: E712
            Notificacion.id_usuario == id_usuario,
            Notificacion.leida == False,  # noqa: E712
        )
        return self.session.execute(stmt).scalar_one()

    def existe_para_usuario(self, id_usuario: int, tipo: str, mensaje: str) -> bool:
        stmt = select(func.count(Notificacion.id_notificacion)).where(
            Notificacion.is_deleted == False,  # noqa: E712
            Notificacion.id_usuario == id_usuario,
            Notificacion.tipo == tipo,
            Notificacion.mensaje == mensaje,
        )
        return self.session.execute(stmt).scalar_one() > 0