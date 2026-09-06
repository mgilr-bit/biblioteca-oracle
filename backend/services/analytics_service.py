"""Servicio de métricas OLAP para el dashboard analítico."""
from repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, session):
        self.repository = AnalyticsRepository(session)

    def resumen(self) -> dict:
        return {
            "totales": self.repository.totales(),
            "prestamos_mensual": self.repository.prestamos_mensual(),
            "top_libros": self.repository.top_libros(),
            "prestamos_por_genero": self.repository.prestamos_por_genero(),
            "multas_mensual": self.repository.multas_mensual(),
        }