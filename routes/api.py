from flask import Blueprint, request, jsonify
from utils.logger import RussianLogger
import tempfile
import os
import uuid
import logging
from services.file_processing import extract_text_from_file, validate_file
from services.analysis import analyze_text
from config import PLANS

logger = logging.getLogger(__name__)

# Создаем Blueprint для API
api_bp = Blueprint('api', __name__)

@api_bp.route('/create-user', methods=['POST'])
def create_user():
    """Создает нового пользователя"""
    try:
        from app import app
        user_id = app.user_manager.generate_user_id()
        user = app.user_manager.get_user(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'Пользователь создан'
        })
    except Exception as e:
        logger.error(f"❌ Ошибка создания пользователя: {e}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/analyze', methods=['POST'])
def analyze_document():
    """Анализ документа"""
    from app import app
    
    real_ip = app.ip_limit_manager.get_client_ip(request)
    logger.info(f"🔍 Анализ запущен для IP: {real_ip}")
    
    # Получаем user_id из формы или используем default
    user_id = request.form.get('user_id', 'default')
    
    # Проверяем лимиты
if not app.user_manager.can_analyze(user_id):
    user = app.user_manager.get_user(user_id)
    plan = PLANS[user['plan']]
    return jsonify({
        'success': False,
        'error': f'❌ Бесплатный лимит исчерпан! Сегодня использовано {user["used_today"]}/{plan["daily_limit"]} анализов.',
        'upgrade_required': True
    }), 402

# Проверяем IP-лимиты для бесплатных пользователей
if user['plan'] == 'free':
    if not app.ip_limit_manager.can_analyze_by_ip(request):
        return jsonify({
            'success': False,
            'error': '❌ Бесплатный лимит по IP исчерпан! Можно сделать только 1 анализ в день с одного IP-адреса.',
            'ip_limit_exceeded': True
        }), 402

temp_path = None
try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не загружен'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        # Валидация файла
        is_valid, message = validate_file(file)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Сохраняем временный файл
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{file.filename}")
        file.save(temp_path)
        
        # Проверяем тариф для фото
        user = app.user_manager.get_user(user_id)
        if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            if user['plan'] == 'free':
                logger.info(f"❌ Отказано в анализе фото для бесплатного пользователя {user_id}")
                return jsonify({
                    'success': False,
                    'error': '📸 Распознавание фото доступно только для платных тарифов!',
                    'upgrade_required': True,
                    'message': '💎 Перейдите на Базовый тариф (199₽/мес) для анализа фото документов'
                }), 402
            
            logger.info(f"✅ Разрешено распознавание фото для пользователя {user_id} (тариф: {user['plan']})")
        
        # Извлекаем текст
        text = extract_text_from_file(temp_path, file.filename)
        
        # Проверяем что текст извлекся
        if not text or len(text.strip()) < 10:
            return jsonify({'error': 'Не удалось извлечь текст из файла'}), 400
        
        # Анализируем текст
        analysis_result = analyze_text(text, user['plan'])
        
        logger.info(f"✅ АНАЛИЗ УСПЕШЕН для {user_id}, IP: {real_ip}")
        
        # Записываем использование
        app.user_manager.record_usage(user_id)
        
        # Для бесплатных пользователей записываем использование IP
        if user['plan'] == 'free':
            app.ip_limit_manager.record_ip_usage(request)
        
        # Добавляем информацию о лимитах в ответ
        user = app.user_manager.get_user(user_id)
        plan = PLANS[user['plan']]
        analysis_result['usage_info'] = {
            'used_today': user['used_today'],
            'daily_limit': plan['daily_limit'],
            'plan_name': plan['name'],
            'remaining': plan['daily_limit'] - user['used_today']
        }
        
        return jsonify({
            'success': True,
            'filename': file.filename,
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
    plan = PLANS[user['plan']]
    
    return jsonify({
        'user_id': user_id,
        'plan': user['plan'],
        'plan_name': plan['name'],
        'used_today': user['used_today'],
        'daily_limit': plan['daily_limit'],
        'remaining': plan['daily_limit'] - user['used_today'],
        'total_used': user['total_used']
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
        
        user = app.user_manager.get_user(user_id)
        user['plan'] = new_plan
        
        logger.info(f"✅ ТАРИФ ИЗМЕНЕН: user_id={user_id}, теперь план={user['plan']}")
        
        return jsonify({
            'success': True, 
            'message': f'Тариф изменен на {new_plan}',
            'plan': new_plan
        })
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
