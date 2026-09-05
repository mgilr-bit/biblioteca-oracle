"""DTOs del recurso Prestamo. La respuesta se arma a mano en el service porque
sale de un join (Prestamo + Libro + Usuario), no de una sola entidad ORM."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PrestamoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_prestamo: int = Field(alias="ID_PRESTAMO")
    id_libro: int = Field(alias="ID_LIBRO")
    id_usuario: int = Field(alias="ID_USUARIO")
    id_ejemplar: Optional[int] = Field(default=None, alias="ID_EJEMPLAR")
    codigo_ejemplar: Optional[str] = Field(default=None, alias="CODIGO_EJEMPLAR")
    fecha_prestamo: Optional[datetime] = Field(default=None, alias="FECHA_PRESTAMO")
    fecha_devolucion_esperada: Optional[datetime] = Field(default=None, alias="FECHA_DEVOLUCION_ESPERADA")
    fecha_devolucion_real: Optional[datetime] = Field(default=None, alias="FECHA_DEVOLUCION_REAL")
    estado: str = Field(alias="ESTADO")
    titulo: str = Field(alias="TITULO")
    autor: str = Field(alias="AUTOR")
    nombre_usuario: str = Field(alias="NOMBRE_USUARIO")


class PrestamoCreate(BaseModel):
    id_libro: int = Field(ge=1)
    id_usuario: Optional[int] = Field(default=None, ge=1)
    dias_prestamo: Optional[int] = Field(default=None, ge=1, le=90)
