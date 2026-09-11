"""add reservas table

Crea la tabla RESERVAS: un usuario encola una reserva sobre un libro (con
la política FIFO del servicio: la más antigua se atiende primero cuando
vuelve una copia). `fecha_expiracion` delimita la ventana para recoger el
préstamo una vez la reserva pasa a CUMPLIDA (la purga la hace el job de
vencidos, fase 4 del plan).

Estados: ACTIVA, CUMPLIDA, CANCELADA, EXPIRADA.

Idempotente a propósito: el borrador `database/08_mejoras_recomendadas.sql`
ya traía una tabla `reservas` parcial (sin columnas de auditoría/soft-delete),
marcada como "funcionalidad futura". Como algunos entornos ya corrieron ese
script:

* si `reservas` NO existe -> se crea completa (caso instalación limpia / Docker).
* si `reservas` YA existe  -> solo se agregan las columnas que falten para
  alinearla con models/reserva.Reserva + models/base.AuditMixin.

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

# Columnas de auditoría/soft-delete (AuditMixin). Son las que le faltan a la
# tabla si vino del borrador de database/08_*.sql.
_COLUMNAS_EXTRA = [
    lambda: sa.Column("fecha_reserva", sa.DateTime(), nullable=False, server_default=sa.text("SYSTIMESTAMP")),
    lambda: sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'ACTIVA'")),
    lambda: sa.Column("fecha_expiracion", sa.DateTime(), nullable=True),
    lambda: sa.Column("created_at", sa.DateTime(), server_default=sa.text("SYSTIMESTAMP")),
    lambda: sa.Column("created_by", sa.String(length=255), nullable=True),
    lambda: sa.Column("updated_at", sa.DateTime(), nullable=True),
    lambda: sa.Column("updated_by", sa.String(length=255), nullable=True),
    lambda: sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    lambda: sa.Column("deleted_at", sa.DateTime(), nullable=True),
    lambda: sa.Column("deleted_by", sa.String(length=255), nullable=True),
]


def _crear_tabla_completa() -> None:
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


def _completar_tabla_existente() -> None:
    inspector = sa.inspect(op.get_bind())
    columnas = {c["name"].lower() for c in inspector.get_columns("reservas")}
    for factory in _COLUMNAS_EXTRA:
        col = factory()
        if col.name.lower() not in columnas:
            op.add_column("reservas", col)


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("reservas"):
        _completar_tabla_existente()
    else:
        _crear_tabla_completa()


def downgrade() -> None:
    for idx in ("ix_reservas_estado", "ix_reservas_id_usuario", "ix_reservas_id_libro"):
        try:
            op.drop_index(idx, table_name="reservas")
        except Exception:  # noqa: BLE001 - el índice puede no existir
            pass
    op.drop_table("reservas")