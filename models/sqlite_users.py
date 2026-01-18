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
    email_subscribed = db.Column(db.Boolean, default=True)  # Подписка на рассылки (по умолчанию включена)

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
            'email_verified': self.email_verified,
            'email_subscribed': self.email_subscribed
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

class Guest(db.Model):
    """Таблица для незарегистрированных пользователей (гостей)"""
    __tablename__ = 'guests'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=False, index=True)
    user_agent = db.Column(db.String(500), nullable=True)
    first_seen = db.Column(db.String(30), nullable=False)
    last_seen = db.Column(db.String(30), nullable=False)
    analyses_count = db.Column(db.Integer, default=0)
    registration_prompted = db.Column(db.Boolean, default=False)
    registered_user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'analyses_count': self.analyses_count,
            'registration_prompted': self.registration_prompted,
            'registered_user_id': self.registered_user_id
        }


class EmailCampaign(db.Model):
    """Таблица для хранения email-рассылок"""
    __tablename__ = 'email_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # Название рассылки
    subject = db.Column(db.String(500), nullable=False)  # Тема письма
    html_content = db.Column(db.Text, nullable=False)  # HTML-содержимое письма
    text_content = db.Column(db.Text, nullable=True)  # Текстовая версия
    recipient_filter = db.Column(db.String(50), nullable=False)  # Фильтр получателей: 'all', 'free', 'paid', 'verified'
    status = db.Column(db.String(20), default='draft')  # Статус: 'draft', 'sending', 'sent', 'cancelled'
    created_at = db.Column(db.String(30), nullable=False)
    sent_at = db.Column(db.String(30), nullable=True)
    created_by = db.Column(db.String(50), nullable=True)  # Кто создал (username админа)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'html_content': self.html_content,
            'text_content': self.text_content,
            'recipient_filter': self.recipient_filter,
            'status': self.status,
            'created_at': self.created_at,
            'sent_at': self.sent_at,
            'created_by': self.created_by
        }


class EmailSend(db.Model):
    """Таблица для истории отправки email-рассылок"""
    __tablename__ = 'email_sends'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaigns.id'), nullable=False)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=True)
    email = db.Column(db.String(255), nullable=False)  # Email получателя
    status = db.Column(db.String(20), default='pending')  # Статус: 'pending', 'sent', 'failed', 'bounced'
    sent_at = db.Column(db.String(30), nullable=True)
    error_message = db.Column(db.Text, nullable=True)  # Сообщение об ошибке, если была
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'user_id': self.user_id,
            'email': self.email,
            'status': self.status,
            'sent_at': self.sent_at,
            'error_message': self.error_message
        }


class SQLiteUserManager:
    """Новый менеджер для работы с SQLite"""
    
    def __init__(self, db, UserModel):
        self.db = db
        self.User = UserModel
        from models.sqlite_users import Guest
        self.Guest = Guest

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
        # ВАЖНО: Всегда получаем свежие данные из БД
        # Используем expire_all() чтобы очистить кеш сессии перед запросом
        self.db.session.expire_all()
        
        # Прямой запрос к БД для получения актуальных данных
        user = self.User.query.filter_by(user_id=user_id).first()
        
        # Если пользователь найден, принудительно обновляем его данные из БД
        if user:
            try:
                # Принудительно обновляем данные из БД для этого объекта
                self.db.session.refresh(user)
            except Exception as e:
                logger.debug(f"Refresh не сработал для {user_id}: {e}, но пользователь получен")
    
        # СБРОС ЛИМИТА: Проверяем нужно ли сбросить дневной лимит
        if user:
            from datetime import date
            today = date.today().isoformat()
            if user.last_reset < today:
                old_used_today = user.used_today
                old_last_reset = user.last_reset
                user.used_today = 0
                user.last_reset = today
                self.db.session.commit()
                logger.info(f"🔄 Сброшен дневной лимит для пользователя {user_id}: {old_last_reset} -> {today}, used_today: {old_used_today} -> 0")
    
        # Проверяем просроченный тариф
        if user and user.plan != 'free' and user.plan_expires:
            from datetime import date
            if user.plan_expires < date.today().isoformat():
                user.plan = 'free'
                user.plan_expires = None
                self.db.session.commit()
        
        # Логируем для диагностики
        if user:
            logger.info(f"🔍 get_user({user_id}): plan={user.plan}, used_today={user.used_today}, last_reset={user.last_reset}, plan_expires={user.plan_expires}")
        
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
        
        # ВАЖНО: Прямой запрос БЕЗ get_user, чтобы избежать конфликтов с expire_all()
        # Используем прямой query для получения пользователя
        user = self.User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return {'success': False, 'error': 'Пользователь не найден'}
        
        # Обновляем тариф
        user.plan = plan_type
        user.used_today = 0  # Сбрасываем дневной лимит
        
        # Устанавливаем срок действия (30 дней)
        expire_date = date.today() + timedelta(days=30)
        user.plan_expires = expire_date.isoformat()
        
        # Сохраняем изменения в БД
        self.db.session.commit()
        
        # ВАЖНО: После commit() проверяем что данные действительно записались в БД
        # Делаем новый прямой запрос к БД, чтобы убедиться что изменения применены
        self.db.session.expire(user)  # Удаляем объект из кеша сессии
        
        # Проверяем что изменения действительно записались
        verify_user = self.User.query.filter_by(user_id=user_id).first()
        if verify_user and verify_user.plan == plan_type:
            logger.info(f"✅ Тариф изменен для {user_id}: {plan_type}, expire_date={expire_date.isoformat()}, проверка БД: OK")
        else:
            logger.error(f"❌ ОШИБКА: Тариф НЕ записался в БД для {user_id}! Ожидался {plan_type}, получен {verify_user.plan if verify_user else 'None'}")
        
        logger.info(f"✅ Тариф изменен для {user_id}: {plan_type}, expire_date={expire_date.isoformat()}, commit выполнен")
        
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
    
    def get_or_create_guest(self, ip_address, user_agent=None):
        """Получает или создает гостя по IP адресу"""
        from models.sqlite_users import Guest
        
        # Ищем существующего гостя по IP
        guest = Guest.query.filter_by(ip_address=ip_address, registered_user_id=None).first()
        
        if not guest:
            # Создаем нового гостя
            now = datetime.now().isoformat()
            guest = Guest(
                ip_address=ip_address,
                user_agent=user_agent or 'Не определен',
                first_seen=now,
                last_seen=now,
                analyses_count=0,
                registration_prompted=False,
                registered_user_id=None
            )
            self.db.session.add(guest)
            self.db.session.commit()
            logger.info(f"👤 Создан новый гость: IP={ip_address}")
        else:
            # Обновляем last_seen
            guest.last_seen = datetime.now().isoformat()
            self.db.session.commit()
        
        return guest
    
    def record_guest_analysis(self, ip_address, user_agent=None):
        """Записывает анализ для гостя"""
        guest = self.get_or_create_guest(ip_address, user_agent)
        
        # Увеличиваем счетчик анализов только если гость существует
        old_count = guest.analyses_count
        guest.analyses_count += 1
        guest.last_seen = datetime.now().isoformat()
        
        # Если это первый анализ, сбрасываем флаг registration_prompted (если был установлен ранее по ошибке)
        if guest.analyses_count == 1:
            guest.registration_prompted = False
        
        self.db.session.commit()
        logger.info(f"📊 Записан анализ для гостя: IP={ip_address}, анализов было={old_count}, стало={guest.analyses_count}, registration_prompted={guest.registration_prompted}")
        return guest
    
    def link_guest_to_user(self, ip_address, user_id):
        """Связывает гостя с зарегистрированным пользователем"""
        from models.sqlite_users import Guest
        
        # Ищем всех гостей с этим IP, которые еще не зарегистрированы
        guests = Guest.query.filter_by(ip_address=ip_address, registered_user_id=None).all()
        
        for guest in guests:
            guest.registered_user_id = user_id
            guest.registration_prompted = True
        
        if guests:
            self.db.session.commit()
            logger.info(f"🔗 Связано {len(guests)} гостей с пользователем {user_id} (IP={ip_address})")
            return True
        
        return False
    
    def get_analysis_history(self, user_id, limit=50):
        """Получает историю анализов пользователя"""
        from models.sqlite_users import AnalysisHistory
        
        history = AnalysisHistory.query.filter_by(user_id=user_id)\
            .order_by(AnalysisHistory.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [h.to_dict() for h in history]
    
    def get_recipients_for_campaign(self, recipient_filter='all'):
        """
        Получает список email-адресов для рассылки по фильтру
        
        Args:
            recipient_filter: 'all' - все, 'free' - только бесплатный тариф,
                            'paid' - платные тарифы, 'verified' - только верифицированные
        
        Returns:
            list: Список словарей с user_id и email
        """
        from models.sqlite_users import EmailCampaign
        
        query = self.User.query.filter(
            self.User.is_registered == True,
            self.User.email.isnot(None),
            self.User.email != '',
            self.User.email_subscribed == True  # Только подписанные
        )
        
        if recipient_filter == 'free':
            query = query.filter(self.User.plan == 'free')
        elif recipient_filter == 'paid':
            query = query.filter(self.User.plan.in_(['basic', 'premium', 'unlimited']))
        elif recipient_filter == 'verified':
            query = query.filter(self.User.email_verified == True)
        # 'all' - без дополнительных фильтров
        
        users = query.all()
        
        recipients = []
        for user in users:
            if user.email:  # Дополнительная проверка
                recipients.append({
                    'user_id': user.user_id,
                    'email': user.email,
                    'plan': user.plan,
                    'email_verified': user.email_verified
                })
        
        logger.info(f"📧 Получено {len(recipients)} получателей для фильтра '{recipient_filter}'")
        return recipients
    
    def create_email_campaign(self, name, subject, html_content, text_content, 
                             recipient_filter, created_by):
        """Создает новую email-рассылку"""
        from models.sqlite_users import EmailCampaign
        
        campaign = EmailCampaign(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            recipient_filter=recipient_filter,
            status='draft',
            created_at=datetime.now().isoformat(),
            created_by=created_by
        )
        
        self.db.session.add(campaign)
        self.db.session.commit()
        
        logger.info(f"📝 Создана рассылка: {name} (ID: {campaign.id})")
        return campaign
    
    def get_email_campaigns(self, limit=50):
        """Получает список всех рассылок"""
        from models.sqlite_users import EmailCampaign
        
        campaigns = EmailCampaign.query.order_by(
            EmailCampaign.created_at.desc()
        ).limit(limit).all()
        
        return [c.to_dict() for c in campaigns]
    
    def get_email_campaign(self, campaign_id):
        """Получает рассылку по ID"""
        from models.sqlite_users import EmailCampaign
        
        return EmailCampaign.query.filter_by(id=campaign_id).first()
    
    def create_email_send(self, campaign_id, user_id, email, status='pending'):
        """Создает запись об отправке email"""
        from models.sqlite_users import EmailSend
        
        email_send = EmailSend(
            campaign_id=campaign_id,
            user_id=user_id,
            email=email,
            status=status,
            sent_at=datetime.now().isoformat() if status == 'sent' else None
        )
        
        self.db.session.add(email_send)
        self.db.session.commit()
        
        return email_send
    
    def update_email_send_status(self, email_send_id, status, error_message=None):
        """Обновляет статус отправки email"""
        from models.sqlite_users import EmailSend
        
        email_send = EmailSend.query.filter_by(id=email_send_id).first()
        if email_send:
            email_send.status = status
            if status == 'sent':
                email_send.sent_at = datetime.now().isoformat()
            if error_message:
                email_send.error_message = error_message
            self.db.session.commit()
            return True
        return False
    
    def get_campaign_stats(self, campaign_id):
        """Получает статистику по рассылке"""
        from models.sqlite_users import EmailSend
        
        total = EmailSend.query.filter_by(campaign_id=campaign_id).count()
        sent = EmailSend.query.filter_by(campaign_id=campaign_id, status='sent').count()
        failed = EmailSend.query.filter_by(campaign_id=campaign_id, status='failed').count()
        pending = EmailSend.query.filter_by(campaign_id=campaign_id, status='pending').count()
        
        return {
            'total': total,
            'sent': sent,
            'failed': failed,
            'pending': pending,
            'success_rate': (sent / total * 100) if total > 0 else 0
        }
