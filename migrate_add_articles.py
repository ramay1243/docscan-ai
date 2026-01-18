#!/usr/bin/env python3
"""
Миграция для добавления таблицы articles
"""

import sys
import os
# Добавляем путь к проекту (для сервера)
sys.path.insert(0, '/var/www/docscan')

from app import app, db
from sqlalchemy import inspect
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def migrate():
    """Выполняет миграцию"""
    with app.app_context():
        try:
            logger.info("🚀 Начало миграции для таблицы articles...")
            
            # Импортируем модель Article, чтобы она была зарегистрирована
            from models.sqlite_users import Article
            
            # Проверяем существующие таблицы
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'articles' not in existing_tables:
                logger.info("➕ Создаем таблицу articles...")
                Article.__table__.create(db.engine, checkfirst=True)
                logger.info("✅ Таблица articles создана")
            else:
                logger.info("✅ Таблица articles уже существует")
            
            logger.info("✅ Миграция завершена успешно!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()

