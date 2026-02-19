from flask import Flask
from flask_cors import CORS
import os
import logging
import sys
from datetime import datetime
from models.sqlite_users import db, User, AnalysisHistory, Guest, SearchBot, NewsItem, FullNews, Question, Answer, AnswerLike, EmailCampaign, EmailSend, Article, Payment, Referral, ReferralReward, Notification, WhitelistedIP, BrandingSettings, APIKey, AnalysisSettings, AnalysisTemplate, BatchProcessingTask, BatchProcessingFile, DocumentComparison

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
    
    # Middleware для отслеживания визитов гостей
    @app.before_request
    def track_guest_visits():
        """Отслеживает визиты гостей при каждом запросе"""
        from flask import request, session
        from models.limits import IPLimitManager
        
        # Пропускаем служебные запросы
        if request.path.startswith(('/static/', '/api/', '/admin/', '/payments/', '/favicon.ico', '/robots.txt', '/sitemap.xml')):
            return None
        
        # Пропускаем если пользователь авторизован
        if session.get('user_id'):
            return None
        
        try:
            # Получаем IP и создаем/обновляем запись гостя
            real_ip = app.ip_limit_manager.get_client_ip(request)
            user_agent = request.headers.get('User-Agent', 'Не определен')
            
            # Исключаем локальные IP
            if real_ip in ['127.0.0.1', 'localhost', 'None']:
                return None
            
            # Проверяем на ботов перед созданием записи гостя
            from utils.bot_detector import is_search_bot, should_block_request, get_bot_type, is_wordpress_scanner
            
            # Блокируем вредоносных ботов и WordPress-сканеры
            if should_block_request(user_agent, request_path=request.path):
                # Если это WordPress-сканер, записываем его как бота перед блокировкой
                if is_wordpress_scanner(request_path=request.path, user_agent=user_agent):
                    app.user_manager.get_or_create_search_bot(real_ip, user_agent or request.path, 'WordPress Scanner')
                    logger.warning(f"🚫 WordPress-сканер заблокирован: {request.path} (IP={real_ip})")
                else:
                    logger.debug(f"🚫 Вредоносный бот заблокирован в middleware: IP={real_ip}")
                # Возвращаем 403 Forbidden для заблокированных запросов
                from flask import Response
                return Response('Forbidden', status=403)
            
            # Записываем поисковых ботов в отдельную таблицу
            is_bot, bot_type = is_search_bot(user_agent)
            if is_bot:
                app.user_manager.get_or_create_search_bot(real_ip, user_agent, bot_type)
                logger.debug(f"🕷️ Поисковый бот записан в middleware: {bot_type} (IP={real_ip})")
                return None
            
            # Создаем/обновляем запись гостя только для реальных пользователей
            guest = app.user_manager.get_or_create_guest(real_ip, user_agent)
            guest.last_seen = datetime.now().isoformat()
            from models.sqlite_users import db
            db.session.commit()
        except Exception as e:
            # Не прерываем запрос при ошибке отслеживания
            logger.debug(f"⚠️ Ошибка отслеживания визита гостя: {e}")
        
        return None
    
    # Обработчик ошибок для API эндпоинтов - всегда возвращаем JSON
    @app.errorhandler(500)
    def handle_500_error(e):
        """Обработчик ошибок 500 для API - возвращает JSON вместо HTML"""
        from flask import request, jsonify
        if request.path.startswith('/api/'):
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"❌ Ошибка 500 в API {request.path}: {e}")
            logger.error(f"Трассировка: {error_trace}")
            # ВСЕГДА возвращаем JSON для API, не пробрасываем исключение
            return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500
        # Для не-API запросов возвращаем стандартную обработку
        raise e
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Обработчик всех исключений для API - возвращает JSON"""
        from flask import request, jsonify
        from werkzeug.exceptions import MethodNotAllowed, HTTPException
        
        # Пропускаем HTTP исключения (405, 404, 403 и т.д.) - у них есть свои обработчики
        if isinstance(e, HTTPException) and e.code != 500:
            raise e
        
        if request.path.startswith('/api/'):
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"❌ Необработанное исключение в API {request.path}: {e}")
            logger.error(f"Трассировка: {error_trace}")
            # ВСЕГДА возвращаем JSON для API, не пробрасываем исключение
            return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500
        # Для не-API запросов пробрасываем исключение дальше
        raise e
    
    # Дополнительный обработчик для всех HTTP ошибок
    @app.errorhandler(404)
    def not_found(error):
        from flask import request, jsonify
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not Found', 'message': str(error)}), 404
        # Для не-API запросов возвращаем простую HTML страницу
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 - Страница не найдена</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #333; }
                p { color: #666; }
                a { color: #4361ee; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>404 - Страница не найдена</h1>
            <p>Запрашиваемая страница не существует.</p>
            <p><a href="/">Вернуться на главную</a></p>
        </body>
        </html>
        ''', 404

    @app.errorhandler(403)
    def forbidden(error):
        from flask import request, jsonify
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden', 'message': str(error)}), 403
        from flask import render_template
        return render_template('403.html'), 403
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Обработчик 405 ошибок с фильтрацией сканеров"""
        from flask import request, jsonify
        from werkzeug.exceptions import MethodNotAllowed
        from utils.bot_detector import is_malicious_bot, is_search_bot, should_block_request
        
        # Получаем информацию о запросе
        user_agent = request.headers.get('User-Agent', 'Не определен')
        method = request.method
        path = request.path
        real_ip = app.ip_limit_manager.get_client_ip(request) if hasattr(app, 'ip_limit_manager') else 'Не определен'
        
        # WebDAV методы, которые часто используют сканеры
        webdav_methods = ['PROPFIND', 'OPTIONS', 'MKCOL', 'DELETE', 'PUT', 'MOVE', 'COPY', 'LOCK', 'UNLOCK']
        is_webdav_method = method in webdav_methods
        
        # Проверяем, является ли это известным сканером
        is_scanner = False
        scanner_type = None
        
        if is_malicious_bot(user_agent):
            is_scanner = True
            scanner_type = 'Вредоносный бот'
        elif should_block_request(user_agent, request_path=path):
            is_scanner = True
            scanner_type = 'Заблокированный бот'
        else:
            is_bot, bot_type = is_search_bot(user_agent)
            if is_bot:
                is_scanner = True
                scanner_type = f'Поисковый бот ({bot_type})'
        
        # Для API запросов возвращаем JSON
        if path.startswith('/api/'):
            if is_scanner:
                # Для сканеров - минимальное логирование (DEBUG)
                logger.debug(f"🚫 405 от сканера [{scanner_type}]: {method} {path} (IP={real_ip})")
            else:
                # Для обычных пользователей - WARNING без traceback
                logger.warning(f"⚠️ 405 Method Not Allowed: {method} {path} (IP={real_ip}, UA={user_agent[:50]})")
            return jsonify({'error': 'Method Not Allowed', 'message': f'Method {method} is not allowed for this URL'}), 405
        
        # Для обычных запросов
        if is_scanner:
            # Для сканеров - минимальное логирование (DEBUG)
            if is_webdav_method:
                logger.debug(f"🚫 WebDAV запрос от сканера [{scanner_type}]: {method} {path} (IP={real_ip})")
            else:
                logger.debug(f"🚫 405 от сканера [{scanner_type}]: {method} {path} (IP={real_ip})")
        else:
            # Для обычных пользователей - WARNING без traceback
            if is_webdav_method:
                logger.warning(f"⚠️ WebDAV метод не поддерживается: {method} {path} (IP={real_ip})")
            else:
                logger.warning(f"⚠️ 405 Method Not Allowed: {method} {path} (IP={real_ip}, UA={user_agent[:50]})")
        
        # Возвращаем стандартный ответ 405
        if path.startswith('/api/'):
            return jsonify({'error': 'Method Not Allowed', 'message': f'Method {method} is not allowed for this URL'}), 405
        else:
            # Для не-API запросов возвращаем простую HTML страницу
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>405 - Метод не разрешен</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    h1 { color: #333; }
                    p { color: #666; }
                    a { color: #4361ee; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <h1>405 - Метод не разрешен</h1>
                <p>Используемый метод HTTP не поддерживается для этого URL.</p>
                <p><a href="/">Вернуться на главную</a></p>
            </body>
            </html>
            ''', 405
    
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
        
        logger.info("📦 Импорт routes.api_v1...")
        from routes.api_v1 import api_v1_bp
        logger.info("✅ routes.api_v1 импортирован")
        
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
        
        logger.info("📝 Регистрация api_v1_bp...")
        app.register_blueprint(api_v1_bp)
        logger.info("✅ api_v1_bp зарегистрирован")
        
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
