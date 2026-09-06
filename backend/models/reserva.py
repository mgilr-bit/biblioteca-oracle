"""Entidad que representa la tabla RESERVAS.

Una reserva encola a un usuario sobre un libro. Las reglas (máximo de
reservas activas por usuario, sin duplicados, cola FIFO, ventana de
recogida) viven en `services.reserva_service.ReservaService`.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Identity, Integer, text
from sqlmodel import Field

from models.base import AuditMixin


class Reserva(AuditMixin, table=True):
    __tablename__ = "reservas"

    id_reserva: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, Identity(always=True), primary_key=True),
    )
    id_libro: int = Field(foreign_key="libros.id_libro", index=True)
    id_usuario: int = Field(foreign_key="usuarios.id_usuario", index=True)
    fecha_reserva: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": text("SYSTIMESTAMP")}
    )
    estado: str = Field(default="ACTIVA", max_length=20)
    fecha_expiracion: Optional[datetime] = Field(default=None)