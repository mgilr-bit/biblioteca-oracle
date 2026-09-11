"""add ADMIN and PROFESOR roles to usuarios CHECK constraint

Oracle no permite modificar un CHECK inline (genera un nombre SYS_C#######),
así que se resuelven por firma (mencionan 'BIBLIOTECARIO') TODOS los CHECK
de rol que haya en la tabla, se eliminan y se recrea uno con nombre estable
`chk_usuarios_rol` y la lista ampliada: LECTOR, PROFESOR, BIBLIOTECARIO, ADMIN.

Idempotente: si se re-ejecuta (p. ej. tras un `alembic stamp` a una revisión
anterior), borra también el `chk_usuarios_rol` de la corrida previa antes de
volver a crearlo. Usa `search_condition_vc` (VARCHAR2, 12.2+) porque
`search_condition` es LONG y no admite LIKE en el WHERE (ORA-00932).

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-05

"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


# Borra TODOS los CHECK de rol de la tabla (el autogenerado SYS_C##### y/o un
# chk_usuarios_rol de una corrida previa). Sin comillas anidadas: el ALTER de
# DROP se arma por concatenación, no lleva literales.
_PLSQL_DROP_CHECKS_ROL = """
BEGIN
    FOR c IN (
        SELECT constraint_name
          FROM user_constraints
         WHERE table_name = 'USUARIOS'
           AND constraint_type = 'C'
           AND search_condition_vc LIKE '%BIBLIOTECARIO%'
    ) LOOP
        EXECUTE IMMEDIATE 'ALTER TABLE usuarios DROP CONSTRAINT ' || c.constraint_name;
    END LOOP;
END;
"""


def upgrade() -> None:
    op.execute(_PLSQL_DROP_CHECKS_ROL)
    op.execute(
        "ALTER TABLE usuarios ADD CONSTRAINT chk_usuarios_rol "
        "CHECK (rol IN ('LECTOR', 'PROFESOR', 'BIBLIOTECARIO', 'ADMIN'))"
    )


def downgrade() -> None:
    op.execute(_PLSQL_DROP_CHECKS_ROL)
    op.execute(
        "ALTER TABLE usuarios ADD CONSTRAINT chk_usuarios_rol "
        "CHECK (rol IN ('LECTOR', 'BIBLIOTECARIO'))"
    )