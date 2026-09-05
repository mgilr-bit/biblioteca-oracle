"""Router de gestión de editoriales (catálogo).

Handlers sync (no `async def`) porque la sesión de BD hace I/O bloqueante
contra Oracle — FastAPI los corre en threadpool (mismo patrón que los
demás routers del proyecto).

Autorización (Casbin): LECTOR/PROFESOR leen; BIBLIOTECARIO/ADMIN
crean/actualizan/eliminan.
"""
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from core.etag import etag_response
from dependencies.db import get_db_session
from dependencies.rbac import require_permission
from schemas.common import MessageResponse
from schemas.editorial import (
    EditorialCreate,
    EditorialListResponse,
    EditorialResponse,
    EditorialUpdate,
)
from services.editorial_service import EditorialService

router = APIRouter()

READ = require_permission("Editorial", "read")


@router.get("/", response_model=EditorialListResponse)
def get_editoriales(
    request: Request,
    page: int = 1,
    per_page: int = 100,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    result = EditorialService(session).get_all(page, per_page)
    payload = EditorialListResponse(
        editoriales=[EditorialResponse.model_validate(e) for e in result["editoriales"]],
        page=result["page"],
        per_page=result["per_page"],
        total=result["total"],
        total_pages=result["total_pages"],
    )
    return etag_response(request, payload)


@router.get("/todas", response_model=list[EditorialResponse])
def get_todas_editoriales(
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    editoriales = EditorialService(session).get_all_flat()
    return etag_response(request, [EditorialResponse.model_validate(e) for e in editoriales])


@router.post("/", response_model=MessageResponse, status_code=201)
def create_editorial(
    body: EditorialCreate,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Editorial", "create")),
):
    return EditorialService(session).create(body.model_dump(), actor=user.email)


@router.get("/{id_editorial}", response_model=EditorialResponse)
def get_editorial(
    id_editorial: int,
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    editorial = EditorialService(session).get_by_id(id_editorial)
    return etag_response(request, EditorialResponse.model_validate(editorial))


@router.put("/{id_editorial}", response_model=MessageResponse)
def update_editorial(
    id_editorial: int,
    body: EditorialUpdate,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Editorial", "update")),
):
    return EditorialService(session).update(id_editorial, body.model_dump(), actor=user.email)


@router.delete("/{id_editorial}", response_model=MessageResponse)
def delete_editorial(
    id_editorial: int,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Editorial", "delete")),
):
    return EditorialService(session).delete(id_editorial, actor=user.email)