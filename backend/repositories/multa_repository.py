"""Repositorio de acceso a datos para la entidad Multa."""
from sqlmodel import Session, func, select

from models.libro import Libro
from models.multa import Multa
from models.prestamo import Prestamo
from models.usuario import Usuario
from repositories.base import BaseRepository


class MultaRepository(BaseRepository[Multa]):
    def __init__(self, session: Session):
        super().__init__(session, Multa)

    def _query_with_details(self):
        return (
            select(Multa, Libro.titulo, Usuario.nombre)
            .join(Prestamo, Multa.id_prestamo == Prestamo.id_prestamo)
            .join(Libro, Prestamo.id_libro == Libro.id_libro)
            .join(Usuario, Multa.id_usuario == Usuario.id_usuario)
            .where(Multa.is_deleted == False)  # noqa: E712
        )

    def get_all_with_details(self) -> list:
        stmt = self._query_with_details().order_by(Multa.created_at.desc())
        return list(self.session.execute(stmt).all())

    def get_pendientes_with_details(self) -> list:
        stmt = (
            self._query_with_details()
            .where(Multa.estado == "PENDIENTE")
            .order_by(Multa.created_at.desc())
        )
        return list(self.session.execute(stmt).all())

    def get_by_usuario_with_details(self, id_usuario: int) -> list:
        stmt = (
            self._query_with_details()
            .where(Multa.id_usuario == id_usuario)
            .order_by(Multa.created_at.desc())
        )
        return list(self.session.execute(stmt).all())

    def get_pendiente_by_prestamo(self, id_prestamo: int) -> Multa | None:
        stmt = (
            select(Multa)
            .where(
                Multa.id_prestamo == id_prestamo,
                Multa.estado == "PENDIENTE",
                Multa.is_deleted == False,  # noqa: E712
            )
        )
        return self.session.exec(stmt).first()

    def usuario_tiene_pendientes(self, id_usuario: int) -> bool:
        """True si el usuario tiene al menos una multa en PENDIENTE (bloqueo
        de nuevos préstamos)."""
        stmt = select(func.count(Multa.id_multa)).where(
            Multa.id_usuario == id_usuario,
            Multa.estado == "PENDIENTE",
            Multa.is_deleted == False,  # noqa: E712
        )
        total = self.session.exec(stmt).one()
        return bool(total > 0)
