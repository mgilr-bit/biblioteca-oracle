"""Router de gestión de libros.

Los handlers son funciones sync (no `async def`): FastAPI las corre en un
threadpool automáticamente, que es lo correcto dado que la sesión de BD
hace I/O bloqueante contra Oracle (ver decisión de mantener la capa de
datos síncrona en el plan de migración) — así no se bloquea el event loop.
"""
import csv
import io
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request, Response
from sqlmodel import Session

from core.etag import etag_response
from dependencies.db import get_db_session
from dependencies.rbac import require_permission
from schemas.common import MessageResponse
from schemas.libro import (
    LibroCopiasUpdate,
    LibroCreate,
    LibroEstadisticasResponse,
    LibroListResponse,
    LibroResponse,
    LibroUpdate,
)
from services.libro_service import LibroService

router = APIRouter()
logger = logging.getLogger(__name__)

READ = require_permission("Libro", "read")
WRITE = require_permission("Libro", "update")


# Rutas estáticas primero para que no compitan con /{id_libro}.
@router.get("/generos", response_model=list[str])
def get_generos(request: Request, session: Session = Depends(get_db_session), user=Depends(READ)):
    generos = LibroService(session).get_generos()
    return etag_response(request, generos)


@router.get("/search", response_model=list[LibroResponse])
def search_libros(
    request: Request,
    titulo: str = "",
    autor: str = "",
    isbn: str = "",
    genero: str = "",
    limit: int = 200,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    libros = LibroService(session).search(titulo, autor, isbn, genero, limit)
    return etag_response(request, [LibroResponse.model_validate(l) for l in libros])


@router.get("/bajo-stock", response_model=list[LibroResponse])
def libros_bajo_stock(request: Request, session: Session = Depends(get_db_session), user=Depends(READ)):
    libros = LibroService(session).get_bajo_stock()
    return etag_response(request, [LibroResponse.model_validate(l) for l in libros])


@router.get("/export/csv")
def export_libros_csv(
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Libro", "read")),
):
    libros = LibroService(session).get_all_for_export()

    rows = [LibroResponse.model_validate(l).model_dump(by_alias=True) for l in libros]

    output = io.StringIO()
    writer = csv.writer(output)
    if rows:
        headers = list(rows[0].keys())
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row.get(h) for h in headers])

    logger.info(f"Exportación CSV: {len(rows)} libros exportados por usuario {user.email}")

    response = Response(content=output.getvalue(), media_type="text/csv; charset=utf-8")
    filename = f"libros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@router.get("/estadisticas", response_model=LibroEstadisticasResponse)
def get_estadisticas(request: Request, session: Session = Depends(get_db_session), user=Depends(READ)):
    stats = LibroService(session).get_estadisticas()
    return etag_response(request, stats)


@router.get("/", response_model=LibroListResponse)
def get_libros(
    request: Request,
    page: int = 1,
    per_page: int = 100,
    limit: Optional[int] = None,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    result = LibroService(session).get_all(page, per_page, limit)
    payload = LibroListResponse(
        libros=[LibroResponse.model_validate(l) for l in result["libros"]],
        page=result["page"],
        per_page=result["per_page"],
        total=result["total"],
        total_pages=result["total_pages"],
    )
    return etag_response(request, payload)


@router.post("/", response_model=MessageResponse, status_code=201)
def create_libro(
    body: LibroCreate,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Libro", "create")),
):
    return LibroService(session).create(body.model_dump())


@router.get("/{id_libro}", response_model=LibroResponse)
def get_libro(id_libro: int, request: Request, session: Session = Depends(get_db_session), user=Depends(READ)):
    libro = LibroService(session).get_by_id(id_libro)
    return etag_response(request, LibroResponse.model_validate(libro))


@router.put("/{id_libro}", response_model=MessageResponse)
def update_libro(id_libro: int, body: LibroUpdate, session: Session = Depends(get_db_session), user=Depends(WRITE)):
    return LibroService(session).update(id_libro, body.model_dump())


@router.patch("/{id_libro}/copias", response_model=MessageResponse)
def update_copias(
    id_libro: int, body: LibroCopiasUpdate, session: Session = Depends(get_db_session), user=Depends(WRITE)
):
    return LibroService(session).update_copias(id_libro, body.copias_disponibles)


@router.delete("/{id_libro}", response_model=MessageResponse)
def delete_libro(
    id_libro: int,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Libro", "delete")),
):
    return LibroService(session).delete(id_libro)
