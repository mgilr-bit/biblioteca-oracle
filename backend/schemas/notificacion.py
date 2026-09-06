"""DTOs del recurso Notificacion."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificacionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id_notificacion: int = Field(alias="ID_NOTIFICACION")
    id_usuario: int = Field(alias="ID_USUARIO")
    tipo: str = Field(alias="TIPO")
    mensaje: str = Field(alias="MENSAJE")
    leida: bool = Field(alias="LEIDA")
    fecha_generacion: Optional[datetime] = Field(default=None, alias="FECHA_GENERACION")


class NotificacionCountResponse(BaseModel):
    no_leidas: int


class MantenimientoResponse(BaseModel):
    success: bool
    message: str
    notificaciones_generadas: int
    reservas_expiradas: int