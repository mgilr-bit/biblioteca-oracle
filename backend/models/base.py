"""Mixin de auditoría + soft-delete, común a toda entidad persistida.

Mirror de `BaseEntity` en wallet-api (created_at/by, updated_at/by,
deleted_at/by, is_deleted) — hasta ahora no existía ningún rastro de quién
creó/modificó/borró un registro. `actor` es el email del usuario en
sesión (o "system" para procesos sin sesión, ej. seed.py).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlmodel import Field, SQLModel


class AuditMixin(SQLModel):
    created_at: Optional[datetime] = Field(
        default=None, sa_column_kwargs={"server_default": text("SYSTIMESTAMP")}
    )
    created_by: Optional[str] = Field(default=None, max_length=255)
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[str] = Field(default=None, max_length=255)

    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[str] = Field(default=None, max_length=255)
