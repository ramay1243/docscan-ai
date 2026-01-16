import os
import tempfile
import uuid
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

def cleanup_temp_files(file_path):
    """Очистка временных файлов"""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"🧹 Удален временный файл: {file_path}")
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении временного файла {file_path}: {e}")

def create_temp_file(file):
    """Создает временный файл и возвращает путь к нему"""
    try:
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{file.filename}")
        file.save(temp_path)
        logger.info(f"📁 Создан временный файл: {temp_path}")
        return temp_path
    except Exception as e:
        logger.error(f"❌ Ошибка создания временного файла: {e}")
        return None

def format_date(date_string):
    """Форматирует дату в читаемый вид"""
    try:
        if isinstance(date_string, str):
            date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        else:
            date_obj = date_string
        
        return date_obj.strftime("%d.%m.%Y %H:%M")
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования даты {date_string}: {e}")
        return date_string

def format_currency(amount):
    """Форматирует сумму в денежный формат"""
    try:
        return f"{int(amount):,}₽".replace(",", " ")
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования суммы {amount}: {e}")
        return f"{amount}₽"

def get_plan_expiry_date(days=30):
    """Возвращает дату истечения тарифа"""
    return (date.today() + timedelta(days=days)).isoformat()

def is_plan_expired(expiry_date):
    """Проверяет истек ли срок действия тарифа"""
    if not expiry_date:
        return True
    
    try:
        if isinstance(expiry_date, str):
            expiry = date.fromisoformat(expiry_date)
        else:
            expiry = expiry_date
        
        return expiry < date.today()
    except Exception as e:
        logger.error(f"❌ Ошибка проверки срока тарифа {expiry_date}: {e}")
        return True

def validate_email(email):
    """Простая валидация email"""
    if not email or '@' not in email:
        return False
    return True

def sanitize_filename(filename):
    """Очищает имя файла от потенциально опасных символов"""
    if not filename:
        return "document"
    
    # Убираем путь и оставляем только имя файла
    filename = os.path.basename(filename)
    
    # Заменяем опасные символы
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Ограничиваем длину
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    
    return filename

def get_file_extension(filename):
    """Возвращает расширение файла в нижнем регистре"""
    if not filename:
        return ""
    
    return os.path.splitext(filename)[1].lower()

def is_image_file(filename):
    """Проверяет является ли файл изображением"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
    return get_file_extension(filename) in image_extensions

def is_document_file(filename):
    """Проверяет является ли файл документом"""
    document_extensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
    return get_file_extension(filename) in document_extensions

def format_file_size(size_bytes):
    """Форматирует размер файла в читаемый вид"""
    if not size_bytes:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"

def generate_secure_filename():
    """Генерирует безопасное имя файла"""
    return f"doc_{uuid.uuid4().hex[:16]}"

def get_user_agent_info(request):
    """Извлекает информацию о браузере пользователя"""
    user_agent = request.headers.get('User-Agent', '')
    
    # Простой парсинг User-Agent
    info = {
        'browser': 'Unknown',
        'platform': 'Unknown',
        'is_mobile': False
    }
    
    user_agent_lower = user_agent.lower()
    
    # Определяем браузер
    if 'chrome' in user_agent_lower:
        info['browser'] = 'Chrome'
    elif 'firefox' in user_agent_lower:
        info['browser'] = 'Firefox'
    elif 'safari' in user_agent_lower:
        info['browser'] = 'Safari'
    elif 'edge' in user_agent_lower:
        info['browser'] = 'Edge'
    
    # Определяем платформу
    if 'windows' in user_agent_lower:
        info['platform'] = 'Windows'
    elif 'mac' in user_agent_lower:
        info['platform'] = 'macOS'
    elif 'linux' in user_agent_lower:
        info['platform'] = 'Linux'
    elif 'android' in user_agent_lower:
        info['platform'] = 'Android'
        info['is_mobile'] = True
    elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
        info['platform'] = 'iOS'
        info['is_mobile'] = True
    
    return info

def rate_limit_key(request):
    """Генерирует ключ для rate limiting"""
    from app import app
    return app.ip_limit_manager.get_client_ip(request)
