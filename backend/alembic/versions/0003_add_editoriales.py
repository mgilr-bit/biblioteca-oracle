"""add editoriales table and libros.id_editorial (reemplaza libros.editorial)

Hasta ahora la editorial era un texto libre en `libros.editorial`, sin
catálogo ni forma de evitar "Planeta" / "planeta " / "Editorial Planeta".
Esta migración:

1. crea `editoriales` (con las columnas de auditoría de AuditMixin),
2. agrega `libros.id_editorial` (FK nullable),
3. convierte cada valor distinto de `libros.editorial` en una fila de
   `editoriales` y enlaza los libros existentes,
4. elimina `libros.editorial` (sus datos ya viven en `editoriales`).

El downgrade restaura la columna de texto desde los nombres.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-10

"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "editoriales",
        sa.Column("id_editorial", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("SYSTIMESTAMP")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_editoriales_nombre", "editoriales", ["nombre"])

    op.add_column("libros", sa.Column("id_editorial", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_libro_editorial", "libros", "editoriales", ["id_editorial"], ["id_editorial"]
    )
    op.create_index("ix_libros_id_editorial", "libros", ["id_editorial"])

    # Backfill: un registro por nombre distinto (TRIM de '' da NULL en Oracle).
    op.execute(
        "INSERT INTO editoriales (nombre, created_by) "
        "SELECT DISTINCT TRIM(editorial), 'migration' FROM libros "
        "WHERE TRIM(editorial) IS NOT NULL"
    )
    op.execute(
        "UPDATE libros l SET id_editorial = ("
        "SELECT e.id_editorial FROM editoriales e WHERE e.nombre = TRIM(l.editorial)"
        ") WHERE TRIM(l.editorial) IS NOT NULL"
    )

    op.drop_column("libros", "editorial")


def downgrade() -> None:
    op.add_column("libros", sa.Column("editorial", sa.String(length=100), nullable=True))
    op.execute(
        "UPDATE libros l SET editorial = ("
        "SELECT e.nombre FROM editoriales e WHERE e.id_editorial = l.id_editorial"
        ") WHERE l.id_editorial IS NOT NULL"
    )
    op.drop_index("ix_libros_id_editorial", table_name="libros")
    op.drop_constraint("fk_libro_editorial", "libros", type_="foreignkey")
    op.drop_column("libros", "id_editorial")
    op.drop_index("ix_editoriales_nombre", table_name="editoriales")
    op.drop_table("editoriales")
