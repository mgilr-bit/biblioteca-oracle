"""Repositorio de acceso a datos para la entidad Reserva."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from models.libro import Libro
from models.reserva import Reserva
from models.usuario import Usuario
from repositories.base import BaseRepository


class ReservaRepository(BaseRepository[Reserva]):
    def __init__(self, session: Session):
        super().__init__(session, Reserva)

    def _query_with_details(self):
        return (
            select(Reserva, Libro.titulo, Libro.autor, Usuario.nombre)
            .join(Libro, Reserva.id_libro == Libro.id_libro)
            .join(Usuario, Reserva.id_usuario == Usuario.id_usuario)
            .where(Reserva.is_deleted == False)  # noqa: E712
        )

    def get_all_with_details(self) -> list:
        stmt = self._query_with_details().order_by(Reserva.fecha_reserva.desc())
        return list(self.session.execute(stmt).all())

    def get_by_usuario_with_details(self, id_usuario: int) -> list:
        stmt = (
            self._query_with_details()
            .where(Reserva.id_usuario == id_usuario)
            .order_by(Reserva.fecha_reserva.desc())
        )
        return list(self.session.execute(stmt).all())

    def count_activas_por_usuario(self, id_usuario: int) -> int:
        stmt = select(func.count(Reserva.id_reserva)).where(
            Reserva.id_usuario == id_usuario,
            Reserva.estado == "ACTIVA",
            Reserva.is_deleted == False,  # noqa: E712
        )
        return self.session.execute(stmt).scalar_one()

    def existe_activa(self, id_libro: int, id_usuario: int) -> bool:
        stmt = select(func.count(Reserva.id_reserva)).where(
            Reserva.id_libro == id_libro,
            Reserva.id_usuario == id_usuario,
            Reserva.estado == "ACTIVA",
            Reserva.is_deleted == False,  # noqa: E712
        )
        return self.session.execute(stmt).scalar_one() > 0

    def get_activas_fifo(self, id_libro: int) -> List[Reserva]:
        stmt = (
            select(Reserva)
            .where(
                Reserva.is_deleted == False,  # noqa: E712
                Reserva.id_libro == id_libro,
                Reserva.estado == "ACTIVA",
            )
            .order_by(Reserva.fecha_reserva)
        )
        return list(self.session.exec(stmt))

    def get_cumplidas_expiradas(self) -> List[Reserva]:
        """Reservas CUMPLIDA cuya ventana de recogida ya venció (para el job)."""
        stmt = (
            select(Reserva)
            .where(
                Reserva.is_deleted == False,  # noqa: E712
                Reserva.estado == "CUMPLIDA",
                Reserva.fecha_expiracion.is_not(None),
                Reserva.fecha_expiracion < datetime.now(),
            )
            .order_by(Reserva.fecha_expiracion)
        )
        return list(self.session.exec(stmt))