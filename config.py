import os
from dotenv import load_dotenv

load_dotenv()

# Базовые настройки
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = False
    TESTING = False
    
    # Yandex Cloud
    YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
    YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
    
    # YooMoney
    YOOMONEY_CLIENT_ID = os.getenv('YOOMONEY_CLIENT_ID')
    YOOMONEY_CLIENT_SECRET = os.getenv('YOOMONEY_CLIENT_SECRET')
    YOOMONEY_REDIRECT_URI = os.getenv('YOOMONEY_REDIRECT_URI', 'https://docscan-ai.ru/payment-success')
    
    # Пути к файлам
    USER_DB_FILE = 'docscan_users.json'
    IP_LIMITS_FILE = 'docscan_ip_limits.json'

# Умная система анализа документов
SMART_ANALYSIS_CONFIG = {
    'lease': {
        'name': 'Договор аренды',
        'keywords': ['аренд', 'найм', 'лизинг', 'арендодатель', 'арендатор', 'помещен', 'недвижимость'],
        'expert_areas': ['Недвижимость', 'Гражданское право', 'Финансы']
    },
    'employment': {
        'name': 'Трудовой договор', 
        'keywords': ['трудовой', 'работодатель', 'работник', 'зарплат', 'отпуск', 'трудовая', 'должность'],
        'expert_areas': ['Трудовое право', 'HR', 'Соц. гарантии']
    },
    'sale': {
        'name': 'Договор купли-продажи',
        'keywords': ['купл', 'продаж', 'покупатель', 'продавец', 'товар', 'оплат', 'доставк'],
        'expert_areas': ['Коммерческое право', 'Логистика', 'Финансы']
    },
    'service': {
        'name': 'Договор оказания услуг',
        'keywords': ['услуг', 'подряд', 'исполнитель', 'заказчик', 'выполнен', 'срок'],
        'expert_areas': ['Гражданское право', 'Проектный менеджмент', 'Контроль качества']
    },
    'nda': {
        'name': 'Соглашение о конфиденциальности',
        'keywords': ['конфиденциальн', 'нда', 'секрет', 'неразглашен', 'коммерческая тайна'],
        'expert_areas': ['Интеллектуальная собственность', 'Корпоративная безопасность']
    },
    'loan': {
        'name': 'Кредитный договор',
        'keywords': ['кредит', 'заем', 'займ', 'процент', 'погашен', 'ссуд'],
        'expert_areas': ['Финансовое право', 'Банковское дело', 'Риск-менеджмент']
    },
    'partnership': {
        'name': 'Договор партнерства', 
        'keywords': ['партнер', 'совместн', 'сотрудничеств', 'долев', 'участник'],
        'expert_areas': ['Корпоративное право', 'Стратегическое планирование', 'Финансы']
    },
    'general': {
        'name': 'Общий договор',
        'keywords': [],
        'expert_areas': ['Гражданское право', 'Деловые отношения']
    }
}

# Уровни риска
RISK_LEVELS = {
    'CRITICAL': {'color': '#e53e3e', 'icon': '🔴', 'description': 'Высокий риск потерь'},
    'HIGH': {'color': '#dd6b20', 'icon': '🟠', 'description': 'Существенный риск'},
    'MEDIUM': {'color': '#d69e2e', 'icon': '🟡', 'description': 'Умеренный риск'},
    'LOW': {'color': '#38a169', 'icon': '🟢', 'description': 'Низкий риск'},
    'INFO': {'color': '#3182ce', 'icon': '🔵', 'description': 'Информация'}
}

# Тарифы
PLANS = {
    'free': {
        'daily_limit': 1,
        'ai_access': True,
        'price': 0,
        'name': 'Бесплатный'
    },
    'basic': {
        'daily_limit': 10,
        'ai_access': True, 
        'price': 199,
        'name': 'Базовый'
    },
    'premium': {
        'daily_limit': 50,
        'ai_access': True,
        'price': 399,
        'name': 'Премиум'
    },
    'unlimited': {
        'daily_limit': 1000,
        'ai_access': True,
        'price': 800,
        'name': 'Безлимитный'
    }
}

# Администраторы
ADMINS = {
    'admin': 'admin123',
    'superuser': 'super123'
}
