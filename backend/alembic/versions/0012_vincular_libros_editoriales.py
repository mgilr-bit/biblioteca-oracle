"""vincula libros.id_editorial con el catálogo EDITORIALES

La 0004 creó el catálogo y la FK, pero el formulario de libros seguía
guardando solo el texto `libros.editorial`, así que ningún libro quedó con
`id_editorial`. Esta migración:

1. Agrega al catálogo las editoriales de los libros de demo (con país y
   sitio web cuando la editorial sigue activa).
2. Normaliza variantes del texto (p. ej. sin tilde) al nombre del catálogo.
3. Promueve al catálogo cualquier otro texto de editorial que no exista.
4. Liga cada libro a su editorial por nombre (sin distinguir mayúsculas).

Idempotente: no duplica editoriales ni toca libros ya vinculados.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-24
"""
import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

# (nombre en el catálogo, país, sitio web, variantes del texto en libros)
EDITORIALES = [
    ("Editorial Sudamericana", "Argentina", None, []),
    ("Editorial Planeta", "España", "https://www.planetadelibros.com/", []),
    ("Editorial Losada", "Argentina", None, []),
    ("Editorial Sur", "Argentina", None, []),
    ("Fondo de Cultura Económica", "México", "https://www.fondodeculturaeconomica.com/",
     ["Fondo de Cultura Economica"]),
    ("Secker and Warburg", "Reino Unido", None, []),
    ("Reynal and Hitchcock", "Estados Unidos", None, []),
    ("Francisco de Robles", "España", None, []),
]


def upgrade() -> None:
    conn = op.get_bind()

    for nombre, pais, sitio_web, variantes in EDITORIALES:
        conn.execute(
            sa.text(
                """
                INSERT INTO editoriales (nombre, pais, sitio_web, created_by)
                SELECT :nombre, :pais, :sitio_web, 'system' FROM dual
                WHERE NOT EXISTS (
                    SELECT 1 FROM editoriales WHERE UPPER(nombre) = UPPER(:nombre)
                )
                """
            ),
            {"nombre": nombre, "pais": pais, "sitio_web": sitio_web},
        )
        for variante in variantes:
            conn.execute(
                sa.text(
                    "UPDATE libros SET editorial = :nombre "
                    "WHERE UPPER(TRIM(editorial)) = UPPER(:variante)"
                ),
                {"nombre": nombre, "variante": variante},
            )

    # "Mexico" y "México" contarían como dos países en el reporte.
    conn.execute(sa.text("UPDATE editoriales SET pais = 'México' WHERE pais = 'Mexico'"))

    # Textos sueltos que no están en la lista de arriba (otras instalaciones).
    conn.execute(
        sa.text(
            """
            INSERT INTO editoriales (nombre, created_by)
            SELECT MIN(TRIM(l.editorial)), 'system'
            FROM libros l
            WHERE l.is_deleted = 0
              AND l.id_editorial IS NULL
              AND TRIM(l.editorial) IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM editoriales e
                  WHERE UPPER(e.nombre) = UPPER(TRIM(l.editorial))
              )
            GROUP BY UPPER(TRIM(l.editorial))
            """
        )
    )

    # Liga y deja el texto igual al nombre del catálogo. (UPDATE y no MERGE:
    # Oracle no deja actualizar en un MERGE las columnas usadas en el ON.)
    conn.execute(
        sa.text(
            """
            UPDATE libros l
            SET (id_editorial, editorial) = (
                SELECT e.id_editorial, e.nombre
                FROM editoriales e
                WHERE e.is_deleted = 0 AND UPPER(e.nombre) = UPPER(TRIM(l.editorial))
                ORDER BY e.id_editorial
                FETCH FIRST 1 ROWS ONLY
            )
            WHERE l.id_editorial IS NULL
              AND EXISTS (
                  SELECT 1 FROM editoriales e
                  WHERE e.is_deleted = 0 AND UPPER(e.nombre) = UPPER(TRIM(l.editorial))
              )
            """
        )
    )


def downgrade() -> None:
    # Migración de datos: no se desvinculan los libros ni se borra el catálogo.
    pass
