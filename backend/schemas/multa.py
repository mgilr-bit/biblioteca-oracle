"""DTOs del recurso Multa. La respuesta se arma a mano en el service porque
sale de un join (Multa + Prestamo + Libro + Usuario), no de una sola
entidad ORM."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MultaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_multa: int = Field(alias="ID_MULTA")
    id_prestamo: int = Field(alias="ID_PRESTAMO")
    id_usuario: int = Field(alias="ID_USUARIO")
    monto: Decimal = Field(alias="MONTO")
    dias_retraso: int = Field(alias="DIAS_RETRASO")
    estado: str = Field(alias="ESTADO")
    motivo: Optional[str] = Field(default=None, alias="MOTIVO")
    fecha_generacion: Optional[datetime] = Field(default=None, alias="FECHA_GENERACION")
    fecha_pago: Optional[datetime] = Field(default=None, alias="FECHA_PAGO")
    titulo: str = Field(alias="TITULO")
    nombre_usuario: str = Field(alias="NOMBRE_USUARIO")
