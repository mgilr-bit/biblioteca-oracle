"""
Script para generar el Diagrama Entidad-Relación (ER) de la base de datos
usando graphviz y la conexión existente
"""
import oracledb
from pathlib import Path
from dotenv import load_dotenv
import os

# Cargar variables de entorno
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Configuración de la base de datos
DB_USER = os.getenv('DB_USER', 'biblioteca_user').upper()  # Oracle convierte a mayúsculas
DB_PASSWORD = os.getenv('DB_PASSWORD', 'BiblioPass123')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '1521')
DB_SERVICE = os.getenv('DB_SERVICE', 'XEPDB1')

print("=" * 80)
print("GENERADOR DE DIAGRAMA ER - SISTEMA BIBLIOTECA")
print("=" * 80)
print(f"\nConectando a: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_SERVICE}\n")

# Conectar a la base de datos - usar configuración completa de DSN
dsn = oracledb.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)
connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn)
cursor = connection.cursor()

print("✓ Conexión exitosa\n")

# Obtener información de las tablas
print("Obteniendo información de las tablas...\n")

tables_query = """
    SELECT table_name,
           (SELECT comments FROM user_tab_comments
            WHERE table_name = ut.table_name) as table_comment
    FROM user_tables ut
    WHERE table_name IN ('LIBROS', 'USUARIOS', 'PRESTAMOS')
    ORDER BY table_name
"""

cursor.execute(tables_query)
tables = cursor.fetchall()

# Obtener columnas de cada tabla
columns_query = """
    SELECT
        utc.column_name,
        utc.data_type,
        utc.data_length,
        utc.nullable,
        (SELECT CASE WHEN COUNT(*) > 0 THEN 'PK' ELSE NULL END
         FROM user_constraints uc
         JOIN user_cons_columns ucc ON uc.constraint_name = ucc.constraint_name
         WHERE uc.constraint_type = 'P'
         AND uc.table_name = :table_name
         AND ucc.column_name = utc.column_name) as is_pk,
        (SELECT uc2.constraint_type
         FROM user_constraints uc2
         JOIN user_cons_columns ucc2 ON uc2.constraint_name = ucc2.constraint_name
         WHERE uc2.constraint_type = 'R'
         AND uc2.table_name = :table_name
         AND ucc2.column_name = utc.column_name
         AND ROWNUM = 1) as is_fk
    FROM user_tab_columns utc
    WHERE utc.table_name = :table_name
    ORDER BY utc.column_id
"""

# Obtener foreign keys
fk_query = """
    SELECT
        uc.constraint_name,
        ucc.column_name,
        uc2.table_name as ref_table,
        ucc2.column_name as ref_column
    FROM user_constraints uc
    JOIN user_cons_columns ucc ON uc.constraint_name = ucc.constraint_name
    JOIN user_constraints uc2 ON uc.r_constraint_name = uc2.constraint_name
    JOIN user_cons_columns ucc2 ON uc2.constraint_name = ucc2.constraint_name
    WHERE uc.constraint_type = 'R'
    AND uc.table_name = :table_name
"""

table_info = {}

for table_name, table_comment in tables:
    print(f"  → {table_name}")

    # Obtener columnas
    cursor.execute(columns_query, table_name=table_name)
    columns = cursor.fetchall()

    # Obtener foreign keys
    cursor.execute(fk_query, table_name=table_name)
    fks = cursor.fetchall()

    table_info[table_name] = {
        'comment': table_comment,
        'columns': columns,
        'foreign_keys': fks
    }

cursor.close()
connection.close()

print("\n✓ Información obtenida correctamente\n")

# Generar diagrama usando graphviz
try:
    from graphviz import Digraph

    print("Generando diagrama ER...\n")

    # Crear el grafo
    dot = Digraph(comment='Sistema de Biblioteca - Diagrama ER', format='png')
    dot.attr(rankdir='LR', size='12,8', bgcolor='white')
    dot.attr('node', shape='plaintext', fontname='Arial')
    dot.attr('edge', color='#555555', fontname='Arial', fontsize='10')

    # Colores para las tablas
    colors = {
        'USUARIOS': '#E3F2FD',    # Azul claro
        'LIBROS': '#E8F5E9',      # Verde claro
        'PRESTAMOS': '#FFF3E0'    # Naranja claro
    }

    # Crear nodos para cada tabla
    for table_name, info in table_info.items():
        # Construir HTML para la tabla
        html = f'''<
        <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="{colors.get(table_name, 'white')}">
            <TR><TD BGCOLOR="#1976D2" ALIGN="CENTER" COLSPAN="3">
                <FONT COLOR="white" POINT-SIZE="14"><B>{table_name}</B></FONT>
            </TD></TR>
            <TR>
                <TD BGCOLOR="#BBDEFB"><B>Columna</B></TD>
                <TD BGCOLOR="#BBDEFB"><B>Tipo</B></TD>
                <TD BGCOLOR="#BBDEFB"><B>Restricción</B></TD>
            </TR>
        '''

        for col_name, data_type, data_length, nullable, is_pk, is_fk in info['columns']:
            # Formato del tipo de dato
            if data_type in ('VARCHAR2', 'CHAR'):
                tipo = f"{data_type}({data_length})"
            elif data_type == 'NUMBER':
                tipo = "NUMBER"
            elif data_type == 'DATE':
                tipo = "DATE"
            else:
                tipo = data_type

            # Restricciones
            constraints = []
            if is_pk:
                constraints.append('<FONT COLOR="#D32F2F">PK</FONT>')
            if is_fk:
                constraints.append('<FONT COLOR="#F57C00">FK</FONT>')
            if nullable == 'N' and not is_pk:
                constraints.append('NOT NULL')

            constraint_str = ', '.join(constraints) if constraints else ''

            # Color de fondo para PKs
            bg_color = '#FFEBEE' if is_pk else 'white'

            html += f'''
            <TR>
                <TD ALIGN="LEFT" BGCOLOR="{bg_color}">{col_name}</TD>
                <TD ALIGN="LEFT">{tipo}</TD>
                <TD ALIGN="LEFT">{constraint_str}</TD>
            </TR>
            '''

        html += '</TABLE>>'

        dot.node(table_name, html)

    # Agregar relaciones (Foreign Keys)
    relationships = set()

    for table_name, info in table_info.items():
        for fk_name, col_name, ref_table, ref_column in info['foreign_keys']:
            # Evitar duplicados
            rel_key = (table_name, ref_table)
            if rel_key not in relationships:
                relationships.add(rel_key)

                # Determinar cardinalidad
                if table_name == 'PRESTAMOS' and ref_table in ['USUARIOS', 'LIBROS']:
                    # Relación 1:N
                    dot.edge(
                        ref_table,
                        table_name,
                        label=f'  1:N  ',
                        arrowhead='crow',
                        arrowtail='none',
                        dir='both',
                        penwidth='2'
                    )

    # Agregar leyenda
    legend = '''<
    <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">
        <TR><TD BGCOLOR="#424242" ALIGN="CENTER">
            <FONT COLOR="white" POINT-SIZE="12"><B>LEYENDA</B></FONT>
        </TD></TR>
        <TR><TD ALIGN="LEFT"><FONT COLOR="#D32F2F"><B>PK</B></FONT> = Primary Key</TD></TR>
        <TR><TD ALIGN="LEFT"><FONT COLOR="#F57C00"><B>FK</B></FONT> = Foreign Key</TD></TR>
        <TR><TD ALIGN="LEFT">1:N = Relación uno a muchos</TD></TR>
    </TABLE>>
    '''
    dot.node('legend', legend)

    # Guardar el diagrama
    output_path = Path(__file__).resolve().parent.parent / 'diagrama_er'
    dot.render(output_path, view=False, cleanup=True)

    print("=" * 80)
    print("✓ DIAGRAMA GENERADO EXITOSAMENTE")
    print("=" * 80)
    print(f"\nArchivo generado: {output_path}.png")
    print("\nResumen de la base de datos:")
    print("-" * 40)
    for table_name, info in table_info.items():
        print(f"  {table_name}: {len(info['columns'])} columnas")
    print(f"\n  Total de relaciones: {len(relationships)}")
    print("\n" + "=" * 80)

except ImportError:
    print("ERROR: graphviz no está instalado")
    print("\nPara instalar graphviz:")
    print("  1. Instala Homebrew si no lo tienes: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
    print("  2. Instala graphviz: brew install graphviz")
    print("  3. Instala el paquete Python: pip install graphviz")
    print("\nAlternativamente, aquí está la información en texto:")
    print("\n" + "=" * 80)
    for table_name, info in table_info.items():
        print(f"\n{table_name}")
        print("-" * 40)
        for col_name, data_type, data_length, nullable, is_pk, is_fk in info['columns']:
            constraints = []
            if is_pk:
                constraints.append('PK')
            if is_fk:
                constraints.append('FK')
            if nullable == 'N' and not is_pk:
                constraints.append('NOT NULL')

            constraint_str = f" [{', '.join(constraints)}]" if constraints else ''
            print(f"  - {col_name}: {data_type}{constraint_str}")

        if info['foreign_keys']:
            print("\n  Foreign Keys:")
            for fk_name, col_name, ref_table, ref_column in info['foreign_keys']:
                print(f"    {col_name} -> {ref_table}.{ref_column}")
    print("\n" + "=" * 80)
