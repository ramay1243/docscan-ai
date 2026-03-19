from flask import Blueprint, request, jsonify
import logging
import json
from config import PLANS

logger = logging.getLogger(__name__)

# Создаем Blueprint для платежей
payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/create-payment', methods=['POST'])
def create_payment():
    """Создание платежа в ЮMoney"""
    from flask import session
    
    try:
        data = request.json
        plan_type = data.get('plan')
        
        # Получаем user_id из сессии (пользователь должен быть авторизован)
        user_id = session.get('user_id')
        
        # Если user_id не в сессии, пытаемся получить из запроса (для обратной совместимости)
        if not user_id:
            user_id = data.get('user_id')
        
        if not user_id or plan_type not in PLANS:
            return jsonify({'success': False, 'error': 'Неверные данные. Необходимо войти в аккаунт.'})
        
        plan = PLANS[plan_type]
        
        # Создаем ссылку для ПРЯМОГО платежа в ЮMoney
        yoomoney_wallet = "4100119233250205"  # ТВОЙ НОМЕР КОШЕЛЬКА
        payment_url = f"https://yoomoney.ru/quickpay/confirm.xml?receiver={yoomoney_wallet}&quickpay-form=button&paymentType=AC&targets=Тариф {plan['name']} - DocScan&sum={plan['price']}&label={user_id}_{plan_type}"
        
        logger.info(f"💰 Создан платеж для пользователя {user_id}: тариф {plan_type} - {plan['price']}₽")
        
        return jsonify({
            'success': True,
            'payment_url': payment_url,
            'message': f'Оплата тарифа {plan["name"]} - {plan["price"]}₽'
        })
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return jsonify({'success': False, 'error': str(e)})

@payments_bp.route('/success')
def payment_success():
    """Страница успешной оплаты"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Платеж успешен - DocScan</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); text-align: center; }
            .success-icon { font-size: 4em; color: #48bb78; margin-bottom: 20px; }
            .btn { background: #48bb78; color: white; border: none; padding: 15px 30px; border-radius: 50px; font-size: 1.1em; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }
            .instructions { background: #f0fff4; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: left; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h1>Платеж успешно завершен!</h1>
            <p>Спасибо за оплату! Тариф будет активирован в течение 5 минут.</p>
            
            <div class="instructions">
                <h3>📧 Для ускорения активации:</h3>
                <p>Напишите нам в поддержку: <strong>docscanhelp@gmail.com</strong></p>
                <p>Укажите ваш ID и сумму платежа</p>
            </div>
            
            <a href="/" class="btn">Вернуться в DocScan</a>
        </div>
    </body>
    </html>
    """

@payments_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """Webhook для уведомлений от ЮMoney - АВТОМАТИЧЕСКАЯ АКТИВАЦИЯ"""
    try:
        logger.info("🔄 Webhook получен от ЮMoney")
        
        # ЮMoney отправляет form-data, а не JSON
        data = request.form
        logger.info(f"📨 Данные от ЮMoney: {dict(data)}")
        
        # Проверяем секрет (если есть в заголовках)
        secret = request.headers.get('Authorization')
        expected_secret = "+1OlQmd/2sC5eUxusyuNpZyh"
        
        if secret and secret != expected_secret:
            logger.info("❌ Неверный секрет webhook")
            return jsonify({'error': 'Invalid secret'}), 403
        
        # Проверяем что это успешный платеж
        if (data.get('unaccepted') == 'false' and 
            data.get('codepro') == 'false'):
            
            # Извлекаем user_id из метки (label)
            label = data.get('label', '')
            if label and '_' in label:
                parts = label.split('_')
                user_id = parts[0]
                plan_type = parts[-1]
                
                # Получаем email пользователя
                from app import app
                user = app.user_manager.get_user(user_id)
                user_email = user.email if user else None
                
                # Сохраняем платеж в БД
                try:
                    from models.sqlite_users import Payment, db
                    from datetime import datetime
                    import json
                    
                    # Получаем дату из webhook или используем текущую
                    payment_datetime = data.get('datetime', '')
                    if not payment_datetime:
                        payment_datetime = datetime.now().isoformat()
                    
                    payment = Payment(
                        user_id=user_id,
                        email=user_email,
                        plan_type=plan_type,
                        amount=float(data.get('amount', 0)),
                        currency=data.get('currency', 'RUB'),
                        provider='yoomoney',
                        status='success',
                        operation_id=data.get('operation_id'),
                        label=label,
                        created_at=payment_datetime,
                        raw_data=json.dumps(dict(data))
                    )
                    db.session.add(payment)
                    db.session.commit()
                    logger.info(f"💰 Платеж сохранен в БД: user_id={user_id}, amount={payment.amount}, plan={plan_type}")
                    
                    # Создаем вознаграждение для партнера если пользователь был приглашен
                    try:
                        user = app.user_manager.get_user(user_id)
                        if user and user.referrer_id:
                            # Создаем вознаграждение 15% от суммы покупки
                            app.user_manager.create_referral_reward(
                                partner_id=user.referrer_id,
                                invited_user_id=user_id,
                                payment_id=payment.id,
                                purchase_amount=payment.amount,
                                reward_percent=15.0
                            )
                            logger.info(f"🎁 Создано вознаграждение для партнера {user.referrer_id}: 15% от {payment.amount}₽")
                    except Exception as e:
                        logger.error(f"❌ Ошибка создания вознаграждения: {e}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка сохранения платежа в БД: {e}")
                
                # Активируем тариф автоматически
                activate_response = activate_plan(user_id, plan_type)
                logger.info(f"✅ Тариф активирован для {user_id}: {activate_response}")
                
                return jsonify({'success': True, 'message': 'Тариф активирован'})
        
        logger.info("ℹ️  Платеж не прошел проверки или тестовый")
        return jsonify({'success': True, 'message': 'Уведомление получено'})
        
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}")
        return jsonify({'success': False, 'error': str(e)})

def activate_plan(user_id, plan_type='basic'):
    """Активация тарифа для пользователя"""
    try:
        from app import app
        
        if plan_type not in PLANS:
            return {'success': False, 'error': 'Неверный тариф'}
        
        # Используем метод set_user_plan из user_manager, который правильно работает с SQLite
        result = app.user_manager.set_user_plan(user_id, plan_type)
        
        if result.get('success'):
            analyses_count = PLANS[plan_type].get('analyses_count', 0)
            logger.info(f"🎉 Активирован тариф {plan_type} для пользователя {user_id}, добавлено {analyses_count} анализов")
            return {
                'success': True,
                'message': result.get('message', f'Тариф {PLANS[plan_type]["name"]} активирован, добавлено {analyses_count} анализов')
            }
        else:
            # Если set_user_plan вернул ошибку, возвращаем её
            return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка активации тарифа: {e}")
        return {'success': False, 'error': str(e)}

@payments_bp.route('/test-webhook', methods=['POST'])
def yoomoney_test_webhook():
    """Тестовый webhook для отладки"""
    logger.info("🎯 ТЕСТОВЫЙ Webhook получен от ЮMoney")
    
    # Логируем ВСЕ что пришло
    logger.info(f"📨 Заголовки: {dict(request.headers)}")
    logger.info(f"📨 Данные: {request.get_data()}")
    logger.info(f"📨 Form data: {request.form}")
    
    return jsonify({'success': True, 'message': 'Тестовый webhook получен'})

# ============================================================
# НОВЫЙ КОД ДЛЯ ЮKASSA (ДОБАВЛЕН В КОНЕЦ ФАЙЛА)
# ============================================================

import os
from config import Config

# Конфигурация ЮKassa
YUKASSA_CONFIG = {
    'shop_id': Config.YOOMONEY_CLIENT_ID or os.getenv('YUKASSA_SHOP_ID', ''),
    'secret_key': Config.YOOMONEY_CLIENT_SECRET or os.getenv('YUKASSA_SECRET_KEY', ''),
    'enabled': False
}

# Если ключи есть - включаем ЮKassa
if YUKASSA_CONFIG['shop_id'] and YUKASSA_CONFIG['secret_key']:
    YUKASSA_CONFIG['enabled'] = True
    logger.info("✅ ЮKassa настроена и готова к работе")
else:
    logger.info("ℹ️ ЮKassa не настроена (ключи не найдены), используется только ЮMoney")

@payments_bp.route('/create-yukassa-payment', methods=['POST'])
def create_yukassa_payment():
    """Создание платежа через ЮKassa (НОВЫЙ ЭНДПОИНТ)"""
    from flask import session
    import requests
    import base64
    import uuid
    
    try:
        data = request.json
        plan_type = data.get('plan')
        
        # Получаем user_id из сессии
        user_id = session.get('user_id')
        
        if not user_id:
            user_id = data.get('user_id')
        
        if not user_id or plan_type not in PLANS:
            return jsonify({'success': False, 'error': 'Неверные данные. Необходимо войти в аккаунт.'})
        
        # Проверяем что ЮKassa включена
        if not YUKASSA_CONFIG['enabled']:
            return jsonify({
                'success': False, 
                'error': 'ЮKassa временно недоступна'
            })
        
        plan = PLANS[plan_type]
        
        # Уникальный номер заказа
        order_id = f"{user_id}_{plan_type}_{uuid.uuid4().hex[:8]}"
        
        # Сумма в копейках
        amount = int(plan['price'] * 100)
        
        # Данные для авторизации (Basic Auth)
        auth = base64.b64encode(
            f"{YUKASSA_CONFIG['shop_id']}:{YUKASSA_CONFIG['secret_key']}".encode()
        ).decode()
        
        # Запрос к API ЮKassa
        response = requests.post(
            'https://api.yookassa.ru/v3/payments',
            headers={
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/json',
                'Idempotence-Key': uuid.uuid4().hex
            },
            json={
                'amount': {
                    'value': str(plan['price']),
                    'currency': 'RUB'
                },
                'confirmation': {
                    'type': 'redirect',
                    'return_url': 'https://docscan-ai.ru/payments/success'
                },
                'capture': True,
                'description': f'Тариф {plan["name"]} для {user_id}',
                'metadata': {
                    'user_id': user_id,
                    'plan_type': plan_type
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            payment_data = response.json()
            logger.info(f"💰 Создан платеж ЮKassa для {user_id}: {plan['name']}")
            
            return jsonify({
                'success': True,
                'payment_url': payment_data['confirmation']['confirmation_url'],
                'payment_id': payment_data['id'],
                'method': 'yukassa',
                'message': f'Оплата тарифа {plan["name"]} через ЮKassa'
            })
        else:
            logger.error(f"❌ Ошибка ЮKassa API: {response.text}")
            return jsonify({
                'success': False,
                'error': 'Ошибка платежной системы'
            })
            
    except Exception as e:
        logger.error(f"❌ Ошибка при создании платежа ЮKassa: {e}")
        return jsonify({'success': False, 'error': str(e)})

@payments_bp.route('/yukassa-webhook', methods=['POST'])
def yukassa_webhook():
    """Webhook для уведомлений от ЮKassa (НОВЫЙ ЭНДПОИНТ)"""
    try:
        # Получаем данные от ЮKassa
        data = request.json
        logger.info(f"🔄 Webhook ЮKassa: {json.dumps(data, ensure_ascii=False)}")
        
        # Проверяем событие
        if data.get('event') == 'payment.succeeded':
            # Получаем метаданные
            metadata = data.get('object', {}).get('metadata', {})
            user_id = metadata.get('user_id')
            plan_type = metadata.get('plan_type')
            amount = data.get('object', {}).get('amount', {}).get('value')
            operation_id = data.get('object', {}).get('id')
            
            if user_id and plan_type:
                # Сохраняем платеж в БД
                try:
                    from models.sqlite_users import Payment, db
                    from datetime import datetime
                    
                    # Идемпотентность: если такой платеж уже сохранен - не создаем дубль
                    if operation_id:
                        existing = Payment.query.filter_by(operation_id=operation_id, provider='yukassa').first()
                        if existing:
                            logger.info(f"ℹ️ Платеж ЮKassa уже сохранен (operation_id={operation_id}), пропускаем создание")
                        else:
                            payment = Payment(
                                user_id=user_id,
                                email=None,
                                plan_type=plan_type,
                                amount=float(amount) if amount else 0,
                                currency='RUB',
                                provider='yukassa',
                                status='success',
                                operation_id=operation_id,
                                label=f"{user_id}_{plan_type}",
                                created_at=datetime.now().isoformat(),
                                raw_data=json.dumps(data, ensure_ascii=False)
                            )
                            db.session.add(payment)
                            db.session.commit()
                            logger.info(f"💰 Платеж ЮKassa сохранен в БД: {user_id} (operation_id={operation_id})")
                    else:
                        # fallback если внезапно нет operation_id
                        payment = Payment(
                            user_id=user_id,
                            email=None,
                            plan_type=plan_type,
                            amount=float(amount) if amount else 0,
                            currency='RUB',
                            provider='yukassa',
                            status='success',
                            operation_id=None,
                            label=f"{user_id}_{plan_type}",
                            created_at=datetime.now().isoformat(),
                            raw_data=json.dumps(data, ensure_ascii=False)
                        )
                        db.session.add(payment)
                        db.session.commit()
                        logger.info(f"💰 Платеж ЮKassa сохранен в БД: {user_id} (operation_id отсутствует)")
                except Exception as e:
                    logger.error(f"❌ Ошибка сохранения платежа: {e}")
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                
                # Активируем тариф даже если запись платежа упала
                try:
                    activate_plan(user_id, plan_type)
                except Exception as e:
                    logger.error(f"❌ Ошибка активации тарифа после webhook ЮKassa: {e}")
                
                return jsonify({'success': True})
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"❌ Ошибка webhook ЮKassa: {e}")
        return jsonify({'success': False, 'error': str(e)})
