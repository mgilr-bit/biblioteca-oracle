"""Motor de autorización RBAC + ABAC (Casbin), políticas persistidas en Oracle.

RBAC: el rol de sesión (`sub.rol`) debe calzar con la política (`p.rol`).
ABAC: cuando la política marca `owner_only=true`, además se exige que el
`owner_id` del objeto (ej. el id_usuario dueño del registro) coincida con
el id del usuario en sesión (`sub.id`) — así un LECTOR nunca puede operar
sobre el registro de otro usuario, sin importar lo que pida en la URL.
"""
from pathlib import Path

import casbin
from casbin_sqlalchemy_adapter import Adapter
from sqlalchemy import Column, Identity, Integer, String
from sqlalchemy.orm import declarative_base

from config.database import engine

_MODEL_PATH = str(Path(__file__).resolve().parent / "casbin_model.conf")

# La tabla `casbin_rule` que trae casbin_sqlalchemy_adapter por defecto usa
# `Column(Integer, primary_key=True)` para `id`, lo cual funciona en
# Postgres/MySQL/SQLite (autoincrement implícito) pero NO en Oracle — ahí
# revienta con ORA-01400 (cannot insert NULL into ID) porque Oracle no
# autogenera nada sin una IDENTITY/sequence explícita. Se redefine la
# misma tabla con `Identity()` en el id y se pasa como `db_class`.
_CasbinBase = declarative_base()


class OracleCasbinRule(_CasbinBase):
    __tablename__ = "casbin_rule"

    id = Column(Integer, Identity(always=True), primary_key=True)
    ptype = Column(String(255))
    v0 = Column(String(255))
    v1 = Column(String(255))
    v2 = Column(String(255))
    v3 = Column(String(255))
    v4 = Column(String(255))
    v5 = Column(String(255))

# (rol, subject, act, owner_only)
DEFAULT_POLICIES = [
    # Libros: lectura abierta a cualquier rol autenticado, escritura solo BIBLIOTECARIO.
    ("BIBLIOTECARIO", "Libro", "read", "false"),
    ("BIBLIOTECARIO", "Libro", "create", "false"),
    ("BIBLIOTECARIO", "Libro", "update", "false"),
    ("BIBLIOTECARIO", "Libro", "delete", "false"),
    ("LECTOR", "Libro", "read", "false"),
    # Usuarios: BIBLIOTECARIO administra a cualquiera; LECTOR solo lee/edita su propio perfil
    # (el servicio impide además que un LECTOR se cambie el rol a sí mismo).
    ("BIBLIOTECARIO", "Usuario", "read", "false"),
    ("BIBLIOTECARIO", "Usuario", "create", "false"),
    ("BIBLIOTECARIO", "Usuario", "update", "false"),
    ("BIBLIOTECARIO", "Usuario", "delete", "false"),
    ("BIBLIOTECARIO", "Usuario", "toggle_estado", "false"),
    ("LECTOR", "Usuario", "read", "true"),
    ("LECTOR", "Usuario", "update", "true"),
    # Prestamos: BIBLIOTECARIO ve/gestiona todo; LECTOR crea y lee solo los suyos.
    ("BIBLIOTECARIO", "Prestamo", "read", "false"),
    ("BIBLIOTECARIO", "Prestamo", "create", "false"),
    ("BIBLIOTECARIO", "Prestamo", "devolver", "false"),
    ("LECTOR", "Prestamo", "read", "true"),
    ("LECTOR", "Prestamo", "create", "false"),
    # Multas: BIBLIOTECARIO ve todas y las cierra (pagar/condonar); LECTOR solo lee las suyas.
    ("BIBLIOTECARIO", "Multa", "read", "false"),
    ("BIBLIOTECARIO", "Multa", "gestionar", "false"),
    ("LECTOR", "Multa", "read", "true"),
]

_adapter = Adapter(engine, db_class=OracleCasbinRule)
enforcer = casbin.Enforcer(_MODEL_PATH, _adapter)


def ensure_default_policies() -> None:
    """Siembra en `casbin_rule` (Oracle) las políticas por defecto que falten.

    Antes solo sembraba cuando la tabla estaba totalmente vacía, lo que
    dejaba fuera cualquier política nueva agregada a `DEFAULT_POLICIES` en
    un despliegue que ya tenía la tabla poblada (p. ej. las de `Multa`).
    Ahora agrega, una por una, solo las que no existen todavía.
    """
    enforcer.load_policy()
    nuevas = [
        (rol, subject, act, owner_only)
        for rol, subject, act, owner_only in DEFAULT_POLICIES
        if not enforcer.has_policy(rol, subject, act, owner_only)
    ]
    if not nuevas:
        return
    for rol, subject, act, owner_only in nuevas:
        enforcer.add_policy(rol, subject, act, owner_only)
    enforcer.save_policy()
