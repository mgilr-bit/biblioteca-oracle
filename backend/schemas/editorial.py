"""DTOs del recurso Editorial."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EditorialResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id_editorial: int = Field(alias="ID_EDITORIAL")
    nombre: str = Field(alias="NOMBRE")
    pais: Optional[str] = Field(default=None, alias="PAIS")
    sitio_web: Optional[str] = Field(default=None, alias="SITIO_WEB")


class EditorialListResponse(BaseModel):
    editoriales: list[EditorialResponse]
    page: int
    per_page: int
    total: int
    total_pages: int


class EditorialCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    pais: Optional[str] = Field(default=None, max_length=100)
    sitio_web: Optional[str] = Field(default=None, max_length=255)


class EditorialUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    pais: Optional[str] = Field(default=None, max_length=100)
    sitio_web: Optional[str] = Field(default=None, max_length=255)