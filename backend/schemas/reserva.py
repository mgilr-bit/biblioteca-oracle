"""DTOs del recurso Reserva."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReservaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_reserva: int = Field(alias="ID_RESERVA")
    id_libro: int = Field(alias="ID_LIBRO")
    id_usuario: int = Field(alias="ID_USUARIO")
    fecha_reserva: Optional[datetime] = Field(default=None, alias="FECHA_RESERVA")
    estado: str = Field(alias="ESTADO")
    fecha_expiracion: Optional[datetime] = Field(default=None, alias="FECHA_EXPIRACION")
    titulo: str = Field(alias="TITULO")
    autor: str = Field(alias="AUTOR")
    nombre_usuario: str = Field(alias="NOMBRE_USUARIO")


class ReservaCreate(BaseModel):
    id_libro: int = Field(ge=1)
    id_usuario: Optional[int] = Field(default=None, ge=1)