#!/usr/bin/env python3
"""
Миграция для добавления таблиц email_campaigns и email_sends, 
а также поля email_subscribed в таблицу users
"""

import sys
import os
# Добавляем путь к проекту (для сервера)
sys.path.insert(0, '/var/www/docscan')

from app import app, db
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def migrate():
    """Выполняет миграцию"""
    with app.app_context():
        try:
            logger.info("🚀 Начало миграции для email-рассылок...")
            
            # Проверяем, существует ли поле email_subscribed
            inspector = inspect(db.engine)
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
                # Импортируем модели, чтобы они были зарегистрированы
                from models.sqlite_users import EmailCampaign, EmailSend
                
                # Проверяем существующие таблицы
                existing_tables = inspector.get_table_names()
                
                if 'email_campaigns' not in existing_tables:
                    logger.info("➕ Создаем таблицу email_campaigns...")
                    EmailCampaign.__table__.create(db.engine, checkfirst=True)
                    logger.info("✅ Таблица email_campaigns создана")
                else:
                    logger.info("✅ Таблица email_campaigns уже существует")
                
                if 'email_sends' not in existing_tables:
                    logger.info("➕ Создаем таблицу email_sends...")
                    EmailSend.__table__.create(db.engine, checkfirst=True)
                    logger.info("✅ Таблица email_sends создана")
                else:
                    logger.info("✅ Таблица email_sends уже существует")
                
                logger.info("✅ Все таблицы для email-рассылок созданы/проверены")
                
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при создании таблиц (возможно, уже существуют): {e}")
                # Пробуем через db.create_all() как резервный вариант
                try:
                    db.create_all()
                    logger.info("✅ Таблицы созданы через db.create_all()")
                except Exception as e2:
                    logger.error(f"❌ Ошибка при создании таблиц через db.create_all(): {e2}")
            
            logger.info("✅ Миграция завершена успешно!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка миграции: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()

