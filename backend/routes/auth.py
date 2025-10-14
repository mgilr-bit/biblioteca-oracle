from flask import Blueprint, request, jsonify
from config.database import db
from utils.security import hash_password, verify_password, generate_token
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Autenticar usuario"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email y contraseña son requeridos"}), 400

        # Buscar usuario
        query = """
            SELECT id_usuario, nombre, email, password, rol, activo
            FROM usuarios
            WHERE email = :email AND activo = 'S'
        """

        result = db.execute_query(query, {"email": email})

        if not result:
            logger.warning(f"Intento de login fallido para email: {email}")
            return jsonify({"error": "Credenciales inválidas"}), 401

        user = result[0]

        # Verificar contraseña
        if not verify_password(password, user['PASSWORD']):
            logger.warning(f"Contraseña incorrecta para email: {email}")
            return jsonify({"error": "Credenciales inválidas"}), 401

        # Generar token JWT
        token = generate_token(
            user['ID_USUARIO'],
            user['EMAIL'],
            user['ROL']
        )

        logger.info(f"Login exitoso para usuario: {email}")

        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user['ID_USUARIO'],
                "nombre": user['NOMBRE'],
                "email": user['EMAIL'],
                "rol": user['ROL']
            },
            "message": "Login exitoso"
        })

    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registrar nuevo usuario - Solo permite crear LECTORES"""
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        email = data.get('email')
        password = data.get('password')
        # SEGURIDAD: Forzar rol LECTOR - ignorar cualquier rol enviado desde el frontend
        rol = 'LECTOR'

        if not nombre or not email or not password:
            return jsonify({"error": "Nombre, email y contraseña son requeridos"}), 400

        # Validar longitud de contraseña
        if len(password) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

        # Verificar si el email ya existe
        check_query = "SELECT COUNT(*) as count FROM usuarios WHERE email = :email"
        check_result = db.execute_query(check_query, {"email": email})

        if check_result[0]['COUNT'] > 0:
            logger.warning(f"Intento de registro con email duplicado: {email}")
            return jsonify({"error": "El email ya está registrado"}), 400

        # Hash de la contraseña
        hashed_password = hash_password(password)

        # Insertar nuevo usuario
        insert_query = """
            INSERT INTO usuarios (nombre, email, password, rol)
            VALUES (:nombre, :email, :password, :rol)
        """

        db.execute_query(
            insert_query,
            {"nombre": nombre, "email": email, "password": hashed_password, "rol": rol},
            fetch=False
        )

        logger.info(f"Nuevo usuario registrado: {email}")

        return jsonify({
            "success": True,
            "message": "Usuario registrado exitosamente"
        }), 201

    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500


