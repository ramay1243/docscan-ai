#!/usr/bin/env python3
"""
Миграция для добавления таблицы branding_settings
Создает таблицу для хранения настроек кастомного брендинга пользователей
"""

import sqlite3
import os
from datetime import datetime

def migrate():
    """Выполняет миграцию"""
    # Путь к базе данных
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'docscan.db')
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли таблица
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='branding_settings'
        """)
        
        if cursor.fetchone():
            print("✅ Таблица branding_settings уже существует")
            conn.close()
            return True
        
        # Создаем таблицу
        cursor.execute("""
            CREATE TABLE branding_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(8) NOT NULL UNIQUE,
                logo_path VARCHAR(500),
                primary_color VARCHAR(7) DEFAULT '#4361ee',
                secondary_color VARCHAR(7) DEFAULT '#764ba2',
                company_name VARCHAR(255),
                is_active BOOLEAN DEFAULT 1,
                created_at VARCHAR(30) NOT NULL,
                updated_at VARCHAR(30),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Создаем индексы
        cursor.execute("""
            CREATE INDEX idx_branding_user_id ON branding_settings(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_branding_active ON branding_settings(is_active)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Таблица branding_settings успешно создана")
        print("✅ Индексы созданы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Запуск миграции для таблицы branding_settings...")
    if migrate():
        print("✅ Миграция завершена успешно")
    else:
        print("❌ Миграция завершена с ошибками")

