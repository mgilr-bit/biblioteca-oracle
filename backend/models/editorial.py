"""Entidad que representa la tabla EDITORIALES."""
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
    nombre: str = Field(min_length=1, max_length=100, index=True)
