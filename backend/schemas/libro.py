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
    titulo: str
    autor: str
    isbn: Optional[str] = None
    anio_publicacion: Optional[int] = None
    genero: Optional[str] = None
    numero_copias: int = 1
    editorial: Optional[str] = None


class LibroUpdate(BaseModel):
    titulo: str
    autor: str
    isbn: Optional[str] = None
    anio_publicacion: Optional[int] = None
    genero: Optional[str] = None
    numero_copias: Optional[int] = None
    editorial: Optional[str] = None


class LibroCopiasUpdate(BaseModel):
    copias_disponibles: int


class LibroEstadisticasResponse(BaseModel):
    total_libros: int
    total_disponibles: int
    total_copias: int
    bajo_stock: int
