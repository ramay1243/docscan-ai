#!/usr/bin/env python3
"""
Миграция: Добавление поля calculator_uses в таблицу guests
"""
import sqlite3
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate():
    """Добавляет поле calculator_uses в таблицу guests"""
    db_path = 'docscan.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже поле
        cursor.execute("PRAGMA table_info(guests)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'calculator_uses' in columns:
            print("✅ Поле calculator_uses уже существует в таблице guests")
            conn.close()
            return True
        
        # Добавляем поле calculator_uses
        print("🔄 Добавление поля calculator_uses в таблицу guests...")
        cursor.execute("ALTER TABLE guests ADD COLUMN calculator_uses INTEGER DEFAULT 0")
        
        # Обновляем существующие записи (устанавливаем 0 для всех существующих гостей)
        cursor.execute("UPDATE guests SET calculator_uses = 0 WHERE calculator_uses IS NULL")
        
        conn.commit()
        conn.close()
        
        print("✅ Миграция успешно выполнена! Поле calculator_uses добавлено в таблицу guests")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Запуск миграции: добавление calculator_uses в guests...")
    success = migrate()
    if success:
        print("✅ Миграция завершена успешно!")
        sys.exit(0)
    else:
        print("❌ Миграция завершилась с ошибкой!")
        sys.exit(1)


