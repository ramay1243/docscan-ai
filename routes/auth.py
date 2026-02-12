"""Маршруты для регистрации, авторизации и управления аккаунтом"""
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from models.sqlite_users import db, User, AnalysisHistory
from utils.auth import hash_password, verify_password, generate_verification_token, generate_reset_token, get_token_expiry, is_token_expired
from utils.email_service import send_verification_email, send_password_reset_email
from utils.helpers import validate_email
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET'])
def register_page():
    """Страница регистрации"""
    return render_template('register.html')

@auth_bp.route('/api/register', methods=['POST'])
def register():
    """API регистрации нового пользователя"""
    try:
        from app import app
        
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        # НОВАЯ ЛОГИКА: user_id НЕ берем из формы для незарегистрированных
        # Всегда создаем новый user_id при регистрации
        
        # Валидация
        if not email or not validate_email(email):
            return jsonify({'success': False, 'error': 'Неверный email адрес'}), 400
        
        if not password or len(password) < 8:
            return jsonify({'success': False, 'error': 'Пароль должен содержать минимум 8 символов'}), 400
        
        # Проверяем существует ли пользователь с таким email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'Пользователь с таким email уже зарегистрирован'}), 400
        
        # Получаем IP адрес для связи с гостем
        real_ip = app.ip_limit_manager.get_client_ip(request)
        
        # Создаем нового пользователя с новым user_id
        import uuid
        user_id = str(uuid.uuid4())[:8]
        user = User(
            user_id=user_id,
            plan='free',
            used_today=0,
            last_reset=datetime.now().date().isoformat(),
            total_used=0,
            created_at=datetime.now().isoformat(),
            ip_address=real_ip,
            email=email,
            password_hash=hash_password(password),
            is_registered=True,
            email_verified=False,
            free_analysis_used=False
        )
        
        # Генерируем токен верификации
        user.verification_token = generate_verification_token()
        user.verification_token_expires = get_token_expiry(24)  # 24 часа
        
        db.session.add(user)
        db.session.commit()
        
        # НОВАЯ ЛОГИКА: Связываем гостя с новым пользователем
        app.user_manager.link_guest_to_user(real_ip, user_id)
        
        # Отправляем email для верификации
        send_verification_email(email, user.verification_token, user_id)
        
        logger.info(f"✅ Пользователь зарегистрирован: {email}, user_id: {user_id}, IP: {real_ip}")
        
        # Создаем сессию
        session['user_id'] = user_id
        session['email'] = email
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': 'Регистрация успешна! Проверьте email для подтверждения.',
            'user_id': user_id,
            'email_verification_required': True
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Ошибка регистрации: {str(e)}'}), 500

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Страница входа"""
    return render_template('login.html')

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """API входа"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email и пароль обязательны'}), 400
        
        # Ищем пользователя
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.is_registered:
            return jsonify({'success': False, 'error': 'Неверный email или пароль'}), 401
        
        # Проверяем пароль
        if not verify_password(user.password_hash, password):
            return jsonify({'success': False, 'error': 'Неверный email или пароль'}), 401
        
        # Создаем сессию
        session['user_id'] = user.user_id
        session['email'] = user.email
        session.permanent = True
        
        logger.info(f"✅ Пользователь вошел: {email}, user_id: {user.user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Вход выполнен успешно',
            'user_id': user.user_id,
            'email': user.email
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка входа: {e}")
        return jsonify({'success': False, 'error': f'Ошибка входа: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Выход из аккаунта"""
    user_id = session.get('user_id')
    if user_id:
        logger.info(f"👋 Пользователь вышел: {user_id}")
    session.clear()
    return redirect(url_for('main.home'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Верификация email по токену"""
    try:
        user = User.query.filter_by(verification_token=token).first()
        
        if not user:
            return render_template('message.html', 
                title='Ошибка верификации',
                message='Токен верификации не найден или недействителен.',
                type='error'
            )
        
        if is_token_expired(user.verification_token_expires):
            return render_template('message.html',
                title='Токен истек',
                message='Срок действия ссылки для верификации истек. Запросите новую ссылку.',
                type='error'
            )
        
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        db.session.commit()
        
        # Создаем сессию если пользователь не авторизован
        if 'user_id' not in session:
            session['user_id'] = user.user_id
            session['email'] = user.email
            session.permanent = True
        
        logger.info(f"✅ Email верифицирован: {user.email}")
        
        return render_template('message.html',
            title='Email подтвержден',
            message='Ваш email успешно подтвержден! Теперь вы можете использовать все возможности сервиса.',
            type='success',
            redirect_url='/cabinet'
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка верификации email: {e}")
        return render_template('message.html',
            title='Ошибка',
            message='Произошла ошибка при верификации email.',
            type='error'
        )

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    """Страница запроса сброса пароля"""
    return render_template('forgot_password.html')

@auth_bp.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """API запроса сброса пароля"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email or not validate_email(email):
            return jsonify({'success': False, 'error': 'Неверный email адрес'}), 400
        
        user = User.query.filter_by(email=email, is_registered=True).first()
        
        # Всегда возвращаем успех (для безопасности не раскрываем, существует ли пользователь)
        if user:
            user.reset_token = generate_reset_token()
            user.reset_token_expires = get_token_expiry(24)  # 24 часа
            db.session.commit()
            
            send_password_reset_email(email, user.reset_token, user.user_id)
            logger.info(f"📧 Запрос сброса пароля для: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Если пользователь с таким email существует, инструкции по сбросу пароля отправлены на почту.'
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка запроса сброса пароля: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Страница сброса пароля"""
    if request.method == 'GET':
        # Проверяем токен
        user = User.query.filter_by(reset_token=token).first()
        
        if not user or is_token_expired(user.reset_token_expires):
            return render_template('message.html',
                title='Токен недействителен',
                message='Ссылка для сброса пароля недействительна или истекла. Запросите новую.',
                type='error'
            )
        
        return render_template('reset_password.html', token=token)
    
    else:
        # POST - сброс пароля
        try:
            data = request.get_json()
            new_password = data.get('password', '')
            
            if not new_password or len(new_password) < 8:
                return jsonify({'success': False, 'error': 'Пароль должен содержать минимум 8 символов'}), 400
            
            user = User.query.filter_by(reset_token=token).first()
            
            if not user:
                return jsonify({'success': False, 'error': 'Токен не найден'}), 404
            
            if is_token_expired(user.reset_token_expires):
                return jsonify({'success': False, 'error': 'Токен истек'}), 400
            
            # Устанавливаем новый пароль
            user.password_hash = hash_password(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            db.session.commit()
            
            logger.info(f"✅ Пароль сброшен для: {user.email}")
            
            return jsonify({
                'success': True,
                'message': 'Пароль успешно изменен. Теперь вы можете войти с новым паролем.'
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка сброса пароля: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/cabinet', methods=['GET'])
def cabinet():
    """Страница личного кабинета"""
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('auth.login_page'))
    
    from app import app
    # ВАЖНО: get_user теперь автоматически обновляет данные из БД
    # используя expire_all() и refresh() для получения актуального тарифа
    logger.info(f"🔍 Cabinet: Получаем пользователя user_id={user_id} из сессии")
    user = app.user_manager.get_user(user_id)
    
    if not user:
        logger.error(f"❌ Cabinet: Пользователь {user_id} не найден в БД!")
        session.clear()
        return redirect(url_for('auth.login_page'))
    
    if not user.is_registered:
        logger.error(f"❌ Cabinet: Пользователь {user_id} не зарегистрирован!")
        session.clear()
        return redirect(url_for('auth.login_page'))
    
    # Получаем историю анализов
    history = app.user_manager.get_analysis_history(user_id, limit=50)
    
    # Получаем статистику - используем актуальный план из БД
    from config import PLANS
    from datetime import date
    current_plan_type = user.plan
    plan = PLANS.get(current_plan_type, PLANS['free'])
    
    # Вычисляем дни до окончания тарифа
    days_left = None
    if user.plan != 'free' and user.plan_expires:
        try:
            expiry_date = date.fromisoformat(user.plan_expires) if isinstance(user.plan_expires, str) else user.plan_expires
            today = date.today()
            delta = expiry_date - today
            days_left = delta.days
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления дней до окончания тарифа: {e}")
            days_left = None
    
    logger.info(f"📊 Cabinet: user_id={user_id}, plan={current_plan_type}, plan_name={plan['name']}, daily_limit={plan['daily_limit']}, used_today={user.used_today}, plan_expires={user.plan_expires}, days_left={days_left}")
    
    return render_template('cabinet.html', 
        user=user,
        history=history,
        plan=plan,
        days_left=days_left
    )

@auth_bp.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Проверка авторизации пользователя"""
    user_id = session.get('user_id')
    session_id = request.cookies.get('session') or 'no-cookie'
    
    # Логирование для диагностики
    logger.debug(f"🔍 check-auth: user_id={user_id}, session_cookie={session_id[:20]}...")
    
    if not user_id:
        logger.debug(f"❌ check-auth: Нет user_id в сессии")
        return jsonify({'authenticated': False})
    
    # ВАЖНО: Обновляем данные пользователя из БД, чтобы получить актуальный тариф
    # Это решает проблему, когда тариф изменен в админке, но не обновляется на сайте
    from app import app
    user = app.user_manager.get_user(user_id)
    
    if not user or not user.is_registered:
        logger.debug(f"❌ check-auth: Пользователь {user_id} не найден или не зарегистрирован")
        session.clear()
        return jsonify({'authenticated': False})
    
    # Обрабатываем plan_expires (может быть строкой или date объектом)
    plan_expires_str = None
    if user.plan_expires:
        if hasattr(user.plan_expires, 'isoformat'):
            plan_expires_str = user.plan_expires.isoformat()
        else:
            plan_expires_str = str(user.plan_expires)
    
    logger.debug(f"✅ check-auth: Пользователь {user_id} авторизован, план: {user.plan}")
    return jsonify({
        'authenticated': True,
        'user_id': user.user_id,
        'email': user.email,
        'email_verified': user.email_verified,
        'plan': user.plan,
        'plan_expires': plan_expires_str
    })

@auth_bp.route('/api/change-email', methods=['POST'])
def change_email():
    """API для смены email"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    try:
        from app import app
        user = app.user_manager.get_user(user_id)
        
        if not user or not user.is_registered:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        data = request.get_json()
        new_email = data.get('new_email', '').strip().lower()
        
        if not new_email:
            return jsonify({'success': False, 'error': 'Введите новый email'}), 400
        
        if not validate_email(new_email):
            return jsonify({'success': False, 'error': 'Неверный формат email'}), 400
        
        # Проверяем, не занят ли email другим пользователем
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user and existing_user.user_id != user_id:
            return jsonify({'success': False, 'error': 'Этот email уже используется'}), 400
        
        # Обновляем email и сбрасываем верификацию
        old_email = user.email
        user.email = new_email
        user.email_verified = False
        user.verification_token = generate_verification_token()
        user.verification_token_expires = get_token_expiry()
        
        db.session.commit()
        
        # Отправляем письмо подтверждения на новый email
        try:
            send_verification_email(new_email, user.verification_token, user_id)
            logger.info(f"✅ Письмо подтверждения отправлено на {new_email} для {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки письма подтверждения: {e}")
        
        logger.info(f"✅ Email изменен для {user_id}: {old_email} -> {new_email}")
        
        return jsonify({
            'success': True,
            'message': 'Email изменен. Проверьте новый email и перейдите по ссылке из письма для подтверждения.'
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка смены email: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/api/change-password', methods=['POST'])
def change_password():
    """API для смены пароля"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    try:
        from app import app
        user = app.user_manager.get_user(user_id)
        
        if not user or not user.is_registered:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Заполните все поля'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Пароль должен содержать минимум 8 символов'}), 400
        
        # Проверяем текущий пароль
        if not verify_password(user.password_hash, current_password):
            return jsonify({'success': False, 'error': 'Неверный текущий пароль'}), 400
        
        # Устанавливаем новый пароль
        user.password_hash = hash_password(new_password)
        db.session.commit()
        
        logger.info(f"✅ Пароль изменен для {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Пароль успешно изменен'
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка смены пароля: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/api/update-notifications', methods=['POST'])
def update_notifications():
    """API для обновления настроек уведомлений"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    try:
        from app import app
        user = app.user_manager.get_user(user_id)
        
        if not user or not user.is_registered:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        data = request.get_json()
        email_subscribed = data.get('email_subscribed', True)
        
        # Обновляем настройку подписки
        user.email_subscribed = bool(email_subscribed)
        db.session.commit()
        
        logger.info(f"✅ Настройки уведомлений обновлены для {user_id}: email_subscribed={email_subscribed}")
        
        return jsonify({
            'success': True,
            'message': 'Настройки сохранены'
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления настроек уведомлений: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

