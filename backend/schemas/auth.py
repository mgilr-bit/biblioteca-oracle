"""DTOs del recurso de autenticación."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RegisterRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


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
