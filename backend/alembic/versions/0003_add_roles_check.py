"""add ADMIN and PROFESOR roles to usuarios CHECK constraint

Oracle no permite modificar un CHECK inline (genera un nombre SYS_C#######),
así que se resuelve el nombre del constraint por tabla + firma del check
(contiene 'BIBLIOTECARIO'), se elimina y se recrea con la lista ampliada
de roles: LECTOR, PROFESOR, BIBLIOTECARIO, ADMIN.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-05

"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

_CONSTRAINT_NUEVO = (
    "ALTER TABLE usuarios ADD CONSTRAINT chk_usuarios_rol "
    "CHECK (rol IN ('LECTOR', 'PROFESOR', 'BIBLIOTECARIO', 'ADMIN'))"
)

# Resuelve el constraint autogenerado del rol (si existe) y lo elimina.
_PLSQL_BORRAR_CHECK_ROL = """
DECLARE
    v_constraint VARCHAR2(30) := NULL;
BEGIN
    BEGIN
        SELECT constraint_name INTO v_constraint
          FROM user_constraints
         WHERE table_name = 'USUARIOS'
           AND constraint_type = 'C'
           AND search_condition LIKE '%BIBLIOTECARIO%'
           AND ROWNUM = 1;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            v_constraint := NULL;
    END;

    IF v_constraint IS NOT NULL THEN
        EXECUTE IMMEDIATE 'ALTER TABLE usuarios DROP CONSTRAINT ' || v_constraint;
    END IF;
END;
"""


def upgrade() -> None:
    op.execute(_PLSQL_BORRAR_CHECK_ROL)
    op.execute(_CONSTRAINT_NUEVO)


def downgrade() -> None:
    op.execute(_PLSQL_BORRAR_CHECK_ROL)
    op.execute(
        "ALTER TABLE usuarios ADD CONSTRAINT chk_usuarios_rol "
        "CHECK (rol IN ('LECTOR', 'BIBLIOTECARIO'))"
    )