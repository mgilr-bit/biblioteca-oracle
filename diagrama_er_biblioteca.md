# Diagrama Entidad-Relación (ER) - Sistema de Biblioteca

## Modelo Conceptual

```
┌─────────────────────────────┐
│        USUARIOS             │
├─────────────────────────────┤
│ PK  ID_USUARIO    NUMBER    │
│     NOMBRE        VARCHAR2  │
│     EMAIL         VARCHAR2  │
│     PASSWORD      VARCHAR2  │
│     ROL           VARCHAR2  │
│     ACTIVO        CHAR(1)   │
│     FECHA_REGISTRO DATE     │
└──────────┬──────────────────┘
           │
           │ 1
           │
           │
           │ N
┌──────────┴──────────────────┐         ┌─────────────────────────────┐
│        PRESTAMOS            │         │         LIBROS              │
├─────────────────────────────┤         ├─────────────────────────────┤
│ PK  ID_PRESTAMO    NUMBER   │    N    │ PK  ID_LIBRO     NUMBER     │
│ FK  ID_USUARIO     NUMBER   ├─────────┤     TITULO       VARCHAR2   │
│ FK  ID_LIBRO       NUMBER   │    1    │     AUTOR        VARCHAR2   │
│     FECHA_PRESTAMO DATE     │         │     ISBN         VARCHAR2   │
│     FECHA_DEV_ESP  DATE     │         │     ANIO_PUBLIC  NUMBER     │
│     FECHA_DEV_REAL DATE     │         │     GENERO       VARCHAR2   │
│     ESTADO         VARCHAR2 │         │     EDITORIAL    VARCHAR2   │
└─────────────────────────────┘         │     NUMERO_COPIAS  NUMBER   │
                                        │     COPIAS_DISPONIBLES NUMBER│
                                        │     FECHA_REGISTRO DATE     │
                                        └─────────────────────────────┘
```

## Relaciones

### 1. USUARIOS → PRESTAMOS (1:N)
- Un usuario puede tener **muchos** préstamos
- Un préstamo pertenece a **un solo** usuario
- **Cardinalidad**: 1:N
- **Foreign Key**: `PRESTAMOS.ID_USUARIO` → `USUARIOS.ID_USUARIO`

### 2. LIBROS → PRESTAMOS (1:N)
- Un libro puede tener **muchos** préstamos
- Un préstamo está asociado a **un solo** libro
- **Cardinalidad**: 1:N
- **Foreign Key**: `PRESTAMOS.ID_LIBRO` → `LIBROS.ID_LIBRO`

## Descripción de Entidades

### USUARIOS
Almacena la información de los usuarios del sistema (lectores y bibliotecarios).

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| ID_USUARIO | NUMBER | PRIMARY KEY | Identificador único del usuario |
| NOMBRE | VARCHAR2(100) | NOT NULL | Nombre completo del usuario |
| EMAIL | VARCHAR2(100) | NOT NULL, UNIQUE | Correo electrónico (login) |
| PASSWORD | VARCHAR2(255) | NOT NULL | Contraseña hasheada con bcrypt |
| ROL | VARCHAR2(20) | NOT NULL | LECTOR o BIBLIOTECARIO |
| ACTIVO | CHAR(1) | DEFAULT 'S' | S = Activo, N = Inactivo |
| FECHA_REGISTRO | DATE | DEFAULT SYSDATE | Fecha de registro |

**Índices**:
- PRIMARY KEY en ID_USUARIO
- UNIQUE en EMAIL

---

### LIBROS
Almacena el catálogo de libros disponibles en la biblioteca.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| ID_LIBRO | NUMBER | PRIMARY KEY | Identificador único del libro |
| TITULO | VARCHAR2(200) | NOT NULL | Título del libro |
| AUTOR | VARCHAR2(100) | NOT NULL | Autor del libro |
| ISBN | VARCHAR2(20) | UNIQUE | ISBN del libro |
| ANIO_PUBLICACION | NUMBER(4) | | Año de publicación |
| GENERO | VARCHAR2(50) | | Género literario |
| EDITORIAL | VARCHAR2(100) | | Casa editorial |
| NUMERO_COPIAS | NUMBER | DEFAULT 1 | Total de copias físicas |
| COPIAS_DISPONIBLES | NUMBER | DEFAULT 1 | Copias actualmente disponibles |
| FECHA_REGISTRO | DATE | DEFAULT SYSDATE | Fecha de registro en el sistema |

**Índices**:
- PRIMARY KEY en ID_LIBRO
- UNIQUE en ISBN

**Lógica de negocio**:
- `COPIAS_DISPONIBLES` = `NUMERO_COPIAS` - (préstamos activos)
- Se actualiza automáticamente al crear/devolver préstamos

---

### PRESTAMOS
Registra todos los préstamos de libros a usuarios.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| ID_PRESTAMO | NUMBER | PRIMARY KEY | Identificador único del préstamo |
| ID_USUARIO | NUMBER | FOREIGN KEY | Usuario que realiza el préstamo |
| ID_LIBRO | NUMBER | FOREIGN KEY | Libro prestado |
| FECHA_PRESTAMO | DATE | DEFAULT SYSDATE | Fecha en que se realizó el préstamo |
| FECHA_DEVOLUCION_ESPERADA | DATE | NOT NULL | Fecha límite para devolver |
| FECHA_DEVOLUCION_REAL | DATE | | Fecha real de devolución |
| ESTADO | VARCHAR2(20) | NOT NULL | ACTIVO, DEVUELTO, o VENCIDO |

**Índices**:
- PRIMARY KEY en ID_PRESTAMO
- FOREIGN KEY en ID_USUARIO → USUARIOS(ID_USUARIO)
- FOREIGN KEY en ID_LIBRO → LIBROS(ID_LIBRO)

**Estados posibles**:
- **ACTIVO**: Préstamo vigente, dentro del plazo
- **VENCIDO**: Préstamo activo pero fuera del plazo
- **DEVUELTO**: Libro ya devuelto

---

## Reglas de Negocio

1. **Control de Stock**:
   - No se puede prestar un libro si `COPIAS_DISPONIBLES` = 0
   - Al prestar: `COPIAS_DISPONIBLES` -= 1
   - Al devolver: `COPIAS_DISPONIBLES` += 1

2. **Estados de Préstamo**:
   - Un préstamo se marca como VENCIDO automáticamente si `FECHA_DEVOLUCION_ESPERADA < SYSDATE`
   - Solo puede haber un préstamo ACTIVO por usuario por libro

3. **Roles de Usuario**:
   - **LECTOR**: Puede ver libros, ver sus propios préstamos
   - **BIBLIOTECARIO**: Acceso completo (CRUD libros, gestionar préstamos, administrar usuarios)

4. **Validaciones**:
   - Email debe ser único
   - ISBN debe ser único
   - No se puede eliminar un libro con préstamos activos
   - No se puede eliminar un usuario con préstamos activos

---

## Triggers y Automatizaciones

### 1. Generación de IDs (Secuencias)
```sql
CREATE SEQUENCE SEQ_USUARIOS START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_LIBROS START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE SEQ_PRESTAMOS START WITH 1 INCREMENT BY 1;
```

### 2. Control de Copias Disponibles
- Al insertar un préstamo: Disminuir `COPIAS_DISPONIBLES`
- Al devolver un préstamo: Aumentar `COPIAS_DISPONIBLES`

### 3. Actualización de Estado
- Job programado que verifica diariamente:
  - Si `FECHA_DEVOLUCION_ESPERADA < SYSDATE` y `ESTADO = 'ACTIVO'`
  - Entonces `ESTADO = 'VENCIDO'`

---

## Estadísticas Actuales del Sistema

- **Total de Libros**: 828
- **Total de Usuarios**: ~10-15
- **Géneros Disponibles**: 26
- **Préstamos Activos**: Variable

---

## Diagrama ER en Notación Chen

```
         ┌───────────┐
         │ USUARIOS  │
         └─────┬─────┘
               │
               │ 1
               │
         ┌─────┴─────┐
         │  Realiza  │  (Relación 1:N)
         └─────┬─────┘
               │ N
               │
         ┌─────┴────────┐
         │  PRESTAMOS   │
         └─────┬────────┘
               │ N
               │
         ┌─────┴─────┐
         │  Involucra│  (Relación 1:N)
         └─────┬─────┘
               │ 1
               │
         ┌─────┴─────┐
         │  LIBROS   │
         └───────────┘
```

---

## Diagrama ER en Notación Crow's Foot

```
USUARIOS ||────o{ PRESTAMOS }o────|| LIBROS
    1              N              N           1
```

**Leyenda**:
- `||` = Uno y solo uno
- `o{` = Cero o muchos
- `}o` = Cero o muchos

---

_Generado automáticamente para el Sistema de Biblioteca - Oracle Database_
_Fecha: Octubre 2025_
