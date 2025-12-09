from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), unique=True, nullable=False)
    plan = db.Column(db.String(20), default='free')
    used_today = db.Column(db.Integer, default=0)
    last_reset = db.Column(db.String(10), nullable=False)
    total_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.String(30), nullable=False)
    plan_expires = db.Column(db.String(10), nullable=True)
    ip_address = db.Column(db.String(50), default='Не определен')
    calculator_uses = db.Column(db.Integer, default=0)
    last_calculator_use = db.Column(db.String(30), nullable=True)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'plan': self.plan,
            'used_today': self.used_today,
            'last_reset': self.last_reset,
            'total_used': self.total_used,
            'created_at': self.created_at,
            'plan_expires': self.plan_expires,
            'ip_address': self.ip_address,
            'calculator_uses': self.calculator_uses,
            'last_calculator_use': self.last_calculator_use
        }

class SQLiteUserManager:
    """Новый менеджер для работы с SQLite"""
    
    def __init__(self, db, UserModel):
        self.db = db
        self.User = UserModel

    def create_user(self, user_data):
        """Создает нового пользователя"""
        user = self.User(
            user_id=user_data['user_id'],
            plan=user_data.get('plan', 'free'),
            used_today=user_data.get('used_today', 0),
            last_reset=user_data.get('last_reset', date.today().isoformat()),
            total_used=user_data.get('total_used', 0),
            created_at=user_data.get('created_at', datetime.now().isoformat()),
            plan_expires=user_data.get('plan_expires'),
            ip_address=user_data.get('ip_address', 'Не определен')
        )
        self.db.session.add(user)
        self.db.session.commit()
        return user

    def get_user(self, user_id):
        """Получает пользователя по ID"""
        return self.User.query.filter_by(user_id=user_id).first()

    def get_or_create_user(self, user_id=None):
        """Получает или создает пользователя (аналог старого get_user)"""
        if not user_id:
            user_id = str(uuid.uuid4())[:8]
        
        user = self.get_user(user_id)
        if not user:
            user_data = {
                'user_id': user_id,
                'plan': 'free',
                'used_today': 0,
                'last_reset': date.today().isoformat(),
                'total_used': 0,
                'created_at': datetime.now().isoformat(),
                'plan_expires': None,
                'ip_address': 'Не определен'
            }
            user = self.create_user(user_data)
        
        # Сбрасываем дневной лимит если новый день
        if user.last_reset < date.today().isoformat():
            user.used_today = 0
            user.last_reset = date.today().isoformat()
            self.db.session.commit()
        
        return user

    def get_all_users(self):
        """Возвращает всех пользователей"""
        return self.User.query.all()

    def get_stats(self):
        """Возвращает статистику по пользователям"""
        users = self.get_all_users()
        total_users = len(users)
        total_analyses = sum(user.total_used for user in users)
        today_analyses = sum(user.used_today for user in users)
        
        return {
            'total_users': total_users,
            'total_analyses': total_analyses,
            'today_analyses': today_analyses
        }
        
    def can_analyze(self, user_id):
        """Проверяет может ли пользователь сделать анализ"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        # Импортируем здесь чтобы избежать циклических импортов
        from config import PLANS
        
        # Проверяем просрочку тарифа
        if user.plan != 'free' and user.plan_expires:
            from datetime import date
            if user.plan_expires < date.today().isoformat():
                user.plan = 'free'
                user.plan_expires = None
                self.db.session.commit()
        
        can_analyze = user.used_today < PLANS[user.plan]['daily_limit']
        return can_analyze

    def record_usage(self, user_id):
        """Записывает использование для пользователя"""
        user = self.get_user(user_id)
        if user:
            user.used_today += 1
            user.total_used += 1
            self.db.session.commit()

    def set_user_plan(self, user_id, plan_type):
        """Устанавливает тариф пользователю"""
        from config import PLANS
        from datetime import date, timedelta
        
        if plan_type not in PLANS:
            return {'success': False, 'error': 'Неверный тариф'}
        
        user = self.get_user(user_id)
        if not user:
            return {'success': False, 'error': 'Пользователь не найден'}
        
        user.plan = plan_type
        user.used_today = 0  # Сбрасываем дневной лимит
        
        # Устанавливаем срок действия (30 дней)
        expire_date = date.today() + timedelta(days=30)
        user.plan_expires = expire_date.isoformat()
        
        self.db.session.commit()
        
        return {
            'success': True,
            'message': f'Пользователю {user_id} выдан тариф: {PLANS[plan_type]["name"]}'
        }
        
    def record_calculator_use(self, user_id):
        """Увеличивает счетчик использования калькулятора"""
        user = self.get_user(user_id)
        if user:
            user.calculator_uses += 1
            user.last_calculator_use = datetime.now().isoformat()
            self.db.session.commit()
            return True
        return False