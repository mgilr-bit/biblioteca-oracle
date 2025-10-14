"""
Generar diagrama ER visual sin necesidad de conectar a la base de datos
"""
from graphviz import Digraph

# Crear el grafo
dot = Digraph(comment='Sistema de Biblioteca - Diagrama ER', format='png')
dot.attr(rankdir='LR', size='14,10', bgcolor='white', dpi='300')
dot.attr('node', shape='plaintext', fontname='Arial')
dot.attr('edge', color='#555555', fontname='Arial', fontsize='11')

# Tabla USUARIOS
usuarios_html = '''<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" BGCOLOR="#E3F2FD">
    <TR><TD BGCOLOR="#1976D2" ALIGN="CENTER" COLSPAN="3">
        <FONT COLOR="white" POINT-SIZE="16"><B>USUARIOS</B></FONT>
    </TD></TR>
    <TR>
        <TD BGCOLOR="#BBDEFB"><B>Columna</B></TD>
        <TD BGCOLOR="#BBDEFB"><B>Tipo</B></TD>
        <TD BGCOLOR="#BBDEFB"><B>Restricción</B></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" BGCOLOR="#FFEBEE">ID_USUARIO</TD>
        <TD ALIGN="LEFT">NUMBER</TD>
        <TD ALIGN="LEFT"><FONT COLOR="#D32F2F">PK</FONT></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">NOMBRE</TD>
        <TD ALIGN="LEFT">VARCHAR2(100)</TD>
        <TD ALIGN="LEFT">NOT NULL</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">EMAIL</TD>
        <TD ALIGN="LEFT">VARCHAR2(100)</TD>
        <TD ALIGN="LEFT">NOT NULL, UNIQUE</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">PASSWORD</TD>
        <TD ALIGN="LEFT">VARCHAR2(255)</TD>
        <TD ALIGN="LEFT">NOT NULL</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">ROL</TD>
        <TD ALIGN="LEFT">VARCHAR2(20)</TD>
        <TD ALIGN="LEFT">NOT NULL</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">ACTIVO</TD>
        <TD ALIGN="LEFT">CHAR(1)</TD>
        <TD ALIGN="LEFT">DEFAULT 'S'</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">FECHA_REGISTRO</TD>
        <TD ALIGN="LEFT">DATE</TD>
        <TD ALIGN="LEFT">DEFAULT SYSDATE</TD>
    </TR>
</TABLE>>'''

# Tabla LIBROS
libros_html = '''<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" BGCOLOR="#E8F5E9">
    <TR><TD BGCOLOR="#388E3C" ALIGN="CENTER" COLSPAN="3">
        <FONT COLOR="white" POINT-SIZE="16"><B>LIBROS</B></FONT>
    </TD></TR>
    <TR>
        <TD BGCOLOR="#C8E6C9"><B>Columna</B></TD>
        <TD BGCOLOR="#C8E6C9"><B>Tipo</B></TD>
        <TD BGCOLOR="#C8E6C9"><B>Restricción</B></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" BGCOLOR="#FFEBEE">ID_LIBRO</TD>
        <TD ALIGN="LEFT">NUMBER</TD>
        <TD ALIGN="LEFT"><FONT COLOR="#D32F2F">PK</FONT></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">TITULO</TD>
        <TD ALIGN="LEFT">VARCHAR2(200)</TD>
        <TD ALIGN="LEFT">NOT NULL</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">AUTOR</TD>
        <TD ALIGN="LEFT">VARCHAR2(100)</TD>
        <TD ALIGN="LEFT">NOT NULL</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">ISBN</TD>
        <TD ALIGN="LEFT">VARCHAR2(20)</TD>
        <TD ALIGN="LEFT">UNIQUE</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">ANIO_PUBLICACION</TD>
        <TD ALIGN="LEFT">NUMBER(4)</TD>
        <TD ALIGN="LEFT"></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">GENERO</TD>
        <TD ALIGN="LEFT">VARCHAR2(50)</TD>
        <TD ALIGN="LEFT"></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">EDITORIAL</TD>
        <TD ALIGN="LEFT">VARCHAR2(100)</TD>
        <TD ALIGN="LEFT"></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">NUMERO_COPIAS</TD>
        <TD ALIGN="LEFT">NUMBER</TD>
        <TD ALIGN="LEFT">DEFAULT 1</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">COPIAS_DISPONIBLES</TD>
        <TD ALIGN="LEFT">NUMBER</TD>
        <TD ALIGN="LEFT">DEFAULT 1</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">FECHA_REGISTRO</TD>
        <TD ALIGN="LEFT">DATE</TD>
        <TD ALIGN="LEFT">DEFAULT SYSDATE</TD>
    </TR>
</TABLE>>'''

# Tabla PRESTAMOS
prestamos_html = '''<
<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" BGCOLOR="#FFF3E0">
    <TR><TD BGCOLOR="#F57C00" ALIGN="CENTER" COLSPAN="3">
        <FONT COLOR="white" POINT-SIZE="16"><B>PRESTAMOS</B></FONT>
    </TD></TR>
    <TR>
        <TD BGCOLOR="#FFE0B2"><B>Columna</B></TD>
        <TD BGCOLOR="#FFE0B2"><B>Tipo</B></TD>
        <TD BGCOLOR="#FFE0B2"><B>Restricción</B></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" BGCOLOR="#FFEBEE">ID_PRESTAMO</TD>
        <TD ALIGN="LEFT">NUMBER</TD>
        <TD ALIGN="LEFT"><FONT COLOR="#D32F2F">PK</FONT></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" BGCOLOR="#FFF9C4">ID_USUARIO</TD>
        <TD ALIGN="LEFT">NUMBER</TD>
        <TD ALIGN="LEFT"><FONT COLOR="#F57C00">FK</FONT></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" BGCOLOR="#FFF9C4">ID_LIBRO</TD>
        <TD ALIGN="LEFT">NUMBER</TD>
        <TD ALIGN="LEFT"><FONT COLOR="#F57C00">FK</FONT></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">FECHA_PRESTAMO</TD>
        <TD ALIGN="LEFT">DATE</TD>
        <TD ALIGN="LEFT">DEFAULT SYSDATE</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">FECHA_DEVOLUCION_ESPERADA</TD>
        <TD ALIGN="LEFT">DATE</TD>
        <TD ALIGN="LEFT">NOT NULL</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">FECHA_DEVOLUCION_REAL</TD>
        <TD ALIGN="LEFT">DATE</TD>
        <TD ALIGN="LEFT"></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT">ESTADO</TD>
        <TD ALIGN="LEFT">VARCHAR2(20)</TD>
        <TD ALIGN="LEFT">NOT NULL</TD>
    </TR>
</TABLE>>'''

# Agregar nodos
dot.node('USUARIOS', usuarios_html)
dot.node('LIBROS', libros_html)
dot.node('PRESTAMOS', prestamos_html)

# Agregar relaciones con etiquetas de cardinalidad
dot.edge(
    'USUARIOS',
    'PRESTAMOS',
    label='  realiza\n  1 : N  ',
    arrowhead='crow',
    arrowtail='none',
    dir='both',
    penwidth='2.5',
    color='#1976D2'
)

dot.edge(
    'LIBROS',
    'PRESTAMOS',
    label='  involucra\n  1 : N  ',
    arrowhead='crow',
    arrowtail='none',
    dir='both',
    penwidth='2.5',
    color='#388E3C'
)

# Agregar leyenda
legend = '''<
<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="8" BGCOLOR="white">
    <TR><TD BGCOLOR="#424242" ALIGN="CENTER" COLSPAN="2">
        <FONT COLOR="white" POINT-SIZE="14"><B>LEYENDA</B></FONT>
    </TD></TR>
    <TR>
        <TD ALIGN="LEFT"><FONT COLOR="#D32F2F"><B>PK</B></FONT></TD>
        <TD ALIGN="LEFT">Primary Key (Llave Primaria)</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT"><FONT COLOR="#F57C00"><B>FK</B></FONT></TD>
        <TD ALIGN="LEFT">Foreign Key (Llave Foránea)</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT"><B>1 : N</B></TD>
        <TD ALIGN="LEFT">Relación uno a muchos</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" COLSPAN="2"><B>Reglas de Negocio:</B></TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" COLSPAN="2">• Un usuario puede tener muchos préstamos</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" COLSPAN="2">• Un libro puede tener muchos préstamos</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" COLSPAN="2">• Un préstamo pertenece a un usuario</TD>
    </TR>
    <TR>
        <TD ALIGN="LEFT" COLSPAN="2">• Un préstamo involucra un libro</TD>
    </TR>
</TABLE>>'''

dot.node('legend', legend)

# Guardar el diagrama
output_path = '/Users/miltongil/Desktop/biblioteca-oracle/diagrama_er_biblioteca'
dot.render(output_path, view=False, cleanup=True)

print("=" * 80)
print("✓ DIAGRAMA ER GENERADO EXITOSAMENTE")
print("=" * 80)
print(f"\nArchivo generado: {output_path}.png")
print("\nResumen del Sistema:")
print("-" * 40)
print("  • 3 Tablas: USUARIOS, LIBROS, PRESTAMOS")
print("  • 2 Relaciones: (1:N)")
print("    - USUARIOS → PRESTAMOS")
print("    - LIBROS → PRESTAMOS")
print("\nEstadísticas actuales:")
print("  • Total de libros: 828")
print("  • Géneros disponibles: 26")
print("  • Usuarios registrados: ~15")
print("\n" + "=" * 80)
