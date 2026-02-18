#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция: добавление таблицы document_comparisons
"""

import sqlite3
import os
from datetime import datetime

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'docscan.db')
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли таблица
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='document_comparisons'
        """)
        
        if cursor.fetchone():
            print("OK: Table document_comparisons already exists")
            return
        
        # Создаем таблицу
        cursor.execute("""
            CREATE TABLE document_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(8) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                original_file_path VARCHAR(500),
                modified_filename VARCHAR(255) NOT NULL,
                modified_file_path VARCHAR(500),
                comparison_result_json TEXT,
                risk_analysis_json TEXT,
                report_path VARCHAR(500),
                status VARCHAR(20) DEFAULT 'pending',
                error_message TEXT,
                created_at VARCHAR(30) NOT NULL,
                completed_at VARCHAR(30),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Создаем индексы
        cursor.execute("CREATE INDEX idx_document_comparisons_user_id ON document_comparisons(user_id)")
        cursor.execute("CREATE INDEX idx_document_comparisons_status ON document_comparisons(status)")
        
        conn.commit()
        print("OK: Table document_comparisons created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Migration error: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()

