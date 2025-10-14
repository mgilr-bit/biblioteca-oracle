# Registro de Cambios - Sistema de Biblioteca

## [2.0.0] - Mejoras de Seguridad y Funcionalidad

### Seguridad - CRÍTICO

#### Autenticación y Contraseñas
- ✅ **Hash de contraseñas con bcrypt**: Todas las contraseñas ahora se almacenan hasheadas
- ✅ **Autenticación JWT**: Sistema de tokens con expiración de 24 horas
- ✅ **Validación de contraseñas**: Mínimo 6 caracteres requeridos

#### Control de Acceso
- ✅ **Decoradores de autenticación**: `@token_required` para rutas protegidas
- ✅ **Control de roles**: `@role_required(['BIBLIOTECARIO'])` para acciones administrativas
- ✅ **Middleware de seguridad**: Validación automática de tokens en requests

#### Seguridad de Red
- ✅ **CORS restringido**: Solo dominios configurados pueden acceder a la API
- ✅ **Headers de seguridad**: Authorization header para tokens JWT

#### Protección de Datos
- ✅ **.gitignore creado**: Archivos sensibles excluidos del control de versiones
- ✅ **Variables de entorno actualizadas**: Nuevas configuraciones de seguridad

### Funcionalidad

#### Backend
- ✅ **Logging implementado**: Sistema de logs rotativos para auditoría
- ✅ **Manejo de errores mejorado**: Logs informativos de eventos de seguridad
- ✅ **Validación de entrada**: Validación de roles y longitud de contraseñas
- ✅ **Módulo de seguridad**: `utils/security.py` con funciones reutilizables

#### Frontend
- ✅ **Cliente API centralizado**: `js/api.js` con todas las funciones de API
- ✅ **Gestión de tokens**: Almacenamiento y envío automático de JWT
- ✅ **Manejo de sesión expirada**: Redirección automática al login
- ✅ **Utilidades de autenticación**: Funciones helper para verificar roles

#### Base de Datos
- ✅ **Índice en email**: Mejora el rendimiento de login
- ✅ **Índices compuestos**: Optimización de consultas de préstamos
- ✅ **Script de actualización**: `07_indices_adicionales.sql`

### Archivos Nuevos

```
backend/
├── utils/security.py          # Módulo de seguridad (JWT, bcrypt, decoradores)
├── requirements.txt           # Dependencias con bcrypt y PyJWT
└── logs/                      # Directorio de logs (auto-creado)

database/
└── 07_indices_adicionales.sql # Índices para optimización

frontend/
└── js/api.js                  # Cliente API completo

/
├── .gitignore                 # Protección de archivos sensibles
├── README.md                  # Documentación completa
└── CHANGELOG.md               # Este archivo
```

### Archivos Modificados

```
backend/
├── app.py                     # Logging, CORS configurado
├── init_data.py               # Hash de contraseñas en datos iniciales
└── routes/
    ├── auth.py                # JWT, bcrypt, validación mejorada
    ├── libros.py              # Protección con decoradores
    └── prestamos.py           # Control de acceso por rol

frontend/
├── index.html                 # Usa API centralizada y JWT
└── .env                       # Nuevas variables de configuración
```

### Endpoints Protegidos

#### Autenticación Requerida (token JWT)
- Todos los endpoints de `/api/libros/*`
- Todos los endpoints de `/api/prestamos/*`
- Todos los endpoints de `/api/usuarios/*`

#### Solo Bibliotecarios
- `POST /api/libros/` - Crear libro
- `PUT /api/libros/<id>` - Actualizar libro
- `DELETE /api/libros/<id>` - Eliminar libro
- `POST /api/prestamos/` - Crear préstamo
- `PUT /api/prestamos/<id>/devolver` - Registrar devolución

### Instrucciones de Actualización

#### 1. Instalar nuevas dependencias

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Aplicar índices adicionales

```bash
sqlplus biblioteca_user/BiblioPass123@//localhost:1521/XEPDB1 @database/07_indices_adicionales.sql
```

#### 3. Actualizar contraseñas existentes

```bash
cd backend
python init_data.py
```

#### 4. Actualizar configuración

Verificar que el archivo `.env` incluya las nuevas variables:
```env
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
PORT=5000
```

#### 5. Reiniciar el servidor

```bash
python app.py
```

### Notas de Migración

#### Usuarios Existentes
- **IMPORTANTE**: Todas las contraseñas antiguas deben ser actualizadas
- Ejecutar `python init_data.py` para rehashear contraseñas de prueba
- Los usuarios en producción deberán usar recuperación de contraseña (pendiente)

#### Frontend
- El localStorage ahora incluye el campo `token`
- Las sesiones expiran después de 24 horas
- Los usuarios serán redirigidos al login automáticamente

#### API
- Todos los requests (excepto login/register) requieren header `Authorization: Bearer <token>`
- Respuestas 401 indican token expirado o inválido
- Respuestas 403 indican falta de permisos (rol incorrecto)

### Mejoras Futuras Sugeridas

#### Alta Prioridad
- [ ] Recuperación de contraseña por email
- [ ] Refresh tokens para sesiones largas
- [ ] Rate limiting para prevenir ataques de fuerza bruta
- [ ] Validación de email con regex

#### Media Prioridad
- [ ] Paginación en listados
- [ ] Búsqueda avanzada con filtros múltiples
- [ ] Exportación de reportes (PDF, Excel)
- [ ] Sistema de notificaciones para préstamos vencidos

#### Baja Prioridad
- [ ] Tests unitarios y de integración
- [ ] Documentación API con Swagger
- [ ] Contenedorización con Docker
- [ ] CI/CD pipeline

### Breaking Changes

⚠️ **ATENCIÓN**: Esta versión introduce cambios incompatibles:

1. **Formato de respuesta de login**: Ahora incluye campo `token`
2. **Headers requeridos**: Todos los endpoints protegidos requieren `Authorization`
3. **Contraseñas**: Las contraseñas antiguas en texto plano no funcionarán
4. **CORS**: Dominios no configurados serán rechazados

### Dependencias Nuevas

```
bcrypt==4.2.1        # Hash de contraseñas
PyJWT==2.10.1        # JSON Web Tokens
```

### Compatibilidad

- Python: 3.8+
- Oracle Database: 11g+
- Navegadores: Chrome 90+, Firefox 88+, Safari 14+

### Créditos

Mejoras de seguridad implementadas siguiendo OWASP Top 10 y mejores prácticas de desarrollo seguro.

---

## [1.0.0] - Versión Inicial

### Características
- CRUD básico de libros, usuarios y préstamos
- Interfaz web con Bootstrap 5
- Base de datos Oracle con triggers
- Autenticación básica (sin hash, sin JWT)
