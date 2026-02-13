#!/usr/bin/env python3
"""
Скрипт для принудительного добавления полей в таблицу users
"""

import sys
import os
import sqlite3

# Добавляем путь к проекту
project_path = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_path, 'instance', 'users.db')

def fix_table():
    """Принудительно добавляет поля в таблицу users"""
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Проверяем структуру таблицы users...")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\n📋 Текущие колонки:")
        column_names = []
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            column_names.append(col[1])
        
        print("\n➕ Добавляем недостающие колонки...")
        
        # Добавляем referral_code
        if 'referral_code' not in column_names:
            print("  → Добавляем referral_code...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN referral_code VARCHAR(20)")
                print("  ✅ referral_code добавлена")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print("  ✓ referral_code уже существует")
                else:
                    raise
        else:
            print("  ✓ referral_code уже существует")
        
        # Добавляем referrer_id
        if 'referrer_id' not in column_names:
            print("  → Добавляем referrer_id...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN referrer_id VARCHAR(8)")
                print("  ✅ referrer_id добавлена")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print("  ✓ referrer_id уже существует")
                else:
                    raise
        else:
            print("  ✓ referrer_id уже существует")
        
        # Добавляем payment_details
        if 'payment_details' not in column_names:
            print("  → Добавляем payment_details...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN payment_details TEXT")
                print("  ✅ payment_details добавлена")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print("  ✓ payment_details уже существует")
                else:
                    raise
        else:
            print("  ✓ payment_details уже существует")
        
        conn.commit()
        
        # Проверяем результат
        print("\n🔍 Проверяем результат...")
        cursor.execute("PRAGMA table_info(users)")
        columns_after = cursor.fetchall()
        column_names_after = [col[1] for col in columns_after]
        
        required_columns = ['referral_code', 'referrer_id', 'payment_details']
        missing = [col for col in required_columns if col not in column_names_after]
        
        if missing:
            print(f"❌ Ошибка: колонки {missing} все еще отсутствуют!")
            conn.close()
            return False
        
        print("\n✅ Все необходимые колонки присутствуют!")
        print("\n📋 Финальная структура таблицы users:")
        for col in columns_after:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_table()
    sys.exit(0 if success else 1)

