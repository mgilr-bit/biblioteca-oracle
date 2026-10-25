"""reservas: estados RECOGIDA y SIN_RECOGER

Nuevo ciclo de la reserva (ver services.reserva_service):

* ACTIVA: pendiente de recoger. Con `fecha_expiracion` tiene una copia
  apartada (3 días); sin ella espera en la cola FIFO a que se libere una.
* RECOGIDA: el usuario la recogió (se registró el préstamo).
* SIN_RECOGER: venció la ventana de 3 días sin que la recogiera.
* CANCELADA.

Los estados anteriores se traducen: CUMPLIDA (copia lista para recoger)
pasa a ACTIVA conservando su fecha de expiración, y EXPIRADA a SIN_RECOGER.

El CHECK original es inline (nombre SYS_C#####), así que se resuelve por
firma como en la migración 0003.

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-24
"""
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

# Borra los CHECK de estado de la tabla (el autogenerado y/o un
# chk_reservas_estado de una corrida previa).
_PLSQL_DROP_CHECKS_ESTADO = """
BEGIN
    FOR c IN (
        SELECT constraint_name
          FROM user_constraints
         WHERE table_name = 'RESERVAS'
           AND constraint_type = 'C'
           AND search_condition_vc LIKE '%CANCELADA%'
    ) LOOP
        EXECUTE IMMEDIATE 'ALTER TABLE reservas DROP CONSTRAINT ' || c.constraint_name;
    END LOOP;
END;
"""


def upgrade() -> None:
    op.execute(_PLSQL_DROP_CHECKS_ESTADO)
    op.execute("UPDATE reservas SET estado = 'ACTIVA' WHERE estado = 'CUMPLIDA'")
    op.execute("UPDATE reservas SET estado = 'SIN_RECOGER' WHERE estado = 'EXPIRADA'")
    op.execute(
        "ALTER TABLE reservas ADD CONSTRAINT chk_reservas_estado "
        "CHECK (estado IN ('ACTIVA', 'RECOGIDA', 'SIN_RECOGER', 'CANCELADA'))"
    )


def downgrade() -> None:
    op.execute(_PLSQL_DROP_CHECKS_ESTADO)
    op.execute(
        "UPDATE reservas SET estado = 'CUMPLIDA' "
        "WHERE estado = 'RECOGIDA' OR (estado = 'ACTIVA' AND fecha_expiracion IS NOT NULL)"
    )
    op.execute("UPDATE reservas SET estado = 'EXPIRADA' WHERE estado = 'SIN_RECOGER'")
    op.execute(
        "ALTER TABLE reservas ADD CONSTRAINT chk_reservas_estado "
        "CHECK (estado IN ('ACTIVA', 'CUMPLIDA', 'CANCELADA', 'EXPIRADA'))"
    )
