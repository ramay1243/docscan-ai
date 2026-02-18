#!/usr/bin/env python3
"""
Миграция для добавления таблиц analysis_settings и analysis_templates
Создает таблицы для хранения настроек анализа документов для бизнес-пользователей
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
        
        # Проверяем, существует ли таблица analysis_settings
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='analysis_settings'
        """)
        
        if cursor.fetchone():
            print("[OK] Таблица analysis_settings уже существует")
        else:
            # Создаем таблицу analysis_settings
            cursor.execute("""
                CREATE TABLE analysis_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(8) NOT NULL UNIQUE,
                    legal_priority INTEGER DEFAULT 5,
                    financial_priority INTEGER DEFAULT 5,
                    operational_priority INTEGER DEFAULT 5,
                    strategic_priority INTEGER DEFAULT 5,
                    detail_level VARCHAR(20) DEFAULT 'standard',
                    custom_checks TEXT,
                    active_template VARCHAR(255),
                    use_default BOOLEAN DEFAULT 1,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            print("[OK] Таблица analysis_settings создана")
        
        # Проверяем, существует ли таблица analysis_templates
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='analysis_templates'
        """)
        
        if cursor.fetchone():
            print("[OK] Таблица analysis_templates уже существует")
        else:
            # Создаем таблицу analysis_templates
            cursor.execute("""
                CREATE TABLE analysis_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(8) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    legal_priority INTEGER DEFAULT 5,
                    financial_priority INTEGER DEFAULT 5,
                    operational_priority INTEGER DEFAULT 5,
                    strategic_priority INTEGER DEFAULT 5,
                    detail_level VARCHAR(20) DEFAULT 'standard',
                    custom_checks TEXT,
                    created_at VARCHAR(30) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            print("[OK] Таблица analysis_templates создана")
        
        # Создаем индексы
        try:
            cursor.execute("""
                CREATE INDEX idx_analysis_settings_user_id ON analysis_settings(user_id)
            """)
        except:
            pass  # Индекс уже существует
        
        try:
            cursor.execute("""
                CREATE INDEX idx_analysis_templates_user_id ON analysis_templates(user_id)
            """)
        except:
            pass  # Индекс уже существует
        
        conn.commit()
        conn.close()
        
        print("[OK] Миграция завершена успешно")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка миграции: {e}")
        return False

if __name__ == '__main__':
    print("Запуск миграции для таблиц analysis_settings и analysis_templates...")
    if migrate():
        print("Миграция завершена успешно")
    else:
        print("Миграция завершена с ошибками")

