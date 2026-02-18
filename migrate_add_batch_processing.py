#!/usr/bin/env python3
"""
Миграция для добавления таблиц batch_processing_tasks и batch_processing_files
Создает таблицы для пакетной обработки документов
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
        
        # Проверяем, существует ли таблица batch_processing_tasks
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='batch_processing_tasks'
        """)
        
        if cursor.fetchone():
            print("[OK] Таблица batch_processing_tasks уже существует")
        else:
            # Создаем таблицу batch_processing_tasks
            cursor.execute("""
                CREATE TABLE batch_processing_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(8) NOT NULL,
                    task_name VARCHAR(255),
                    status VARCHAR(20) DEFAULT 'pending',
                    total_files INTEGER DEFAULT 0,
                    processed_files INTEGER DEFAULT 0,
                    failed_files INTEGER DEFAULT 0,
                    results_json TEXT,
                    summary_report_path VARCHAR(500),
                    created_at VARCHAR(30) NOT NULL,
                    started_at VARCHAR(30),
                    completed_at VARCHAR(30),
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            print("[OK] Таблица batch_processing_tasks создана")
        
        # Проверяем, существует ли таблица batch_processing_files
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='batch_processing_files'
        """)
        
        if cursor.fetchone():
            print("[OK] Таблица batch_processing_files уже существует")
        else:
            # Создаем таблицу batch_processing_files
            cursor.execute("""
                CREATE TABLE batch_processing_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500),
                    status VARCHAR(20) DEFAULT 'pending',
                    analysis_result_json TEXT,
                    analysis_history_id INTEGER,
                    created_at VARCHAR(30) NOT NULL,
                    processed_at VARCHAR(30),
                    error_message TEXT,
                    FOREIGN KEY (task_id) REFERENCES batch_processing_tasks(id),
                    FOREIGN KEY (analysis_history_id) REFERENCES analysis_history(id)
                )
            """)
            print("[OK] Таблица batch_processing_files создана")
        
        # Создаем индексы
        try:
            cursor.execute("""
                CREATE INDEX idx_batch_tasks_user_id ON batch_processing_tasks(user_id)
            """)
        except:
            pass  # Индекс уже существует
        
        try:
            cursor.execute("""
                CREATE INDEX idx_batch_tasks_status ON batch_processing_tasks(status)
            """)
        except:
            pass
        
        try:
            cursor.execute("""
                CREATE INDEX idx_batch_files_task_id ON batch_processing_files(task_id)
            """)
        except:
            pass
        
        conn.commit()
        conn.close()
        
        print("[OK] Миграция завершена успешно")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка миграции: {e}")
        return False

if __name__ == '__main__':
    print("Запуск миграции для таблиц batch_processing_tasks и batch_processing_files...")
    if migrate():
        print("Миграция завершена успешно")
    else:
        print("Миграция завершена с ошибками")

