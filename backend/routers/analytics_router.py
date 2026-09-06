"""Router del dashboard analítico (OLAP).

Solo BIBLIOTECARIO/ADMIN (Casbin). Lee las vistas materializadas creadas
por la migración 0010; la respuesta es un snapshot estructurado que la SPA
renderiza sin librerías de gráficas externas.
"""
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from core.etag import etag_response
from dependencies.db import get_db_session
from dependencies.rbac import require_permission
from services.analytics_service import AnalyticsService

router = APIRouter()

READ = require_permission("Analitica", "read")


@router.get("/olap")
def get_resumen_olap(
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(READ),
):
    return etag_response(request, AnalyticsService(session).resumen())