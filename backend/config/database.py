"""Configuración de conexión a Oracle Database usando SQLModel (SQLAlchemy)."""
import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from config.oracle_dsn import get_dsn

# Cargar .env desde el directorio raíz del proyecto
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# El DSN se resuelve en un solo lugar (config/oracle_dsn.py): descriptor
# completo TCPS para Oracle Autonomous Database si DB_DSN está definida, o
# Easy Connect host:puerto/servicio para el Oracle XE local.
_database_url = URL.create(
    "oracle+oracledb",
    username=DB_USER,
    password=DB_PASSWORD,
)

engine = create_engine(
    _database_url,
    connect_args={"dsn": get_dsn()},
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_session():
    """Provee una sesión por request, confirmando o revirtiendo al final."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connection() -> None:
    """Verifica que la conexión a la base de datos sea funcional."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1 FROM DUAL"))


def init_db() -> None:
    """Crea las tablas si no existen (solo para entornos de prueba)."""
    import models  # noqa: F401  (registra las entidades en la metadata)
    SQLModel.metadata.create_all(engine)
