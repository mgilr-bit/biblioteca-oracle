"""Router de consulta de la bitácora de auditoría.

Solo lectura y restringido a BIBLIOTECARIO/ADMIN (Casbin). Los eventos se
escriben desde los servicios (AuthService, PrestamoService, MultaService,
ReservaService, UsuarioService, EjemplarService); aquí no hay escritura
manual a la bitácora.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from core.etag import etag_response
from dependencies.db import get_db_session
from dependencies.rbac import require_permission
from schemas.auditoria import AuditoriaListResponse, AuditoriaResponse
from services.auditoria_service import AuditoriaService

router = APIRouter()

READ = require_permission("Auditoria", "read")


@router.get("/", response_model=AuditoriaListResponse)
def get_auditoria(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    accion: Optional[str] = None,
    recurso: Optional[str] = None,
    id_usuario: Optional[int] = None,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    result = AuditoriaService(session).listar(
        page, per_page, accion=accion, recurso=recurso, id_usuario=id_usuario
    )
    payload = AuditoriaListResponse(
        auditoria=[AuditoriaResponse.model_validate(r) for r in result["auditoria"]],
        page=result["page"],
        per_page=result["per_page"],
        total=result["total"],
        total_pages=result["total_pages"],
    )
    return etag_response(request, payload)


@router.get("/acciones", response_model=list[str])
def get_acciones(
    request: Request, session: Session = Depends(get_db_session), user=Depends(READ)
):
    return etag_response(request, AuditoriaService(session).get_acciones_disponibles())


@router.get("/recursos", response_model=list[str])
def get_recursos(
    request: Request, session: Session = Depends(get_db_session), user=Depends(READ)
):
    return etag_response(request, AuditoriaService(session).get_recursos_disponibles())