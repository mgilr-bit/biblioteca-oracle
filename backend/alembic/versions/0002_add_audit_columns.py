"""add audit + soft-delete columns to usuarios, libros, prestamos

Agrega las columnas de `AuditMixin` (models/base.py) a las 3 tablas:
created_at/by, updated_at/by, is_deleted, deleted_at/by. Antes no había
ningún rastro de quién creó/modificó/borró un registro, y el DELETE de
`/api/*` era físico — a partir de esta migración es soft-delete.

`is_deleted` va NOT NULL DEFAULT 0 para que las filas ya existentes
queden como "no borradas" sin intervención manual. `created_at` usa
SYSTIMESTAMP como default para que las filas existentes queden con la
fecha de esta migración (mejor eso que NULL). El resto de las columnas
de auditoría quedan NULL para filas históricas — no sabemos quién las
creó, y no tiene sentido inventarlo.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-24

"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

_TABLES = ("usuarios", "libros", "prestamos")


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("created_at", sa.DateTime(), server_default=sa.text("SYSTIMESTAMP")))
        op.add_column(table, sa.Column("created_by", sa.String(length=255), nullable=True))
        op.add_column(table, sa.Column("updated_at", sa.DateTime(), nullable=True))
        op.add_column(table, sa.Column("updated_by", sa.String(length=255), nullable=True))
        op.add_column(
            table,
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(), nullable=True))
        op.add_column(table, sa.Column("deleted_by", sa.String(length=255), nullable=True))


def downgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, "deleted_by")
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "is_deleted")
        op.drop_column(table, "updated_by")
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_by")
        op.drop_column(table, "created_at")
