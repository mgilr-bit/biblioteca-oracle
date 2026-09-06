"""DTOs del recurso Ejemplar."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EjemplarResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_ejemplar: int = Field(alias="ID_EJEMPLAR")
    id_libro: int = Field(alias="ID_LIBRO")
    codigo_ejemplar: str = Field(alias="CODIGO_EJEMPLAR")
    estado: str = Field(alias="ESTADO")
    ubicacion: Optional[str] = Field(default=None, alias="UBICACION")
    fecha_adquisicion: Optional[datetime] = Field(default=None, alias="FECHA_ADQUISICION")
    titulo: str = Field(alias="TITULO")


class EjemplarListResponse(BaseModel):
    ejemplares: list[EjemplarResponse]
    page: int
    per_page: int
    total: int
    total_pages: int


class EjemplarCreate(BaseModel):
    id_libro: int
    codigo_ejemplar: Optional[str] = Field(default=None, max_length=40)
    ubicacion: Optional[str] = Field(default=None, max_length=100)
    fecha_adquisicion: Optional[datetime] = Field(default=None)


class EjemplarUpdate(BaseModel):
    ubicacion: Optional[str] = Field(default=None, max_length=100)
    fecha_adquisicion: Optional[datetime] = Field(default=None)


class EjemplarEstadoUpdate(BaseModel):
    estado: str = Field(min_length=1, max_length=20)