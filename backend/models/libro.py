"""Entidad que representa la tabla LIBROS."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Identity, Integer, text
from sqlmodel import Field

from models.base import AuditMixin


class Libro(AuditMixin, table=True):
    __tablename__ = "libros"

    id_libro: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, Identity(always=True), primary_key=True),
    )
    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=150)
    isbn: Optional[str] = Field(default=None, max_length=20, unique=True)
    anio_publicacion: Optional[int] = Field(default=None, ge=1900, le=2030)
    genero: Optional[str] = Field(default=None, max_length=50)
    numero_copias: int = Field(default=1, ge=0)
    copias_disponibles: int = Field(default=1, ge=0)
    fecha_registro: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": text("SYSDATE")}
    )
    id_editorial: Optional[int] = Field(default=None, foreign_key="editoriales.id_editorial", index=True)
    editorial: Optional[str] = Field(default=None, max_length=100)
