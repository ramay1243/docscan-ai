#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для управления API-ключами
Генерация, проверка и управление API-ключами для бизнес-пользователей
"""

import secrets
import hashlib
import logging
from datetime import datetime
from models.sqlite_users import db, APIKey, User

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Менеджер для работы с API-ключами"""
    
    @staticmethod
    def generate_api_key():
        """Генерирует новый API-ключ"""
        # Генерируем случайную строку длиной 32 байта (64 символа в hex)
        key = secrets.token_urlsafe(32)
        return key
    
    @staticmethod
    def hash_api_key(api_key):
        """Хеширует API-ключ для безопасного хранения"""
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    @staticmethod
    def create_api_key(user_id, name=None, expires_at=None):
        """Создает новый API-ключ для пользователя"""
        try:
            # Проверяем, что пользователь существует
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                return None, "Пользователь не найден"
            
            # Проверяем, что пользователь имеет бизнес-тариф (premium или выше)
            if user.plan not in ['premium', 'business']:
                return None, "API-ключи доступны только для бизнес-тарифов"
            
            # Генерируем новый ключ
            api_key = APIKeyManager.generate_api_key()
            api_key_hash = APIKeyManager.hash_api_key(api_key)
            
            # Создаем запись в БД
            new_key = APIKey(
                user_id=user_id,
                api_key=api_key,  # Сохраняем оригинальный ключ (пользователь должен его скопировать)
                api_key_hash=api_key_hash,
                name=name,
                is_active=True,
                requests_count=0,
                created_at=datetime.now().isoformat(),
                expires_at=expires_at
            )
            
            db.session.add(new_key)
            db.session.commit()
            
            logger.info(f"✅ API-ключ создан для пользователя {user_id}")
            
            # Возвращаем оригинальный ключ (только при создании!)
            return api_key, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка создания API-ключа: {e}")
            return None, str(e)
    
    @staticmethod
    def verify_api_key(api_key):
        """Проверяет API-ключ и возвращает информацию о пользователе"""
        try:
            # Хешируем переданный ключ
            api_key_hash = APIKeyManager.hash_api_key(api_key)
            
            # Ищем ключ в БД
            key_record = APIKey.query.filter_by(
                api_key_hash=api_key_hash,
                is_active=True
            ).first()
            
            if not key_record:
                return None, "Неверный или неактивный API-ключ"
            
            # Проверяем срок действия
            if key_record.expires_at:
                expires = datetime.fromisoformat(key_record.expires_at)
                if datetime.now() > expires:
                    return None, "API-ключ истек"
            
            # Обновляем статистику использования
            key_record.last_used = datetime.now().isoformat()
            key_record.requests_count += 1
            db.session.commit()
            
            # Получаем информацию о пользователе
            user = User.query.filter_by(user_id=key_record.user_id).first()
            if not user:
                return None, "Пользователь не найден"
            
            return {
                'user_id': user.user_id,
                'plan': user.plan,
                'api_key_id': key_record.id,
                'api_key_name': key_record.name
            }, None
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки API-ключа: {e}")
            return None, str(e)
    
    @staticmethod
    def get_user_api_keys(user_id):
        """Получает все API-ключи пользователя"""
        try:
            keys = APIKey.query.filter_by(user_id=user_id).order_by(APIKey.created_at.desc()).all()
            return [key.to_dict() for key in keys]
        except Exception as e:
            logger.error(f"❌ Ошибка получения API-ключей: {e}")
            return []
    
    @staticmethod
    def deactivate_api_key(api_key_id, user_id):
        """Деактивирует API-ключ"""
        try:
            key = APIKey.query.filter_by(id=api_key_id, user_id=user_id).first()
            if not key:
                return False, "API-ключ не найден"
            
            key.is_active = False
            db.session.commit()
            
            logger.info(f"✅ API-ключ {api_key_id} деактивирован")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка деактивации API-ключа: {e}")
            return False, str(e)
    
    @staticmethod
    def delete_api_key(api_key_id, user_id):
        """Удаляет API-ключ"""
        try:
            key = APIKey.query.filter_by(id=api_key_id, user_id=user_id).first()
            if not key:
                return False, "API-ключ не найден"
            
            db.session.delete(key)
            db.session.commit()
            
            logger.info(f"✅ API-ключ {api_key_id} удален")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Ошибка удаления API-ключа: {e}")
            return False, str(e)

