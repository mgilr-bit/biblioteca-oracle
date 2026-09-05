"""add notificaciones table

Crea la tabla NOTIFICACIONES (bandeja para cada usuario). Las genera el
job de mantenimiento (`NotificacionService.ejecutar_mantenimiento`, fase 4
del plan) y también procesos puntuales: recordatorios de devolución,
avisos de vencimiento, reservas disponibles y multas.

Tipos (`NotificacionService.TIPOS`): RECORDATORIO_3D, RECORDATORIO_HOY,
VENCIDO, RESERVA_DISPONIBLE, MULTA, SISTEMA.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notificaciones",
        sa.Column("id_notificacion", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("usuarios.id_usuario"), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("mensaje", sa.String(length=500), nullable=False),
        sa.Column("leida", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "fecha_generacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("SYSTIMESTAMP"),
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("SYSTIMESTAMP")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_notificaciones_id_usuario", "notificaciones", ["id_usuario"])
    op.create_index("ix_notificaciones_leida", "notificaciones", ["leida"])


def downgrade() -> None:
    op.drop_index("ix_notificaciones_leida", table_name="notificaciones")
    op.drop_index("ix_notificaciones_id_usuario", table_name="notificaciones")
    op.drop_table("notificaciones")