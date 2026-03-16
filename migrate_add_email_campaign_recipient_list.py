"""
Миграция: добавить поле recipient_list в таблицу email_campaigns (SQLite)

Запуск:
  python3 migrate_add_email_campaign_recipient_list.py
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        from app import app
        from models.sqlite_users import db

        with app.app_context():
            result = db.session.execute("PRAGMA table_info(email_campaigns)").fetchall()
            columns = [row[1] for row in result]

            if "recipient_list" in columns:
                logger.info("✅ Колонка recipient_list уже существует в email_campaigns")
                return

            logger.info("➕ Добавляем колонку recipient_list в email_campaigns ...")
            db.session.execute("ALTER TABLE email_campaigns ADD COLUMN recipient_list TEXT")
            db.session.commit()
            logger.info("✅ Колонка recipient_list добавлена")

    except Exception as e:
        logger.error(f"❌ Ошибка миграции recipient_list: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass


if __name__ == "__main__":
    main()


