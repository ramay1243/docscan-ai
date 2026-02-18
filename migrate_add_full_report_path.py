#!/usr/bin/env python3
"""
Миграция для добавления поля full_report_path в таблицу batch_processing_files
"""

import sqlite3
import os

def migrate():
    """Выполняет миграцию"""
    base_dir = os.path.dirname(__file__)
    db_path = os.path.join(base_dir, 'docscan.db')
    
    if not os.path.exists(db_path):
        db_path = os.path.join(base_dir, 'instance', 'docscan.db')
    
    if not os.path.exists(db_path):
        print(f"[ERROR] База данных не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли колонка
        cursor.execute("PRAGMA table_info(batch_processing_files)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'full_report_path' in columns:
            print("[OK] Колонка full_report_path уже существует")
        else:
            # Добавляем колонку
            cursor.execute("""
                ALTER TABLE batch_processing_files 
                ADD COLUMN full_report_path VARCHAR(500)
            """)
            print("[OK] Колонка full_report_path добавлена")
        
        conn.commit()
        conn.close()
        
        print("[OK] Миграция завершена успешно")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка миграции: {e}")
        return False

if __name__ == '__main__':
    print("Запуск миграции для добавления full_report_path...")
    if migrate():
        print("Миграция завершена успешно")
    else:
        print("Миграция завершена с ошибками")

