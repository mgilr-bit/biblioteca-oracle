"""DTOs del recurso de autenticación."""
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    nombre: str
    email: str
    password: str


class SessionUserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: int
    nombre: str = Field(default="")
    email: str
    rol: str


class LoginResponse(BaseModel):
    success: bool
    user: SessionUserResponse
    message: str
