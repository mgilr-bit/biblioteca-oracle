"""Mensajes de error centralizados (mirror de VALIDATION_ERRORS en wallet-api).

Un único lugar para el texto de cada error de negocio/autorización: evita
strings repetidos e inconsistentes desperdigados por services, routers y
dependencies, y es el punto donde traducir o auditar lo que ve el cliente.
"""


class AuthMessages:
    CREDENCIALES_INVALIDAS = "Credenciales inválidas"
    TOKEN_REQUERIDO = "Token requerido"
    SESION_EXPIRADA = "Sesión expirada"
    SESION_REVOCADA = "Sesión revocada"
    DEMASIADOS_INTENTOS = "Demasiados intentos fallidos, intente de nuevo más tarde"
    SIN_PERMISOS = "No tiene permisos para realizar esta acción"
    CSRF_INVALIDO = "CSRF token inválido"
    NO_ENCONTRADO = "No encontrado"
    EMAIL_PASSWORD_REQUERIDOS = "Email y contraseña son requeridos"


class UsuarioMessages:
    NOT_FOUND = "Usuario no encontrado"
    REGISTRO_CAMPOS_REQUERIDOS = "Nombre, email y contraseña son requeridos"
    ADMIN_CAMPOS_REQUERIDOS = "Nombre, email, contraseña y rol son requeridos"
    UPDATE_CAMPOS_REQUERIDOS = "Nombre, email y rol son requeridos"
    EMAIL_DUPLICADO = "El email ya está registrado"
    ROL_INVALIDO = "Rol inválido. Debe ser LECTOR, PROFESOR, BIBLIOTECARIO o ADMIN"
    PASSWORD_MUY_CORTA = "La contraseña debe tener al menos 8 caracteres"
    PASSWORD_MUY_LARGA = "La contraseña no puede superar los 72 caracteres"
    ESTADO_INVALIDO = "Estado inválido. Debe ser 'S' o 'N'"
    TIENE_PRESTAMOS_ACTIVOS = "No se puede eliminar el usuario. Tiene préstamos activos."
    SOLO_ADMIN_GESTIONA_ADMIN = "Solo un ADMIN del sistema puede gestionar usuarios con rol ADMIN"
    ROL_SUPERIOR_BLOQUEADO = "No puede crear o asignar un rol que no puede gestionar (BIBLIOTECARIO o ADMIN)"


class LibroMessages:
    NOT_FOUND = "Libro no encontrado"
    CAMPOS_REQUERIDOS = "Los campos titulo y autor son requeridos"
    COPIAS_REQUERIDO = "copias_disponibles es requerido"


class EditorialMessages:
    NOT_FOUND = "Editorial no encontrada"
    NOMBRE_REQUERIDO = "El nombre de la editorial es requerido"
    NOMBRE_DUPLICADO = "Ya existe una editorial con ese nombre"


class EjemplarMessages:
    NOT_FOUND = "Ejemplar no encontrado"
    ID_LIBRO_REQUERIDO = "id_libro es requerido"
    LIBRO_NO_EXISTE = "El libro no existe"
    CODIGO_DUPLICADO = "Ya existe un ejemplar con ese código"
    ESTADO_INVALIDO = "Estado inválido. Debe ser uno de: {estados}"
    NO_CAMBIAR_PRESTADO = "Un ejemplar prestado no puede cambiar de estado manualmente; regístrelo como devuelto primero"
    NO_BORRAR_PRESTADO = "No se puede eliminar un ejemplar prestado; devuélvalo primero"


class ReservaMessages:
    NOT_FOUND = "Reserva no encontrada"
    CAMPOS_REQUERIDOS = "id_libro e id_usuario son requeridos"
    ID_USUARIO_REQUERIDO = "id_usuario es requerido"
    LIBRO_NO_EXISTE = "El libro no existe"
    MAX_RESERVAS = "Límite de {max} reservas simultáneas alcanzado"
    RESERVA_DUPLICADA = "Ya tiene una reserva activa para este libro"
    NO_CANCELABLE = "Solo se pueden cancelar reservas activas"


class PrestamoMessages:
    NOT_FOUND = "Préstamo no encontrado"
    YA_DEVUELTO = "El préstamo ya fue devuelto"
    CAMPOS_REQUERIDOS = "id_libro e id_usuario son requeridos"
    SIN_COPIAS = "No hay copias disponibles"


class GenericMessages:
    ERROR_INTERNO = "Error interno del servidor"
    CUERPO_INVALIDO = "Cuerpo de la solicitud inválido"
    PAYLOAD_MUY_GRANDE = "El cuerpo de la solicitud supera el tamaño máximo permitido"
