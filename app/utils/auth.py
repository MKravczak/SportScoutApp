from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
import jwt
from datetime import datetime, timedelta
from app.models import User

def generate_jwt_token(user_id, expiration=24):
    """Generate JWT token for a user"""
    payload = {
        'exp': datetime.utcnow() + timedelta(hours=expiration),
        'iat': datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def decode_jwt_token(token):
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

def token_required(f):
    """Decorator for protecting API routes with JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        user_id = decode_jwt_token(token)
        if not user_id:
            return jsonify({'message': 'Token is invalid or expired!'}), 401
            
        current_user = User.query.get(user_id)
        if not current_user:
            return jsonify({'message': 'User not found!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

def role_required(*roles):
    """Decorator for role-based access control"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'message': 'Authentication required!'}), 401
            if current_user.role not in roles:
                return jsonify({'message': 'Permission denied!'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator 