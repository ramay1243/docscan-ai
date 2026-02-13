#!/usr/bin/env python3
"""
Скрипт для создания SQLite базы данных и таблиц
"""

import sys
import os

# Добавляем путь к проекту
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)

def create_database():
    """Создает базу данных и таблицы"""
    try:
        # Импортируем только необходимые компоненты для создания таблиц
        from models.sqlite_users import db
        from flask import Flask
        
        # Создаем минимальное приложение Flask только для создания таблиц
        temp_app = Flask(__name__)
        
        # Используем путь из config.py если доступен
        try:
            sys.path.insert(0, project_path)
            from config import Config
            db_uri = Config.SQLALCHEMY_DATABASE_URI
            temp_app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
            print(f"📁 Используется путь из config.py: {db_uri}")
        except Exception as e:
            # Fallback на стандартный путь
            db_path = os.path.join(project_path, 'docscan.db')
            temp_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            print(f"⚠️ Не удалось загрузить config, используем: {db_path}")
            print(f"   Ошибка: {e}")
        
        temp_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(temp_app)
        
        with temp_app.app_context():
            # Создаем директорию instance если её нет
            instance_dir = os.path.join(project_path, 'instance')
            os.makedirs(instance_dir, exist_ok=True)
            
            # Создаем все таблицы
            db.create_all()
            
            db_path = temp_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            print("✅ Таблицы базы данных успешно созданы!")
            print(f"📁 Файл базы данных: {db_path}")
            
            # Проверяем созданные таблицы
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Создано таблиц: {len(tables)}")
            print(f"📋 Таблицы: {', '.join(tables)}")
            
            return True
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)
