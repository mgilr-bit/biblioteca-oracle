"""Router de gestión de reservas.

Handlers sync (no `async def`) porque la sesión de BD hace I/O bloqueante
contra Oracle — FastAPI los corre en threadpool.

Autorización (Casbin, RBAC+ABAC): BIBLIOTECARIO/ADMIN ve y gestiona la
lista completa y la cola; un LECTOR/PROFESOR solo lee/cancela las suyas
(`/usuario/{id}` y `/{id}/cancelar` con chequeo de dueño).
"""
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from core.etag import etag_response
from core.sessions import SessionUser
from dependencies.db import get_db_session
from dependencies.rbac import require_permission, require_permission_owned
from schemas.common import MessageResponse
from schemas.reserva import ReservaCreate, ReservaResponse
from services.reserva_service import ReservaService

router = APIRouter()

LIST_ALL = require_permission("Reserva", "read")


@router.get("/", response_model=list[ReservaResponse])
def get_reservas(request: Request, session: Session = Depends(get_db_session), user=Depends(LIST_ALL)):
    return etag_response(request, ReservaService(session).get_all())


@router.get("/cola/{id_libro}", response_model=list[dict])
def get_cola_reservas(
    id_libro: int,
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(LIST_ALL),
):
    return etag_response(request, ReservaService(session).get_cola(id_libro))


@router.get("/usuario/{id_usuario}", response_model=list[ReservaResponse])
def get_reservas_usuario(
    id_usuario: int,
    request: Request,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission_owned("Reserva", "read", "id_usuario")),
):
    return etag_response(request, ReservaService(session).get_by_usuario(id_usuario))


@router.post("/", response_model=MessageResponse, status_code=201)
def create_reserva(
    body: ReservaCreate,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission("Reserva", "create")),
):
    return ReservaService(session).create(body.id_libro, body.id_usuario, requesting_user=user)


@router.put("/{id_reserva}/cancelar", response_model=MessageResponse)
def cancelar_reserva(
    id_reserva: int,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission_owned("Reserva", "cancel", "id_reserva")),
):
    return ReservaService(session).cancelar(id_reserva, requesting_user=user)