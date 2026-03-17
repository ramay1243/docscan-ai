"""
Миграция: создать таблицу page_views (SQLite)

Запуск:
  python migrate_add_page_views_table.py
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        from app import app
        from models.sqlite_users import db
        from sqlalchemy import text

        with app.app_context():
            # Проверяем, есть ли таблица
            res = db.session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='page_views'"
            )).fetchone()
            if res:
                logger.info("✅ Таблица page_views уже существует")
                return

            logger.info("➕ Создаем таблицу page_views ...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS page_views (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path VARCHAR(255) NOT NULL,
                    ip_address VARCHAR(50),
                    user_id VARCHAR(8),
                    user_agent VARCHAR(500),
                    created_at VARCHAR(30) NOT NULL
                )
                """))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_page_views_path ON page_views(path)"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_page_views_created_at ON page_views(created_at)"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_page_views_ip ON page_views(ip_address)"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_page_views_user_id ON page_views(user_id)"))
            db.session.commit()
            logger.info("✅ Таблица page_views создана")

    except Exception as e:
        logger.error(f"❌ Ошибка миграции page_views: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass


if __name__ == "__main__":
    main()

