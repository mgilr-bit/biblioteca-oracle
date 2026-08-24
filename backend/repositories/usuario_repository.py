"""Repositorio de acceso a datos para la entidad Usuario."""
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from models.prestamo import Prestamo
from models.usuario import Usuario
from repositories.base import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: Session):
        super().__init__(session, Usuario)

    def get_by_email(self, email: str) -> Optional[Usuario]:
        """Sin filtrar is_deleted a propósito: se usa tanto para login como
        para chequear duplicados al registrar/crear, y en ambos casos hay
        que ver también las cuentas borradas (no permitir re-registrar ese
        email, y que el login de una cuenta borrada falle explícitamente
        en vez de simplemente "no encontrada")."""
        stmt = select(Usuario).where(Usuario.email == email)
        return self.session.exec(stmt).first()

    def get_all(self) -> List[Usuario]:
        stmt = select(Usuario).where(Usuario.is_deleted == False).order_by(Usuario.nombre)  # noqa: E712
        return list(self.session.exec(stmt))

    def count_active_prestamos(self, id_usuario: int) -> int:
        stmt = select(func.count(Prestamo.id_prestamo)).where(
            Prestamo.id_usuario == id_usuario,
            Prestamo.estado.in_(("ACTIVO", "VENCIDO")),
        )
        return self.session.execute(stmt).scalar_one()
