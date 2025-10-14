"""
Script para exportar libros de Oracle a Excel
Uso: python export_libros_excel.py
"""
import oracledb
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def export_libros_to_excel():
    """Exporta todos los libros de la base de datos a un archivo Excel"""
    try:
        # Conectar a la base de datos
        connection = oracledb.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            dsn=f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_SERVICE')}"
        )

        print("✓ Conectado a la base de datos Oracle")

        # Query para obtener todos los libros
        query = """
            SELECT
                id_libro AS "ID",
                titulo AS "Título",
                autor AS "Autor",
                isbn AS "ISBN",
                anio_publicacion AS "Año Publicación",
                genero AS "Género",
                editorial AS "Editorial",
                numero_copias AS "Total Copias",
                copias_disponibles AS "Copias Disponibles",
                fecha_registro AS "Fecha Registro"
            FROM libros
            ORDER BY titulo
        """

        # Leer datos con pandas
        df = pd.read_sql(query, connection)

        print(f"✓ Se encontraron {len(df)} libros")

        # Cerrar conexión
        connection.close()

        # Generar nombre de archivo con fecha
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"libros_export_{timestamp}.xlsx"
        filepath = Path(__file__).resolve().parent.parent / filename

        # Exportar a Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Libros', index=False)

            # Ajustar ancho de columnas
            worksheet = writer.sheets['Libros']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)

        print(f"✓ Archivo Excel creado: {filename}")
        print(f"✓ Ubicación: {filepath}")

        return filepath

    except oracledb.Error as e:
        print(f"✗ Error de base de datos: {e}")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def export_libros_with_stats():
    """Exporta libros con estadísticas adicionales en múltiples hojas"""
    try:
        connection = oracledb.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            dsn=f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_SERVICE')}"
        )

        print("✓ Conectado a la base de datos Oracle")

        # Query principal de libros
        query_libros = """
            SELECT
                id_libro AS "ID",
                titulo AS "Título",
                autor AS "Autor",
                isbn AS "ISBN",
                anio_publicacion AS "Año",
                genero AS "Género",
                editorial AS "Editorial",
                numero_copias AS "Total",
                copias_disponibles AS "Disponibles",
                (numero_copias - copias_disponibles) AS "Prestados",
                fecha_registro AS "Fecha Registro"
            FROM libros
            ORDER BY titulo
        """

        # Query de estadísticas por género
        query_por_genero = """
            SELECT
                genero AS "Género",
                COUNT(*) AS "Total Libros",
                SUM(numero_copias) AS "Total Copias",
                SUM(copias_disponibles) AS "Copias Disponibles"
            FROM libros
            WHERE genero IS NOT NULL
            GROUP BY genero
            ORDER BY COUNT(*) DESC
        """

        # Query de libros más prestados
        query_mas_prestados = """
            SELECT
                l.titulo AS "Título",
                l.autor AS "Autor",
                l.genero AS "Género",
                COUNT(p.id_prestamo) AS "Total Préstamos"
            FROM libros l
            LEFT JOIN prestamos p ON l.id_libro = p.id_libro
            GROUP BY l.titulo, l.autor, l.genero
            ORDER BY COUNT(p.id_prestamo) DESC
            FETCH FIRST 20 ROWS ONLY
        """

        # Query de bajo stock
        query_bajo_stock = """
            SELECT
                titulo AS "Título",
                autor AS "Autor",
                numero_copias AS "Total Copias",
                copias_disponibles AS "Disponibles"
            FROM libros
            WHERE copias_disponibles < 2
            ORDER BY copias_disponibles, titulo
        """

        # Leer datos
        df_libros = pd.read_sql(query_libros, connection)
        df_genero = pd.read_sql(query_por_genero, connection)
        df_prestados = pd.read_sql(query_mas_prestados, connection)
        df_stock = pd.read_sql(query_bajo_stock, connection)

        connection.close()

        print(f"✓ Libros: {len(df_libros)}")
        print(f"✓ Géneros: {len(df_genero)}")
        print(f"✓ Más prestados: {len(df_prestados)}")
        print(f"✓ Bajo stock: {len(df_stock)}")

        # Generar archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"biblioteca_completo_{timestamp}.xlsx"
        filepath = Path(__file__).resolve().parent.parent / filename

        # Exportar con múltiples hojas
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Hoja 1: Todos los libros
            df_libros.to_excel(writer, sheet_name='Todos los Libros', index=False)

            # Hoja 2: Estadísticas por género
            df_genero.to_excel(writer, sheet_name='Por Género', index=False)

            # Hoja 3: Más prestados
            df_prestados.to_excel(writer, sheet_name='Más Prestados', index=False)

            # Hoja 4: Bajo stock
            df_stock.to_excel(writer, sheet_name='Bajo Stock', index=False)

            # Ajustar anchos de columnas para todas las hojas
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"✓ Archivo Excel completo creado: {filename}")
        print(f"✓ Ubicación: {filepath}")

        return filepath

    except Exception as e:
        print(f"✗ Error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("EXPORTACIÓN DE LIBROS A EXCEL")
    print("=" * 60)
    print()
    print("Opciones:")
    print("1. Exportar solo libros (simple)")
    print("2. Exportar con estadísticas (completo)")
    print()

    opcion = input("Seleccione una opción (1 o 2): ").strip()

    print()
    if opcion == "1":
        export_libros_to_excel()
    elif opcion == "2":
        export_libros_with_stats()
    else:
        print("Opción inválida")

    print()
    print("=" * 60)
