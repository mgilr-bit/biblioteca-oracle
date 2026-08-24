"""DTOs del recurso Libro."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LibroResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id_libro: int = Field(alias="ID_LIBRO")
    titulo: str = Field(alias="TITULO")
    autor: str = Field(alias="AUTOR")
    isbn: Optional[str] = Field(default=None, alias="ISBN")
    anio_publicacion: Optional[int] = Field(default=None, alias="ANIO_PUBLICACION")
    genero: Optional[str] = Field(default=None, alias="GENERO")
    numero_copias: int = Field(alias="NUMERO_COPIAS")
    copias_disponibles: int = Field(alias="COPIAS_DISPONIBLES")
    fecha_registro: Optional[datetime] = Field(default=None, alias="FECHA_REGISTRO")
    editorial: Optional[str] = Field(default=None, alias="EDITORIAL")


class LibroListResponse(BaseModel):
    libros: list[LibroResponse]
    page: int
    per_page: int
    total: int
    total_pages: int


class LibroCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=150)
    isbn: Optional[str] = Field(default=None, max_length=20)
    anio_publicacion: Optional[int] = Field(default=None, ge=1900, le=2030)
    genero: Optional[str] = Field(default=None, max_length=50)
    numero_copias: int = Field(default=1, ge=0, le=10_000)
    editorial: Optional[str] = Field(default=None, max_length=100)


class LibroUpdate(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=150)
    isbn: Optional[str] = Field(default=None, max_length=20)
    anio_publicacion: Optional[int] = Field(default=None, ge=1900, le=2030)
    genero: Optional[str] = Field(default=None, max_length=50)
    numero_copias: Optional[int] = Field(default=None, ge=0, le=10_000)
    editorial: Optional[str] = Field(default=None, max_length=100)


class LibroCopiasUpdate(BaseModel):
    copias_disponibles: int = Field(ge=0, le=10_000)


class LibroEstadisticasResponse(BaseModel):
    total_libros: int
    total_disponibles: int
    total_copias: int
    bajo_stock: int
