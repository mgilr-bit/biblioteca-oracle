"""baseline: refleja el esquema ya creado por database/02_tables.sql y 03_triggers.sql

Este esquema (usuarios, libros, prestamos + triggers de negocio que
ajustan copias_disponibles) ya existe en todo entorno real, creado a mano
por los scripts SQL en `database/`. Esta migración es intencionalmente un
no-op: Alembic se está introduciendo de forma retroactiva sobre una base
de datos que ya tiene las tablas, no se está creando desde cero.

Se aplica con `alembic stamp head` (no `alembic upgrade head`) para que
Alembic registre "estamos en 0001" sin ejecutar ningún DDL contra objetos
que ya existen (evita ORA-00955). Las migraciones reales empiezan en la
revisión siguiente.

Revision ID: 0001
Revises:
Create Date: 2026-08-23

"""
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
