"""Entidad que representa la tabla PRESTAMOS."""
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlmodel import Field, SQLModel


class Prestamo(SQLModel, table=True):
    __tablename__ = "prestamos"

    id_prestamo: Optional[int] = Field(default=None, primary_key=True)
    id_libro: int = Field(foreign_key="libros.id_libro", index=True)
    id_usuario: int = Field(foreign_key="usuarios.id_usuario", index=True)
    fecha_prestamo: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": text("SYSDATE")}
    )
    fecha_devolucion_esperada: datetime
    fecha_devolucion_real: Optional[datetime] = Field(default=None)
    estado: str = Field(default="ACTIVO", max_length=20)
