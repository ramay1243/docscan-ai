from flask import Flask
from flask_cors import CORS
import os
import logging
import sys
from models.sqlite_users import db

# Настройка логирования
# Настройка логирования на русском
from utils.logger import RussianLogger
logger = RussianLogger.setup_logging()

def create_app():
    """Фабрика для создания приложения Flask"""
    app = Flask(__name__, template_folder='static/templates')
    # Настройки сессий
    app.config['SECRET_KEY'] = 'docscan-super-secret-key-2024'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600
    
    # Конфигурация
    from config import Config
    app.config.from_object(Config)
    
    # Инициализация базы данных
    db.init_app(app)
    
    # CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Инициализация модулей
    init_services(app)
    register_routes(app)
    
    logger.info("🚀 DocScan App инициализирован!")
    return app

def init_services(app):
    """Инициализация сервисов"""
    # Импортируем здесь чтобы избежать циклических импортов
    from models.sqlite_users import SQLiteUserManager, User
    from models.limits import IPLimitManager
    
    # Инициализируем менеджеры
    app.user_manager = SQLiteUserManager(db, User)
    app.ip_limit_manager = IPLimitManager()
    
    logger.info("✅ Сервисы инициализированы")

def register_routes(app):
    """Регистрация маршрутов"""
    # Импортируем здесь чтобы избежать циклических импортов
    from routes.main import main_bp
    from routes.api import api_bp
    from routes.admin import admin_bp
    from routes.payments import payments_bp
    
    # Регистрируем blueprint'ы
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    
    logger.info("✅ Маршруты зарегистрированы")

# Создаем приложение
app = create_app()

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
