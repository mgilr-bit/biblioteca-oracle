-- 02_tables.sql
CREATE TABLE usuarios (
    id_usuario NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR2(100) NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    password VARCHAR2(255) NOT NULL,
    rol VARCHAR2(20) DEFAULT 'LECTOR' CHECK (rol IN ('BIBLIOTECARIO', 'LECTOR')),
    fecha_registro DATE DEFAULT SYSDATE,
    activo CHAR(1) DEFAULT 'S' CHECK (activo IN ('S', 'N'))
) TABLESPACE PROYECTO_BD;

CREATE TABLE libros (
    id_libro NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titulo VARCHAR2(200) NOT NULL,
    autor VARCHAR2(150) NOT NULL,
    isbn VARCHAR2(20) UNIQUE,
    anio_publicacion NUMBER CHECK (anio_publicacion > 1900 AND anio_publicacion <= 2030),
    genero VARCHAR2(50),
    numero_copias NUMBER DEFAULT 1 CHECK (numero_copias >= 0),
    copias_disponibles NUMBER DEFAULT 1 CHECK (copias_disponibles >= 0),
    fecha_registro DATE DEFAULT SYSDATE,
    editorial VARCHAR2(100)
) TABLESPACE PROYECTO_BD;

CREATE TABLE prestamos (
    id_prestamo NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_libro NUMBER NOT NULL,
    id_usuario NUMBER NOT NULL,
    fecha_prestamo DATE DEFAULT SYSDATE,
    fecha_devolucion_esperada DATE NOT NULL,
    fecha_devolucion_real DATE,
    estado VARCHAR2(20) DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'DEVUELTO', 'VENCIDO')),
    CONSTRAINT fk_prestamo_libro FOREIGN KEY (id_libro) REFERENCES libros(id_libro) ON DELETE CASCADE,
    CONSTRAINT fk_prestamo_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT chk_fecha_devolucion CHECK (fecha_devolucion_esperada > fecha_prestamo)
) TABLESPACE PROYECTO_BD;

CREATE INDEX idx_libros_titulo ON libros(titulo);
CREATE INDEX idx_libros_autor ON libros(autor);
CREATE INDEX idx_libros_genero ON libros(genero);
CREATE INDEX idx_prestamos_usuario ON prestamos(id_usuario);
CREATE INDEX idx_prestamos_estado ON prestamos(estado);
CREATE INDEX idx_prestamos_libro ON prestamos(id_libro);

COMMIT;
EXIT;
