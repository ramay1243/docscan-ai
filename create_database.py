#!/usr/bin/env python3
"""
Скрипт для создания SQLite базы данных и таблиц
"""

import sys
import os
sys.path.insert(0, '/var/www/docscan')

from app import app, db

def create_database():
    """Создает базу данных и таблицы"""
    with app.app_context():
        try:
            db.create_all()
            print("✅ Таблицы базы данных успешно созданы!")
            print(f"📁 Файл базы данных: {app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')}")
        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")
            return False
    return True

if __name__ == '__main__':
    create_database()
