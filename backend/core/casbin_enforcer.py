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
    # ADMIN del sistema: control total sobre cualquier recurso y acción.
    # El matcher interpreta "*" como comodín (ver casbin_model.conf).
    ("ADMIN", "*", "*", "false"),
    # Libros: lectura abierta a cualquier rol autenticado, escritura solo BIBLIOTECARIO/ADMIN.
    ("BIBLIOTECARIO", "Libro", "read", "false"),
    ("BIBLIOTECARIO", "Libro", "create", "false"),
    ("BIBLIOTECARIO", "Libro", "update", "false"),
    ("BIBLIOTECARIO", "Libro", "delete", "false"),
    ("LECTOR", "Libro", "read", "false"),
    ("PROFESOR", "Libro", "read", "false"),
    # Usuarios: BIBLIOTECARIO administra a cualquiera salvo a roles superiores
    # (la protección de jerarquía vive en UsuarioService: no puede tocar a un
    # ADMIN ni crear bibliotecarios/administradores); LECTOR/PROFESOR solo
    # lee/edita su propio perfil (owner_only=true) y el servicio impide además
    # que se cambien el rol a sí mismos.
    ("BIBLIOTECARIO", "Usuario", "read", "false"),
    ("BIBLIOTECARIO", "Usuario", "create", "false"),
    ("BIBLIOTECARIO", "Usuario", "update", "false"),
    ("BIBLIOTECARIO", "Usuario", "delete", "false"),
    ("BIBLIOTECARIO", "Usuario", "toggle_estado", "false"),
    ("LECTOR", "Usuario", "read", "true"),
    ("LECTOR", "Usuario", "update", "true"),
    ("PROFESOR", "Usuario", "read", "true"),
    ("PROFESOR", "Usuario", "update", "true"),
    # Prestamos: BIBLIOTECARIO ve/gestiona todo; LECTOR y PROFESOR crean y leen solo los suyos.
    ("BIBLIOTECARIO", "Prestamo", "read", "false"),
    ("BIBLIOTECARIO", "Prestamo", "create", "false"),
    ("BIBLIOTECARIO", "Prestamo", "devolver", "false"),
    ("LECTOR", "Prestamo", "read", "true"),
    ("LECTOR", "Prestamo", "create", "false"),
    ("PROFESOR", "Prestamo", "read", "true"),
    ("PROFESOR", "Prestamo", "create", "false"),
    # Editoriales: catálogo legible para todos, gestionable solo por BIBLIOTECARIO/ADMIN.
    ("BIBLIOTECARIO", "Editorial", "read", "false"),
    ("BIBLIOTECARIO", "Editorial", "create", "false"),
    ("BIBLIOTECARIO", "Editorial", "update", "false"),
    ("BIBLIOTECARIO", "Editorial", "delete", "false"),
    ("LECTOR", "Editorial", "read", "false"),
    ("PROFESOR", "Editorial", "read", "false"),
    # Ejemplares: venta/trazabilidad de copias físicas; lectura libre, gestión BIBLIOTECARIO/ADMIN.
    ("BIBLIOTECARIO", "Ejemplar", "read", "false"),
    ("BIBLIOTECARIO", "Ejemplar", "create", "false"),
    ("BIBLIOTECARIO", "Ejemplar", "update", "false"),
    ("BIBLIOTECARIO", "Ejemplar", "delete", "false"),
    ("LECTOR", "Ejemplar", "read", "false"),
    ("PROFESOR", "Ejemplar", "read", "false"),
    # Reservas: biblioteca gestiona todas; LECTOR/PROFESOR crea y atiende las suyas.
    ("BIBLIOTECARIO", "Reserva", "read", "false"),
    ("BIBLIOTECARIO", "Reserva", "create", "false"),
    ("BIBLIOTECARIO", "Reserva", "cancel", "false"),
    ("LECTOR", "Reserva", "read", "true"),
    ("LECTOR", "Reserva", "create", "false"),
    ("LECTOR", "Reserva", "cancel", "true"),
    ("PROFESOR", "Reserva", "read", "true"),
    ("PROFESOR", "Reserva", "create", "false"),
    ("PROFESOR", "Reserva", "cancel", "true"),
]

_adapter = Adapter(engine, db_class=OracleCasbinRule)
enforcer = casbin.Enforcer(_MODEL_PATH, _adapter)


def ensure_default_policies() -> None:
    """Siembra las políticas por defecto en `casbin_rule` (Oracle).

    Es idempotente: en instalaciones nuevas siembra todas, y en instalaciones
    existentes solo agrega las que falten (así nuevos roles/permisos llegan
    sin tener que truncar la tabla ni tocar la BD a mano).
    """
    enforcer.load_policy()
    existing = {tuple(policy) for policy in enforcer.get_policy()}
    for rol, subject, act, owner_only in DEFAULT_POLICIES:
        policy = (rol, subject, act, owner_only)
        if policy not in existing:
            enforcer.add_policy(*policy)
            existing.add(policy)
    enforcer.save_policy()
