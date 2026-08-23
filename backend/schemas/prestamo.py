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
    fecha_prestamo: Optional[datetime] = Field(default=None, alias="FECHA_PRESTAMO")
    fecha_devolucion_esperada: Optional[datetime] = Field(default=None, alias="FECHA_DEVOLUCION_ESPERADA")
    fecha_devolucion_real: Optional[datetime] = Field(default=None, alias="FECHA_DEVOLUCION_REAL")
    estado: str = Field(alias="ESTADO")
    titulo: str = Field(alias="TITULO")
    autor: str = Field(alias="AUTOR")
    nombre_usuario: str = Field(alias="NOMBRE_USUARIO")


class PrestamoCreate(BaseModel):
    id_libro: int
    id_usuario: Optional[int] = None
    dias_prestamo: Optional[int] = None
