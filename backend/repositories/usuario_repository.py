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
        stmt = select(Usuario).where(Usuario.email == email)
        return self.session.exec(stmt).first()

    def get_all(self) -> List[Usuario]:
        stmt = select(Usuario).order_by(Usuario.nombre)
        return list(self.session.exec(stmt))

    def count_active_prestamos(self, id_usuario: int) -> int:
        stmt = select(func.count(Prestamo.id_prestamo)).where(
            Prestamo.id_usuario == id_usuario,
            Prestamo.estado.in_(("ACTIVO", "VENCIDO")),
        )
        return self.session.execute(stmt).scalar_one()
