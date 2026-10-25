"""estado y ubicación pasan a LIBROS; se retira EJEMPLARES

El módulo de ejemplares (una fila por copia física) se quitó de la
aplicación: el estado y la ubicación ahora se gestionan por libro.

1. Agrega `libros.estado` (DISPONIBLE, DANADO, REPARACION, BAJA) y
   `libros.ubicacion`.
2. Copia a cada libro la ubicación de sus ejemplares, si tenía.
3. Elimina `prestamos.id_ejemplar` (con su FK) y la tabla EJEMPLARES.

Idempotente: cada paso revisa el diccionario de datos antes de actuar.

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def _existe_columna(conn, tabla: str, columna: str) -> bool:
    return bool(
        conn.execute(
            sa.text(
                "SELECT COUNT(*) FROM user_tab_columns "
                "WHERE table_name = :tabla AND column_name = :columna"
            ),
            {"tabla": tabla, "columna": columna},
        ).scalar()
    )


def _existe_tabla(conn, tabla: str) -> bool:
    return bool(
        conn.execute(
            sa.text("SELECT COUNT(*) FROM user_tables WHERE table_name = :tabla"),
            {"tabla": tabla},
        ).scalar()
    )


def upgrade() -> None:
    conn = op.get_bind()

    if not _existe_columna(conn, "LIBROS", "ESTADO"):
        op.add_column(
            "libros",
            sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'DISPONIBLE'")),
        )
        op.create_check_constraint(
            "chk_libros_estado", "libros", "estado IN ('DISPONIBLE', 'DANADO', 'REPARACION', 'BAJA')"
        )
    if not _existe_columna(conn, "LIBROS", "UBICACION"):
        op.add_column("libros", sa.Column("ubicacion", sa.String(length=100), nullable=True))

    if _existe_tabla(conn, "EJEMPLARES"):
        conn.execute(
            sa.text(
                """
                UPDATE libros l
                SET ubicacion = (
                    SELECT MIN(e.ubicacion) FROM ejemplares e
                    WHERE e.id_libro = l.id_libro AND e.is_deleted = 0 AND e.ubicacion IS NOT NULL
                )
                WHERE l.ubicacion IS NULL
                """
            )
        )

    if _existe_columna(conn, "PRESTAMOS", "ID_EJEMPLAR"):
        # El nombre de la FK puede variar según cómo se creó la BD.
        fks = conn.execute(
            sa.text(
                """
                SELECT c.constraint_name
                FROM user_constraints c
                JOIN user_cons_columns cc ON cc.constraint_name = c.constraint_name
                WHERE c.table_name = 'PRESTAMOS' AND c.constraint_type = 'R'
                  AND cc.column_name = 'ID_EJEMPLAR'
                """
            )
        ).scalars().all()
        for fk in fks:
            op.drop_constraint(fk, "prestamos", type_="foreignkey")
        op.drop_column("prestamos", "id_ejemplar")

    if _existe_tabla(conn, "EJEMPLARES"):
        op.drop_table("ejemplares")


def downgrade() -> None:
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

    op.add_column("prestamos", sa.Column("id_ejemplar", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_prestamos_ejemplar", "prestamos", "ejemplares", ["id_ejemplar"], ["id_ejemplar"]
    )

    op.drop_constraint("chk_libros_estado", "libros", type_="check")
    op.drop_column("libros", "ubicacion")
    op.drop_column("libros", "estado")
