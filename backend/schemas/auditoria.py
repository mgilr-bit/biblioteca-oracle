"""DTOs del recurso Auditoria (bitácora de eventos clave)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AuditoriaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id_auditoria: int = Field(alias="ID_AUDITORIA")
    id_usuario: Optional[int] = Field(default=None, alias="ID_USUARIO")
    email: Optional[str] = Field(default=None, alias="EMAIL")
    rol: Optional[str] = Field(default=None, alias="ROL")
    accion: str = Field(alias="ACCION")
    recurso: str = Field(alias="RECURSO")
    id_recurso: Optional[int] = Field(default=None, alias="ID_RECURSO")
    detalle: Optional[str] = Field(default=None, alias="DETALLE")
    created_at: datetime = Field(alias="FECHA")


class AuditoriaListResponse(BaseModel):
    auditoria: list[AuditoriaResponse]
    page: int
    per_page: int
    total: int
    total_pages: int