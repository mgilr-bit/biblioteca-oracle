"""Repositorio de acceso a datos para la entidad Prestamo."""
from datetime import datetime

from sqlmodel import Session, select

from models.libro import Libro
from models.prestamo import Prestamo
from models.usuario import Usuario
from repositories.base import BaseRepository


class PrestamoRepository(BaseRepository[Prestamo]):
    def __init__(self, session: Session):
        super().__init__(session, Prestamo)

    def _query_with_details(self):
        return (
            select(Prestamo, Libro.titulo, Libro.autor, Usuario.nombre)
            .join(Libro, Prestamo.id_libro == Libro.id_libro)
            .join(Usuario, Prestamo.id_usuario == Usuario.id_usuario)
        )

    def get_all_with_details(self) -> list:
        stmt = self._query_with_details().order_by(Prestamo.fecha_prestamo.desc())
        return list(self.session.execute(stmt).all())

    def get_activos_with_details(self) -> list:
        stmt = (
            self._query_with_details()
            .where(Prestamo.estado == "ACTIVO")
            .order_by(Prestamo.fecha_devolucion_esperada)
        )
        return list(self.session.execute(stmt).all())

    def get_by_usuario_with_details(self, id_usuario: int) -> list:
        stmt = (
            self._query_with_details()
            .where(Prestamo.id_usuario == id_usuario)
            .order_by(Prestamo.fecha_prestamo.desc())
        )
        return list(self.session.execute(stmt).all())

    def get_vencidos_with_details(self) -> list:
        stmt = (
            self._query_with_details()
            .where(
                Prestamo.estado == "ACTIVO",
                Prestamo.fecha_devolucion_esperada < datetime.now(),
            )
            .order_by(Prestamo.fecha_devolucion_esperada)
        )
        return list(self.session.execute(stmt).all())
