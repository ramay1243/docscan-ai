"""
Миграция: добавить поле last_login_at в таблицу users (SQLite)

Запуск:
  python migrate_add_last_login_at.py
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        from app import app
        from models.sqlite_users import db

        with app.app_context():
            # Проверяем наличие колонки через PRAGMA table_info
            result = db.session.execute("PRAGMA table_info(users)").fetchall()
            columns = [row[1] for row in result]  # row[1] = name

            if "last_login_at" in columns:
                logger.info("✅ Колонка last_login_at уже существует в users")
                return

            logger.info("➕ Добавляем колонку last_login_at в users ...")
            db.session.execute("ALTER TABLE users ADD COLUMN last_login_at VARCHAR(30)")
            db.session.commit()
            logger.info("✅ Колонка last_login_at добавлена")

    except Exception as e:
        logger.error(f"❌ Ошибка миграции last_login_at: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass


if __name__ == "__main__":
    main()


