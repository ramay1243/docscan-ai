import json
import uuid
import os
from datetime import datetime, date
from config import PLANS, Config
import logging

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        self.users_db = self.load_users()
        logger.info(f"👥 Менеджер пользователей загружен: {len(self.users_db)} пользователей")

    def load_users(self):
        """Загружает пользователей из файла"""
        try:
            if os.path.exists(Config.USER_DB_FILE):
                with open(Config.USER_DB_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"DEBUG: В файле {len(data)} пользователей: {list(data.keys())}")
                    
                    logger.info(f"✅ Загружено {len(data)} пользователей из файла")
                    return data
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки пользователей: {e}")
        
        # База по умолчанию если файла нет
        default_db = {
            'default': {
                'plan': 'free',
                'used_today': 0,
                'last_reset': date.today().isoformat(),
                'total_used': 0,
                'user_id': 'default',
                'created_at': datetime.now().isoformat()
            }
        }
        logger.info("✅ Создана база пользователей по умолчанию")
        return default_db

    def save_users(self):
        """Сохраняет пользователей в файл"""
        try:
            with open(Config.USER_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users_db, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Сохранено {len(self.users_db)} пользователей")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения пользователей: {e}")

    def generate_user_id(self):
        """Генерирует уникальный ID пользователя"""
        return str(uuid.uuid4())[:8]

    def get_user(self, user_id=None):
        """Получает или создает пользователя"""
        if not user_id:
            user_id = self.generate_user_id()
        
        if user_id not in self.users_db:
            self.users_db[user_id] = {
                'user_id': user_id,
                'plan': 'free',
                'used_today': 0,
                'last_reset': date.today().isoformat(),
                'total_used': 0,
                'created_at': datetime.now().isoformat(),
                'plan_expires': None
            }
            self.save_users()
            logger.info(f"👤 Создан новый пользователь: {user_id}")
        
        user = self.users_db[user_id]
        
        # Сбрасываем дневной лимит если новый день
        if user['last_reset'] < date.today().isoformat():
            user['used_today'] = 0
            user['last_reset'] = date.today().isoformat()
            logger.info(f"🔄 Сброшен лимит для пользователя {user_id}")
        
        # Проверяем просрочку тарифа
        if user['plan'] != 'free' and user.get('plan_expires'):
            if user['plan_expires'] < date.today().isoformat():
                user['plan'] = 'free'
                user['plan_expires'] = None
                logger.info(f"🔄 Тариф пользователя {user_id} сброшен на бесплатный (истек)")
        
        self.save_users()
        return user

    def can_analyze(self, user_id='default'):
        """Проверяет может ли пользователь сделать анализ"""
        user = self.get_user(user_id)
        
        # Дополнительная проверка (на всякий случай)
        if user['plan'] != 'free' and user.get('plan_expires'):
            if user['plan_expires'] < date.today().isoformat():
                user['plan'] = 'free'
                user['plan_expires'] = None
                self.save_users()
        
        can_user_analyze = user['used_today'] < PLANS[user['plan']]['daily_limit']
        logger.info(f"🔍 Проверка лимита {user_id}: {can_user_analyze} (использовано {user['used_today']} из {PLANS[user['plan']]['daily_limit']})")
        return can_user_analyze

    def record_usage(self, user_id='default'):
        """Записывает использование для пользователя"""
        user = self.get_user(user_id)
        user['used_today'] += 1
        user['total_used'] += 1
        self.save_users()
        logger.info(f"📊 Записан анализ для {user_id}. Сегодня: {user['used_today']}, Всего: {user['total_used']}")

    def set_user_plan(self, user_id, plan_type):
        """Устанавливает тариф пользователю"""
        if plan_type not in PLANS:
            return {'success': False, 'error': 'Неверный тариф'}
        
        user = self.get_user(user_id)
        user['plan'] = plan_type
        user['used_today'] = 0  # Сбрасываем дневной лимит
        
        # Устанавливаем срок действия (30 дней)
        from datetime import timedelta
        expire_date = date.today() + timedelta(days=30)
        user['plan_expires'] = expire_date.isoformat()
        
        self.save_users()
        logger.info(f"🎉 Установлен тариф {plan_type} для пользователя {user_id} до {expire_date}")
        
        return {
            'success': True,
            'message': f'Пользователю {user_id} выдан тариф: {PLANS[plan_type]["name"]}'
        }

    def get_all_users(self):
        """Возвращает всех пользователей"""
        return self.users_db

    def get_stats(self):
        """Возвращает статистику по пользователям"""
        total_users = len(self.users_db)
        total_analyses = sum(user['total_used'] for user in self.users_db.values())
        today_analyses = sum(user['used_today'] for user in self.users_db.values())
        
        return {
            'total_users': total_users,
            'total_analyses': total_analyses,
            'today_analyses': today_analyses
        }
