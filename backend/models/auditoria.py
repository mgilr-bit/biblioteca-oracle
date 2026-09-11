"""Bitácora de auditoría (append-only, sin soft-delete)."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Identity, Integer, String, text
from sqlmodel import Field, SQLModel


class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"

    id_auditoria: int = Field(
        default=None,
        sa_column=Column("id_auditoria", Integer, Identity(always=True), primary_key=True),
    )
    id_usuario: Optional[int] = Field(
        default=None,
        sa_column=Column(
            "id_usuario",
            Integer,
            ForeignKey("usuarios.id_usuario", ondelete="SET NULL", name="fk_auditoria_usuario"),
            nullable=True,
        ),
    )
    email: Optional[str] = Field(
        default=None, sa_column=Column("email", String(length=255))
    )
    rol: Optional[str] = Field(default=None, sa_column=Column("rol", String(20)))
    accion: str = Field(sa_column=Column("accion", String(length=50), nullable=False))
    recurso: str = Field(sa_column=Column("recurso", String(length=50), nullable=False))
    id_recurso: Optional[int] = Field(default=None, sa_column=Column("id_recurso", Integer))
    detalle: Optional[str] = Field(default=None, sa_column=Column("detalle", String(500)))
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            "created_at", DateTime, nullable=False, server_default=text("SYSTIMESTAMP")
        ),
    )