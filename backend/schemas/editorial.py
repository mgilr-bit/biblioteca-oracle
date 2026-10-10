"""DTOs del recurso Editorial."""
from pydantic import BaseModel, ConfigDict, Field


class EditorialResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id_editorial: int = Field(alias="ID_EDITORIAL")
    nombre: str = Field(alias="NOMBRE")


class EditorialCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)


class EditorialUpdate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
