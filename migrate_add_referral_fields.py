#!/usr/bin/env python3
"""
Скрипт для добавления новых полей в таблицу users для партнерской программы
"""

import sys
import os
import sqlite3

# Добавляем путь к проекту
project_path = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_path, 'instance', 'users.db')

def check_column_exists(cursor, table_name, column_name):
    """Проверяет существование колонки в таблице"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate():
    """Добавляет новые поля в таблицу users"""
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Проверка существующих колонок...")
        
        # Проверяем и добавляем referral_code
        if not check_column_exists(cursor, 'users', 'referral_code'):
            print("➕ Добавляем колонку referral_code...")
            cursor.execute("ALTER TABLE users ADD COLUMN referral_code VARCHAR(20) UNIQUE")
            print("✅ Колонка referral_code добавлена")
        else:
            print("✓ Колонка referral_code уже существует")
        
        # Проверяем и добавляем referrer_id
        if not check_column_exists(cursor, 'users', 'referrer_id'):
            print("➕ Добавляем колонку referrer_id...")
            cursor.execute("ALTER TABLE users ADD COLUMN referrer_id VARCHAR(8)")
            print("✅ Колонка referrer_id добавлена")
        else:
            print("✓ Колонка referrer_id уже существует")
        
        # Проверяем и добавляем payment_details
        if not check_column_exists(cursor, 'users', 'payment_details'):
            print("➕ Добавляем колонку payment_details...")
            cursor.execute("ALTER TABLE users ADD COLUMN payment_details TEXT")
            print("✅ Колонка payment_details добавлена")
        else:
            print("✓ Колонка payment_details уже существует")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Миграция успешно завершена!")
        return True
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"⚠️ Колонка уже существует: {e}")
            return True
        else:
            print(f"❌ Ошибка SQLite: {e}")
            return False
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)




