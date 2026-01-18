from flask import Flask
from flask_cors import CORS
import os
import logging
import sys
from models.sqlite_users import db, User, AnalysisHistory, Guest, EmailCampaign, EmailSend

# Настройка логирования
# Настройка логирования на русском
from utils.logger import RussianLogger
logger = RussianLogger.setup_logging()

def create_app():
    """Фабрика для создания приложения Flask"""
    app = Flask(__name__, template_folder='static/templates')
    # Настройки сессий
    app.config['SECRET_KEY'] = 'docscan-super-secret-key-2024'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600
    # Настройки cookies для работы сессий между страницами
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Для продакшена (HTTPS) установить в True через переменную окружения
    # По умолчанию False для работы с HTTP
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    
    # Конфигурация
    from config import Config
    app.config.from_object(Config)
    
    # Инициализация базы данных
    db.init_app(app)
    
    # CORS - настройки для работы с cookies
    CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})
    
    # Инициализация модулей
    try:
        init_services(app)
        logger.info("✅ Сервисы инициализированы")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации сервисов: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        raise
    
    try:
        register_routes(app)
        logger.info("✅ Маршруты зарегистрированы")
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации маршрутов: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        raise
    
    logger.info("🚀 DocScan App инициализирован!")
    return app

def init_services(app):
    """Инициализация сервисов"""
    try:
        # Импортируем здесь чтобы избежать циклических импортов
        from models.sqlite_users import SQLiteUserManager, User
        from models.limits import IPLimitManager
        
        # Инициализируем менеджеры
        app.user_manager = SQLiteUserManager(db, User)
        app.ip_limit_manager = IPLimitManager()
        
        logger.info("✅ Сервисы инициализированы")
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при инициализации сервисов: {e}")
        import traceback
        logger.error(f"Полная трассировка:\n{traceback.format_exc()}")
        raise

def register_routes(app):
    """Регистрация маршрутов"""
    try:
        # Импортируем здесь чтобы избежать циклических импортов
        logger.info("📦 Импорт routes.main...")
        from routes.main import main_bp
        logger.info("✅ routes.main импортирован")
        
        logger.info("📦 Импорт routes.api...")
        from routes.api import api_bp
        logger.info("✅ routes.api импортирован")
        
        logger.info("📦 Импорт routes.admin...")
        from routes.admin import admin_bp
        logger.info("✅ routes.admin импортирован")
        
        logger.info("📦 Импорт routes.payments...")
        from routes.payments import payments_bp
        logger.info("✅ routes.payments импортирован")
        
        logger.info("📦 Импорт routes.auth...")
        from routes.auth import auth_bp
        logger.info("✅ routes.auth импортирован")
        
        # Регистрируем blueprint'ы
        logger.info("📝 Регистрация main_bp...")
        app.register_blueprint(main_bp)
        logger.info("✅ main_bp зарегистрирован")
        
        logger.info("📝 Регистрация api_bp...")
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.info("✅ api_bp зарегистрирован")
        
        logger.info("📝 Регистрация admin_bp...")
        app.register_blueprint(admin_bp, url_prefix='/admin')
        logger.info("✅ admin_bp зарегистрирован")
        
        logger.info("📝 Регистрация payments_bp...")
        app.register_blueprint(payments_bp, url_prefix='/payments')
        logger.info("✅ payments_bp зарегистрирован")
        
        logger.info("📝 Регистрация auth_bp...")
        app.register_blueprint(auth_bp)
        logger.info("✅ auth_bp зарегистрирован")
        
        logger.info("✅ Все маршруты зарегистрированы")
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при регистрации маршрутов: {e}")
        import traceback
        logger.error(f"Полная трассировка:\n{traceback.format_exc()}")
        # Выводим также в stderr для supervisor
        import sys
        sys.stderr.write(f"❌ ОШИБКА регистрации маршрутов: {e}\n")
        sys.stderr.write(f"{traceback.format_exc()}\n")
        raise

# Создаем приложение
app = create_app()

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
