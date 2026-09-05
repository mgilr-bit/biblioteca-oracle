"""Entidad que representa la tabla EJEMPLARES (una fila por copia física).

Cada copia de un libro tiene un estado que se mueve solo (prestar/devolver
marcan PRESTADO/DISPONIBLE) o por gestión del bibliotecario (reparación,
baja, etc.). Los estados válidos viven en
`services.ejemplar_service.EJEMPLAR_ESTADOS`.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Identity, Integer, text
from sqlmodel import Field

from models.base import AuditMixin


class Ejemplar(AuditMixin, table=True):
    __tablename__ = "ejemplares"

    id_ejemplar: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, Identity(always=True), primary_key=True),
    )
    id_libro: int = Field(foreign_key="libros.id_libro", index=True)
    codigo_ejemplar: str = Field(min_length=1, max_length=40)
    estado: str = Field(
        default="DISPONIBLE",
        max_length=20,
        sa_column_kwargs={"server_default": text("'DISPONIBLE'")},
    )
    ubicacion: Optional[str] = Field(default=None, max_length=100)
    fecha_adquisicion: Optional[datetime] = Field(default=None)