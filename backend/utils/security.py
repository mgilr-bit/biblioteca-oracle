import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
JWT_EXPIRATION_HOURS = 24

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def generate_token(user_id: int, email: str, rol: str) -> str:
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'rol': rol,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise ValueError('Token expirado')
    except jwt.InvalidTokenError:
        raise ValueError('Token inválido')

def token_required(f):
    """Decorator to require JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Formato de token inválido'}), 401

        if not token:
            return jsonify({'error': 'Token requerido'}), 401

        try:
            payload = decode_token(token)
            request.user = payload
        except ValueError as e:
            return jsonify({'error': str(e)}), 401

        return f(*args, **kwargs)

    return decorated

def role_required(roles: list):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'user'):
                return jsonify({'error': 'No autenticado'}), 401

            user_role = request.user.get('rol')
            if user_role not in roles:
                return jsonify({
                    'error': 'No tiene permisos para realizar esta acción'
                }), 403

            return f(*args, **kwargs)
        return decorated
    return decorator
