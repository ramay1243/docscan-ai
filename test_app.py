#!/usr/bin/env python3
"""
Тестовый скрипт для проверки новой структуры приложения
"""

import sys
import os

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Проверяем что все модули импортируются без ошибок"""
    print("🧪 Тестируем импорты модулей...")
    
    try:
        from app import app
        print("✅ app.py - OK")
        
        from config import Config, PLANS
        print("✅ config.py - OK")
        
        from models.users import UserManager
        print("✅ models/users.py - OK")
        
        from models.limits import IPLimitManager
        print("✅ models/limits.py - OK")
        
        from services.file_processing import extract_text_from_file
        print("✅ services/file_processing.py - OK")
        
        from services.analysis import analyze_text
        print("✅ services/analysis.py - OK")
        
        from services.yandex_gpt import detect_document_type
        print("✅ services/yandex_gpt.py - OK")
        
        from routes.main import main_bp
        print("✅ routes/main.py - OK")
        
        from routes.api import api_bp
        print("✅ routes/api.py - OK")
        
        from routes.admin import admin_bp
        print("✅ routes/admin.py - OK")
        
        from routes.payments import payments_bp
        print("✅ routes/payments.py - OK")
        
        from utils.helpers import cleanup_temp_files
        print("✅ utils/helpers.py - OK")
        
        print("\n🎉 Все модули импортируются успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_app_creation():
    """Проверяем создание приложения"""
    print("\n🧪 Тестируем создание приложения...")
    
    try:
        from app import app
        print("✅ Приложение создано успешно!")
        print(f"✅ Имя приложения: {app.name}")
        print(f"✅ Режим отладки: {app.debug}")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания приложения: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запускаем тестирование новой структуры DocScan...\n")
    
    success = True
    success &= test_imports()
    success &= test_app_creation()
    
    if success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Новая структура готова к использованию!")
        print("\n📝 Дальнейшие действия:")
        print("1. Запусти: python app.py")
        print("2. Открой: http://localhost:5000")
        print("3. Протестируй загрузку документов")
    else:
        print("\n❌ Есть ошибки, нужно исправить перед запуском")
