"""Router de gestión de ejemplares (copias físicas de un libro).

La respuesta sale de un join (Ejemplar + Libro) por lo que se arma en el
service. Handlers sync porque la sesión de BD hace I/O bloqueante contra
Oracle.

Autorización (Casbin): lectura abierta a roles autenticados; gestión
(crear/actualizar/estado/borrar) solo BIBLIOTECARIO/ADMIN.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from core.etag import etag_response
from dependencies.db import get_db_session
from dependencies.rbac import require_permission
from schemas.common import MessageResponse
from schemas.ejemplar import (
    EjemplarCreate,
    EjemplarEstadoUpdate,
    EjemplarListResponse,
    EjemplarResponse,
    EjemplarUpdate,
)
from services.ejemplar_service import EjemplarService

router = APIRouter()

READ = require_permission("Ejemplar", "read")
WRITE = require_permission("Ejemplar", "update")


@router.get("/", response_model=EjemplarListResponse)
def get_ejemplares(
    request: Request,
    page: int = 1,
    per_page: int = 100,
    id_libro: Optional[int] = None,
    estado: Optional[str] = None,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    result = EjemplarService(session).get_all(page, per_page, id_libro, estado)
    payload = EjemplarListResponse(
        ejemplares=[EjemplarResponse.model_validate(e) for e in result["ejemplares"]],
        page=result["page"],
        per_page=result["per_page"],
        total=result["total"],
        total_pages=result["total_pages"],
    )
    return etag_response(request, payload)


@router.get("/estados", response_model=list[str])
def get_estados(request: Request, session: Session = Depends(get_db_session), user=Depends(READ)):
    return etag_response(request, EjemplarService(session).get_estados())


@router.get("/por-libro/{id_libro}", response_model=list[EjemplarResponse])
def get_ejemplares_por_libro(
    id_libro: int,
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    ejemplares = EjemplarService(session).get_by_libro(id_libro)
    return etag_response(request, [EjemplarResponse.model_validate(e) for e in ejemplares])


@router.post("/", response_model=MessageResponse, status_code=201)
def create_ejemplar(
    body: EjemplarCreate,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Ejemplar", "create")),
):
    return EjemplarService(session).create(body.model_dump(), actor=user.email)


@router.get("/{id_ejemplar}", response_model=EjemplarResponse)
def get_ejemplar(
    id_ejemplar: int,
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    ejemplar = EjemplarService(session).get_by_id(id_ejemplar)
    servicio = EjemplarService(session)
    payload = servicio.serializar_ejemplar(ejemplar, servicio._titulo_de(ejemplar.id_libro))
    return etag_response(request, EjemplarResponse.model_validate(payload))


@router.put("/{id_ejemplar}", response_model=MessageResponse)
def update_ejemplar(
    id_ejemplar: int,
    body: EjemplarUpdate,
    session: Session = Depends(get_db_session),
    user=Depends(WRITE),
):
    return EjemplarService(session).update(id_ejemplar, body.model_dump(), actor=user.email)


@router.put("/{id_ejemplar}/estado", response_model=MessageResponse)
def change_estado_ejemplar(
    id_ejemplar: int,
    body: EjemplarEstadoUpdate,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Ejemplar", "update")),
):
    return EjemplarService(session).change_estado(id_ejemplar, body.estado, actor=user.email)


@router.delete("/{id_ejemplar}", response_model=MessageResponse)
def delete_ejemplar(
    id_ejemplar: int,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Ejemplar", "delete")),
):
    return EjemplarService(session).delete(id_ejemplar, actor=user.email)