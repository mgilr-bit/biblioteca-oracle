# Guía de Seguridad - Sistema de Biblioteca

## Descripción General

Este documento describe las medidas de seguridad implementadas en el sistema de gestión de biblioteca.

## Implementaciones de Seguridad

### 1. Autenticación

#### Hash de Contraseñas (bcrypt)
- **Implementación**: Todas las contraseñas se hashean usando bcrypt con salt automático
- **Ubicación**: `backend/utils/security.py`
- **Funciones**:
  - `hash_password(password)`: Genera hash bcrypt
  - `verify_password(password, hashed_password)`: Verifica contraseña

```python
# Ejemplo de uso
from utils.security import hash_password, verify_password

# Al registrar
hashed = hash_password("mi_contraseña")

# Al validar
is_valid = verify_password("mi_contraseña", hashed)
```

#### JSON Web Tokens (JWT)
- **Expiración**: 24 horas desde la emisión
- **Algoritmo**: HS256
- **Payload**: user_id, email, rol, exp, iat
- **Ubicación**: `backend/utils/security.py`

```python
# Generar token
token = generate_token(user_id, email, rol)

# Decodificar token
payload = decode_token(token)
```

### 2. Control de Acceso

#### Decorador @token_required
Protege endpoints que requieren autenticación:

```python
@libros_bp.route('/', methods=['GET'])
@token_required
def get_libros():
    # request.user contiene el payload del token
    user_email = request.user['email']
    user_role = request.user['rol']
    ...
```

#### Decorador @role_required
Restringe acceso a roles específicos:

```python
@libros_bp.route('/', methods=['POST'])
@token_required
@role_required(['BIBLIOTECARIO'])
def create_libro():
    # Solo usuarios con rol BIBLIOTECARIO pueden acceder
    ...
```

### 3. Seguridad de Red

#### CORS Configurado
- **No permite todos los orígenes** (eliminado `"origins": "*"`)
- **Lista blanca configurable** vía variable de entorno
- **Headers permitidos**: Content-Type, Authorization
- **Métodos permitidos**: GET, POST, PUT, DELETE, PATCH

```python
# En app.py
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '...').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### 4. Logging y Auditoría

#### Sistema de Logs
- **Ubicación**: `backend/logs/biblioteca.log`
- **Rotación**: 10MB por archivo, 10 backups
- **Nivel**: INFO en producción, DEBUG en desarrollo

#### Eventos Registrados
- Login exitoso/fallido
- Intentos de login con email no existente
- Intentos de login con contraseña incorrecta
- Registros de nuevos usuarios
- Errores de autenticación
- Errores internos del servidor

```python
# Ejemplo de log
logger.info(f"Login exitoso para usuario: {email}")
logger.warning(f"Intento de login fallido para email: {email}")
logger.error(f"Error en login: {str(e)}")
```

### 5. Validación de Entrada

#### Backend
- Validación de campos requeridos
- Longitud mínima de contraseña (6 caracteres)
- Validación de roles permitidos (LECTOR, BIBLIOTECARIO)
- Verificación de email único
- Parámetros SQL parametrizados (previene SQL injection)

```python
# Ejemplo
if len(password) < 6:
    return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

if rol not in ['LECTOR', 'BIBLIOTECARIO']:
    return jsonify({"error": "Rol inválido"}), 400
```

#### Frontend
- Validación HTML5 (required, type="email", etc.)
- Manejo automático de tokens expirados
- Redirección a login si no hay token válido

### 6. Protección de Archivos Sensibles

#### .gitignore
Archivos excluidos del control de versiones:
- `.env` (credenciales)
- `__pycache__/` (cache Python)
- `logs/` (logs del sistema)
- `venv/` (entorno virtual)
- `oracle-data/` (datos Oracle)
- `.DS_Store` (archivos macOS)

#### .env.example
Plantilla para configuración sin datos sensibles

## Matriz de Permisos

| Endpoint | Público | LECTOR | BIBLIOTECARIO |
|----------|---------|--------|---------------|
| POST /api/auth/login | ✅ | ✅ | ✅ |
| POST /api/auth/register | ✅ | ✅ | ✅ |
| GET /api/libros/ | ❌ | ✅ | ✅ |
| GET /api/libros/<id> | ❌ | ✅ | ✅ |
| GET /api/libros/search | ❌ | ✅ | ✅ |
| POST /api/libros/ | ❌ | ❌ | ✅ |
| PUT /api/libros/<id> | ❌ | ❌ | ✅ |
| DELETE /api/libros/<id> | ❌ | ❌ | ✅ |
| GET /api/prestamos/ | ❌ | ✅ | ✅ |
| POST /api/prestamos/ | ❌ | ❌ | ✅ |
| PUT /api/prestamos/<id>/devolver | ❌ | ❌ | ✅ |

## Flujo de Autenticación

```
1. Usuario envía credentials
   POST /api/auth/login
   { "email": "...", "password": "..." }
   
2. Backend valida
   - Busca usuario por email
   - Verifica hash con bcrypt
   
3. Si válido, genera JWT
   token = generate_token(user_id, email, rol)
   
4. Frontend almacena token
   localStorage.setItem('user', JSON.stringify({
     ...user_data,
     token: token
   }))
   
5. Requests subsecuentes incluyen token
   Authorization: Bearer <token>
   
6. Backend valida token en cada request
   @token_required verifica y decodifica
   
7. Si token expirado (401)
   Frontend redirige a login
```

## Configuración de Seguridad

### Variables de Entorno Críticas

```env
# Clave para firmar JWT (DEBE ser aleatoria y secreta)
SECRET_KEY=valor_aleatorio_largo_y_seguro

# Lista blanca de dominios
ALLOWED_ORIGINS=https://tu-dominio.com

# En producción
FLASK_ENV=production
FLASK_DEBUG=False
```

### Generación de SECRET_KEY Segura

```bash
# Opción 1: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Opción 2: OpenSSL
openssl rand -hex 32
```

## Checklist de Seguridad para Producción

### Antes de Desplegar

- [ ] Cambiar `SECRET_KEY` a valor aleatorio
- [ ] Configurar `ALLOWED_ORIGINS` con dominio real
- [ ] Establecer `FLASK_DEBUG=False`
- [ ] Usar HTTPS (certificado SSL/TLS)
- [ ] Configurar firewall de base de datos
- [ ] Cambiar contraseña de base de datos
- [ ] Revisar permisos de archivos en servidor
- [ ] Configurar backups automáticos
- [ ] Implementar rate limiting
- [ ] Configurar monitoreo de logs
- [ ] Validar que .env no esté en repositorio
- [ ] Habilitar HTTPS Strict Transport Security
- [ ] Implementar Content Security Policy

### Monitoreo Continuo

- [ ] Revisar logs regularmente
- [ ] Monitorear intentos de login fallidos
- [ ] Actualizar dependencias (vulnerabilidades)
- [ ] Auditorías de seguridad periódicas
- [ ] Backups verificados

## Vulnerabilidades Conocidas Pendientes

### Alta Prioridad
1. **No hay rate limiting**: Vulnerable a ataques de fuerza bruta
2. **No hay recuperación de contraseña**: Usuarios bloqueados sin opción
3. **No hay 2FA**: Solo una capa de autenticación
4. **Session management básico**: No hay invalidación activa de tokens

### Media Prioridad
1. **No hay validación de email**: Emails falsos aceptados
2. **Logs en disco local**: Podrían llenarse/perderse
3. **No hay cifrado de datos sensibles en BD**: Solo contraseñas hasheadas
4. **CSRF no implementado**: Aunque API REST con JWT mitiga

## Reportar Vulnerabilidades

Si encuentras una vulnerabilidad de seguridad:

1. **NO** la publiques públicamente
2. Envía un email privado al equipo
3. Incluye:
   - Descripción del problema
   - Pasos para reproducir
   - Impacto potencial
   - Sugerencias de solución (opcional)

## Referencias

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [bcrypt](https://github.com/pyca/bcrypt/)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)

## Última Actualización

Documento actualizado: 2025-01-12
Versión del sistema: 2.0.0
