"""
Миграция: Добавление таблицы whitelisted_ips для белого списка IP-адресов
"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.sqlite_users import db, WhitelistedIP

def migrate():
    """Создает таблицу whitelisted_ips"""
    app = create_app()
    
    with app.app_context():
        try:
            # Создаем таблицу
            db.create_all()
            
            # Проверяем, что таблица создана
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'whitelisted_ips' in tables:
                print("✅ Таблица whitelisted_ips успешно создана")
                return True
            else:
                print("❌ Ошибка: таблица whitelisted_ips не найдена")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)

