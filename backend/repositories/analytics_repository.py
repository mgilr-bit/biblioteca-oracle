"""Repositorio de métricas OLAP (ejecuta SQL nativo sobre las vistas
materializadas creadas por la migración 0010)."""
from sqlalchemy import text
from sqlmodel import Session


class AnalyticsRepository:
    def __init__(self, session: Session):
        self.session = session

    def _scalar(self, query: str) -> int:
        return self.session.execute(text(query)).scalar() or 0

    def totales(self) -> dict:
        prestamos_activos = self._scalar(
            "SELECT COUNT(*) FROM prestamos WHERE is_deleted = 0 AND estado IN ('ACTIVO', 'VENCIDO')"
        )
        copias_disponibles = self._scalar(
            "SELECT NVL(SUM(copias_disponibles), 0) FROM libros WHERE is_deleted = 0"
        )
        usuarios_activos = self._scalar(
            "SELECT COUNT(*) FROM usuarios WHERE activo = 'S' AND is_deleted = 0"
        )
        multas_pendientes = self._scalar(
            "SELECT COUNT(*) FROM multas WHERE is_deleted = 0 AND estado = 'PENDIENTE'"
        )
        deuda_pendiente = self.session.execute(
            text("SELECT NVL(SUM(monto), 0) FROM multas WHERE is_deleted = 0 AND estado = 'PENDIENTE'")
        ).scalar()
        return {
            "prestamos_activos": prestamos_activos,
            "copias_disponibles": copias_disponibles,
            "usuarios_activos": usuarios_activos,
            "multas_pendientes": multas_pendientes,
            "deuda_pendiente": float(deuda_pendiente or 0),
        }

    def prestamos_mensual(self) -> list:
        rows = self.session.execute(
            text(
                "SELECT anio, mes, total_prestamos, devueltos, activos, vencidos "
                "FROM V_OLAP_PRESTAMOS_MENSUAL "
                "ORDER BY anio DESC, mes DESC FETCH FIRST 12 ROWS ONLY"
            )
        ).all()
        return [
            {
                "anio": int(r.anio),
                "mes": int(r.mes),
                "total_prestamos": int(r.total_prestamos),
                "devueltos": int(r.devueltos),
                "activos": int(r.activos),
                "vencidos": int(r.vencidos),
            }
            for r in rows
        ][::-1]  # cronológico

    def top_libros(self) -> list:
        rows = self.session.execute(
            text(
                "SELECT id_libro, titulo, autor, total_prestamos "
                "FROM V_OLAP_TOP_LIBROS ORDER BY total_prestamos DESC"
            )
        ).all()
        return [
            {
                "id_libro": int(r.id_libro),
                "titulo": r.titulo,
                "autor": r.autor,
                "total_prestamos": int(r.total_prestamos),
            }
            for r in rows
        ]

    def prestamos_por_genero(self) -> list:
        rows = self.session.execute(
            text("SELECT genero, total_prestamos FROM V_OLAP_PRESTAMOS_GENERO ORDER BY total_prestamos DESC")
        ).all()
        return [{"genero": r.genero, "total_prestamos": int(r.total_prestamos)} for r in rows]

    def multas_mensual(self) -> list:
        rows = self.session.execute(
            text(
                "SELECT anio, mes, monto_generado, monto_recaudado, pendientes "
                "FROM V_OLAP_MULTAS_MENSUAL "
                "ORDER BY anio DESC, mes DESC FETCH FIRST 12 ROWS ONLY"
            )
        ).all()
        return [
            {
                "anio": int(r.anio),
                "mes": int(r.mes),
                "monto_generado": float(r.monto_generado or 0),
                "monto_recaudado": float(r.monto_recaudado or 0),
                "pendientes": int(r.pendientes),
            }
            for r in rows
        ][::-1]  # cronológico