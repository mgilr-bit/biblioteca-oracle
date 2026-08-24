"""Entidad que representa la tabla USUARIOS."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Identity, Integer, text
from sqlmodel import Field

from models.base import AuditMixin


class Usuario(AuditMixin, table=True):
    __tablename__ = "usuarios"

    id_usuario: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, Identity(always=True), primary_key=True),
    )
    nombre: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=100, unique=True, index=True)
    password: str = Field(max_length=255)
    rol: str = Field(default="LECTOR", max_length=20)
    fecha_registro: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": text("SYSDATE")}
    )
    activo: str = Field(default="S", max_length=1)
