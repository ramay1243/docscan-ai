"""Утилита для определения и блокировки ботов"""
import logging

logger = logging.getLogger(__name__)

# Список вредоносных ботов для блокировки
MALICIOUS_BOTS = [
    'got',
    'zgrab',
    'GetIntent Crawler',
    'python-requests',
    'curl',
    'wget',
    'scrapy',
    'Palo Alto Networks',
    'Hello from Palo Alto Networks'
]

# Список поисковых ботов (белый список - не блокировать)
SEARCH_BOTS = {
    'YandexBot': 'Yandex',
    'Googlebot': 'Google',
    'Bingbot': 'Bing',
    'DuckDuckBot': 'DuckDuckGo',
    'YaDirectFetcher': 'Yandex Direct',
    'Slurp': 'Yahoo',
    'Baiduspider': 'Baidu',
    'Applebot': 'Apple',
    'facebookexternalhit': 'Facebook',
    'Twitterbot': 'Twitter',
    'LinkedInBot': 'LinkedIn',
    'WhatsApp': 'WhatsApp',
    'TelegramBot': 'Telegram'
}

def is_malicious_bot(user_agent):
    """
    Проверяет является ли запрос от вредоносного бота
    
    Args:
        user_agent: User-Agent строка из заголовков запроса
    
    Returns:
        bool: True если это вредоносный бот, False если нет
    """
    if not user_agent or user_agent == 'Не определен':
        return False
    
    user_agent_lower = user_agent.lower()
    
    for bot_name in MALICIOUS_BOTS:
        if bot_name.lower() in user_agent_lower:
            logger.warning(f"🚫 Обнаружен вредоносный бот: {bot_name} (User-Agent: {user_agent[:50]}...)")
            return True
    
    return False

def is_search_bot(user_agent):
    """
    Проверяет является ли запрос от поискового бота
    
    Args:
        user_agent: User-Agent строка из заголовков запроса
    
    Returns:
        tuple: (is_bot: bool, bot_type: str) - является ли ботом и тип бота
    """
    if not user_agent or user_agent == 'Не определен':
        return False, None
    
    user_agent_lower = user_agent.lower()
    
    for bot_name, bot_type in SEARCH_BOTS.items():
        if bot_name.lower() in user_agent_lower:
            logger.info(f"🕷️ Обнаружен поисковый бот: {bot_type} ({bot_name})")
            return True, bot_name
    
    return False, None

def get_bot_type(user_agent):
    """
    Определяет тип бота по User-Agent
    
    Args:
        user_agent: User-Agent строка из заголовков запроса
    
    Returns:
        str: Тип бота или None если это не бот
    """
    is_bot, bot_type = is_search_bot(user_agent)
    if is_bot:
        return SEARCH_BOTS.get(bot_type, bot_type)
    return None

def is_wordpress_scanner(request_path):
    """
    Проверяет является ли запрос сканером WordPress по пути запроса
    
    Args:
        request_path: Путь запроса (например, '/wp-admin/setup-config.php')
    
    Returns:
        bool: True если это WordPress-сканер, False если нет
    """
    if not request_path:
        return False
    
    # Список путей, которые ищут WordPress-сканеры
    wordpress_paths = [
        '/wp-admin',
        '/wp-login',
        '/wp-content',
        '/wp-includes',
        '/wordpress',
        '/wp-config',
        '/xmlrpc.php',
        '/wp-json',
        '/wp-cron',
        '/wp-mail.php',
        '/wp-load.php',
        '/wp-signup.php',
        '/wp-trackback.php',
        '/wp-comments-post.php'
    ]
    
    request_path_lower = request_path.lower()
    
    for wp_path in wordpress_paths:
        if wp_path in request_path_lower:
            logger.warning(f"🔍 Обнаружен WordPress-сканер: {request_path}")
            return True
    
    return False

def should_block_request(user_agent):
    """
    Определяет нужно ли блокировать запрос
    
    Args:
        user_agent: User-Agent строка из заголовков запроса
    
    Returns:
        bool: True если нужно блокировать, False если нет
    """
    return is_malicious_bot(user_agent)

