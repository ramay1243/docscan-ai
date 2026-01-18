#!/usr/bin/env python3
"""
Миграция для добавления таблиц email_campaigns и email_sends, 
а также поля email_subscribed в таблицу users
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Выполняет миграцию"""
    with app.app_context():
        try:
            # Проверяем, существует ли поле email_subscribed
            inspector = db.inspect(db.engine)
            users_columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'email_subscribed' not in users_columns:
                logger.info("➕ Добавляем поле email_subscribed в таблицу users...")
                db.session.execute(text("ALTER TABLE users ADD COLUMN email_subscribed BOOLEAN DEFAULT 1"))
                db.session.commit()
                logger.info("✅ Поле email_subscribed добавлено")
            else:
                logger.info("✅ Поле email_subscribed уже существует")
            
            # Создаем таблицы для рассылок (если их нет)
            try:
                db.create_all()
                logger.info("✅ Таблицы для email-рассылок созданы/проверены")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при создании таблиц (возможно, уже существуют): {e}")
            
            logger.info("✅ Миграция завершена успешно!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()

