"""DTOs del recurso Usuario (nunca incluyen el hash de password)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id_usuario: int = Field(alias="ID_USUARIO")
    nombre: str = Field(alias="NOMBRE")
    email: str = Field(alias="EMAIL")
    rol: str = Field(alias="ROL")
    fecha_registro: Optional[datetime] = Field(default=None, alias="FECHA_REGISTRO")
    activo: str = Field(alias="ACTIVO")


class UsuarioAdminCreate(BaseModel):
    nombre: str
    email: str
    password: str
    rol: str


class UsuarioUpdate(BaseModel):
    nombre: str
    email: str
    rol: str


class UsuarioEstadoUpdate(BaseModel):
    activo: str
