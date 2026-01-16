from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import uuid
import logging

logger = logging.getLogger(__name__)

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
    
    # Новые поля для регистрации и авторизации
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    is_registered = db.Column(db.Boolean, default=False)
    free_analysis_used = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    verification_token_expires = db.Column(db.String(30), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.String(30), nullable=True)

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
            'last_calculator_use': self.last_calculator_use,
            'email': self.email,
            'is_registered': self.is_registered,
            'free_analysis_used': self.free_analysis_used,
            'email_verified': self.email_verified
        }

class AnalysisHistory(db.Model):
    __tablename__ = 'analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(50), nullable=True)
    document_type_name = db.Column(db.String(100), nullable=True)
    risk_level = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.String(30), nullable=False)
    analysis_summary = db.Column(db.Text, nullable=True)  # Краткое резюме для отображения
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'document_type': self.document_type,
            'document_type_name': self.document_type_name,
            'risk_level': self.risk_level,
            'created_at': self.created_at,
            'analysis_summary': self.analysis_summary
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
        """Получает пользователя по ID с проверкой тарифа"""
        user = self.User.query.filter_by(user_id=user_id).first()
    
        # Проверяем просроченный тариф
        if user and user.plan != 'free' and user.plan_expires:
            from datetime import date
            if user.plan_expires < date.today().isoformat():
                user.plan = 'free'
                user.plan_expires = None
                self.db.session.commit()
    
        return user

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
        users = self.User.query.all()
        
        # Проверяем просроченные тарифы
        from datetime import date
        expired_found = False
        
        for user in users:
            if user.plan != 'free' and user.plan_expires:
                if user.plan_expires < date.today().isoformat():
                    user.plan = 'free'
                    user.plan_expires = None
                    expired_found = True
        
        if expired_found:
            self.db.session.commit()
        
        return users

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
        
    def get_calculator_stats(self):
        """Возвращает статистику по использованию калькулятора"""
        users = self.get_all_users()
        
        total_calculator_uses = sum(user.calculator_uses for user in users)
        users_with_calculator_use = sum(1 for user in users if user.calculator_uses > 0)
        
        # Пользователи с наибольшим использованием
        top_users = sorted(
            [(user.user_id, user.calculator_uses, user.last_calculator_use) 
             for user in users if user.calculator_uses > 0],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_calculator_uses': total_calculator_uses,
            'users_with_calculator_use': users_with_calculator_use,
            'total_users': len(users),
            'top_users': top_users
        }
    
    def get_user_by_email(self, email):
        """Получает пользователя по email"""
        return self.User.query.filter_by(email=email).first()
    
    def mark_free_analysis_used(self, user_id):
        """Отмечает что бесплатный анализ использован"""
        user = self.get_user(user_id)
        if user:
            user.free_analysis_used = True
            self.db.session.commit()
            return True
        return False
    
    def save_analysis_history(self, user_id, filename, analysis_result):
        """Сохраняет историю анализа"""
        from models.sqlite_users import AnalysisHistory
        
        try:
            summary = analysis_result.get('executive_summary', {})
            risk_level = summary.get('risk_level', 'UNKNOWN')
            doc_type = analysis_result.get('document_type', 'general')
            doc_type_name = analysis_result.get('document_type_name', 'Общий документ')
            
            # Создаем краткое резюме
            risk_desc = summary.get('risk_description', '')
            if len(risk_desc) > 200:
                risk_desc = risk_desc[:200] + '...'
            
            history = AnalysisHistory(
                user_id=user_id,
                filename=filename,
                document_type=doc_type,
                document_type_name=doc_type_name,
                risk_level=risk_level,
                created_at=datetime.now().isoformat(),
                analysis_summary=risk_desc
            )
            
            self.db.session.add(history)
            self.db.session.commit()
            
            return history
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения истории анализа: {e}")
            self.db.session.rollback()
            return None
    
    def get_analysis_history(self, user_id, limit=50):
        """Получает историю анализов пользователя"""
        from models.sqlite_users import AnalysisHistory
        
        history = AnalysisHistory.query.filter_by(user_id=user_id)\
            .order_by(AnalysisHistory.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [h.to_dict() for h in history]
