"""Entidad que representa la tabla EDITORIALES (catálogo de editoriales).

Cada valor distinto que existía suelto en `libros.editorial` se promovió a
una fila de este catálogo (ver migración 0004). `AuditMixin` trae la
auditoría + soft-delete común, así un "borrado" nunca destruye el historial
de libros que lo referencian.
"""
from typing import Optional

from sqlalchemy import Column, Identity, Integer
from sqlmodel import Field

from models.base import AuditMixin


class Editorial(AuditMixin, table=True):
    __tablename__ = "editoriales"

    id_editorial: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, Identity(always=True), primary_key=True),
    )
    nombre: str = Field(min_length=1, max_length=100)
    pais: Optional[str] = Field(default=None, max_length=100)
    sitio_web: Optional[str] = Field(default=None, max_length=255)