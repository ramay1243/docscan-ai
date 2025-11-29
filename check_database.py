#!/usr/bin/env python3
"""
Скрипт для проверки данных в SQLite базе
"""

import sys
sys.path.insert(0, '/var/www/docscan')

from app import app, db
from models.sqlite_users import User, SQLiteUserManager

def check_database():
    """Проверяет данные в базе"""
    with app.app_context():
        sqlite_manager = SQLiteUserManager(db, User)
        
        # Получаем всех пользователей
        users = sqlite_manager.get_all_users()
        print(f"📊 Всего пользователей в SQLite: {len(users)}")
        
        # Выводим информацию о каждом пользователе
        for user in users:
            print(f"👤 {user.user_id}: {user.plan} план, использовано сегодня: {user.used_today}, всего: {user.total_used}")
        
        # Проверяем статистику
        stats = sqlite_manager.get_stats()
        print(f"\n📈 Статистика:")
        print(f"   Всего пользователей: {stats['total_users']}")
        print(f"   Всего анализов: {stats['total_analyses']}")
        print(f"   Анализов сегодня: {stats['today_analyses']}")

if __name__ == '__main__':
    check_database()
