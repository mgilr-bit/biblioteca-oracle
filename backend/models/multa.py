"""Modelo de multas por devolución tardía."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Identity, Integer, Numeric, String
from sqlmodel import Field, SQLModel

from models.base import AuditMixin


class Multa(AuditMixin, SQLModel, table=True):
    """Sanción fija (Q35) generada al devolver un préstamo con retraso."""

    __tablename__ = "multas"
    __table_args__ = (
        CheckConstraint("monto >= 0", name="chk_multa_monto"),
        CheckConstraint(
            "estado IN ('PENDIENTE', 'PAGADA', 'CONDONADA')",
            name="chk_multa_estado",
        ),
    )

    id_multa: int = Field(
        default=None,
        sa_column=Column("id_multa", Integer, Identity(always=True), primary_key=True),
    )
    id_prestamo: int = Field(
        sa_column=Column(
            "id_prestamo",
            Integer,
            ForeignKey("prestamos.id_prestamo", ondelete="CASCADE", name="fk_multa_prestamo"),
            nullable=False,
        )
    )
    id_usuario: int = Field(
        sa_column=Column(
            "id_usuario",
            Integer,
            ForeignKey("usuarios.id_usuario", ondelete="CASCADE", name="fk_multa_usuario"),
            nullable=False,
        )
    )
    monto: Decimal = Field(
        default=Decimal("35"),
        sa_column=Column("monto", Numeric(10, 2), nullable=False, server_default="35"),
    )
    dias_retraso: int = Field(
        default=0,
        sa_column=Column("dias_retraso", Integer, nullable=False, server_default="0"),
    )
    estado: str = Field(
        default="PENDIENTE",
        sa_column=Column("estado", String(length=20), nullable=False, server_default="PENDIENTE"),
    )
    motivo: str | None = Field(default=None, sa_column=Column("motivo", String(200)))
    fecha_pago: datetime | None = Field(
        default=None, sa_column=Column("fecha_pago", DateTime)
    )