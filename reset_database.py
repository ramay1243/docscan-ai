#!/usr/bin/env python3
"""
Скрипт для удаления и пересоздания базы данных SQLite
ВНИМАНИЕ: Это удалит ВСЕ данные!
"""

import sys
import os

# Для сервера
if os.path.exists('/var/www/docscan'):
    sys.path.insert(0, '/var/www/docscan')
    db_path = '/var/www/docscan/docscan.db'
else:
    # Для локальной разработки
    db_path = os.path.join(os.path.dirname(__file__), 'docscan.db')

from app import app, db

def reset_database():
    """Удаляет старую базу и создает новую"""
    
    print("⚠️  ВНИМАНИЕ: Это удалит ВСЮ базу данных!")
    print(f"📁 Файл базы данных: {db_path}")
    
    # Проверяем существует ли файл
    if os.path.exists(db_path):
        print(f"✅ Файл найден: {db_path}")
        
        # Удаляем файл базы данных
        try:
            os.remove(db_path)
            print(f"✅ Старая база данных удалена: {db_path}")
        except Exception as e:
            print(f"❌ Ошибка при удалении базы данных: {e}")
            return False
    else:
        print(f"ℹ️  Файл базы данных не найден: {db_path}")
        print("   Создадим новую базу данных...")
    
    # Создаем новую базу данных
    with app.app_context():
        try:
            db.create_all()
            print("✅ Новая база данных успешно создана!")
            print(f"📁 Файл: {db_path}")
            print("\n📋 Созданные таблицы:")
            print("   - users (пользователи)")
            print("   - analysis_history (история анализов)")
            print("   - guests (незарегистрированные пользователи)")
            return True
        except Exception as e:
            print(f"❌ Ошибка при создании базы данных: {e}")
            return False

if __name__ == '__main__':
    confirm = input("\n❓ Вы уверены, что хотите удалить ВСЮ базу данных? (yes/no): ")
    if confirm.lower() in ['yes', 'y', 'да', 'д']:
        reset_database()
    else:
        print("❌ Операция отменена")

