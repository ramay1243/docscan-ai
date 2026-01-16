import logging
import sys
from datetime import datetime

class RussianLogger:
    """Логгер с русскоязычными сообщениями"""
    
    @staticmethod
    def setup_logging():
        """Настройка логирования на русском"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            stream=sys.stdout
        )
        return logging.getLogger(__name__)

    @staticmethod
    def log_request(request, user_id=None):
        """Логирование HTTP запросов на русском"""
        ip = request.remote_addr
        method = request.method
        path = request.path
        user_info = f" | 👤 Пользователь: {user_id}" if user_id else ""
        
        logging.info(f"🌐 Запрос: {method} {path} | IP: {ip}{user_info}")

    @staticmethod
    def log_page_view(page_name):
        """Логирование просмотра страниц"""
        logging.info(f"📄 Страница: {page_name}")

    @staticmethod
    def log_app_start():
        """Логирование запуска приложения"""
        logging.info("🚀 Приложение DocScan запущено!")

    @staticmethod
    def log_server_ready(host, port):
        """Логирование готовности сервера"""
        logging.info(f"🌐 Сервер запущен: http://{host}:{port}")

    @staticmethod
    def log_user_created(user_id):
        """Логирование создания пользователя"""
        logging.info(f"👤 Создан новый пользователь: {user_id}")
