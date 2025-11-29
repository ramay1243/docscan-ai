#!/usr/bin/env python3
"""
Скрипт для миграции пользователей из JSON в SQLite
"""

import json
import sys
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, '/var/www/docscan')

from app import app, db
from models.sqlite_users import User, SQLiteUserManager

def migrate_users():
    """Переносит пользователей из JSON в SQLite"""
    
    # Загружаем старые данные из JSON
    json_path = '/var/www/data/docscan_users.json'
    if not os.path.exists(json_path):
        logger.error(f"❌ JSON файл не найден: {json_path}")
        return False

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            old_users = json.load(f)
        logger.info(f"📁 Загружено {len(old_users)} пользователей из JSON")
    except Exception as e:
        logger.error(f"❌ Ошибка чтения JSON: {e}")
        return False

    # Создаем менеджер для SQLite
    sqlite_manager = SQLiteUserManager(db, User)

    migrated_count = 0
    with app.app_context():
        for user_id, user_data in old_users.items():
            try:
                # Проверяем, нет ли уже такого пользователя в БД
                existing_user = sqlite_manager.get_user(user_id)
                if existing_user:
                    logger.info(f"⏭️  Пользователь {user_id} уже существует, пропускаем")
                    continue

                # Создаем пользователя в SQLite
                user_data['user_id'] = user_id
                sqlite_manager.create_user(user_data)
                logger.info(f"✅ Успешно мигрирован: {user_id}")
                migrated_count += 1

            except Exception as e:
                logger.error(f"❌ Ошибка при миграции {user_id}: {e}")

    logger.info(f"🎉 Миграция завершена. Успешно мигрировано: {migrated_count}/{len(old_users)} пользователей")
    return True

if __name__ == '__main__':
    migrate_users()
