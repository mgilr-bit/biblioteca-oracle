"""Repositorio de acceso a datos para la entidad Reserva."""
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from core.zona_horaria import ahora_utc
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

    def get_en_cola(self, id_libro: int) -> List[Reserva]:
        """ACTIVA sin copia apartada todavía (sin fecha de expiración), en orden FIFO."""
        stmt = (
            select(Reserva)
            .where(
                Reserva.is_deleted == False,  # noqa: E712
                Reserva.id_libro == id_libro,
                Reserva.estado == "ACTIVA",
                Reserva.fecha_expiracion.is_(None),
            )
            .order_by(Reserva.fecha_reserva)
        )
        return list(self.session.exec(stmt))

    def get_libros_con_cola(self) -> List[int]:
        stmt = (
            select(Reserva.id_libro)
            .where(
                Reserva.is_deleted == False,  # noqa: E712
                Reserva.estado == "ACTIVA",
                Reserva.fecha_expiracion.is_(None),
            )
            .distinct()
        )
        return list(self.session.exec(stmt))

    def count_apartadas(self, id_libro: int, excluir_usuario: Optional[int] = None) -> int:
        """Copias apartadas: reservas ACTIVA con ventana de recogida abierta."""
        conditions = [
            Reserva.is_deleted == False,  # noqa: E712
            Reserva.id_libro == id_libro,
            Reserva.estado == "ACTIVA",
            Reserva.fecha_expiracion.is_not(None),
        ]
        if excluir_usuario is not None:
            conditions.append(Reserva.id_usuario != excluir_usuario)
        stmt = select(func.count(Reserva.id_reserva)).where(*conditions)
        return self.session.execute(stmt).scalar_one()

    def get_activa_de_usuario(self, id_libro: int, id_usuario: int) -> Optional[Reserva]:
        stmt = (
            select(Reserva)
            .where(
                Reserva.is_deleted == False,  # noqa: E712
                Reserva.id_libro == id_libro,
                Reserva.id_usuario == id_usuario,
                Reserva.estado == "ACTIVA",
            )
            .order_by(Reserva.fecha_reserva)
        )
        return self.session.exec(stmt).first()

    def get_copias_disponibles(self, id_libro: int) -> int:
        # Consulta directa: los triggers de PRESTAMOS cambian este valor en la
        # BD y la entidad Libro en sesión podría tenerlo desactualizado.
        stmt = select(Libro.copias_disponibles).where(Libro.id_libro == id_libro)
        return self.session.execute(stmt).scalar_one_or_none() or 0

    def get_cola_with_details(self, id_libro: int) -> list:
        """Misma cola FIFO que `get_activas_fifo`, con el nombre del usuario."""
        stmt = (
            self._query_with_details()
            .where(Reserva.id_libro == id_libro, Reserva.estado == "ACTIVA")
            .order_by(Reserva.fecha_reserva)
        )
        return list(self.session.execute(stmt).all())

    def get_vencidas_sin_recoger(self) -> List[Reserva]:
        """ACTIVA cuya ventana de recogida ya venció (pasan a SIN_RECOGER)."""
        stmt = (
            select(Reserva)
            .where(
                Reserva.is_deleted == False,  # noqa: E712
                Reserva.estado == "ACTIVA",
                Reserva.fecha_expiracion.is_not(None),
                Reserva.fecha_expiracion < ahora_utc(),
            )
            .order_by(Reserva.fecha_expiracion)
        )
        return list(self.session.exec(stmt))
