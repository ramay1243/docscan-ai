"""Утилиты для работы с аутентификацией и паролями"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

def hash_password(password):
    """Хеширует пароль"""
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """Проверяет пароль"""
    return check_password_hash(password_hash, password)

def generate_verification_token():
    """Генерирует токен для верификации email"""
    return secrets.token_urlsafe(32)

def generate_reset_token():
    """Генерирует токен для сброса пароля"""
    return secrets.token_urlsafe(32)

def get_token_expiry(hours=24):
    """Возвращает дату истечения токена"""
    return (datetime.now() + timedelta(hours=hours)).isoformat()

def is_token_expired(expiry_date_str):
    """Проверяет истек ли токен"""
    if not expiry_date_str:
        return True
    try:
        expiry_date = datetime.fromisoformat(expiry_date_str)
        return datetime.now() > expiry_date
    except:
        return True


