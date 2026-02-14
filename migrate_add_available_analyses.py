#!/usr/bin/env python3
import sys
import os
import sqlite3
import logging

project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def get_db_path():
    try:
        from config import Config
        db_uri = Config.SQLALCHEMY_DATABASE_URI
        return db_uri.replace('sqlite:///', '')
    except Exception:
        return os.path.join(project_path, "docscan.db")

def migrate():
    db_path = get_db_path()
    logger.info(f"📁 Используется база данных: {db_path}")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔍 Проверка существующих колонок...")
        
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        if 'available_analyses' not in existing_columns:
            logger.info("→ Добавляем available_analyses...")
            cursor.execute("ALTER TABLE users ADD COLUMN available_analyses INTEGER DEFAULT 0")
            conn.commit()
            logger.info("✅ available_analyses добавлена")
        else:
            logger.info("✓ Колонка available_analyses уже существует")
        
        logger.info("✅ Миграция успешно завершена!")
        return True
    except sqlite3.Error as e:
        logger.error(f"❌ Ошибка SQLite при миграции: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    if migrate():
        sys.exit(0)
    else:
        sys.exit(1)

