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
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        user_id = data.get('user_id')  # Может быть передан, если пользователь был создан ранее
        
        # Валидация
        if not email or not validate_email(email):
            return jsonify({'success': False, 'error': 'Неверный email адрес'}), 400
        
        if not password or len(password) < 8:
            return jsonify({'success': False, 'error': 'Пароль должен содержать минимум 8 символов'}), 400
        
        # Проверяем существует ли пользователь с таким email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'Пользователь с таким email уже зарегистрирован'}), 400
        
        # Получаем или создаем пользователя
        if user_id:
            user = User.query.filter_by(user_id=user_id).first()
            # Если пользователь с таким user_id не найден, создаем нового
            if not user:
                user_id = None  # Сбросим, чтобы создать нового ниже
        
        if not user_id:
            import uuid
            user_id = str(uuid.uuid4())[:8]
            user = User(
                user_id=user_id,
                plan='free',
                used_today=0,
                last_reset=datetime.now().date().isoformat(),
                total_used=0,
                created_at=datetime.now().isoformat(),
                ip_address='Не определен'
            )
            db.session.add(user)
        
        # Обновляем данные пользователя
        user.email = email
        user.password_hash = hash_password(password)
        user.is_registered = True
        
        # Генерируем токен верификации
        user.verification_token = generate_verification_token()
        user.verification_token_expires = get_token_expiry(24)  # 24 часа
        user.email_verified = False
        
        db.session.commit()
        
        # Отправляем email для верификации
        send_verification_email(email, user.verification_token, user_id)
        
        logger.info(f"✅ Пользователь зарегистрирован: {email}, user_id: {user_id}")
        
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
    user = app.user_manager.get_user(user_id)
    
    if not user or not user.is_registered:
        session.clear()
        return redirect(url_for('auth.login_page'))
    
    # Получаем историю анализов
    history = app.user_manager.get_analysis_history(user_id, limit=50)
    
    # Получаем статистику
    from config import PLANS
    plan = PLANS.get(user.plan, PLANS['free'])
    
    return render_template('cabinet.html', 
        user=user,
        history=history,
        plan=plan
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
    
    user = User.query.filter_by(user_id=user_id).first()
    
    if not user or not user.is_registered:
        logger.debug(f"❌ check-auth: Пользователь {user_id} не найден или не зарегистрирован")
        session.clear()
        return jsonify({'authenticated': False})
    
    logger.debug(f"✅ check-auth: Пользователь {user_id} авторизован")
    return jsonify({
        'authenticated': True,
        'user_id': user.user_id,
        'email': user.email,
        'email_verified': user.email_verified,
        'plan': user.plan
    })

