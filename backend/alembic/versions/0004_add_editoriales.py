"""add editoriales table + libros.id_editorial FK

Crea la tabla EDITORIALES como catálogo: cada valor distinto (no nulo) de
`libros.editorial` se siembra como fila, preservando el historial. Luego
agrega a LIBROS la columna `id_editorial` (nullable, FK) para ligar libros
al catálogo sin romper el CRUD existente, que sigue mostrando el texto
`editorial` por compatibilidad con el frontend actual.

Las columnas de auditoría replican `AuditMixin` (models/base.py): mismo
formato que la migración 0002 usa para usuarios/libros/prestamos.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "editoriales",
        sa.Column("id_editorial", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("pais", sa.String(length=100), nullable=True),
        sa.Column("sitio_web", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("SYSTIMESTAMP")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint("uq_editoriales_nombre", "editoriales", ["nombre"])

    # Backfill: enumera los valores de libros.editorial ya existentes.
    op.execute(
        """
        INSERT INTO editoriales (nombre, created_by)
        SELECT DISTINCT INITCAP(TRIM(editorial)), 'system'
        FROM libros
        WHERE editorial IS NOT NULL AND TRIM(editorial) <> ''
        """
    )

    op.add_column("libros", sa.Column("id_editorial", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_libros_editorial", "libros", "editoriales", ["id_editorial"], ["id_editorial"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_libros_editorial", "libros", type_="foreignkey")
    op.drop_column("libros", "id_editorial")
    op.drop_table("editoriales")