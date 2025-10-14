"""
Script simplificado para generar el Diagrama ER desde dentro del contenedor Docker
"""
import oracledb

# Conectar directamente
connection = oracledb.connect(
    user='BIBLIOTECA_USER',
    password='BiblioPass123',
    dsn='localhost:1521/XEPDB1'
)

print("✓ Conectado a la base de datos\n")
cursor = connection.cursor()

# Obtener información de las tablas
tables_query = "SELECT table_name FROM user_tables WHERE table_name IN ('LIBROS', 'USUARIOS', 'PRESTAMOS') ORDER BY table_name"
cursor.execute(tables_query)
tables = [row[0] for row in cursor.fetchall()]

print("Tablas encontradas:", tables)
print("\n" + "="*80)

for table_name in tables:
    print(f"\nTabla: {table_name}")
    print("-" * 40)

    # Obtener columnas
    cursor.execute(f"""
        SELECT column_name, data_type, data_length, nullable
        FROM user_tab_columns
        WHERE table_name = '{table_name}'
        ORDER BY column_id
    """)

    columns = cursor.fetchall()
    for col_name, data_type, data_length, nullable in columns:
        null_str = "NULL" if nullable == 'Y' else "NOT NULL"
        if data_type in ('VARCHAR2', 'CHAR'):
            print(f"  {col_name}: {data_type}({data_length}) {null_str}")
        else:
            print(f"  {col_name}: {data_type} {null_str}")

    # Obtener PKs
    cursor.execute(f"""
        SELECT ucc.column_name
        FROM user_constraints uc
        JOIN user_cons_columns ucc ON uc.constraint_name = ucc.constraint_name
        WHERE uc.constraint_type = 'P' AND uc.table_name = '{table_name}'
    """)
    pks = [row[0] for row in cursor.fetchall()]
    if pks:
        print(f"\n  PRIMARY KEY: {', '.join(pks)}")

    # Obtener FKs
    cursor.execute(f"""
        SELECT
            ucc.column_name,
            uc2.table_name as ref_table,
            ucc2.column_name as ref_column
        FROM user_constraints uc
        JOIN user_cons_columns ucc ON uc.constraint_name = ucc.constraint_name
        JOIN user_constraints uc2 ON uc.r_constraint_name = uc2.constraint_name
        JOIN user_cons_columns ucc2 ON uc2.constraint_name = ucc2.constraint_name
        WHERE uc.constraint_type = 'R' AND uc.table_name = '{table_name}'
    """)
    fks = cursor.fetchall()
    if fks:
        print(f"\n  FOREIGN KEYS:")
        for col_name, ref_table, ref_column in fks:
            print(f"    {col_name} → {ref_table}.{ref_column}")

cursor.close()
connection.close()

print("\n" + "="*80)
print("\nDiagrama ER (Texto):")
print("""
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│    USUARIOS     │         │    PRESTAMOS     │         │     LIBROS      │
├─────────────────┤         ├──────────────────┤         ├─────────────────┤
│ ID_USUARIO (PK) │◄────────┤ ID_PRESTAMO (PK) │         │ ID_LIBRO (PK)   │
│ NOMBRE          │         │ ID_USUARIO (FK)  │────────►│ TITULO          │
│ EMAIL           │         │ ID_LIBRO (FK)    │         │ AUTOR           │
│ PASSWORD        │         │ FECHA_PRESTAMO   │         │ ISBN            │
│ ROL             │         │ FECHA_DEV_ESP    │         │ ANIO_PUBLIC     │
│ ACTIVO          │         │ FECHA_DEV_REAL   │         │ GENERO          │
│ FECHA_REGISTRO  │         │ ESTADO           │         │ EDITORIAL       │
└─────────────────┘         └──────────────────┘         │ NUMERO_COPIAS   │
                                                          │ COPIAS_DISPONIB │
        1                           N                     │ FECHA_REGISTRO  │
        │                           │                     └─────────────────┘
        │                           │                              1
        └───────────────────────────┘                              │
                                                                   │
                                                                   N
""")
print("="*80)
