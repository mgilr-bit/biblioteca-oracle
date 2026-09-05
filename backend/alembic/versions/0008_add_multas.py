"""tabla multas (sanción Q35 por devolución tardía)

Portada de `0003_crear_tabla_multas.py` de la rama `feat/multas` (Bryan),
renumerada para encadenar tras 0007 en esta rama. Cuando un préstamo se
devuelve después de la fecha esperada se genera una multa fija de Q35 en
estado PENDIENTE; una multa pendiente bloquea nuevos préstamos para el
usuario hasta que el bibliotecario la marque PAGADA o CONDONADA.

Idempotente a propósito (el borrador `database/08_mejoras_recomendadas.sql`
ya traía una tabla `multas` parcial en algunos entornos):
* si `multas` NO existe -> se crea completa.
* si `multas` YA existe  -> se agregan las columnas que falten para
  alinearla con models/multa.Multa + models/base.AuditMixin.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

_COLUMNAS_EXTRA = [
    lambda: sa.Column("dias_retraso", sa.Integer(), nullable=False, server_default=sa.text("0")),
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
        "multas",
        sa.Column("id_multa", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "id_prestamo",
            sa.Integer(),
            sa.ForeignKey("prestamos.id_prestamo", ondelete="CASCADE", name="fk_multa_prestamo"),
            nullable=False,
        ),
        sa.Column(
            "id_usuario",
            sa.Integer(),
            sa.ForeignKey("usuarios.id_usuario", ondelete="CASCADE", name="fk_multa_usuario"),
            nullable=False,
        ),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False, server_default=sa.text("35")),
        sa.Column("dias_retraso", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'PENDIENTE'")),
        sa.Column("motivo", sa.String(length=200), nullable=True),
        sa.Column("fecha_pago", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("SYSTIMESTAMP")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", sa.String(length=255), nullable=True),
        sa.CheckConstraint("monto >= 0", name="chk_multa_monto"),
        sa.CheckConstraint("estado IN ('PENDIENTE', 'PAGADA', 'CONDONADA')", name="chk_multa_estado"),
    )
    op.create_index("idx_multas_usuario", "multas", ["id_usuario"])
    op.create_index("idx_multas_estado", "multas", ["estado"])
    op.create_index("idx_multas_prestamo", "multas", ["id_prestamo"])


def _completar_tabla_existente() -> None:
    inspector = sa.inspect(op.get_bind())
    columnas = {c["name"].lower() for c in inspector.get_columns("multas")}
    for factory in _COLUMNAS_EXTRA:
        col = factory()
        if col.name.lower() not in columnas:
            op.add_column("multas", col)


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("multas"):
        _completar_tabla_existente()
    else:
        _crear_tabla_completa()


def downgrade() -> None:
    for idx in ("idx_multas_prestamo", "idx_multas_estado", "idx_multas_usuario"):
        try:
            op.drop_index(idx, table_name="multas")
        except Exception:  # noqa: BLE001 - el índice puede no existir
            pass
    op.drop_table("multas")