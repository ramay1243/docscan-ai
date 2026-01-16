from flask import Blueprint, request, jsonify
from utils.logger import RussianLogger
import tempfile
import os
import uuid
import logging
from services.file_processing import extract_text_from_file, validate_file
from services.analysis import analyze_text
from config import PLANS
from flask_cors import cross_origin, CORS

logger = logging.getLogger(__name__)

# Создаем Blueprint для API
api_bp = Blueprint('api', __name__)

@api_bp.route('/create-user', methods=['POST'])
def create_user():
    """Создает нового пользователя"""
    try:
        from app import app
        user_id = str(uuid.uuid4())[:8]
        user = app.user_manager.get_or_create_user(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'Пользователь создан'
        })
    except Exception as e:
        logger.error(f"❌ Ошибка создания пользователя: {e}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/analyze', methods=['POST'])
@cross_origin()
def analyze_document():
    """Анализ документа - поддерживает multipart/form-data и application/json с base64"""
    from app import app
    
    real_ip = app.ip_limit_manager.get_client_ip(request)
    logger.info(f"🔍 Анализ запущен для IP: {real_ip}")
    logger.info(f"📨 === НОВЫЙ ЗАПРОС ===")
    logger.info(f"📨 Метод: {request.method}")
    logger.info(f"📨 Content-Type: {request.content_type}")
    logger.info(f"📨 Полный запрос: {request}")
    
    temp_path = None
    file = None
    filename = ""
    
    try:
        # РАЗДЕЛ 1: ОПРЕДЕЛЯЕМ ФОРМАТ ЗАПРОСА
        if request.content_type and 'application/json' in request.content_type:
            # 🆕 РЕЖИМ 1: JSON с base64 (для мобильного приложения)
            logger.info("📱 Режим: JSON с base64 (мобильное приложение)")
            
            data = request.get_json()
            logger.info(f"📱 JSON данные: {data}")
            
            if not data:
                return jsonify({'error': 'Пустой JSON'}), 400
            
            # Извлекаем данные из JSON
            user_id = data.get('user_id', 'default')
            file_base64 = data.get('file')
            filename = data.get('filename', 'document.pdf')
            mime_type = data.get('mimeType', 'application/octet-stream')
            
            if not file_base64:
                return jsonify({'error': 'Файл не загружен (отсутствует base64)'}), 400
            
            # Декодируем base64 в файл
            import base64
            try:
                file_content = base64.b64decode(file_base64)
            except Exception as e:
                logger.error(f"❌ Ошибка декодирования base64: {e}")
                return jsonify({'error': f'Неверный формат base64: {str(e)}'}), 400
            
            # Сохраняем временный файл
            temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{filename}")
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"📱 Файл сохранен: {temp_path}, размер: {len(file_content)} байт")
            
        else:
            # 📄 РЕЖИМ 2: Multipart/form-data (для веб-сайта, как раньше)
            logger.info("🌐 Режим: multipart/form-data (веб-сайт)")
            
            # Получаем user_id из формы или используем default
            user_id = request.form.get('user_id', 'default')
            
            logger.info(f"📨 Файлы в запросе: {request.files}")
            logger.info(f"📨 Форма данные: {request.form}")
            
            if 'file' not in request.files:
                return jsonify({'error': 'Файл не загружен'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Файл не выбран'}), 400
            
            filename = file.filename
            
            # Валидация файла
            is_valid, message = validate_file(file)
            if not is_valid:
                return jsonify({'error': message}), 400
            
            # Сохраняем временный файл
            temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{filename}")
            file.save(temp_path)
        
        # РАЗДЕЛ 2: ОБЩАЯ ЛОГИКА (работает для обоих режимов)
        # Проверяем лимиты
        user = app.user_manager.get_user(user_id)
        if user is None:
            logger.info(f"🆕 Создаём нового пользователя: {user_id}")
            user = app.user_manager.get_or_create_user(user_id)
            if user is None:
                logger.error(f"❌ Не удалось создать пользователя: {user_id}")
                return jsonify({'success': False, 'error': 'Ошибка создания пользователя'}), 500
        
        # НОВАЯ ЛОГИКА: Проверка на бесплатный анализ для незарегистрированных
        if not user.is_registered:
            # Если бесплатный анализ уже использован - требуем регистрацию
            if user.free_analysis_used:
                return jsonify({
                    'success': False,
                    'error': 'Вы использовали 1 бесплатный анализ. Для продолжения необходимо зарегистрироваться.',
                    'registration_required': True
                }), 403
            
            # Первый анализ - разрешаем и отмечаем как использованный
            user.free_analysis_used = True
            from models.sqlite_users import db
            db.session.commit()
            logger.info(f"✅ Первый бесплатный анализ для незарегистрированного пользователя {user_id}")
        
        # Для зарегистрированных пользователей проверяем обычные лимиты
        if user.is_registered:
            if not app.user_manager.can_analyze(user_id):
                plan = PLANS[user.plan]
                if user.plan == 'free':
                    return jsonify({
                        'success': False,
                        'error': f'❌ Бесплатный лимит исчерпан! Вы использовали {user.used_today}/{plan["daily_limit"]} анализов.',
                        'upgrade_required': True
                    }), 402
                else:
                    return jsonify({
                        'success': False,
                        'error': f'❌ Лимит исчерпан! Сегодня использовано {user.used_today}/{plan["daily_limit"]} анализов.',
                        'upgrade_required': True
                    }), 402
        
        # Проверяем IP-лимиты для незарегистрированных пользователей
        if not user.is_registered:
            if not app.ip_limit_manager.can_analyze_by_ip(request):
                return jsonify({
                    'success': False,
                    'error': '❌ Бесплатный анализ с этого IP уже использован. Зарегистрируйтесь для продолжения.',
                    'registration_required': True,
                    'ip_limit_exceeded': True
                }), 403
        
        # Для зарегистрированных с бесплатным тарифом тоже проверяем IP (на случай если они используют свой лимит)
        elif user.plan == 'free' and user.is_registered:
            if not app.ip_limit_manager.can_analyze_by_ip(request):
                return jsonify({
                    'success': False,
                    'error': '❌ Бесплатный лимит по IP исчерпан! Можно сделать только 3 анализа в день с одного IP-адреса.',
                    'ip_limit_exceeded': True,
                    'upgrade_required': True
                }), 402
        
        # Проверяем тариф для фото (только для реальных файлов, не для base64)
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            if user.plan == 'free':
                logger.info(f"❌ Отказано в анализе фото для бесплатного пользователя {user_id}")
                return jsonify({
                    'success': False,
                    'error': '📸 Распознавание фото доступно только для платных тарифов!',
                    'upgrade_required': True,
                    'message': '💎 Перейдите на Базовый тариф (490₽/мес) для анализа фото документов'
                }), 402
            
            logger.info(f"✅ Разрешено распознавание фото для пользователя {user_id} (тариф: {user.plan})")
        
        # Извлекаем текст
        text = extract_text_from_file(temp_path, filename)
        
        # Проверяем что текст извлекся
        if not text or len(text.strip()) < 10:
            return jsonify({'error': 'Не удалось извлечь текст из файла'}), 400
        
        # Анализируем текст
        analysis_result = analyze_text(text, user.plan)
        
        logger.info(f"✅ АНАЛИЗ УСПЕШЕН для {user_id}, IP: {real_ip}, режим: {'JSON' if request.content_type and 'application/json' in request.content_type else 'multipart'}")
        
        # Записываем использование (только для зарегистрированных)
        if user.is_registered:
            app.user_manager.record_usage(user_id)
        else:
            # Для незарегистрированных просто обновляем счетчик IP
            app.ip_limit_manager.record_ip_usage(request, user_id)
        
        # Сохраняем историю анализа (для всех пользователей)
        # Убеждаемся что все изменения пользователя сохранены
        try:
            from models.sqlite_users import db
            # Коммитим изменения пользователя (free_analysis_used и т.д.)
            db.session.commit()
            
            # Сохраняем историю
            history = app.user_manager.save_analysis_history(user_id, filename, analysis_result)
            if history:
                logger.info(f"✅ История анализа сохранена для {user_id}, файл: {filename}")
            else:
                logger.warning(f"⚠️ Не удалось сохранить историю для {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения истории анализа: {e}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
        
        # Добавляем информацию о лимитах в ответ
        user = app.user_manager.get_user(user_id)
        
        if not user.is_registered:
            # Для незарегистрированных показываем что бесплатный анализ использован
            analysis_result['usage_info'] = {
                'used_today': 1,
                'daily_limit': 1,
                'plan_name': 'Пробный',
                'remaining': 0,
                'free_analysis_used': True,
                'registration_required': True
            }
        else:
            plan = PLANS[user.plan]
            analysis_result['usage_info'] = {
                'used_today': user.used_today,
                'daily_limit': plan['daily_limit'],
                'plan_name': plan['name'],
                'remaining': plan['daily_limit'] - user.used_today
            }
        
        return jsonify({
            'success': True,
            'filename': filename,
            'user_id': user_id,
            'result': analysis_result
        })

    except Exception as e:
        logger.error(f"❌ Ошибка анализа документа: {e}")
        return jsonify({'error': f'Ошибка обработки: {str(e)}'}), 500

    finally:
        # Удаляем временный файл
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении временного файла: {e}")

@api_bp.route('/usage', methods=['GET'])
def get_usage():
    """Получить информацию об использовании"""
    from app import app
    
    user_id = request.args.get('user_id', 'default')
    RussianLogger.log_request(request, user_id)
    user = app.user_manager.get_user(user_id)
    
    # Для незарегистрированных показываем лимит 1
    if not user.is_registered:
        used_today = 1 if user.free_analysis_used else 0
        return jsonify({
            'user_id': user_id,
            'plan': 'free',
            'plan_name': 'Пробный',
            'used_today': used_today,
            'daily_limit': 1,
            'remaining': 1 - used_today,
            'total_used': user.total_used,
            'is_registered': False
        })
    
    plan = PLANS[user.plan]
    
    return jsonify({
        'user_id': user_id,
        'plan': user.plan,
        'plan_name': plan['name'],
        'used_today': user.used_today,
        'daily_limit': plan['daily_limit'],
        'remaining': plan['daily_limit'] - user.used_today,
        'total_used': user.total_used,
        'is_registered': True
    })

@api_bp.route('/plans', methods=['GET'])
def get_plans():
    """Получить информацию о тарифах"""
    return jsonify(PLANS)

@api_bp.route('/debug-ip')
def debug_ip():
    """Эндпоинт для отладки IP"""
    from app import app
    
    return jsonify({
        'remote_addr': request.remote_addr,
        'x_forwarded_for': request.headers.get('X-Forwarded-For'),
        'x_real_ip': request.headers.get('X-Real-IP'),
        'real_ip_detected': app.ip_limit_manager.get_client_ip(request)
    })

@api_bp.route('/upgrade-plan', methods=['POST'])
def upgrade_plan():
    """Обновить тариф пользователя"""
    from app import app
    
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        new_plan = data.get('plan', 'basic')
        
        logger.info(f"🔄 СМЕНА ТАРИФА: user_id={user_id}, новый план={new_plan}")
        
        result = app.user_manager.set_user_plan(user_id, new_plan)
        
        if result['success']:
            logger.info(f"✅ ТАРИФ ИЗМЕНЕН: user_id={user_id}, теперь план={new_plan}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Ошибка смены тарифа: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/')
def api_info():
    """Информация о API"""
    return jsonify({
        'message': 'DocScan API работает!',
        'status': 'active',
        'ai_available': True,
        'pdf_export': False,
        'version': '1.0.0'
    })
    
    
@api_bp.route('/calculator-click', methods=['POST'])
def calculator_click():
    """Увеличиваем счетчик использования калькулятора"""
    try:
        from app import app
        
        data = request.json
        user_id = data.get('user_id') if data else None
        
        if user_id:
            # Используем менеджер для обновления счетчика
            success = app.user_manager.record_calculator_use(user_id)
            if success:
                logger.info(f"✅ Calculator used by user {user_id}")
            else:
                logger.info(f"⚠️ Unknown user {user_id} used calculator")
        else:
            logger.info(f"🔸 Anonymous calculator use")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"❌ Calculator click error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
