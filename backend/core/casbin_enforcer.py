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

    # El adapter reconstruye cada política al cargar haciendo `str(fila)` y
    # parseando "p, v0, v1, …" (mismo formato que la CasbinRule de la
    # librería). Sin este método `load_policy()` no leía ninguna regla.
    def __str__(self):
        valores = [self.ptype]
        for valor in (self.v0, self.v1, self.v2, self.v3, self.v4, self.v5):
            if valor is None:
                break
            valores.append(valor)
        return ", ".join(valores)

    def __repr__(self):
        return f'<CasbinRule {self.id}: "{self}">'

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
    # Prestamos: BIBLIOTECARIO ve/gestiona todo; PROFESOR crea y lee solo los
    # suyos; LECTOR solo los consulta (el préstamo se lo registra la biblioteca).
    ("BIBLIOTECARIO", "Prestamo", "read", "false"),
    ("BIBLIOTECARIO", "Prestamo", "create", "false"),
    ("BIBLIOTECARIO", "Prestamo", "devolver", "false"),
    ("LECTOR", "Prestamo", "read", "true"),
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
    # Notificaciones: bandeja personal (owner_only para LECTOR/PROFESOR);
    # BIBLIOTECARIO lee todas (asiste a usuarios); mantenimiento solo ADMIN.
    ("BIBLIOTECARIO", "Notificacion", "read", "false"),
    ("BIBLIOTECARIO", "Notificacion", "update", "false"),
    ("LECTOR", "Notificacion", "read", "true"),
    ("LECTOR", "Notificacion", "update", "true"),
    ("PROFESOR", "Notificacion", "read", "true"),
    ("PROFESOR", "Notificacion", "update", "true"),
    # Multas: BIBLIOTECARIO lee/gestiona todas (cobrar); LECTOR y
    # PROFESOR solo ven las suyas (owner_only), sin acciones de gestión.
    ("BIBLIOTECARIO", "Multa", "read", "false"),
    ("BIBLIOTECARIO", "Multa", "gestionar", "false"),
    ("LECTOR", "Multa", "read", "true"),
    ("PROFESOR", "Multa", "read", "true"),
    # Auditoría: la bitácora es exclusiva del ADMIN (cubierto por su política
    # comodín). Ningún otro rol —BIBLIOTECARIO incluido— la consulta: es el
    # registro que deja constancia de lo que hace el propio equipo.
    # Analítica OLAP: dashboard de métricas, solo BIBLIOTECARIO/ADMIN.
    ("BIBLIOTECARIO", "Analitica", "read", "false"),
]

# Políticas retiradas de DEFAULT_POLICIES que deben desaparecer también de
# las instalaciones ya sembradas: `ensure_default_policies` solo agrega, así
# que sin esta lista la fila seguiría viva en `casbin_rule` concediendo un
# acceso que ya se revocó.
REVOKED_POLICIES = [
    # Auditoría pasó a ser exclusiva del ADMIN (2026-09-17).
    ("BIBLIOTECARIO", "Auditoria", "read", "false"),
    # El LECTOR ya no registra préstamos por su cuenta (QA 2026-10-06).
    ("LECTOR", "Prestamo", "create", "false"),
]

_adapter = Adapter(engine, db_class=OracleCasbinRule)
enforcer = casbin.Enforcer(_MODEL_PATH, _adapter)


def ensure_default_policies() -> None:
    """Siembra las políticas por defecto en `casbin_rule` (Oracle).

    Es idempotente: en instalaciones nuevas siembra todas, y en instalaciones
    existentes solo agrega las que falten (así nuevos roles/permisos llegan
    sin tener que truncar la tabla ni tocar la BD a mano).

    Con auto-save activo cada `add_policy` es un INSERT + COMMIT propio: contra
    Oracle en la nube eso son decenas de viajes de red y el arranque superaba
    el timeout del worker de gunicorn (WORKER TIMEOUT en bucle). Por eso el
    cálculo se hace en memoria y, solo si algo cambió, se persiste todo en
    una única transacción con `save_policy()`.
    """
    enforcer.enable_auto_save(False)
    try:
        enforcer.load_policy()
        actuales = [tuple(policy) for policy in enforcer.get_policy()]
        # dict.fromkeys deduplica conservando el orden (un arranque cortado a
        # medias con el código anterior pudo dejar filas repetidas).
        deseadas = list(dict.fromkeys(actuales))
        presentes = set(deseadas)
        deseadas += [policy for policy in DEFAULT_POLICIES if policy not in presentes]
        revocadas = set(REVOKED_POLICIES)
        deseadas = [policy for policy in deseadas if policy not in revocadas]

        if deseadas != actuales:
            enforcer.clear_policy()
            enforcer.add_policies([list(policy) for policy in deseadas])
            enforcer.save_policy()
    finally:
        enforcer.enable_auto_save(True)
