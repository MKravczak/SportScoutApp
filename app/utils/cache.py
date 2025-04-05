# app/utils/cache.py
import json
import pickle
from functools import wraps
from flask import current_app, request
from datetime import datetime, timedelta

# This is a simple in-memory cache implementation
# For production, replace with Redis or similar cache service
_cache = {}

def cache_key(func_name, *args, **kwargs):
    """Generate a unique cache key based on function name and arguments"""
    key_parts = [func_name]
    
    # Add args to key
    for arg in args:
        if hasattr(arg, '__dict__'):  # For objects
            key_parts.append(str(hash(frozenset(arg.__dict__.items()))))
        else:
            key_parts.append(str(arg))
    
    # Add kwargs to key
    sorted_kwargs = sorted(kwargs.items())
    for k, v in sorted_kwargs:
        if hasattr(v, '__dict__'):  # For objects
            key_parts.append(f"{k}:{str(hash(frozenset(v.__dict__.items())))}")
        else:
            key_parts.append(f"{k}:{v}")
    
    return ":".join(key_parts)

def cache_result(timeout=300):
    """
    Decorator to cache function results
    
    :param timeout: Cache timeout in seconds (default: 5 minutes)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip caching if disabled in config
            if not current_app.config.get('CACHE_ENABLED', True):
                return f(*args, **kwargs)
                
            key = cache_key(f.__name__, *args, **kwargs)
            
            # Check if result is in cache and not expired
            if key in _cache:
                timestamp, result = _cache[key]
                if datetime.utcnow() < timestamp:
                    return pickle.loads(result)  # Return cached result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            expiry = datetime.utcnow() + timedelta(seconds=timeout)
            _cache[key] = (expiry, pickle.dumps(result))
            
            return result
        return decorated_function
    return decorator

def clear_cache(pattern=None):
    """
    Clear cache entries
    
    :param pattern: Optional pattern to match cache keys
    """
    global _cache
    
    if pattern is None:
        _cache = {}  # Clear all cache
    else:
        # Clear cache entries matching pattern
        keys_to_delete = [k for k in _cache.keys() if pattern in k]
        for k in keys_to_delete:
            del _cache[k]

# For Redis implementation (to be used in production)
# Uncomment and configure when Redis is available
"""
import redis
from flask import current_app

def get_redis_client():
    return redis.Redis(
        host=current_app.config.get('REDIS_HOST', 'localhost'),
        port=current_app.config.get('REDIS_PORT', 6379),
        db=current_app.config.get('REDIS_DB', 0),
        password=current_app.config.get('REDIS_PASSWORD', None)
    )
    
def cache_result_redis(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_app.config.get('CACHE_ENABLED', True):
                return f(*args, **kwargs)
                
            redis_client = get_redis_client()
            key = cache_key(f.__name__, *args, **kwargs)
            
            # Check if result is in cache
            cached_value = redis_client.get(key)
            if cached_value:
                return pickle.loads(cached_value)
                
            # Execute function and cache result
            result = f(*args, **kwargs)
            redis_client.setex(key, timeout, pickle.dumps(result))
            
            return result
        return decorated_function
    return decorator
""" 