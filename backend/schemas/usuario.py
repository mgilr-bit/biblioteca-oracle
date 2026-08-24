"""DTOs del recurso Usuario (nunca incluyen el hash de password)."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id_usuario: int = Field(alias="ID_USUARIO")
    nombre: str = Field(alias="NOMBRE")
    email: str = Field(alias="EMAIL")
    rol: str = Field(alias="ROL")
    fecha_registro: Optional[datetime] = Field(default=None, alias="FECHA_REGISTRO")
    activo: str = Field(alias="ACTIVO")


class UsuarioAdminCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    rol: Literal["LECTOR", "BIBLIOTECARIO"]


class UsuarioUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: EmailStr
    rol: Literal["LECTOR", "BIBLIOTECARIO"]


class UsuarioEstadoUpdate(BaseModel):
    activo: Literal["S", "N"]
