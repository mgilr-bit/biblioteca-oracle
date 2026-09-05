"""Entidad que representa la tabla MULTAS.

Una multa se genera cuando un préstamo se devuelve después de la fecha
esperada (ver PrestamoService.devolver). El monto es fijo (Q35, ver
services.multa_service.TARIFA_MULTA_ATRASO) sin importar cuántos días de
retraso hubo; `dias_retraso` se guarda solo como dato informativo.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Identity, Integer, Numeric, text
from sqlmodel import Field

from models.base import AuditMixin


class Multa(AuditMixin, table=True):
    __tablename__ = "multas"

    id_multa: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, Identity(always=True), primary_key=True),
    )
    id_prestamo: int = Field(foreign_key="prestamos.id_prestamo", index=True)
    id_usuario: int = Field(foreign_key="usuarios.id_usuario", index=True)
    monto: Decimal = Field(
        default=Decimal("35.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default=text("35")),
    )
    dias_retraso: int = Field(default=0)
    estado: str = Field(default="PENDIENTE", max_length=20)
    motivo: Optional[str] = Field(default=None, max_length=200)
    fecha_pago: Optional[datetime] = Field(default=None)
