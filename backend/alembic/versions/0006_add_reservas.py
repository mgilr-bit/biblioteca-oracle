"""add reservas table

Crea la tabla RESERVAS: un usuario encola una reserva sobre un libro (con
la política FIFO del servicio: la más antigua se atiende primero cuando
vuelve una copia). `fecha_expiracion` delimita la ventana para recoger el
préstamo una vez la reserva pasa a CUMPLIDA (la purga la hace el job de
vencidos, fase 4 del plan).

Estados: ACTIVA, CUMPLIDA, CANCELADA, EXPIRADA.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reservas",
        sa.Column("id_reserva", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_libro", sa.Integer(), sa.ForeignKey("libros.id_libro"), nullable=False),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("usuarios.id_usuario"), nullable=False),
        sa.Column(
            "fecha_reserva",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("SYSTIMESTAMP"),
        ),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'ACTIVA'")),
        sa.Column("fecha_expiracion", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("SYSTIMESTAMP")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_reservas_id_libro", "reservas", ["id_libro"])
    op.create_index("ix_reservas_id_usuario", "reservas", ["id_usuario"])
    op.create_index("ix_reservas_estado", "reservas", ["estado"])


def downgrade() -> None:
    op.drop_index("ix_reservas_estado", table_name="reservas")
    op.drop_index("ix_reservas_id_usuario", table_name="reservas")
    op.drop_index("ix_reservas_id_libro", table_name="reservas")
    op.drop_table("reservas")