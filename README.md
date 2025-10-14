# Sistema de Gestión de Biblioteca - Oracle Database

Sistema completo de gestión de biblioteca con backend Flask, Oracle Database y frontend web.

## Características

- Autenticación segura con JWT
- Hash de contraseñas con bcrypt
- Control de acceso basado en roles (Bibliotecario/Lector)
- CRUD completo de libros
- Gestión de préstamos con triggers automáticos
- Dashboard con estadísticas
- API REST documentada

## Tecnologías

- **Backend**: Flask (Python 3.13)
- **Base de Datos**: Oracle Database Express Edition
- **Frontend**: HTML, CSS, JavaScript (Vanilla), Bootstrap 5
- **Seguridad**: JWT, bcrypt

## Requisitos Previos

- Python 3.8+
- Oracle Database Express Edition 21c
- pip (gestor de paquetes Python)

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd biblioteca-oracle
```

### 2. Configurar la Base de Datos

Ejecutar los scripts SQL en orden:

```bash
cd database
sqlplus sys/password@//localhost:1521/XE as sysdba @00_cleanup.sql
sqlplus sys/password@//localhost:1521/XE as sysdba @01_setup.sql
sqlplus biblioteca_user/BiblioPass123@//localhost:1521/XEPDB1 @02_tables.sql
sqlplus biblioteca_user/BiblioPass123@//localhost:1521/XEPDB1 @03_triggers.sql
sqlplus biblioteca_user/BiblioPass123@//localhost:1521/XEPDB1 @04_data.sql
sqlplus biblioteca_user/BiblioPass123@//localhost:1521/XEPDB1 @07_indices_adicionales.sql
```

### 3. Configurar el Backend

```bash
cd backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Editar el archivo `.env` en la raíz del proyecto:

```env
# Base de datos
DB_USER=biblioteca_user
DB_PASSWORD=BiblioPass123
DB_HOST=localhost
DB_PORT=1521
DB_SERVICE=XEPDB1

# Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=cambiar_en_produccion_a_clave_segura

# CORS (dominios permitidos, separados por comas)
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

### 5. Actualizar contraseñas de usuarios existentes

Después de instalar, las contraseñas de prueba deben ser actualizadas con hash. Ejecutar el script Python:

```bash
cd backend
python init_data.py
```

## Ejecución

### Iniciar el Backend

```bash
cd backend
source venv/bin/activate  # En Windows: venv\Scripts\activate
python app.py
```

El backend estará disponible en `http://localhost:5000`

### Iniciar el Frontend

Opción 1: Usar un servidor HTTP simple con Python:

```bash
cd frontend
python3 -m http.server 5500
```

Opción 2: Usar Live Server de VSCode o cualquier otro servidor web.

El frontend estará disponible en `http://localhost:5500`

## Usuarios de Prueba

Después de ejecutar `init_data.py`:

- **Administrador**:
  - Email: admin@biblioteca.com
  - Contraseña: admin123
  - Rol: BIBLIOTECARIO

- **Lector**:
  - Email: juan@email.com
  - Contraseña: lector123
  - Rol: LECTOR

## Endpoints de la API

### Autenticación

- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/register` - Registrar usuario

### Libros (requiere autenticación)

- `GET /api/libros/` - Listar todos los libros
- `GET /api/libros/<id>` - Obtener libro por ID
- `GET /api/libros/search?titulo=&autor=&genero=` - Buscar libros
- `GET /api/libros/bajo-stock` - Libros con bajo stock
- `POST /api/libros/` - Crear libro (solo bibliotecarios)
- `PUT /api/libros/<id>` - Actualizar libro (solo bibliotecarios)
- `DELETE /api/libros/<id>` - Eliminar libro (solo bibliotecarios)

### Préstamos (requiere autenticación)

- `GET /api/prestamos/` - Listar todos los préstamos
- `GET /api/prestamos/activos` - Préstamos activos
- `GET /api/prestamos/vencidos` - Préstamos vencidos
- `GET /api/prestamos/usuario/<id>` - Préstamos de un usuario
- `POST /api/prestamos/` - Crear préstamo (solo bibliotecarios)
- `PUT /api/prestamos/<id>/devolver` - Registrar devolución (solo bibliotecarios)

### Usuarios (requiere autenticación)

- `GET /api/usuarios/` - Listar usuarios
- `GET /api/usuarios/<id>` - Obtener usuario por ID

## Estructura del Proyecto

```
biblioteca-oracle/
├── backend/
│   ├── config/
│   │   └── database.py        # Configuración de conexión Oracle
│   ├── routes/
│   │   ├── auth.py            # Autenticación
│   │   ├── libros.py          # Gestión de libros
│   │   ├── prestamos.py       # Gestión de préstamos
│   │   └── usuarios.py        # Gestión de usuarios
│   ├── utils/
│   │   └── security.py        # JWT, bcrypt, decoradores
│   ├── app.py                 # Aplicación principal
│   ├── init_data.py           # Script para actualizar contraseñas
│   └── requirements.txt       # Dependencias
├── database/
│   ├── 00_cleanup.sql         # Limpieza
│   ├── 01_setup.sql           # Configuración inicial
│   ├── 02_tables.sql          # Creación de tablas
│   ├── 03_triggers.sql        # Triggers
│   ├── 04_data.sql            # Datos de prueba
│   └── 07_indices_adicionales.sql  # Índices adicionales
├── frontend/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── api.js             # Cliente API centralizado
│   ├── pages/
│   │   ├── dashboard.html     # Dashboard
│   │   ├── libros.html        # Gestión de libros
│   │   └── prestamos.html     # Gestión de préstamos
│   └── index.html             # Login/Registro
├── .env                       # Variables de entorno
├── .gitignore                 # Archivos ignorados
└── README.md                  # Esta documentación
```

## Seguridad

### Implementaciones de Seguridad

1. **Contraseñas hasheadas**: Todas las contraseñas se almacenan con bcrypt
2. **JWT**: Autenticación basada en tokens con expiración de 24 horas
3. **Control de acceso basado en roles**: Decoradores para proteger endpoints
4. **CORS restringido**: Solo dominios configurados pueden acceder
5. **Validación de entrada**: Validación de datos en backend
6. **Logging**: Registro de eventos importantes

### Recomendaciones para Producción

1. Cambiar `SECRET_KEY` en `.env` a un valor aleatorio y seguro
2. Configurar `ALLOWED_ORIGINS` con el dominio de producción
3. Desactivar `FLASK_DEBUG=False`
4. Usar HTTPS en producción
5. Configurar firewall para la base de datos
6. Implementar rate limiting
7. Agregar validación de email
8. Implementar recuperación de contraseñas

## Troubleshooting

### Error de conexión a Oracle

```
ORA-12541: TNS:no listener
```

**Solución**: Verificar que Oracle esté corriendo:

```bash
lsnrctl status
```

### Error de módulo bcrypt

```
ModuleNotFoundError: No module named 'bcrypt'
```

**Solución**: Instalar dependencias:

```bash
pip install -r requirements.txt
```

### Error de CORS

```
Access-Control-Allow-Origin error
```

**Solución**: Agregar el origen del frontend en `.env`:

```env
ALLOWED_ORIGINS=http://localhost:5500
```

## Licencia

Este proyecto es de código abierto para fines educativos.

## Contacto

Para problemas o sugerencias, crear un issue en el repositorio.
