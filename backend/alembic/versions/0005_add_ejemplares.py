"""add ejemplares table + prestamos.id_ejemplar FK

Crea la tabla EJEMPLARES (una fila por copia física de un libro) y la
resembra desde `libros.numero_copias`: cada libro con N copias genera N
ejemplares `L-<id_libro>-<i>` en estado DISPONIBLE. Luego agrega a
PRESTAMOS la columna `id_ejemplar` (nullable, FK) para ligar cada préstamo
a la copia física prestada.

Estados del ejemplar (ver services.ejemplar_service.EJEMPLAR_ESTADOS):
DISPONIBLE, PRESTADO, RESERVADO, DANADO, REPARACION, BAJA, DEVUELTO.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

_BACKFILL = """
DECLARE
    v_codigo VARCHAR2(40);
BEGIN
    FOR libro IN (
        SELECT id_libro, numero_copias FROM libros WHERE is_deleted = 0
    ) LOOP
        FOR i IN 1 .. libro.numero_copias LOOP
            v_codigo := 'L-' || libro.id_libro || '-' || i;
            INSERT INTO ejemplares (id_libro, codigo_ejemplar, estado, created_by)
            VALUES (libro.id_libro, v_codigo, 'DISPONIBLE', 'system');
        END LOOP;
    END LOOP;
END;
"""


def upgrade() -> None:
    op.create_table(
        "ejemplares",
        sa.Column("id_ejemplar", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_libro", sa.Integer(), sa.ForeignKey("libros.id_libro"), nullable=False),
        sa.Column("codigo_ejemplar", sa.String(length=40), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'DISPONIBLE'")),
        sa.Column("ubicacion", sa.String(length=100), nullable=True),
        sa.Column("fecha_adquisicion", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("SYSTIMESTAMP")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint("uq_ejemplares_codigo", "ejemplares", ["codigo_ejemplar"])
    op.create_index("ix_ejemplares_id_libro", "ejemplares", ["id_libro"])
    op.create_index("ix_ejemplares_estado", "ejemplares", ["estado"])

    op.execute(_BACKFILL)

    op.add_column("prestamos", sa.Column("id_ejemplar", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_prestamos_ejemplar", "prestamos", "ejemplares", ["id_ejemplar"], ["id_ejemplar"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_prestamos_ejemplar", "prestamos", type_="foreignkey")
    op.drop_column("prestamos", "id_ejemplar")
    op.drop_index("ix_ejemplares_estado", table_name="ejemplares")
    op.drop_index("ix_ejemplares_id_libro", table_name="ejemplares")
    op.drop_table("ejemplares")