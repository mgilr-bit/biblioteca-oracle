"""Router de multas por devolución tardía.

Lectura: BIBLIOTECARIO ve todas; LECTOR/PROFESOR solo las propias
(owner_only según la política Casbin). Gestión (pagar/condonar) solo
BIBLIOTECARIO/ADMIN. La multa se genera automáticamente en
PrestamoService.devolver, aquí no hay creación manual.
"""
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from core.etag import etag_response
from dependencies.db import get_db_session
from dependencies.rbac import require_permission, require_permission_owned
from schemas.common import MessageResponse
from schemas.multa import MultaResponse
from services.multa_service import MultaService

router = APIRouter()

READ = require_permission("Multa", "read")


@router.get("/", response_model=list[MultaResponse])
def get_multas(
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    if user.rol not in ("BIBLIOTECARIO", "ADMIN"):
        multas = MultaService(session).get_by_usuario(user.id)
    else:
        multas = MultaService(session).get_all()
    return etag_response(request, multas)


@router.get("/pendientes", response_model=list[MultaResponse])
def get_multas_pendientes(
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Multa", "gestionar")),
):
    return etag_response(request, MultaService(session).get_pendientes())


@router.get("/usuario/{id_usuario}", response_model=list[MultaResponse])
def get_multas_by_usuario(
    id_usuario: int,
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission_owned("Multa", "read", "id_usuario")),
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
