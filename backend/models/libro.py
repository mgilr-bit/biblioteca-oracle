"""Entidad que representa la tabla LIBROS."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Identity, Integer, text
from sqlmodel import Field, Relationship

from models.base import AuditMixin
from models.editorial import Editorial


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

    editorial_rel: Optional[Editorial] = Relationship()

    @property
    def editorial(self) -> Optional[str]:
        """Nombre de la editorial del catálogo (contrato de la API: EDITORIAL).

        Ya no es una columna: la fuente de verdad es `id_editorial`; el
        nombre se deriva de la relación (migración 0012 eliminó el texto).
        """
        return self.editorial_rel.nombre if self.editorial_rel else None
