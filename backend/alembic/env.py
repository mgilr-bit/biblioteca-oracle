"""Wiring de Alembic contra el mismo engine/metadata que usa la app.

Reutiliza `config.database.engine` (construido a partir de las mismas env
vars DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_SERVICE) en vez de rearmar la
URL de Oracle por separado — un solo lugar construye la conexión.
"""
from logging.config import fileConfig

from alembic import context

import models  # noqa: F401  (registra las entidades en SQLModel.metadata)
from config.database import engine
from sqlmodel import SQLModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
