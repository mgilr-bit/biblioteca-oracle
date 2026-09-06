"""Bitácora de auditoría (eventos clave de la aplicación).

Registro inmutable y de solo-append de las operaciones críticas del sistema
(login/logout/register, préstamos, multas, reservas, usuarios, ejemplares).
A diferencia de las demás tablas (AuditMixin + soft-delete), la bitácora NO
tiene borrado lógico: es un registro de auditoría y cada fila debe
permanecer intacta por integridad del historial. Solo ADMIN/BIBLIOTECARIO
la consultan.

Tabla:
* id_usuario: el actor (nullable: eventos sin sesión, ej. login fallido).
* email/rol: snapshot del actor por si luego se elimina/desactiva el usuario.
* accion: LOGIN, LOGIN_FALLIDO, LOGOUT, REGISTER, PRESTAMO_CREADO,
  PRESTAMO_DEVUELTO, MULTA_GENERADA, MULTA_PAGADA, MULTA_CONDONADA,
  RESERVA_CREADA, RESERVA_CANCELADA, USUARIO_CREADO, USUARIO_ACTUALIZADO,
  USUARIO_ELIMINADO, USUARIO_ESTADO, EJEMPLAR_CREADO, EJEMPLAR_ESTADO.
* recurso: nombre del recurso sobre el que opera la acción.
* id_recurso: PK del registro afectado (nullable).
* detalle: contexto legible (ej. "devolución tardía: 3 día(s)").

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auditoria",
        sa.Column("id_auditoria", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "id_usuario",
            sa.Integer(),
            sa.ForeignKey("usuarios.id_usuario", ondelete="SET NULL", name="fk_auditoria_usuario"),
            nullable=True,
        ),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("rol", sa.String(length=20), nullable=True),
        sa.Column("accion", sa.String(length=50), nullable=False),
        sa.Column("recurso", sa.String(length=50), nullable=False),
        sa.Column("id_recurso", sa.Integer(), nullable=True),
        sa.Column("detalle", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("SYSTIMESTAMP"), nullable=False),
    )
    op.create_index("idx_auditoria_created_at", "auditoria", ["created_at"])
    op.create_index("idx_auditoria_recurso", "auditoria", ["recurso", "accion"])
    op.create_index("idx_auditoria_usuario", "auditoria", ["id_usuario"])


def downgrade() -> None:
    for idx in ("idx_auditoria_usuario", "idx_auditoria_recurso", "idx_auditoria_created_at"):
        try:
            op.drop_index(idx, table_name="auditoria")
        except Exception:  # noqa: BLE001 - el índice puede no existir
            pass
    op.drop_table("auditoria")