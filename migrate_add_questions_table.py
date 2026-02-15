#!/usr/bin/env python3
"""
Скрипт миграции: Создание таблиц questions, answers и answer_likes для системы Q&A
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
    backup_path = f"{db_path}.backup_qa_{int(os.path.getmtime(db_path))}"
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
        # Создаем таблицу questions
        if not check_table_exists(cursor, 'questions'):
            print("→ Создаем таблицу questions...")
            cursor.execute("""
                CREATE TABLE questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(8) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'open',
                    views_count INTEGER DEFAULT 0,
                    answers_count INTEGER DEFAULT 0,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30),
                    best_answer_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            print("✅ Таблица questions создана")
        else:
            print("✓ Таблица questions уже существует")
        
        # Создаем таблицу answers
        if not check_table_exists(cursor, 'answers'):
            print("→ Создаем таблицу answers...")
            cursor.execute("""
                CREATE TABLE answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    user_id VARCHAR(8) NOT NULL,
                    content TEXT NOT NULL,
                    is_best BOOLEAN DEFAULT 0,
                    likes_count INTEGER DEFAULT 0,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30),
                    FOREIGN KEY (question_id) REFERENCES questions(id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            print("✅ Таблица answers создана")
        else:
            print("✓ Таблица answers уже существует")
        
        # Создаем таблицу answer_likes
        if not check_table_exists(cursor, 'answer_likes'):
            print("→ Создаем таблицу answer_likes...")
            cursor.execute("""
                CREATE TABLE answer_likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    answer_id INTEGER NOT NULL,
                    user_id VARCHAR(8) NOT NULL,
                    created_at VARCHAR(30) NOT NULL,
                    FOREIGN KEY (answer_id) REFERENCES answers(id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(answer_id, user_id)
                )
            """)
            print("✅ Таблица answer_likes создана")
        else:
            print("✓ Таблица answer_likes уже существует")
        
        conn.commit()
        print("✅ Миграция успешно завершена!")
        return True
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("Миграция: Создание таблиц для системы Q&A")
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

