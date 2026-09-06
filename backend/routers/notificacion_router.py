"""Router de notificaciones (bandeja por usuario) y mantenimiento (cron).

Autorización (Casbin, RBAC+ABAC):
* Operaciones sobre la propia bandeja (`/`, `/no-leidas/count`,
  `/marcar-todas-leidas`, `/{id}/leida`) usan `require_permission_session_owned`:
  el "dueño" es el usuario en sesión; LECTOR/PROFESOR solo consigo mismos y
  BIBLIOTECARIO/ADMIN con cualquiera.
* `GET /usuario/{id}` (ver la bandeja de otro) exige permiso sin restricción
  de dueño, que solo tienen BIBLIOTECARIO/ADMIN.
* `PUT /mantenimiento` (cron) es solo de ADMIN (política wildcard de ADMIN).

Handlers sync porque la sesión de BD hace I/O bloqueante contra Oracle.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from core.etag import etag_response
from core.sessions import SessionUser
from dependencies.db import get_db_session
from dependencies.rbac import require_permission, require_permission_session_owned
from schemas.common import MessageResponse
from schemas.notificacion import MantenimientoResponse, NotificacionCountResponse, NotificacionResponse
from services.notificacion_service import NotificacionService

router = APIRouter()

OWN = require_permission_session_owned


@router.get("/", response_model=list[NotificacionResponse])
def get_mis_notificaciones(
    request: Request,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(OWN("Notificacion", "read")),
):
    return etag_response(request, NotificacionService(session).get_mis_notificaciones(user.id))


@router.get("/usuario/{id_usuario}", response_model=list[NotificacionResponse])
def get_notificaciones_usuario(
    id_usuario: int,
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Notificacion", "read")),
):
    return etag_response(request, NotificacionService(session).get_mis_notificaciones(id_usuario))


@router.get("/no-leidas/count", response_model=NotificacionCountResponse)
def get_no_leidas(
    request: Request,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(OWN("Notificacion", "read")),
):
    return etag_response(request, {"no_leidas": NotificacionService(session).get_no_leidas_count(user.id)})


@router.put("/marcar-todas-leidas", response_model=MessageResponse)
def marcar_todas_leidas(
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(OWN("Notificacion", "update")),
):
    return NotificacionService(session).marcar_todas_leidas(user.id, actor=user.email)


@router.put("/mantenimiento", response_model=MantenimientoResponse)
def ejecutar_mantenimiento(
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission("Notificacion", "mantenimiento")),
):
    return NotificacionService(session).ejecutar_mantenimiento(actor=user.email)


@router.put("/{id_notificacion}/leida", response_model=MessageResponse)
def marcar_leida(
    id_notificacion: int,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(OWN("Notificacion", "update")),
):
    notificacion = NotificacionService(session).get_by_id(id_notificacion)
    if notificacion.id_usuario != user.id and user.rol in ("LECTOR", "PROFESOR"):
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return NotificacionService(session).marcar_leida(id_notificacion, actor=user.email)