"""Router de gestión de multas por devolución tardía.

Las multas no se crean vía API: nacen solas al registrar una devolución
tardía (ver PrestamoService.devolver). Este router solo expone consultas y
las acciones del bibliotecario para cerrarlas (pagar / condonar).

Autorización: BIBLIOTECARIO ve y gestiona todas; un LECTOR solo puede leer
las suyas (`GET /usuario/{id}` con chequeo de dueño).

Handlers sync (no `async def`) porque la sesión de BD hace I/O bloqueante
contra Oracle — FastAPI los corre en threadpool.
"""
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from core.etag import etag_response
from core.sessions import SessionUser
from dependencies.db import get_db_session
from dependencies.rbac import require_permission, require_permission_owned
from schemas.common import MessageResponse
from schemas.multa import MultaResponse
from services.multa_service import MultaService

router = APIRouter()

LIST_ALL = require_permission("Multa", "read")


@router.get("/", response_model=list[MultaResponse])
def get_multas(request: Request, session: Session = Depends(get_db_session), user=Depends(LIST_ALL)):
    return etag_response(request, MultaService(session).get_all())


@router.get("/pendientes", response_model=list[MultaResponse])
def get_multas_pendientes(
    request: Request, session: Session = Depends(get_db_session), user=Depends(LIST_ALL)
):
    return etag_response(request, MultaService(session).get_pendientes())


@router.get("/usuario/{id_usuario}", response_model=list[MultaResponse])
def get_multas_usuario(
    id_usuario: int,
    request: Request,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission_owned("Multa", "read", "id_usuario")),
):
    return etag_response(request, MultaService(session).get_by_usuario(id_usuario))


@router.put("/{id_multa}/pagar", response_model=MessageResponse)
def pagar_multa(
    id_multa: int,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Multa", "gestionar")),
):
    return MultaService(session).pagar(id_multa, actor=user.email)


@router.put("/{id_multa}/condonar", response_model=MessageResponse)
def condonar_multa(
    id_multa: int,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Multa", "gestionar")),
):
    return MultaService(session).condonar(id_multa, actor=user.email)
