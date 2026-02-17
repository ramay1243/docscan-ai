#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v1 для внешних интеграций
Поддерживает аутентификацию по API-ключам
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from utils.logger import RussianLogger
from datetime import datetime
import tempfile
import os
import base64
import uuid
import logging
from services.file_processing import extract_text_from_file, validate_file
from services.analysis import analyze_text
from utils.api_key_manager import APIKeyManager

logger = logging.getLogger(__name__)

# Создаем Blueprint для API v1
api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

def require_api_key(f):
    """Декоратор для проверки API-ключа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Получаем API-ключ из заголовка
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API-ключ не предоставлен. Используйте заголовок X-API-Key или Authorization: Bearer <key>'
            }), 401
        
        # Проверяем API-ключ
        user_info, error = APIKeyManager.verify_api_key(api_key)
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 401
        
        # Добавляем информацию о пользователе в request
        request.api_user = user_info
        
        return f(*args, **kwargs)
    
    return decorated_function

@api_v1_bp.route('/analyze', methods=['POST'])
@require_api_key
def analyze_document():
    """
    Анализ документа через API
    
    Поддерживает два формата:
    1. multipart/form-data с файлом
    2. application/json с base64
    
    Headers:
        X-API-Key: ваш API-ключ
        или
        Authorization: Bearer ваш-API-ключ
    
    Returns:
        JSON с результатами анализа
    """
    from app import app
    
    user_info = request.api_user
    user_id = user_info['user_id']
    
    logger.info(f"🔐 API запрос на анализ от пользователя {user_id} (API Key: {user_info.get('api_key_name', 'без названия')})")
    
    temp_path = None
    filename = ""
    
    try:
        # Определяем формат запроса
        if request.content_type and 'application/json' in request.content_type:
            # JSON с base64
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Пустой JSON'
                }), 400
            
            file_base64 = data.get('file')
            filename = data.get('filename', 'document.pdf')
            
            if not file_base64:
                return jsonify({
                    'success': False,
                    'error': 'Файл не загружен (отсутствует base64)'
                }), 400
            
            # Декодируем base64
            try:
                file_content = base64.b64decode(file_base64)
            except Exception as e:
                logger.error(f"❌ Ошибка декодирования base64: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Неверный формат base64: {str(e)}'
                }), 400
            
            # Сохраняем во временный файл
            temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{filename}")
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
        else:
            # multipart/form-data
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'Файл не загружен'
                }), 400
            
            file = request.files['file']
            filename = file.filename or 'document.pdf'
            
            # Валидация файла
            validation_error = validate_file(file)
            if validation_error:
                return jsonify({
                    'success': False,
                    'error': validation_error
                }), 400
            
            # Сохраняем во временный файл
            temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_{filename}")
            file.save(temp_path)
        
        # Извлекаем текст из файла
        text, pages_count = extract_text_from_file(temp_path)
        
        if not text or len(text.strip()) < 50:
            return jsonify({
                'success': False,
                'error': 'Не удалось извлечь текст из документа или документ слишком короткий (минимум 50 символов)'
            }), 400
        
        logger.info(f"📄 Извлечен текст: {len(text)} символов из {pages_count} страниц")
        
        # Получаем информацию о пользователе
        user = app.user_manager.get_user(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Пользователь не найден'
            }), 404
        
        # Проверяем лимиты
        if not app.user_manager.can_analyze(user_id):
            return jsonify({
                'success': False,
                'error': 'Достигнут дневной лимит анализов для вашего тарифа'
            }), 429
        
        # Выполняем анализ
        analysis_result = analyze_text(
            text=text,
            user_plan=user.plan if hasattr(user, 'plan') else user.get('plan', 'free'),
            is_authenticated=True
        )
        
        # Записываем использование
        app.user_manager.record_usage(user_id)
        
        # Сохраняем в историю
        try:
            from models.sqlite_users import AnalysisHistory, db
            history = AnalysisHistory(
                user_id=user_id,
                filename=filename,
                document_type=analysis_result.get('document_type'),
                document_type_name=analysis_result.get('document_type_name'),
                risk_level=analysis_result.get('risk_level'),
                created_at=datetime.now().isoformat(),
                analysis_summary=analysis_result.get('summary', '')[:500]  # Первые 500 символов
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в историю: {e}")
        
        # Возвращаем результат
        return jsonify({
            'success': True,
            'analysis': {
                'document_type': analysis_result.get('document_type'),
                'document_type_name': analysis_result.get('document_type_name'),
                'risk_level': analysis_result.get('risk_level'),
                'summary': analysis_result.get('summary'),
                'expert_analysis': analysis_result.get('expert_analysis'),
                'recommendations': analysis_result.get('recommendations'),
                'pages_count': pages_count,
                'text_length': len(text)
            },
            'metadata': {
                'filename': filename,
                'analyzed_at': datetime.now().isoformat(),
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка анализа через API: {e}")
        return jsonify({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500
        
    finally:
        # Удаляем временный файл
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"❌ Ошибка удаления временного файла: {e}")

@api_v1_bp.route('/usage', methods=['GET'])
@require_api_key
def get_usage():
    """
    Получить статистику использования API
    
    Returns:
        JSON со статистикой использования
    """
    from app import app
    
    user_info = request.api_user
    user_id = user_info['user_id']
    
    try:
        user = app.user_manager.get_user(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Пользователь не найден'
            }), 404
        
        # Получаем информацию о тарифе
        from config import PLANS
        plan_info = PLANS.get(user.plan if hasattr(user, 'plan') else user.get('plan', 'free'), {})
        
        return jsonify({
            'success': True,
            'usage': {
                'used_today': user.used_today if hasattr(user, 'used_today') else user.get('used_today', 0),
                'total_used': user.total_used if hasattr(user, 'total_used') else user.get('total_used', 0),
                'daily_limit': plan_info.get('daily_limit', 0),
                'plan': user.plan if hasattr(user, 'plan') else user.get('plan', 'free'),
                'plan_expires': user.plan_expires if hasattr(user, 'plan_expires') else user.get('plan_expires')
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return jsonify({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500

@api_v1_bp.route('/health', methods=['GET'])
def health_check():
    """
    Проверка работоспособности API
    
    Returns:
        JSON со статусом API
    """
    return jsonify({
        'success': True,
        'status': 'ok',
        'version': '1.0',
        'timestamp': datetime.now().isoformat()
    })

