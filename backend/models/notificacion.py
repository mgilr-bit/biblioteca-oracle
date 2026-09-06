"""Entidad que representa la tabla NOTIFICACIONES (bandeja por usuario)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Identity, Integer, text
from sqlmodel import Field

from models.base import AuditMixin


class Notificacion(AuditMixin, table=True):
    __tablename__ = "notificaciones"

    id_notificacion: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, Identity(always=True), primary_key=True),
    )
    id_usuario: int = Field(foreign_key="usuarios.id_usuario", index=True)
    tipo: str = Field(min_length=1, max_length=40)
    mensaje: str = Field(min_length=1, max_length=500)
    leida: bool = Field(
        default=False,
        sa_column_kwargs={"server_default": "0"},
    )
    fecha_generacion: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": text("SYSTIMESTAMP")}
    )