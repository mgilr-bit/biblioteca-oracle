"""libros: la editorial pasa a ser solo FK (elimina libros.editorial)

La migración 0004 creó el catálogo `editoriales` y `libros.id_editorial`,
pero dejó `libros.editorial` (texto libre) "por compatibilidad con el
frontend actual". Mientras convivían las dos, nada garantizaba que
coincidieran: el CRUD aceptaba un nombre suelto sin enlazarlo al catálogo.

Esta migración cierra esa convivencia:

1. da de alta en el catálogo los nombres de `libros.editorial` que aún no
   estén (comparación sin distinguir mayúsculas), con created_by='migration',
2. enlaza `id_editorial` en los libros que lo tenían vacío,
3. elimina `libros.editorial`.

El downgrade restaura la columna de texto desde el nombre de la editorial.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-10
"""
import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Catálogo: nombres en texto libre que todavía no tienen fila.
    op.execute(
        """
        INSERT INTO editoriales (nombre, created_by)
        SELECT MIN(TRIM(l.editorial)), 'migration'
        FROM libros l
        WHERE TRIM(l.editorial) IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM editoriales e
              WHERE e.is_deleted = 0 AND UPPER(e.nombre) = UPPER(TRIM(l.editorial))
          )
        GROUP BY UPPER(TRIM(l.editorial))
        """
    )

    # 2. Enlace: solo donde el libro no tenía id_editorial.
    op.execute(
        """
        UPDATE libros l
        SET id_editorial = (
            SELECT MIN(e.id_editorial) FROM editoriales e
            WHERE e.is_deleted = 0 AND UPPER(e.nombre) = UPPER(TRIM(l.editorial))
        )
        WHERE l.id_editorial IS NULL AND TRIM(l.editorial) IS NOT NULL
        """
    )

    # 3. El texto ya vive en el catálogo.
    op.drop_column("libros", "editorial")


def downgrade() -> None:
    op.add_column("libros", sa.Column("editorial", sa.String(length=100), nullable=True))
    op.execute(
        """
        UPDATE libros l
        SET editorial = (
            SELECT e.nombre FROM editoriales e WHERE e.id_editorial = l.id_editorial
        )
        WHERE l.id_editorial IS NOT NULL
        """
    )
