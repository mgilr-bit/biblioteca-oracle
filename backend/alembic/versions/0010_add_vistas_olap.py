"""Vistas materializadas OLAP para el dashboard analítico.

Pre-agregan las métricas que consulta la SPA (endpoint /api/dashboard/olap)
para que los correlatos de negocio no corran sobre los datos operativos:
* V_OLAP_PRESTAMOS_MENSUAL : serie mensual de préstamos (total, devueltos,
  activos y vencidos al corte) para los últimos 12 meses.
* V_OLAP_TOP_LIBROS        : libros con más préstamos (top por demanda).
* V_OLAP_PRESTAMOS_GENERO  : demanda desagregada por género del libro.
* V_OLAP_MULTAS_MENSUAL    : monto generado, recaudado y pendiente por mes.

REFRESH ON DEMAND: el procedimiento que se ejecuta junto con el job de
notificaciones (09_cron_jobs.sql) refresca las cuatro. Materializado para
no recalcular agregados en cada lectura del dashboard.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-05
"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

_VISTAS = [
    (
        "V_OLAP_PRESTAMOS_MENSUAL",
        """
        SELECT
          TO_CHAR(p.fecha_prestamo, 'YYYY') AS anio,
          TO_CHAR(p.fecha_prestamo, 'MM')   AS mes,
          COUNT(*)                          AS total_prestamos,
          SUM(CASE WHEN p.estado = 'DEVUELTO' THEN 1 ELSE 0 END) AS devueltos,
          SUM(CASE WHEN p.estado IN ('ACTIVO', 'VENCIDO') THEN 1 ELSE 0 END) AS activos,
          SUM(CASE WHEN p.estado = 'VENCIDO' OR (p.estado = 'ACTIVO' AND p.fecha_devolucion_esperada < SYSDATE) THEN 1 ELSE 0 END) AS vencidos
        FROM prestamos p
        WHERE p.is_deleted = 0 AND p.fecha_prestamo >= ADD_MONTHS(SYSDATE, -12)
        GROUP BY TO_CHAR(p.fecha_prestamo, 'YYYY'), TO_CHAR(p.fecha_prestamo, 'MM')
        """,
    ),
    (
        "V_OLAP_TOP_LIBROS",
        # Sin ORDER BY / FETCH FIRST: una vista materializada no admite la
        # cláusula de limitación de filas (ORA-03049). El "top 10" lo aplica
        # analytics_repository.top_libros() al leer la vista.
        """
        SELECT l.id_libro, l.titulo, l.autor, COUNT(*) AS total_prestamos
        FROM prestamos p
        JOIN libros l ON p.id_libro = l.id_libro
        WHERE p.is_deleted = 0 AND l.is_deleted = 0
        GROUP BY l.id_libro, l.titulo, l.autor
        """,
    ),
    (
        "V_OLAP_PRESTAMOS_GENERO",
        """
        SELECT NVL(l.genero, '(sin género)') AS genero, COUNT(*) AS total_prestamos
        FROM prestamos p
        JOIN libros l ON p.id_libro = l.id_libro
        WHERE p.is_deleted = 0 AND l.is_deleted = 0
        GROUP BY NVL(l.genero, '(sin género)')
        ORDER BY COUNT(*) DESC
        """,
    ),
    (
        "V_OLAP_MULTAS_MENSUAL",
        """
        SELECT
          TO_CHAR(m.created_at, 'YYYY') AS anio,
          TO_CHAR(m.created_at, 'MM')   AS mes,
          SUM(m.monto)                  AS monto_generado,
          SUM(CASE WHEN m.estado = 'PAGADA' THEN m.monto ELSE 0 END) AS monto_recaudado,
          SUM(CASE WHEN m.estado = 'PENDIENTE' THEN 1 ELSE 0 END)    AS pendientes
        FROM multas m
        WHERE m.is_deleted = 0 AND m.created_at >= ADD_MONTHS(SYSDATE, -12)
        GROUP BY TO_CHAR(m.created_at, 'YYYY'), TO_CHAR(m.created_at, 'MM')
        """,
    ),
]


def upgrade() -> None:
    # Idempotente: cada CREATE MATERIALIZED VIEW es DDL y Oracle la
    # auto-commitea al toque, así que un intento previo que fallara a mitad
    # de camino (p. ej. en la 3ra vista) ya dejó creadas la 1ra y la 2da.
    # Sin este chequeo, reintentar la migración choca con ORA-12006.
    conn = op.get_bind()
    # Las vistas materializadas no aparecen en user_views (van en user_mviews,
    # también respaldadas por una tabla); no sirve inspector.get_view_names().
    existentes = {
        row[0]
        for row in conn.execute(sa.text("SELECT mview_name FROM user_mviews"))
    }
    for nombre, query in _VISTAS:
        if nombre.upper() in existentes:
            continue
        conn.execute(
            sa.text(
                f"CREATE MATERIALIZED VIEW {nombre} BUILD IMMEDIATE REFRESH ON DEMAND AS {query}"
            )
        )


def downgrade() -> None:
    conn = op.get_bind()
    for nombre, _ in reversed(_VISTAS):
        try:
            conn.execute(sa.text(f"DROP MATERIALIZED VIEW {nombre}"))
        except Exception:  # noqa: BLE001 - la vista puede no existir
            pass