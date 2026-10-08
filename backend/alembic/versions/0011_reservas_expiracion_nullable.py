"""reservas.fecha_expiracion admite NULL

Las instalaciones que corrieron el borrador `database/08_mejoras_recomendadas.sql`
traían `fecha_expiracion DATE NOT NULL`, y la 0006 solo agregaba columnas
faltantes sin tocar las existentes. Pero una reserva ACTIVA no tiene fecha
de expiración (se fija al pasar a CUMPLIDA), así que toda reserva nueva
reventaba con ORA-01400.

Idempotente: solo altera la columna si hoy es NOT NULL.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-06
"""
import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    nullable = conn.execute(
        sa.text(
            "SELECT nullable FROM user_tab_columns "
            "WHERE table_name = 'RESERVAS' AND column_name = 'FECHA_EXPIRACION'"
        )
    ).scalar()
    if nullable == "N":
        conn.execute(sa.text("ALTER TABLE reservas MODIFY (fecha_expiracion NULL)"))


def downgrade() -> None:
    # No se vuelve a NOT NULL: las reservas ACTIVA tienen la columna vacía.
    pass
