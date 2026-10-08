"""Repositorio de métricas OLAP (SQL nativo de agregación).

Las agregaciones corren en vivo sobre las tablas operativas. Antes se leían
de las vistas materializadas de la migración 0010 (REFRESH ON DEMAND), pero
en la base de la nube no hay job que las refresque: quedaron congeladas en
el snapshot de su creación (vacío) y el dashboard no mostraba nada. Con el
volumen de una biblioteca universitaria la consulta directa es barata.
"""
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
                "SELECT TO_CHAR(fecha_prestamo, 'YYYY') AS anio, "
                "TO_CHAR(fecha_prestamo, 'MM') AS mes, "
                "COUNT(*) AS total_prestamos, "
                "SUM(CASE WHEN estado = 'DEVUELTO' THEN 1 ELSE 0 END) AS devueltos, "
                "SUM(CASE WHEN estado IN ('ACTIVO', 'VENCIDO') THEN 1 ELSE 0 END) AS activos, "
                "SUM(CASE WHEN estado = 'VENCIDO' OR (estado = 'ACTIVO' "
                "AND fecha_devolucion_esperada < SYSDATE) THEN 1 ELSE 0 END) AS vencidos "
                "FROM prestamos "
                "WHERE is_deleted = 0 AND fecha_prestamo >= ADD_MONTHS(SYSDATE, -12) "
                "GROUP BY TO_CHAR(fecha_prestamo, 'YYYY'), TO_CHAR(fecha_prestamo, 'MM') "
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
                "SELECT l.id_libro, l.titulo, l.autor, COUNT(*) AS total_prestamos "
                "FROM prestamos p JOIN libros l ON p.id_libro = l.id_libro "
                "WHERE p.is_deleted = 0 AND l.is_deleted = 0 "
                "GROUP BY l.id_libro, l.titulo, l.autor "
                "ORDER BY total_prestamos DESC FETCH FIRST 10 ROWS ONLY"
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
            text(
                "SELECT NVL(l.genero, '(sin género)') AS genero, COUNT(*) AS total_prestamos "
                "FROM prestamos p JOIN libros l ON p.id_libro = l.id_libro "
                "WHERE p.is_deleted = 0 AND l.is_deleted = 0 "
                "GROUP BY NVL(l.genero, '(sin género)') "
                "ORDER BY total_prestamos DESC"
            )
        ).all()
        return [{"genero": r.genero, "total_prestamos": int(r.total_prestamos)} for r in rows]

    def multas_mensual(self) -> list:
        rows = self.session.execute(
            text(
                "SELECT TO_CHAR(created_at, 'YYYY') AS anio, "
                "TO_CHAR(created_at, 'MM') AS mes, "
                "SUM(monto) AS monto_generado, "
                "SUM(CASE WHEN estado = 'PAGADA' THEN monto ELSE 0 END) AS monto_recaudado, "
                "SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END) AS pendientes "
                "FROM multas "
                "WHERE is_deleted = 0 AND created_at >= ADD_MONTHS(SYSDATE, -12) "
                "GROUP BY TO_CHAR(created_at, 'YYYY'), TO_CHAR(created_at, 'MM') "
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