#!/usr/bin/env python3
"""
Скрипт миграции: Создание таблицы news_items для управления новостями
"""

import sys
import os
import sqlite3

# Добавляем путь к проекту
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)

def get_db_path():
    """Получает путь к базе данных"""
    try:
        from config import Config
        db_uri = Config.SQLALCHEMY_DATABASE_URI
        return db_uri.replace('sqlite:///', '')
    except Exception as e:
        # Fallback на стандартный путь
        db_path = os.path.join(project_path, 'docscan.db')
        print(f"⚠️ Не удалось загрузить config, используем: {db_path}")
        print(f"   Ошибка: {e}")
        return db_path

def check_table_exists(cursor, table_name):
    """Проверяет существует ли таблица"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def migrate():
    """Выполняет миграцию"""
    db_path = get_db_path()
    print(f"📁 Используется база данных: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    # Создаем резервную копию
    backup_path = f"{db_path}.backup_news_{int(os.path.getmtime(db_path))}"
    print(f"💾 Создание резервной копии...")
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Резервная копия создана: {backup_path}")
    except Exception as e:
        print(f"⚠️ Не удалось создать резервную копию: {e}")
        response = input("Продолжить без резервной копии? (y/n): ")
        if response.lower() != 'y':
            return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем существует ли таблица
        if check_table_exists(cursor, 'news_items'):
            print("✓ Таблица news_items уже существует")
            conn.close()
            return True
        
        print("→ Создаем таблицу news_items...")
        
        # Создаем таблицу
        cursor.execute("""
            CREATE TABLE news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(20) NOT NULL,
                title VARCHAR(500) NOT NULL,
                description TEXT NOT NULL,
                date VARCHAR(30) NOT NULL,
                link VARCHAR(500),
                link_text VARCHAR(100),
                created_at VARCHAR(30) NOT NULL,
                updated_at VARCHAR(30),
                created_by VARCHAR(50)
            )
        """)
        
        conn.commit()
        print("✅ Таблица news_items создана")
        
        # Проверяем структуру
        cursor.execute("PRAGMA table_info(news_items)")
        columns = cursor.fetchall()
        print(f"📊 Структура таблицы:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        conn.close()
        print("✅ Миграция успешно завершена!")
        return True
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("Миграция: Создание таблицы news_items")
    print("=" * 50)
    print()
    
    success = migrate()
    
    if success:
        print()
        print("=" * 50)
        print("✅ Миграция завершена успешно!")
        print("=" * 50)
        sys.exit(0)
    else:
        print()
        print("=" * 50)
        print("❌ Миграция завершилась с ошибками")
        print("=" * 50)
        sys.exit(1)



