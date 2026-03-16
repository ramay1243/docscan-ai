from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from calendar import monthrange
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
    available_analyses = db.Column(db.Integer, default=0)  # Количество доступных анализов (для разовых тарифов)
    ip_address = db.Column(db.String(50), default='Не определен')
    calculator_uses = db.Column(db.Integer, default=0)
    last_calculator_use = db.Column(db.String(30), nullable=True)
    last_login_at = db.Column(db.String(30), nullable=True)  # Последний вход в аккаунт (ISO datetime)
    
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
    referral_code = db.Column(db.String(20), nullable=True, unique=True)  # Уникальный реферальный код
    referrer_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=True)  # Кто пригласил этого пользователя
    payment_details = db.Column(db.Text, nullable=True)  # Реквизиты для получения выплат (JSON)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'plan': self.plan,
            'used_today': self.used_today,
            'last_reset': self.last_reset,
            'total_used': self.total_used,
            'created_at': self.created_at,
            'plan_expires': self.plan_expires,
            'available_analyses': self.available_analyses,
            'ip_address': self.ip_address,
            'calculator_uses': self.calculator_uses,
            'last_calculator_use': self.last_calculator_use,
            'last_login_at': self.last_login_at,
            'email': self.email,
            'is_registered': self.is_registered,
            'free_analysis_used': self.free_analysis_used,
            'email_verified': self.email_verified,
            'email_subscribed': self.email_subscribed,
            'referral_code': self.referral_code,
            'referrer_id': self.referrer_id,
            'payment_details': self.payment_details
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
    calculator_uses = db.Column(db.Integer, default=0)
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
            'calculator_uses': self.calculator_uses,
            'registration_prompted': self.registration_prompted,
            'registered_user_id': self.registered_user_id
        }


class SearchBot(db.Model):
    """Таблица для хранения поисковых ботов"""
    __tablename__ = 'search_bots'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=False, index=True)
    user_agent = db.Column(db.String(500), nullable=True)
    bot_type = db.Column(db.String(50), nullable=False)  # YandexBot, Googlebot и т.д.
    first_seen = db.Column(db.String(30), nullable=False)
    last_seen = db.Column(db.String(30), nullable=False)
    visits_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'bot_type': self.bot_type,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'visits_count': self.visits_count
        }


class NewsItem(db.Model):
    """Таблица для хранения новостей"""
    __tablename__ = 'news_items'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False)  # 'updates' или 'news'
    title = db.Column(db.String(500), nullable=False)  # Заголовок новости
    description = db.Column(db.Text, nullable=False)  # Описание/текст новости
    date = db.Column(db.String(30), nullable=False)  # Дата публикации
    link = db.Column(db.String(500), nullable=True)  # Опциональная ссылка
    link_text = db.Column(db.String(100), nullable=True)  # Текст ссылки
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания записи
    updated_at = db.Column(db.String(30), nullable=True)  # Дата последнего обновления
    created_by = db.Column(db.String(50), nullable=True)  # Кто создал (username админа)
    full_news_id = db.Column(db.Integer, db.ForeignKey('full_news.id'), nullable=True)  # Связь с полной новостью
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'link': self.link,
            'link_text': self.link_text,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'created_by': self.created_by,
            'full_news_id': self.full_news_id
        }


class FullNews(db.Model):
    """Таблица для хранения полных новостей (статей)"""
    __tablename__ = 'full_news'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), unique=True, nullable=False)  # URL-адрес новости
    title = db.Column(db.String(500), nullable=False)  # Заголовок
    short_description = db.Column(db.Text, nullable=False)  # Краткое описание для карточки
    full_content = db.Column(db.Text, nullable=False)  # Полный HTML-контент
    category = db.Column(db.String(50), nullable=True)  # Категория (Недвижимость, Финансы, и т.д.)
    image_url = db.Column(db.String(500), nullable=True)  # URL изображения обложки
    author = db.Column(db.String(100), nullable=True, default='Редакция DocScan')  # Автор
    meta_title = db.Column(db.String(200), nullable=True)  # Meta title для SEO
    meta_description = db.Column(db.String(500), nullable=True)  # Meta description для SEO
    meta_keywords = db.Column(db.String(300), nullable=True)  # Meta keywords для SEO
    published_at = db.Column(db.String(30), nullable=False)  # Дата публикации
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания записи
    updated_at = db.Column(db.String(30), nullable=True)  # Дата последнего обновления
    is_published = db.Column(db.Boolean, default=True)  # Опубликовано или черновик
    views_count = db.Column(db.Integer, default=0)  # Количество просмотров
    created_by = db.Column(db.String(50), nullable=True)  # Кто создал (username админа)
    
    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'short_description': self.short_description,
            'full_content': self.full_content,
            'category': self.category,
            'image_url': self.image_url,
            'author': self.author,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'published_at': self.published_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_published': self.is_published,
            'views_count': self.views_count,
            'created_by': self.created_by
        }


class Question(db.Model):
    """Таблица для хранения вопросов пользователей"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Договоры, Трудовое право, Недвижимость и т.д.
    status = db.Column(db.String(20), default='open')  # open, answered, solved, closed
    views_count = db.Column(db.Integer, default=0)
    answers_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.String(30), nullable=False)
    updated_at = db.Column(db.String(30), nullable=True)
    best_answer_id = db.Column(db.Integer, nullable=True)  # ID лучшего ответа
    
    def to_dict(self):
        # Подсчитываем реальное количество ответов
        answers_count = len(self.answers) if hasattr(self, 'answers') and self.answers else self.answers_count
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'status': self.status,
            'views_count': self.views_count,
            'answers_count': answers_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'best_answer_id': self.best_answer_id,
            'author_email': self.user.email if hasattr(self, 'user') and self.user else 'Неизвестно'
        }


class Answer(db.Model):
    """Таблица для хранения ответов на вопросы"""
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_best = db.Column(db.Boolean, default=False)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.String(30), nullable=False)
    updated_at = db.Column(db.String(30), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'user_id': self.user_id,
            'content': self.content,
            'is_best': self.is_best,
            'likes_count': self.likes_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class AnswerLike(db.Model):
    """Таблица для хранения лайков ответов"""
    __tablename__ = 'answer_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=False)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.String(30), nullable=False)
    
    # Уникальный индекс для предотвращения двойных лайков
    __table_args__ = (db.UniqueConstraint('answer_id', 'user_id', name='unique_answer_like'),)


class Notification(db.Model):
    """Таблица для хранения уведомлений пользователей"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)  # 'answer', 'like', 'best_answer'
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=True)
    title = db.Column(db.String(500), nullable=False)
    message = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(500), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.String(30), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'question_id': self.question_id,
            'answer_id': self.answer_id,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at
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
    recipient_list = db.Column(db.Text, nullable=True)  # JSON список получателей для ручного выбора
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
            'recipient_list': self.recipient_list,
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


class Article(db.Model):
    """Таблица для хранения статей блога"""
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)  # Заголовок статьи
    slug = db.Column(db.String(500), unique=True, nullable=False, index=True)  # URL-адрес статьи (уникальный)
    description = db.Column(db.Text, nullable=True)  # Краткое описание для карточки
    icon = db.Column(db.String(10), nullable=True)  # Иконка/эмодзи (например, 🏠)
    html_content = db.Column(db.Text, nullable=False)  # HTML-содержимое статьи
    meta_keywords = db.Column(db.String(500), nullable=True)  # SEO ключевые слова
    meta_description = db.Column(db.String(500), nullable=True)  # SEO описание
    status = db.Column(db.String(20), default='draft')  # Статус: 'draft', 'published', 'archived'
    created_at = db.Column(db.String(30), nullable=False)
    published_at = db.Column(db.String(30), nullable=True)  # Дата публикации
    updated_at = db.Column(db.String(30), nullable=True)  # Дата последнего обновления
    author = db.Column(db.String(50), nullable=True)  # Автор (admin username)
    views_count = db.Column(db.Integer, default=0)  # Количество просмотров
    category = db.Column(db.String(100), nullable=True)  # Категория статьи (опционально)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'icon': self.icon,
            'html_content': self.html_content,
            'meta_keywords': self.meta_keywords,
            'meta_description': self.meta_description,
            'status': self.status,
            'created_at': self.created_at,
            'published_at': self.published_at,
            'updated_at': self.updated_at,
            'author': self.author,
            'views_count': self.views_count,
            'category': self.category
        }


class Payment(db.Model):
    """Таблица для хранения платежей"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)
    email = db.Column(db.String(255), nullable=True)  # Email пользователя на момент оплаты
    plan_type = db.Column(db.String(20), nullable=False)  # Тип тарифа: 'basic', 'premium', etc.
    amount = db.Column(db.Float, nullable=False)  # Сумма платежа (фактически оплаченная)
    currency = db.Column(db.String(10), default='RUB')  # Валюта
    provider = db.Column(db.String(50), default='yoomoney')  # Платежный провайдер
    status = db.Column(db.String(20), default='success')  # Статус: 'success', 'failed', 'refund'
    operation_id = db.Column(db.String(100), nullable=True)  # ID операции от провайдера
    label = db.Column(db.String(100), nullable=True)  # Метка платежа (user_id_plan)
    created_at = db.Column(db.String(30), nullable=False)  # Дата и время платежа
    raw_data = db.Column(db.Text, nullable=True)  # Сырые данные webhook (JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'plan_type': self.plan_type,
            'amount': self.amount,
            'currency': self.currency,
            'provider': self.provider,
            'status': self.status,
            'operation_id': self.operation_id,
            'label': self.label,
            'created_at': self.created_at,
            'raw_data': self.raw_data
        }

class Referral(db.Model):
    """Таблица для хранения приглашений (рефералов)"""
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)  # Кто пригласил
    invited_user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)  # Кого пригласили
    created_at = db.Column(db.String(30), nullable=False)  # Дата приглашения
    registered_at = db.Column(db.String(30), nullable=True)  # Дата регистрации приглашенного
    
    def to_dict(self):
        return {
            'id': self.id,
            'referrer_id': self.referrer_id,
            'invited_user_id': self.invited_user_id,
            'created_at': self.created_at,
            'registered_at': self.registered_at
        }

class ReferralReward(db.Model):
    """Таблица для хранения вознаграждений партнеров"""
    __tablename__ = 'referral_rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)  # Кто пригласил (партнер)
    invited_user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)  # Кого пригласили
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=True)  # ID платежа приглашенного
    purchase_amount = db.Column(db.Float, nullable=False)  # Сумма покупки приглашенного
    reward_amount = db.Column(db.Float, nullable=False)  # 15% к выплате
    reward_percent = db.Column(db.Float, default=15.0)  # Процент вознаграждения
    status = db.Column(db.String(20), default='pending')  # 'pending' (ожидает) / 'paid' (выплачено)
    paid_at = db.Column(db.String(30), nullable=True)  # Дата выплаты
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания записи
    notes = db.Column(db.Text, nullable=True)  # Заметки админа
    
    def to_dict(self):
        return {
            'id': self.id,
            'partner_id': self.partner_id,
            'invited_user_id': self.invited_user_id,
            'payment_id': self.payment_id,
            'purchase_amount': self.purchase_amount,
            'reward_amount': self.reward_amount,
            'reward_percent': self.reward_percent,
            'status': self.status,
            'paid_at': self.paid_at,
            'created_at': self.created_at,
            'notes': self.notes
        }

class WhitelistedIP(db.Model):
    """Таблица для хранения белого списка IP-адресов для бизнес-тарифов"""
    __tablename__ = 'whitelisted_ips'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)  # Пользователь, которому разрешен IP
    ip_address = db.Column(db.String(50), nullable=False)  # IP-адрес или диапазон (например, 192.168.1.0/24)
    description = db.Column(db.String(255), nullable=True)  # Описание (например, "Офис в Москве")
    is_active = db.Column(db.Boolean, default=True)  # Активен ли IP
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания
    created_by = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=True)  # Кто добавил (админ)
    notes = db.Column(db.Text, nullable=True)  # Заметки
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'created_by': self.created_by,
            'notes': self.notes
        }

class BrandingSettings(db.Model):
    """Таблица для хранения настроек кастомного брендинга для пользователей"""
    __tablename__ = 'branding_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False, unique=True)  # Пользователь (один брендинг на пользователя)
    logo_path = db.Column(db.String(500), nullable=True)  # Путь к файлу логотипа
    primary_color = db.Column(db.String(7), default='#4361ee')  # Основной цвет (hex, например #4361ee)
    secondary_color = db.Column(db.String(7), default='#764ba2')  # Вторичный цвет (hex)
    company_name = db.Column(db.String(255), nullable=True)  # Название компании (для отображения в отчетах)
    is_active = db.Column(db.Boolean, default=True)  # Активен ли брендинг
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания
    updated_at = db.Column(db.String(30), nullable=True)  # Дата обновления
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'logo_path': self.logo_path,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'company_name': self.company_name,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class APIKey(db.Model):
    """Таблица для хранения API-ключей для бизнес-пользователей"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)  # Пользователь, которому принадлежит ключ
    api_key = db.Column(db.String(64), unique=True, nullable=False, index=True)  # Сам API-ключ (хеш)
    api_key_hash = db.Column(db.String(128), nullable=False)  # Хеш ключа для проверки
    name = db.Column(db.String(255), nullable=True)  # Название ключа (для удобства управления)
    is_active = db.Column(db.Boolean, default=True)  # Активен ли ключ
    last_used = db.Column(db.String(30), nullable=True)  # Дата последнего использования
    requests_count = db.Column(db.Integer, default=0)  # Количество запросов через этот ключ
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания
    expires_at = db.Column(db.String(30), nullable=True)  # Дата истечения (опционально)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'api_key': self.api_key[:8] + '...' + self.api_key[-4:] if len(self.api_key) > 12 else '***',  # Показываем только часть ключа
            'name': self.name,
            'is_active': self.is_active,
            'last_used': self.last_used,
            'requests_count': self.requests_count,
            'created_at': self.created_at,
            'expires_at': self.expires_at
        }

class AnalysisSettings(db.Model):
    """Таблица для хранения настроек анализа документов для бизнес-пользователей"""
    __tablename__ = 'analysis_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False, unique=True)  # Пользователь (одни настройки на пользователя)
    
    # Приоритеты областей экспертизы (1-10)
    legal_priority = db.Column(db.Integer, default=5)  # Приоритет юридической экспертизы
    financial_priority = db.Column(db.Integer, default=5)  # Приоритет финансового анализа
    operational_priority = db.Column(db.Integer, default=5)  # Приоритет операционных рисков
    strategic_priority = db.Column(db.Integer, default=5)  # Приоритет стратегической оценки
    
    # Уровень детализации: 'brief', 'standard', 'detailed'
    detail_level = db.Column(db.String(20), default='standard')  # Уровень детализации
    
    # Кастомные проверки (JSON строка с массивом критериев)
    custom_checks = db.Column(db.Text, nullable=True)  # JSON: ["критерий 1", "критерий 2"]
    
    # Активный шаблон (если используется)
    active_template = db.Column(db.String(255), nullable=True)  # Название активного шаблона
    
    # Использовать настройки по умолчанию
    use_default = db.Column(db.Boolean, default=True)  # Использовать настройки по умолчанию
    
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания
    updated_at = db.Column(db.String(30), nullable=True)  # Дата обновления
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'legal_priority': self.legal_priority,
            'financial_priority': self.financial_priority,
            'operational_priority': self.operational_priority,
            'strategic_priority': self.strategic_priority,
            'detail_level': self.detail_level,
            'custom_checks': json.loads(self.custom_checks) if self.custom_checks else [],
            'active_template': self.active_template,
            'use_default': self.use_default,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class AnalysisTemplate(db.Model):
    """Таблица для хранения шаблонов настроек анализа"""
    __tablename__ = 'analysis_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)  # Владелец шаблона
    name = db.Column(db.String(255), nullable=False)  # Название шаблона
    
    # Приоритеты областей экспертизы
    legal_priority = db.Column(db.Integer, default=5)
    financial_priority = db.Column(db.Integer, default=5)
    operational_priority = db.Column(db.Integer, default=5)
    strategic_priority = db.Column(db.Integer, default=5)
    
    # Уровень детализации
    detail_level = db.Column(db.String(20), default='standard')
    
    # Кастомные проверки
    custom_checks = db.Column(db.Text, nullable=True)  # JSON
    
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'legal_priority': self.legal_priority,
            'financial_priority': self.financial_priority,
            'operational_priority': self.operational_priority,
            'strategic_priority': self.strategic_priority,
            'detail_level': self.detail_level,
            'custom_checks': json.loads(self.custom_checks) if self.custom_checks else [],
            'created_at': self.created_at
        }

class BatchProcessingTask(db.Model):
    """Таблица для отслеживания пакетных задач обработки документов"""
    __tablename__ = 'batch_processing_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)  # Пользователь
    task_name = db.Column(db.String(255), nullable=True)  # Название задачи (опционально)
    
    # Статус задачи: 'pending', 'processing', 'completed', 'failed', 'cancelled'
    status = db.Column(db.String(20), default='pending')
    
    # Прогресс обработки
    total_files = db.Column(db.Integer, default=0)  # Всего файлов
    processed_files = db.Column(db.Integer, default=0)  # Обработано файлов
    failed_files = db.Column(db.Integer, default=0)  # Файлов с ошибками
    
    # Результаты
    results_json = db.Column(db.Text, nullable=True)  # JSON с результатами всех анализов
    summary_report_path = db.Column(db.String(500), nullable=True)  # Путь к сводному отчету (PDF)
    
    # Метаданные
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания
    started_at = db.Column(db.String(30), nullable=True)  # Дата начала обработки
    completed_at = db.Column(db.String(30), nullable=True)  # Дата завершения
    error_message = db.Column(db.Text, nullable=True)  # Сообщение об ошибке (если есть)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_name': self.task_name,
            'status': self.status,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'results': json.loads(self.results_json) if self.results_json else [],
            'summary_report_path': self.summary_report_path,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error_message': self.error_message,
            'progress_percent': int((self.processed_files / self.total_files * 100)) if self.total_files > 0 else 0
        }

class BatchProcessingFile(db.Model):
    """Таблица для отслеживания отдельных файлов в пакетной задаче"""
    __tablename__ = 'batch_processing_files'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('batch_processing_tasks.id'), nullable=False)  # Задача
    filename = db.Column(db.String(255), nullable=False)  # Имя файла
    file_path = db.Column(db.String(500), nullable=True)  # Путь к файлу (временный)
    
    # Статус обработки: 'pending', 'processing', 'completed', 'failed'
    status = db.Column(db.String(20), default='pending')
    
    # Результаты анализа
    analysis_result_json = db.Column(db.Text, nullable=True)  # JSON с результатом анализа
    analysis_history_id = db.Column(db.Integer, db.ForeignKey('analysis_history.id'), nullable=True)  # Связь с историей
    full_report_path = db.Column(db.String(500), nullable=True)  # Путь к полному отчету (PDF)
    
    # Метаданные
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания
    processed_at = db.Column(db.String(30), nullable=True)  # Дата обработки
    error_message = db.Column(db.Text, nullable=True)  # Сообщение об ошибке
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'task_id': self.task_id,
            'filename': self.filename,
            'status': self.status,
            'analysis_result': json.loads(self.analysis_result_json) if self.analysis_result_json else None,
            'full_report_path': self.full_report_path,  # Путь к полному PDF отчету
            'created_at': self.created_at,
            'processed_at': self.processed_at,
            'error_message': self.error_message
        }


class DocumentComparison(db.Model):
    """Таблица для хранения сравнений документов"""
    __tablename__ = 'document_comparisons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)  # Пользователь
    
    # Файлы для сравнения
    original_filename = db.Column(db.String(255), nullable=False)  # Имя оригинального файла
    original_file_path = db.Column(db.String(500), nullable=True)  # Путь к оригинальному файлу
    modified_filename = db.Column(db.String(255), nullable=False)  # Имя измененного файла
    modified_file_path = db.Column(db.String(500), nullable=True)  # Путь к измененному файлу
    
    # Результаты сравнения
    comparison_result_json = db.Column(db.Text, nullable=True)  # JSON с различиями
    risk_analysis_json = db.Column(db.Text, nullable=True)  # JSON с анализом рисков от AI
    report_path = db.Column(db.String(500), nullable=True)  # Путь к отчету (PDF/HTML)
    
    # Статус обработки: 'pending', 'processing', 'completed', 'failed'
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text, nullable=True)  # Сообщение об ошибке
    
    # Метаданные
    created_at = db.Column(db.String(30), nullable=False)  # Дата создания
    completed_at = db.Column(db.String(30), nullable=True)  # Дата завершения
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'modified_filename': self.modified_filename,
            'status': self.status,
            'comparison_result': json.loads(self.comparison_result_json) if self.comparison_result_json else None,
            'risk_analysis': json.loads(self.risk_analysis_json) if self.risk_analysis_json else None,
            'report_path': self.report_path,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'error_message': self.error_message
        }

class ChatMessage(db.Model):
    """Таблица для хранения сообщений юридического чата"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(8), db.ForeignKey('users.user_id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    is_legal = db.Column(db.Boolean, default=True)  # Является ли вопрос юридическим
    created_at = db.Column(db.String(30), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question': self.question,
            'answer': self.answer,
            'is_legal': self.is_legal,
            'created_at': self.created_at
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
            available_analyses=user_data.get('available_analyses', 0),
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
    
        # Для бесплатного тарифа НЕ сбрасываем счетчик (используется free_analysis_used - один раз навсегда)
        # Сброс счетчика убран, т.к. бесплатный анализ дается только один раз после регистрации
    
        # Проверяем просроченный тариф
        if user and user.plan != 'free' and user.plan_expires:
            from datetime import date
            if user.plan_expires < date.today().isoformat():
                user.plan = 'free'
                user.plan_expires = None
                self.db.session.commit()
        
        # Логируем для диагностики
        if user:
            logger.info(f"🔍 get_user({user_id}): plan={user.plan}, used_today={user.used_today}, last_reset={user.last_reset}, available_analyses={user.available_analyses}")
        
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
                'available_analyses': 0,
                'ip_address': 'Не определен'
            }
            user = self.create_user(user_data)
        
        # Для бесплатного тарифа НЕ сбрасываем счетчик (используется free_analysis_used - один раз навсегда)
        # Сброс убран, т.к. бесплатный анализ дается только один раз после регистрации
        
        return user

    def get_all_users(self):
        """Возвращает всех пользователей, отсортированных по дате создания (новые сначала)"""
        # Сортируем по created_at в порядке убывания (новые сначала)
        users = self.User.query.order_by(self.User.created_at.desc()).all()
        
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
        """Возвращает статистику по пользователям и гостям"""
        from models.sqlite_users import Guest, AnalysisHistory
        from datetime import datetime, date
        
        users = self.get_all_users()
        total_users = len(users)
        
        # Анализы зарегистрированных пользователей (общее количество)
        registered_analyses = sum(user.total_used for user in users)
        
        # ТОЧНЫЙ подсчет анализов за сегодня через AnalysisHistory
        today = date.today().isoformat()
        today_registered_analyses = AnalysisHistory.query.filter(
            AnalysisHistory.created_at.like(f'{today}%')
        ).count()
        
        # Анализы гостей (незарегистрированных пользователей)
        guests = Guest.query.all()
        total_guest_analyses = sum(guest.analyses_count for guest in guests)
        
        # Анализы гостей за сегодня (если last_seen сегодня, считаем что был анализ)
        today_guest_analyses = 0
        for guest in guests:
            if guest.last_seen and guest.last_seen[:10] == today:
                # Если последний визит сегодня, считаем что был хотя бы 1 анализ сегодня
                # (но не больше чем analyses_count)
                today_guest_analyses += min(1, guest.analyses_count)
        
        # Общая статистика
        total_analyses = registered_analyses + total_guest_analyses
        today_analyses = today_registered_analyses + today_guest_analyses
        
        return {
            'total_users': total_users,
            'total_analyses': total_analyses,
            'today_analyses': today_analyses,
            'registered_analyses': registered_analyses,
            'guest_analyses': total_guest_analyses
        }
        
    def can_analyze(self, user_id):
        """Проверяет может ли пользователь сделать анализ"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        # Импортируем здесь чтобы избежать циклических импортов
        from config import PLANS
        
        # Для бесплатного тарифа проверяем free_analysis_used (один анализ навсегда)
        if user.plan == 'free':
            # Пользователь может сделать анализ только если еще не использовал бесплатный анализ
            can_analyze = not user.free_analysis_used
            return can_analyze
        
        # Для платных тарифов проверяем available_analyses
        if user.available_analyses is None:
            user.available_analyses = 0
            self.db.session.commit()
        
        # Безлимит: available_analyses == -1 означает, что лимита по анализам нет
        if user.available_analyses == -1:
            return True
        
        # Пользователь может анализировать, если у него есть доступные анализы
        return user.available_analyses > 0

    def record_usage(self, user_id):
        """Записывает использование для пользователя"""
        user = self.get_user(user_id)
        if user:
            user.total_used += 1
            
            # Для бесплатного тарифа отмечаем что бесплатный анализ использован
            if user.plan == 'free':
                user.free_analysis_used = True
                logger.info(f"📊 Бесплатный анализ использован для пользователя {user_id}. Дальше доступна только покупка тарифа.")
            else:
                # Для платных тарифов уменьшаем счетчик доступных анализов
                if user.available_analyses is not None and user.available_analyses > 0:
                    user.available_analyses -= 1
                    logger.info(f"📊 Использован анализ для {user_id} (платный тариф). Осталось: {user.available_analyses}")
                    # Если анализы закончились, переводим на бесплатный тариф
                    if user.available_analyses <= 0:
                        user.plan = 'free'
                        user.available_analyses = 0
                        logger.info(f"📊 У пользователя {user_id} закончились анализы, переведен на бесплатный тариф")
            
            self.db.session.commit()

    def set_user_plan(self, user_id, plan_type):
        """Устанавливает тариф пользователю и добавляет анализы к балансу"""
        from config import PLANS
        
        if plan_type not in PLANS:
            return {'success': False, 'error': 'Неверный тариф'}
        
        # ВАЖНО: Прямой запрос БЕЗ get_user, чтобы избежать конфликтов с expire_all()
        # Используем прямой query для получения пользователя
        user = self.User.query.filter_by(user_id=user_id).first()
        
        if not user:
            return {'success': False, 'error': 'Пользователь не найден'}
        
        # Получаем количество анализов из тарифа
        analyses_to_add = PLANS[plan_type].get('analyses_count', 0)
        
        # Для бесплатного тарифа не добавляем анализы (он работает по free_analysis_used - один раз навсегда)
        if plan_type == 'free':
            user.plan = plan_type
            user.plan_expires = None
            user.available_analyses = 0
            # free_analysis_used НЕ сбрасываем - если пользователь уже использовал бесплатный анализ, он остается использованным
            # used_today не используется для бесплатного тарифа (используется free_analysis_used)
        elif plan_type in ['standard', 'premium']:
            # Для разовых тарифов (физлица): добавляем анализы и устанавливаем срок действия
            if user.available_analyses is None:
                user.available_analyses = 0
            user.available_analyses += analyses_to_add
            user.plan = plan_type
            # Устанавливаем срок действия
            validity_days = PLANS[plan_type].get('validity_days', 30)
            user.plan_expires = (date.today() + timedelta(days=validity_days)).isoformat()
        elif plan_type.startswith('business_'):
            # Для бизнес-тарифов (месячная подписка): устанавливаем месячный лимит
            user.plan = plan_type
            if analyses_to_add == -1:
                # Безлимит
                user.available_analyses = -1
            else:
                user.available_analyses = analyses_to_add
            # Устанавливаем срок действия до конца текущего месяца (или следующего, если выдаем в начале месяца)
            today = date.today()
            # Если сегодня 1-е число, устанавливаем на конец следующего месяца, иначе - конец текущего
            if today.day == 1:
                # Следующий месяц
                if today.month == 12:
                    next_month = date(today.year + 1, 1, 1)
                else:
                    next_month = date(today.year, today.month + 1, 1)
                # Последний день следующего месяца
                last_day = monthrange(next_month.year, next_month.month)[1]
                user.plan_expires = date(next_month.year, next_month.month, last_day).isoformat()
            else:
                # Конец текущего месяца
                last_day = monthrange(today.year, today.month)[1]
                user.plan_expires = date(today.year, today.month, last_day).isoformat()
        else:
            # Для старых тарифов (basic) - оставляем для совместимости
            if user.available_analyses is None:
                user.available_analyses = 0
            user.available_analyses += analyses_to_add
            user.plan = plan_type
            user.plan_expires = None
        
        # Сохраняем изменения в БД
        self.db.session.commit()
        
        # ВАЖНО: После commit() проверяем что данные действительно записались в БД
        self.db.session.expire(user)  # Удаляем объект из кеша сессии
        
        # Проверяем что изменения действительно записались
        verify_user = self.User.query.filter_by(user_id=user_id).first()
        if verify_user:
            logger.info(f"✅ Тариф изменен для {user_id}: {plan_type}, добавлено анализов: {analyses_to_add}, всего доступно: {verify_user.available_analyses}, проверка БД: OK")
        else:
            logger.error(f"❌ ОШИБКА: Пользователь не найден после commit для {user_id}!")
        
        return {
            'success': True,
            'message': f'Пользователю {user_id} добавлено {analyses_to_add} анализов. Всего доступно: {verify_user.available_analyses if verify_user else 0}'
        }
        
    def record_calculator_use(self, user_id):
        """Увеличивает счетчик использования калькулятора"""
        if not user_id:
            logger.warning("⚠️ Попытка записать использование калькулятора без user_id")
            return False
        
        # Получаем пользователя напрямую из БД
        user = self.User.query.filter_by(user_id=user_id).first()
        if user:
            # Обновляем счетчик
            old_count = user.calculator_uses or 0
            user.calculator_uses = old_count + 1
            user.last_calculator_use = datetime.now().isoformat()
            self.db.session.commit()
            logger.info(f"✅ Записано использование калькулятора для {user_id}: {old_count} -> {user.calculator_uses}")
            return True
        else:
            logger.warning(f"⚠️ Пользователь {user_id} не найден при попытке записать использование калькулятора")
            return False
        
    def get_calculator_stats(self):
        """Возвращает статистику по использованию калькулятора"""
        # Обновляем данные из БД перед подсчетом
        self.db.session.expire_all()
        
        # Получаем всех пользователей напрямую из БД
        users = self.User.query.all()
        
        # Обновляем данные для каждого пользователя
        for user in users:
            try:
                self.db.session.refresh(user)
            except Exception:
                pass  # Игнорируем ошибки refresh
        
        # Анализы зарегистрированных пользователей
        registered_calculator_uses = sum(user.calculator_uses or 0 for user in users)
        users_with_calculator_use = sum(1 for user in users if (user.calculator_uses or 0) > 0)
        
        # Анализы гостей (незарегистрированных пользователей)
        from models.sqlite_users import Guest
        guests = Guest.query.all()
        total_guest_calculator_uses = sum(guest.calculator_uses or 0 for guest in guests)
        
        # Общая статистика
        total_calculator_uses = registered_calculator_uses + total_guest_calculator_uses
        
        # Пользователи с наибольшим использованием
        top_users = sorted(
            [(user.user_id, user.calculator_uses or 0, user.last_calculator_use or 'Нет данных') 
             for user in users if (user.calculator_uses or 0) > 0],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        logger.info(f"📊 Статистика калькулятора: всего использований={total_calculator_uses} (пользователи: {registered_calculator_uses}, гости: {total_guest_calculator_uses}), пользователей использовали={users_with_calculator_use}/{len(users)}")
        
        return {
            'total_calculator_uses': total_calculator_uses,
            'registered_calculator_uses': registered_calculator_uses,
            'guest_calculator_uses': total_guest_calculator_uses,
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
                calculator_uses=0,
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
    
    def record_guest_calculator_use(self, ip_address):
        """Записывает использование калькулятора для гостя"""
        from models.sqlite_users import Guest
        
        guest = self.get_or_create_guest(ip_address)
        if guest:
            old_count = guest.calculator_uses or 0
            guest.calculator_uses = old_count + 1
            guest.last_seen = datetime.now().isoformat()
            self.db.session.commit()
            logger.info(f"🧮 Записано использование калькулятора для гостя: IP={ip_address}, использований было={old_count}, стало={guest.calculator_uses}")
            return True
        return False
    
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
    
    def get_or_create_search_bot(self, ip_address, user_agent, bot_type):
        """Получает или создает запись поискового бота"""
        from models.sqlite_users import SearchBot
        
        # Ищем существующего бота по IP и типу
        bot = SearchBot.query.filter_by(ip_address=ip_address, bot_type=bot_type).first()
        
        if not bot:
            # Создаем нового бота
            now = datetime.now().isoformat()
            bot = SearchBot(
                ip_address=ip_address,
                user_agent=user_agent or 'Не определен',
                bot_type=bot_type,
                first_seen=now,
                last_seen=now,
                visits_count=0
            )
            self.db.session.add(bot)
            self.db.session.commit()
            if bot_type == 'WordPress Scanner':
                logger.warning(f"🔍 Создан новый WordPress-сканер: {bot_type} (IP={ip_address})")
            else:
                logger.info(f"🕷️ Создан новый поисковый бот: {bot_type} (IP={ip_address})")
        else:
            # Обновляем last_seen и увеличиваем счетчик
            bot.last_seen = datetime.now().isoformat()
            bot.visits_count += 1
            if user_agent and bot.user_agent != user_agent:
                bot.user_agent = user_agent  # Обновляем User-Agent если изменился
            self.db.session.commit()
        
        return bot
    
    def get_all_search_bots(self, limit=500):
        """Получает всех поисковых ботов"""
        from models.sqlite_users import SearchBot
        bots = SearchBot.query.order_by(SearchBot.last_seen.desc()).limit(limit).all()
        return [bot.to_dict() for bot in bots]
    
    def get_search_bots_stats(self):
        """Получает статистику по поисковым ботам"""
        from models.sqlite_users import SearchBot
        from datetime import date
        
        today_str = date.today().isoformat()
        
        # Новые боты за сегодня
        new_bots_24h = SearchBot.query.filter(SearchBot.first_seen.like(f'{today_str}%')).count()
        
        # Всего ботов
        total_bots = SearchBot.query.count()
        
        # Активность ботов сегодня (визиты)
        today_visits = SearchBot.query.filter(SearchBot.last_seen.like(f'{today_str}%')).count()
        
        # Количество уникальных типов ботов
        unique_bot_types = self.db.session.query(SearchBot.bot_type).distinct().count()
        
        return {
            'new_bots_24h': new_bots_24h,
            'total_bots': total_bots,
            'today_visits': today_visits,
            'unique_bot_types': unique_bot_types
        }
    
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
            # Платные тарифы в текущей системе
            query = query.filter(self.User.plan.in_([
                'standard', 'premium',
                'business_start', 'business_pro', 'business_max', 'business_unlimited'
            ]))
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

    def get_registered_users_for_manual_selection(self):
        """
        Получить список зарегистрированных пользователей для ручного выбора получателей в админке.
        Возвращает только минимально нужные поля (user_id, email, verified, subscribed, plan).
        """
        query = self.User.query.filter(
            self.User.is_registered == True,
            self.User.email.isnot(None),
            self.User.email != ''
        )
        users = query.order_by(self.User.created_at.desc()).all()
        return [{
            'user_id': u.user_id,
            'email': u.email,
            'email_verified': bool(u.email_verified),
            'email_subscribed': bool(u.email_subscribed),
            'plan': u.plan
        } for u in users]
    
    def create_email_campaign(self, name, subject, html_content, text_content,
                             recipient_filter, created_by, recipient_list=None):
        """Создает новую email-рассылку"""
        from models.sqlite_users import EmailCampaign
        
        campaign = EmailCampaign(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            recipient_filter=recipient_filter,
            recipient_list=recipient_list,
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
    
    # ========== МЕТОДЫ ДЛЯ РАБОТЫ СО СТАТЬЯМИ ==========
    
    def create_article(self, title, slug, html_content, description=None, icon=None,
                      meta_keywords=None, meta_description=None, author=None, category=None):
        """Создает новую статью"""
        from models.sqlite_users import Article
        
        # Проверяем уникальность slug
        existing = Article.query.filter_by(slug=slug).first()
        if existing:
            raise ValueError(f"Статья с URL '{slug}' уже существует")
        
        article = Article(
            title=title,
            slug=slug,
            description=description,
            icon=icon,
            html_content=html_content,
            meta_keywords=meta_keywords,
            meta_description=meta_description,
            status='draft',
            created_at=datetime.now().isoformat(),
            author=author,
            category=category,
            views_count=0
        )
        
        self.db.session.add(article)
        self.db.session.commit()
        
        logger.info(f"📝 Создана статья: {title} (slug: {slug})")
        return article
    
    def get_article(self, slug_or_id):
        """Получает статью по slug или ID (без проверки статуса, для админки и просмотра)"""
        from models.sqlite_users import Article
        
        # Пробуем сначала по slug (если это строка)
        if isinstance(slug_or_id, str):
            article = Article.query.filter_by(slug=slug_or_id).first()
            return article
        
        # Если не найдено или передан ID (число)
        try:
            article_id = int(slug_or_id)
            article = Article.query.filter_by(id=article_id).first()
            return article
        except (ValueError, TypeError):
            return None
    
    def get_published_article_by_slug(self, slug):
        """Получает ОПУБЛИКОВАННУЮ статью по slug (для публичного просмотра)"""
        from models.sqlite_users import Article
        
        article = Article.query.filter_by(slug=slug, status='published').first()
        
        if article:
            # Увеличиваем счетчик просмотров
            article.views_count += 1
            self.db.session.commit()
        
        return article
    
    def get_published_articles(self, limit=100, offset=0):
        """Получает список опубликованных статей"""
        from models.sqlite_users import Article
        
        articles = Article.query.filter_by(status='published')\
            .order_by(Article.published_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return [a.to_dict() for a in articles]
    
    def get_all_articles(self, limit=100, status_filter=None):
        """Получает все статьи (для админки)"""
        from models.sqlite_users import Article
        
        query = Article.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        articles = query.order_by(Article.created_at.desc()).limit(limit).all()
        
        return [a.to_dict() for a in articles]
    
    def update_article(self, article_id, **kwargs):
        """Обновляет статью"""
        from models.sqlite_users import Article
        
        article = Article.query.filter_by(id=article_id).first()
        if not article:
            return None
        
        # Обновляем только переданные поля
        if 'title' in kwargs:
            article.title = kwargs['title']
        if 'slug' in kwargs:
            # Проверяем уникальность нового slug
            existing = Article.query.filter_by(slug=kwargs['slug']).first()
            if existing and existing.id != article_id:
                raise ValueError(f"Статья с URL '{kwargs['slug']}' уже существует")
            article.slug = kwargs['slug']
        if 'description' in kwargs:
            article.description = kwargs['description']
        if 'icon' in kwargs:
            article.icon = kwargs['icon']
        if 'html_content' in kwargs:
            article.html_content = kwargs['html_content']
        if 'meta_keywords' in kwargs:
            article.meta_keywords = kwargs['meta_keywords']
        if 'meta_description' in kwargs:
            article.meta_description = kwargs['meta_description']
        if 'status' in kwargs:
            article.status = kwargs['status']
            if kwargs['status'] == 'published' and not article.published_at:
                article.published_at = datetime.now().isoformat()
        if 'category' in kwargs:
            article.category = kwargs['category']
        
        article.updated_at = datetime.now().isoformat()
        self.db.session.commit()
        
        logger.info(f"📝 Обновлена статья: {article.title} (ID: {article_id})")
        return article
    
    def delete_article(self, article_id):
        """Удаляет статью"""
        from models.sqlite_users import Article
        
        article = Article.query.filter_by(id=article_id).first()
        if not article:
            return False
        
        self.db.session.delete(article)
        self.db.session.commit()
        
        logger.info(f"🗑️ Удалена статья: {article.title} (ID: {article_id})")
        return True
    
    def publish_article(self, article_id):
        """Публикует статью"""
        from models.sqlite_users import Article
        
        article = Article.query.filter_by(id=article_id).first()
        if not article:
            return None
        
        article.status = 'published'
        if not article.published_at:
            article.published_at = datetime.now().isoformat()
        article.updated_at = datetime.now().isoformat()
        self.db.session.commit()
        
        logger.info(f"📢 Опубликована статья: {article.title} (ID: {article_id})")
        return article
    
    def unpublish_article(self, article_id):
        """Снимает статью с публикации"""
        from models.sqlite_users import Article
        
        article = Article.query.filter_by(id=article_id).first()
        if not article:
            return None
        
        article.status = 'draft'
        article.updated_at = datetime.now().isoformat()
        self.db.session.commit()
        
        logger.info(f"🔒 Снята с публикации статья: {article.title} (ID: {article_id})")
        return article
    
    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С НОВОСТЯМИ ==========
    
    def create_news_item(self, category, title, description, date, link=None, link_text=None, created_by=None):
        """Создает новую новость"""
        from models.sqlite_users import NewsItem
        
        news = NewsItem(
            category=category,
            title=title,
            description=description,
            date=date,
            link=link,
            link_text=link_text,
            created_at=datetime.now().isoformat(),
            created_by=created_by
        )
        
        self.db.session.add(news)
        self.db.session.commit()
        
        logger.info(f"📰 Создана новость: {title} (категория: {category})")
        return news
    
    def get_news_items(self, category=None, limit=100):
        """Получает список новостей"""
        from models.sqlite_users import NewsItem
        
        query = NewsItem.query
        
        if category:
            query = query.filter_by(category=category)
        
        news_items = query.order_by(NewsItem.date.desc()).limit(limit).all()
        
        return [news.to_dict() for news in news_items]
    
    def get_news_item(self, news_id):
        """Получает новость по ID"""
        from models.sqlite_users import NewsItem
        
        return NewsItem.query.filter_by(id=news_id).first()
    
    def update_news_item(self, news_id, **kwargs):
        """Обновляет новость"""
        from models.sqlite_users import NewsItem
        
        news = NewsItem.query.filter_by(id=news_id).first()
        if not news:
            return None
        
        # Обновляем только переданные поля
        if 'category' in kwargs:
            news.category = kwargs['category']
        if 'title' in kwargs:
            news.title = kwargs['title']
        if 'description' in kwargs:
            news.description = kwargs['description']
        if 'date' in kwargs:
            news.date = kwargs['date']
        if 'link' in kwargs:
            news.link = kwargs['link']
        if 'link_text' in kwargs:
            news.link_text = kwargs['link_text']
        
        news.updated_at = datetime.now().isoformat()
        self.db.session.commit()
        
        logger.info(f"📰 Обновлена новость: {news.title} (ID: {news_id})")
        return news
    
    def delete_news_item(self, news_id):
        """Удаляет новость"""
        from models.sqlite_users import NewsItem
        
        news = NewsItem.query.filter_by(id=news_id).first()
        if not news:
            return False
        
        self.db.session.delete(news)
        self.db.session.commit()
        
        logger.info(f"🗑️ Удалена новость: {news.title} (ID: {news_id})")
        return True
    
    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛНЫМИ НОВОСТЯМИ ==========
    
    def create_full_news(self, slug, title, short_description, full_content, category=None,
                         image_url=None, author=None, meta_title=None, meta_description=None,
                         meta_keywords=None, published_at=None, created_by=None):
        """Создает полную новость"""
        from models.sqlite_users import FullNews
        
        # Проверяем уникальность slug
        existing = FullNews.query.filter_by(slug=slug).first()
        if existing:
            logger.error(f"❌ Новость с slug '{slug}' уже существует")
            return None
        
        if not published_at:
            published_at = datetime.now().isoformat()
        
        full_news = FullNews(
            slug=slug,
            title=title,
            short_description=short_description,
            full_content=full_content,
            category=category,
            image_url=image_url,
            author=author or 'Редакция DocScan',
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            published_at=published_at,
            created_at=datetime.now().isoformat(),
            is_published=True,
            views_count=0,
            created_by=created_by
        )
        
        self.db.session.add(full_news)
        self.db.session.commit()
        
        logger.info(f"✅ Создана полная новость: {title} (slug: {slug})")
        return full_news
    
    def get_full_news_by_slug(self, slug):
        """Получает полную новость по slug"""
        from models.sqlite_users import FullNews
        
        full_news = FullNews.query.filter_by(slug=slug, is_published=True).first()
        if full_news:
            # Увеличиваем счетчик просмотров
            full_news.views_count = (full_news.views_count or 0) + 1
            self.db.session.commit()
        
        return full_news
    
    def get_all_full_news(self, limit=100, category=None, is_published=None):
        """Получает список всех полных новостей"""
        from models.sqlite_users import FullNews
        
        query = FullNews.query
        
        if category:
            query = query.filter_by(category=category)
        
        if is_published is not None:
            query = query.filter_by(is_published=is_published)
        
        news_list = query.order_by(FullNews.published_at.desc()).limit(limit).all()
        return [news.to_dict() for news in news_list]
    
    def get_full_news(self, news_id):
        """Получает полную новость по ID"""
        from models.sqlite_users import FullNews
        
        return FullNews.query.filter_by(id=news_id).first()
    
    def update_full_news(self, news_id, **kwargs):
        """Обновляет полную новость"""
        from models.sqlite_users import FullNews
        
        full_news = FullNews.query.filter_by(id=news_id).first()
        if not full_news:
            return None
        
        # Обновляем только переданные поля
        updatable_fields = ['slug', 'title', 'short_description', 'full_content', 'category',
                           'image_url', 'author', 'meta_title', 'meta_description', 'meta_keywords',
                           'published_at', 'is_published']
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(full_news, field, kwargs[field])
        
        full_news.updated_at = datetime.now().isoformat()
        self.db.session.commit()
        
        logger.info(f"✅ Обновлена полная новость ID: {news_id}")
        return full_news
    
    def delete_full_news(self, news_id):
        """Удаляет полную новость"""
        from models.sqlite_users import FullNews
        
        full_news = FullNews.query.filter_by(id=news_id).first()
        if not full_news:
            return False
        
        # Удаляем связь в NewsItem если есть
        from models.sqlite_users import NewsItem
        news_items = NewsItem.query.filter_by(full_news_id=news_id).all()
        for item in news_items:
            item.full_news_id = None
        
        self.db.session.delete(full_news)
        self.db.session.commit()
        
        logger.info(f"✅ Удалена полная новость ID: {news_id}")
        return True
    
    def get_related_full_news(self, current_slug, category=None, limit=5):
        """Получает похожие полные новости"""
        from models.sqlite_users import FullNews
        
        query = FullNews.query.filter_by(is_published=True).filter(FullNews.slug != current_slug)
        
        if category:
            query = query.filter_by(category=category)
        
        related = query.order_by(FullNews.published_at.desc()).limit(limit).all()
        return [news.to_dict() for news in related]
    
    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С ВОПРОСАМИ И ОТВЕТАМИ ==========
    
    def create_question(self, user_id, title, content, category):
        """Создает новый вопрос"""
        from models.sqlite_users import Question
        
        question = Question(
            user_id=user_id,
            title=title,
            content=content,
            category=category,
            status='open',
            views_count=0,
            answers_count=0,
            created_at=datetime.now().isoformat()
        )
        
        self.db.session.add(question)
        self.db.session.commit()
        
        logger.info(f"❓ Создан вопрос: {title} (ID: {question.id}, пользователь: {user_id})")
        return question
    
    def get_questions(self, category=None, status=None, limit=50, offset=0, sort_by='newest'):
        """Получает список вопросов с фильтрацией"""
        from models.sqlite_users import Question, Answer
        from datetime import datetime
        
        query = Question.query
        
        if category:
            query = query.filter_by(category=category)
        if status:
            query = query.filter_by(status=status)
        
        # Сортировка
        if sort_by == 'newest':
            query = query.order_by(Question.created_at.desc())
        elif sort_by == 'popular':
            query = query.order_by(Question.views_count.desc(), Question.answers_count.desc())
        elif sort_by == 'unanswered':
            query = query.filter(Question.answers_count == 0).order_by(Question.created_at.desc())
        elif sort_by == 'solved':
            query = query.filter_by(status='solved').order_by(Question.updated_at.desc())
        else:
            query = query.order_by(Question.created_at.desc())
        
        questions = query.limit(limit).offset(offset).all()
        
        # ИСПРАВЛЕНИЕ: Синхронизируем статусы вопросов с реальным количеством ответов
        for question in questions:
            real_answers_count = Answer.query.filter_by(question_id=question.id).count()
            
            # Обновляем счетчик ответов
            if question.answers_count != real_answers_count:
                question.answers_count = real_answers_count
            
            # Обновляем статус если нужно
            if real_answers_count == 0 and question.status == 'answered':
                question.status = 'open'
                question.updated_at = datetime.now().isoformat()
                logger.info(f"🔄 Статус вопроса {question.id} обновлен на 'open' (ответов нет)")
            elif real_answers_count > 0 and question.status == 'open':
                question.status = 'answered'
                question.updated_at = datetime.now().isoformat()
                logger.info(f"🔄 Статус вопроса {question.id} обновлен на 'answered' ({real_answers_count} ответов)")
        
        # Сохраняем изменения
        if questions:
            self.db.session.commit()
        
        return [q.to_dict() for q in questions]
    
    def get_question(self, question_id):
        """Получает вопрос по ID и увеличивает счетчик просмотров"""
        from models.sqlite_users import Question
        
        question = Question.query.filter_by(id=question_id).first()
        if question:
            question.views_count += 1
            self.db.session.commit()
        return question
    
    def update_question(self, question_id, **kwargs):
        """Обновляет вопрос"""
        from models.sqlite_users import Question
        
        question = Question.query.filter_by(id=question_id).first()
        if not question:
            return None
        
        if 'title' in kwargs:
            question.title = kwargs['title']
        if 'content' in kwargs:
            question.content = kwargs['content']
        if 'category' in kwargs:
            question.category = kwargs['category']
        if 'status' in kwargs:
            question.status = kwargs['status']
        
        question.updated_at = datetime.now().isoformat()
        self.db.session.commit()
        
        logger.info(f"✏️ Обновлен вопрос ID: {question_id}")
        return question
    
    def delete_question(self, question_id):
        """Удаляет вопрос и все связанные ответы"""
        from models.sqlite_users import Question, Answer, AnswerLike
        
        question = Question.query.filter_by(id=question_id).first()
        if not question:
            return False
        
        # Удаляем все лайки ответов этого вопроса
        answers = Answer.query.filter_by(question_id=question_id).all()
        for answer in answers:
            AnswerLike.query.filter_by(answer_id=answer.id).delete()
        
        # Удаляем все ответы
        Answer.query.filter_by(question_id=question_id).delete()
        
        # Удаляем вопрос
        self.db.session.delete(question)
        self.db.session.commit()
        
        logger.info(f"🗑️ Удален вопрос ID: {question_id}")
        return True
    
    def create_answer(self, question_id, user_id, content):
        """Создает ответ на вопрос"""
        from models.sqlite_users import Answer, Question
        
        answer = Answer(
            question_id=question_id,
            user_id=user_id,
            content=content,
            is_best=False,
            likes_count=0,
            created_at=datetime.now().isoformat()
        )
        
        self.db.session.add(answer)
        
        # Обновляем счетчик ответов в вопросе
        question = Question.query.filter_by(id=question_id).first()
        if question:
            question.answers_count += 1
            if question.status == 'open':
                question.status = 'answered'
            question.updated_at = datetime.now().isoformat()
        
        self.db.session.commit()
        
        # Создаем уведомление для автора вопроса (если это не он сам отвечает)
        if question and question.user_id != user_id:
            answer_preview = content[:100] + '...' if len(content) > 100 else content
            from models.sqlite_users import Notification
            notification = Notification(
                user_id=question.user_id,
                type='answer',
                question_id=question_id,
                answer_id=answer.id,
                title=f'Новый ответ на ваш вопрос "{question.title[:50]}{"..." if len(question.title) > 50 else ""}"',
                message=f'Пользователь ответил: {answer_preview}',
                link=f'/questions/{question_id}',
                is_read=False,
                created_at=datetime.now().isoformat()
            )
            self.db.session.add(notification)
            self.db.session.commit()
            
            # Отправляем email-уведомление
            try:
                question_author = self.get_user(question.user_id)
                if question_author and question_author.email and question_author.email_subscribed:
                    from utils.email_service import send_email
                    email_subject = f'Новый ответ на ваш вопрос "{question.title[:50]}{"..." if len(question.title) > 50 else ""}"'
                    
                    text_content = f'''Здравствуйте!

На ваш вопрос ответил пользователь:

Вопрос: "{question.title}"
{question.content[:200]}{"..." if len(question.content) > 200 else ""}

Ответ:
{content[:300]}{"..." if len(content) > 300 else ""}

Перейти к вопросу: https://docscan-ai.ru/questions/{question_id}

---
DocScan AI
                    '''
                    
                    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #4361ee, #7209b7); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: #4361ee; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .question-box {{ background: white; padding: 15px; border-left: 4px solid #4361ee; margin: 15px 0; border-radius: 5px; }}
        .answer-box {{ background: #e6f3ff; padding: 15px; border-left: 4px solid #7209b7; margin: 15px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 DocScan AI</h1>
            <p>Новый ответ на ваш вопрос</p>
        </div>
        <div class="content">
            <p>Здравствуйте!</p>
            
            <p>На ваш вопрос ответил пользователь:</p>
            
            <div class="question-box">
                <strong>Вопрос: "{question.title}"</strong>
                <p>{question.content[:200]}{"..." if len(question.content) > 200 else ""}</p>
            </div>
            
            <div class="answer-box">
                <strong>Ответ:</strong>
                <p>{content[:300]}{"..." if len(content) > 300 else ""}</p>
            </div>
            
            <div style="text-align: center;">
                <a href="https://docscan-ai.ru/questions/{question_id}" class="button">Перейти к вопросу →</a>
            </div>
            
            <p style="margin-top: 30px; color: #666; font-size: 0.9rem;">
                С уважением,<br>Команда DocScan AI
            </p>
        </div>
    </div>
</body>
</html>
                    '''
                    
                    send_email(question_author.email, email_subject, html_content, text_content)
                    logger.info(f"📧 Email-уведомление отправлено на {question_author.email}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки email-уведомления: {e}")
        
        logger.info(f"💬 Создан ответ на вопрос ID: {question_id} (пользователь: {user_id})")
        return answer
    
    def get_answers(self, question_id, sort_by='best_first'):
        """Получает ответы на вопрос"""
        from models.sqlite_users import Answer
        
        query = Answer.query.filter_by(question_id=question_id)
        
        if sort_by == 'best_first':
            # Сначала лучший ответ, потом по дате
            query = query.order_by(Answer.is_best.desc(), Answer.created_at.asc())
        elif sort_by == 'newest':
            query = query.order_by(Answer.created_at.desc())
        elif sort_by == 'popular':
            query = query.order_by(Answer.likes_count.desc(), Answer.created_at.asc())
        else:
            query = query.order_by(Answer.created_at.asc())
        
        answers = query.all()
        return [a.to_dict() for a in answers]
    
    def set_best_answer(self, question_id, answer_id, user_id):
        """Устанавливает лучший ответ (только автор вопроса может)"""
        from models.sqlite_users import Question, Answer
        
        question = Question.query.filter_by(id=question_id).first()
        if not question or question.user_id != user_id:
            return False
        
        # Снимаем статус лучшего с предыдущего ответа
        if question.best_answer_id:
            old_best = Answer.query.filter_by(id=question.best_answer_id).first()
            if old_best:
                old_best.is_best = False
        
        # Устанавливаем новый лучший ответ
        answer = Answer.query.filter_by(id=answer_id, question_id=question_id).first()
        if not answer:
            return False
        
        answer.is_best = True
        question.best_answer_id = answer_id
        # НЕ меняем статус вопроса на 'solved' - это отдельное действие
        question.updated_at = datetime.now().isoformat()
        
        self.db.session.commit()
        
        logger.info(f"⭐ Установлен лучший ответ ID: {answer_id} для вопроса ID: {question_id}")
        return True
    
    def mark_question_solved(self, question_id, user_id):
        """Отмечает вопрос как решенный (только автор вопроса может)"""
        from models.sqlite_users import Question
        
        question = Question.query.filter_by(id=question_id).first()
        if not question or question.user_id != user_id:
            return False
        
        question.status = 'solved'
        question.updated_at = datetime.now().isoformat()
        
        self.db.session.commit()
        
        logger.info(f"✅ Вопрос ID: {question_id} отмечен как решенный пользователем {user_id}")
        return True
    
    def mark_question_open(self, question_id, user_id):
        """Возвращает вопрос в статус 'open' или 'answered' (только автор вопроса может)"""
        from models.sqlite_users import Question
        
        question = Question.query.filter_by(id=question_id).first()
        if not question or question.user_id != user_id:
            return False
        
        # Если есть ответы, ставим статус 'answered', иначе 'open'
        if question.answers_count and question.answers_count > 0:
            question.status = 'answered'
        else:
            question.status = 'open'
        
        question.updated_at = datetime.now().isoformat()
        
        self.db.session.commit()
        
        logger.info(f"🔄 Вопрос ID: {question_id} возвращен в статус '{question.status}' пользователем {user_id}")
        return True
    
    def toggle_answer_like(self, answer_id, user_id):
        """Переключает лайк на ответе (добавляет или убирает)"""
        from models.sqlite_users import Answer, AnswerLike
        
        # Проверяем, есть ли уже лайк
        existing_like = AnswerLike.query.filter_by(answer_id=answer_id, user_id=user_id).first()
        
        answer = Answer.query.filter_by(id=answer_id).first()
        if not answer:
            return False
        
        if existing_like:
            # Убираем лайк
            self.db.session.delete(existing_like)
            answer.likes_count = max(0, answer.likes_count - 1)
            liked = False
        else:
            # Добавляем лайк
            like = AnswerLike(
                answer_id=answer_id,
                user_id=user_id,
                created_at=datetime.now().isoformat()
            )
            self.db.session.add(like)
            answer.likes_count += 1
            liked = True
        
        self.db.session.commit()
        return {'liked': liked, 'likes_count': answer.likes_count}
    
    def check_answer_liked(self, answer_id, user_id):
        """Проверяет, лайкнул ли пользователь ответ"""
        from models.sqlite_users import AnswerLike
        
        if not user_id:
            return False
        
        return AnswerLike.query.filter_by(answer_id=answer_id, user_id=user_id).first() is not None
    
    def get_user_questions(self, user_id, limit=50):
        """Получает вопросы пользователя"""
        from models.sqlite_users import Question
        
        questions = Question.query.filter_by(user_id=user_id)\
            .order_by(Question.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [q.to_dict() for q in questions]
    
    def get_user_answers(self, user_id, limit=50):
        """Получает ответы пользователя"""
        from models.sqlite_users import Answer
        
        answers = Answer.query.filter_by(user_id=user_id)\
            .order_by(Answer.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [a.to_dict() for a in answers]
    
    def get_or_generate_referral_code(self, user_id):
        """Получает или генерирует реферальный код для пользователя"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        if not user.referral_code:
            # Генерируем уникальный код на основе user_id
            import hashlib
            code = hashlib.md5(f"{user_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:8].upper()
            # Проверяем уникальность
            while self.User.query.filter_by(referral_code=code).first():
                code = hashlib.md5(f"{user_id}_{datetime.now().isoformat()}_{uuid.uuid4()}".encode()).hexdigest()[:8].upper()
            
            user.referral_code = code
            self.db.session.commit()
            logger.info(f"🎁 Сгенерирован реферальный код для {user_id}: {code}")
        
        return user.referral_code
    
    def get_referral_stats(self, user_id):
        """Получает статистику партнерской программы для пользователя"""
        from models.sqlite_users import Referral, ReferralReward
        
        # Количество приглашенных
        invited_count = Referral.query.filter_by(referrer_id=user_id).count()
        
        # Количество покупок от приглашенных
        rewards = ReferralReward.query.filter_by(partner_id=user_id).all()
        purchases_count = len(rewards)
        
        # Общая сумма ожидающих выплаты
        pending_rewards = ReferralReward.query.filter_by(partner_id=user_id, status='pending').all()
        pending_amount = sum(r.reward_amount for r in pending_rewards)
        
        # Общая сумма выплаченных
        paid_rewards = ReferralReward.query.filter_by(partner_id=user_id, status='paid').all()
        paid_amount = sum(r.reward_amount for r in paid_rewards)
        
        return {
            'invited_count': invited_count,
            'purchases_count': purchases_count,
            'pending_amount': pending_amount,
            'paid_amount': paid_amount
        }
    
    def create_referral(self, referrer_id, invited_user_id):
        """Создает запись о приглашении"""
        from models.sqlite_users import Referral
        
        # Проверяем, не существует ли уже такая запись
        existing = Referral.query.filter_by(
            referrer_id=referrer_id,
            invited_user_id=invited_user_id
        ).first()
        
        if existing:
            return existing
        
        referral = Referral(
            referrer_id=referrer_id,
            invited_user_id=invited_user_id,
            created_at=datetime.now().isoformat(),
            registered_at=datetime.now().isoformat()
        )
        self.db.session.add(referral)
        self.db.session.commit()
        
        logger.info(f"🎁 Создано приглашение: {referrer_id} -> {invited_user_id}")
        return referral
    
    def create_referral_reward(self, partner_id, invited_user_id, payment_id, purchase_amount, reward_percent=15.0):
        """Создает запись о вознаграждении партнера"""
        from models.sqlite_users import ReferralReward
        
        # Проверяем, не существует ли уже награда за этот платеж
        existing = ReferralReward.query.filter_by(payment_id=payment_id).first()
        if existing:
            return existing
        
        reward_amount = purchase_amount * (reward_percent / 100)
        
        reward = ReferralReward(
            partner_id=partner_id,
            invited_user_id=invited_user_id,
            payment_id=payment_id,
            purchase_amount=purchase_amount,
            reward_amount=reward_amount,
            reward_percent=reward_percent,
            status='pending',
            created_at=datetime.now().isoformat()
        )
        self.db.session.add(reward)
        self.db.session.commit()
        
        logger.info(f"💰 Создано вознаграждение: партнер {partner_id}, сумма покупки {purchase_amount}₽, вознаграждение {reward_amount}₽ ({reward_percent}%)")
        return reward
    
    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С УВЕДОМЛЕНИЯМИ ==========
    
    def create_notification(self, user_id, type, question_id=None, answer_id=None, title=None, message=None, link=None):
        """Создает уведомление для пользователя"""
        from models.sqlite_users import Notification
        
        notification = Notification(
            user_id=user_id,
            type=type,
            question_id=question_id,
            answer_id=answer_id,
            title=title or 'Новое уведомление',
            message=message,
            link=link,
            is_read=False,
            created_at=datetime.now().isoformat()
        )
        
        self.db.session.add(notification)
        self.db.session.commit()
        
        logger.info(f"🔔 Создано уведомление для пользователя {user_id}: {title}")
        return notification
    
    def get_notifications(self, user_id, limit=50, unread_only=False):
        """Получает уведомления пользователя"""
        from models.sqlite_users import Notification
        
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        
        return [n.to_dict() for n in notifications]
    
    def get_unread_count(self, user_id):
        """Получает количество непрочитанных уведомлений"""
        from models.sqlite_users import Notification
        
        count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        return count
    
    def mark_notification_read(self, notification_id, user_id):
        """Отмечает уведомление как прочитанное"""
        from models.sqlite_users import Notification
        
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.is_read = True
            self.db.session.commit()
            return True
        return False
    
    def mark_all_notifications_read(self, user_id):
        """Отмечает все уведомления пользователя как прочитанные"""
        from models.sqlite_users import Notification
        
        count = Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        self.db.session.commit()
        
        logger.info(f"✅ Отмечено {count} уведомлений как прочитанные для пользователя {user_id}")
        return count
    
    def delete_notification(self, notification_id, user_id):
        """Удаляет уведомление"""
        from models.sqlite_users import Notification
        
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            self.db.session.delete(notification)
            self.db.session.commit()
            return True
        return False
    
    # ========== МЕТОДЫ ДЛЯ БЕЛОГО СПИСКА IP ==========
    
    def add_whitelisted_ip(self, user_id, ip_address, description=None, created_by=None, notes=None):
        """Добавляет IP-адрес в белый список для пользователя"""
        from models.sqlite_users import WhitelistedIP
        from datetime import datetime
        
        # Проверяем, не существует ли уже такой IP для этого пользователя
        existing = WhitelistedIP.query.filter_by(user_id=user_id, ip_address=ip_address).first()
        if existing:
            return {'success': False, 'error': 'Этот IP-адрес уже добавлен в белый список'}
        
        whitelisted_ip = WhitelistedIP(
            user_id=user_id,
            ip_address=ip_address,
            description=description,
            is_active=True,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            notes=notes
        )
        
        self.db.session.add(whitelisted_ip)
        self.db.session.commit()
        
        logger.info(f"✅ IP {ip_address} добавлен в белый список для пользователя {user_id}")
        return {'success': True, 'id': whitelisted_ip.id, 'message': 'IP-адрес добавлен в белый список'}
    
    def remove_whitelisted_ip(self, ip_id, user_id=None):
        """Удаляет IP-адрес из белого списка"""
        from models.sqlite_users import WhitelistedIP
        
        query = WhitelistedIP.query.filter_by(id=ip_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        whitelisted_ip = query.first()
        if whitelisted_ip:
            self.db.session.delete(whitelisted_ip)
            self.db.session.commit()
            logger.info(f"✅ IP {whitelisted_ip.ip_address} удален из белого списка")
            return {'success': True, 'message': 'IP-адрес удален из белого списка'}
        
        return {'success': False, 'error': 'IP-адрес не найден'}
    
    def get_whitelisted_ips(self, user_id):
        """Получает список всех IP-адресов из белого списка для пользователя"""
        from models.sqlite_users import WhitelistedIP
        
        ips = WhitelistedIP.query.filter_by(user_id=user_id, is_active=True).all()
        return [ip.to_dict() for ip in ips]
    
    def is_ip_whitelisted(self, user_id, ip_address):
        """Проверяет, разрешен ли IP-адрес для пользователя"""
        from models.sqlite_users import WhitelistedIP
        import ipaddress
        
        # Получаем все активные IP из белого списка для пользователя
        whitelisted_ips = WhitelistedIP.query.filter_by(user_id=user_id, is_active=True).all()
        
        if not whitelisted_ips:
            # Если белый список пуст, доступ разрешен (для обратной совместимости)
            return True
        
        # Проверяем каждый IP в белом списке
        for whitelisted_ip in whitelisted_ips:
            ip_str = whitelisted_ip.ip_address.strip()
            
            # Если это точный IP-адрес
            if '/' not in ip_str:
                if ip_str == ip_address:
                    logger.info(f"✅ IP {ip_address} найден в белом списке (точное совпадение)")
                    return True
            else:
                # Если это диапазон IP (CIDR notation, например 192.168.1.0/24)
                try:
                    network = ipaddress.ip_network(ip_str, strict=False)
                    if ipaddress.ip_address(ip_address) in network:
                        logger.info(f"✅ IP {ip_address} найден в белом списке (диапазон {ip_str})")
                        return True
                except ValueError as e:
                    logger.warning(f"⚠️ Неверный формат IP-диапазона {ip_str}: {e}")
                    continue
        
        logger.warning(f"🚫 IP {ip_address} НЕ найден в белом списке для пользователя {user_id}")
        return False
    
    # ========== МЕТОДЫ ДЛЯ КАСТОМНОГО БРЕНДИНГА ==========
    
    def get_branding_settings(self, user_id):
        """Получает настройки брендинга для пользователя"""
        from models.sqlite_users import BrandingSettings
        
        branding = BrandingSettings.query.filter_by(user_id=user_id, is_active=True).first()
        if branding:
            return branding.to_dict()
        return None
    
    def save_branding_settings(self, user_id, logo_path=None, primary_color=None, secondary_color=None, company_name=None):
        """Сохраняет или обновляет настройки брендинга"""
        from models.sqlite_users import BrandingSettings
        from datetime import datetime
        
        branding = BrandingSettings.query.filter_by(user_id=user_id).first()
        
        if branding:
            # Обновляем существующие настройки
            if logo_path is not None:
                branding.logo_path = logo_path
            if primary_color is not None:
                branding.primary_color = primary_color
            if secondary_color is not None:
                branding.secondary_color = secondary_color
            if company_name is not None:
                branding.company_name = company_name
            branding.updated_at = datetime.now().isoformat()
        else:
            # Создаем новые настройки
            branding = BrandingSettings(
                user_id=user_id,
                logo_path=logo_path,
                primary_color=primary_color or '#4361ee',
                secondary_color=secondary_color or '#764ba2',
                company_name=company_name,
                is_active=True,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            self.db.session.add(branding)
        
        self.db.session.commit()
        logger.info(f"✅ Настройки брендинга сохранены для пользователя {user_id}")
        return {'success': True, 'branding': branding.to_dict()}
    
    def toggle_branding(self, user_id, is_active=None):
        """Включает/выключает брендинг для пользователя"""
        from models.sqlite_users import BrandingSettings
        
        branding = BrandingSettings.query.filter_by(user_id=user_id).first()
        if branding:
            if is_active is not None:
                branding.is_active = is_active
            else:
                branding.is_active = not branding.is_active
            self.db.session.commit()
            logger.info(f"✅ Брендинг {'активирован' if branding.is_active else 'деактивирован'} для пользователя {user_id}")
            return {'success': True, 'is_active': branding.is_active}
        
        return {'success': False, 'error': 'Настройки брендинга не найдены'}
    
    def delete_branding(self, user_id):
        """Удаляет настройки брендинга и логотип"""
        from models.sqlite_users import BrandingSettings
        import os
        
        branding = BrandingSettings.query.filter_by(user_id=user_id).first()
        if branding:
            # Удаляем файл логотипа, если он существует
            if branding.logo_path and os.path.exists(branding.logo_path):
                try:
                    os.remove(branding.logo_path)
                    logger.info(f"🗑️ Логотип удален: {branding.logo_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить логотип: {e}")
            
            self.db.session.delete(branding)
            self.db.session.commit()
            logger.info(f"✅ Настройки брендинга удалены для пользователя {user_id}")
            return {'success': True, 'message': 'Настройки брендинга удалены'}
        
        return {'success': False, 'error': 'Настройки брендинга не найдены'}
    
    def toggle_whitelisted_ip(self, ip_id, user_id=None):
        """Включает/выключает IP-адрес в белом списке"""
        from models.sqlite_users import WhitelistedIP
        
        query = WhitelistedIP.query.filter_by(id=ip_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        whitelisted_ip = query.first()
        if whitelisted_ip:
            whitelisted_ip.is_active = not whitelisted_ip.is_active
            self.db.session.commit()
            status = "активирован" if whitelisted_ip.is_active else "деактивирован"
            logger.info(f"✅ IP {whitelisted_ip.ip_address} {status}")
            return {'success': True, 'is_active': whitelisted_ip.is_active, 'message': f'IP-адрес {status}'}
        
        return {'success': False, 'error': 'IP-адрес не найден'}
