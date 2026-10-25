"""Avisos (notificaciones) que disparan los flujos de negocio.

Vive aparte de NotificacionService para que préstamos, multas y reservas
puedan avisar sin importarse entre sí (NotificacionService ya depende de
esos servicios para el mantenimiento periódico). Solo usa repositorios.
"""
from datetime import datetime

from core.zona_horaria import a_local
from models.notificacion import Notificacion
from repositories.notificacion_repository import NotificacionRepository
from repositories.usuario_repository import UsuarioRepository

ACTOR = "sistema"


def fecha(valor: datetime) -> str:
    """Fecha de la BD (UTC) como la lee el usuario: dd/mm/aaaa en hora local."""
    return a_local(valor).strftime("%d/%m/%Y")


def fecha_hora(valor: datetime) -> str:
    return a_local(valor).strftime("%d/%m/%Y %H:%M")


def avisar_usuario(session, id_usuario: int, tipo: str, mensaje: str) -> None:
    NotificacionRepository(session).add(
        Notificacion(id_usuario=id_usuario, tipo=tipo, mensaje=mensaje[:500]), actor=ACTOR
    )


def avisar_personal(session, tipo: str, mensaje: str) -> None:
    """Un aviso a cada BIBLIOTECARIO/ADMIN activo (las bandejas son personales)."""
    for personal in UsuarioRepository(session).get_personal_activo():
        avisar_usuario(session, personal.id_usuario, tipo, mensaje)
