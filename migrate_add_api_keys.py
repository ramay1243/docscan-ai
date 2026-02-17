#!/usr/bin/env python3
"""
Миграция для добавления таблицы api_keys
Создает таблицу для хранения API-ключей для бизнес-пользователей
"""

import sqlite3
import os
from datetime import datetime

def migrate():
    """Выполняет миграцию"""
    # Путь к базе данных (сначала пробуем корень проекта, потом instance)
    base_dir = os.path.dirname(__file__)
    db_path = os.path.join(base_dir, 'docscan.db')
    
    # Если база не найдена в корне, пробуем instance
    if not os.path.exists(db_path):
        db_path = os.path.join(base_dir, 'instance', 'docscan.db')
    
    if not os.path.exists(db_path):
        print(f"[ERROR] База данных не найдена. Проверенные пути:")
        print(f"   - {os.path.join(base_dir, 'docscan.db')}")
        print(f"   - {os.path.join(base_dir, 'instance', 'docscan.db')}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли таблица
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='api_keys'
        """)
        
        if cursor.fetchone():
            print("[OK] Таблица api_keys уже существует")
            conn.close()
            return True
        
        # Создаем таблицу
        cursor.execute("""
            CREATE TABLE api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(8) NOT NULL,
                api_key VARCHAR(64) NOT NULL UNIQUE,
                api_key_hash VARCHAR(128) NOT NULL,
                name VARCHAR(255),
                is_active BOOLEAN DEFAULT 1,
                last_used VARCHAR(30),
                requests_count INTEGER DEFAULT 0,
                created_at VARCHAR(30) NOT NULL,
                expires_at VARCHAR(30),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Создаем индексы
        cursor.execute("""
            CREATE INDEX idx_api_key ON api_keys(api_key)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_api_user_id ON api_keys(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_api_active ON api_keys(is_active)
        """)
        
        conn.commit()
        conn.close()
        
        print("[OK] Таблица api_keys успешно создана")
        print("[OK] Индексы созданы")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка миграции: {e}")
        return False

if __name__ == '__main__':
    print("Запуск миграции для таблицы api_keys...")
    if migrate():
        print("Миграция завершена успешно")
    else:
        print("Миграция завершена с ошибками")

