"""Dependencia FastAPI que inyecta la sesión de SQLAlchemy en los routers.

Equivalente al repositorio inyectado por constructor en NestJS: evita
repetir `with get_session() as session:` en cada handler de cada router.
"""
from typing import Generator

from sqlmodel import Session

from config.database import get_session


def get_db_session() -> Generator[Session, None, None]:
    with get_session() as session:
        yield session
