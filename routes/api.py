from flask import Blueprint, request, jsonify, session, send_file, redirect
from utils.logger import RussianLogger
import tempfile
import os
import uuid
import logging
from services.file_processing import extract_text_from_file, validate_file
from services.analysis import analyze_text
from services.pdf_generator import generate_analysis_pdf
from config import PLANS
from flask_cors import cross_origin, CORS
from io import BytesIO

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
    from utils.bot_detector import should_block_request, is_search_bot, get_bot_type
    
    real_ip = app.ip_limit_manager.get_client_ip(request)
    user_agent = request.headers.get('User-Agent', 'Не определен')
    
    # ПРОВЕРКА НА ВРЕДОНОСНЫХ БОТОВ - БЛОКИРОВКА
    if should_block_request(user_agent):
        logger.warning(f"🚫 Запрос заблокирован: вредоносный бот (IP: {real_ip}, User-Agent: {user_agent[:50]}...)")
        return jsonify({
            'success': False,
            'error': 'Доступ запрещен'
        }), 403
    
    # ПРОВЕРКА НА ПОИСКОВЫХ БОТОВ - ЗАПИСЬ В ОТДЕЛЬНУЮ ТАБЛИЦУ
    is_bot, bot_type = is_search_bot(user_agent)
    if is_bot:
        bot_display_type = get_bot_type(user_agent)
        app.user_manager.get_or_create_search_bot(real_ip, user_agent, bot_type)
        logger.info(f"🕷️ Поисковый бот обнаружен: {bot_display_type} (IP: {real_ip})")
        # Поисковые боты не должны делать анализ, но мы их записали
        return jsonify({
            'success': False,
            'error': 'Этот функционал доступен только для пользователей'
        }), 403
    
    # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ IP для диагностики
    x_forwarded_for = request.headers.get('X-Forwarded-For', '')
    x_real_ip = request.headers.get('X-Real-IP', '')
    remote_addr = request.remote_addr or 'None'
    logger.info(f"🔍 IP диагностика: real_ip={real_ip}, X-Real-IP='{x_real_ip}', X-Forwarded-For='{x_forwarded_for}', remote_addr='{remote_addr}'")
    logger.info(f"🔍 Анализ запущен для IP: {real_ip}, User-Agent: {user_agent[:50]}...")
    
    # ЛОГИРОВАНИЕ: Проверяем есть ли уже гости с похожим User-Agent для диагностики
    try:
        from models.sqlite_users import Guest
        similar_guests = Guest.query.filter(Guest.user_agent.like(f'%{user_agent[:30]}%'), Guest.registered_user_id == None).limit(5).all()
        if similar_guests:
            logger.info(f"🔍 Найдено {len(similar_guests)} похожих гостей с похожим User-Agent (разные IP): {[g.ip_address for g in similar_guests]}")
    except:
        pass
    
    # ПРОВЕРЯЕМ АВТОРИЗАЦИЮ: получаем user_id из сессии (только для зарегистрированных)
    user_id = session.get('user_id')
    is_authenticated = bool(user_id)
    
    logger.info(f"🔐 Авторизация: {'ДА' if is_authenticated else 'НЕТ'} (user_id={user_id})")
    
    temp_path = None
    file = None
    filename = ""
    user = None
    
    try:
        # РАЗДЕЛ 1: ОПРЕДЕЛЯЕМ ФОРМАТ ЗАПРОСА И ОБРАБАТЫВАЕМ ФАЙЛ
        if request.content_type and 'application/json' in request.content_type:
            # 🆕 РЕЖИМ 1: JSON с base64 (для мобильного приложения)
            logger.info("📱 Режим: JSON с base64 (мобильное приложение)")
            
            data = request.get_json()
            logger.info(f"📱 JSON данные: {data}")
            
            if not data:
                return jsonify({'error': 'Пустой JSON'}), 400
            
            # Для мобильного приложения user_id должен быть в сессии или в JSON
            if not is_authenticated:
                # Проверяем, не передан ли user_id в JSON (для обратной совместимости)
                user_id_from_json = data.get('user_id')
                if user_id_from_json and user_id_from_json != 'default':
                    # Пытаемся найти пользователя - может быть зарегистрирован
                    user = app.user_manager.get_user(user_id_from_json)
                    if user and user.is_registered:
                        # Пользователь существует и зарегистрирован - используем его
                        user_id = user_id_from_json
                        is_authenticated = True
                        logger.info(f"✅ Найден зарегистрированный пользователь из JSON: {user_id}")
            
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
            # 📄 РЕЖИМ 2: Multipart/form-data (для веб-сайта)
            logger.info("🌐 Режим: multipart/form-data (веб-сайт)")
            
            # НОВАЯ ЛОГИКА: для веб-сайта user_id НЕ берем из формы для незарегистрированных
            # Если пользователь авторизован, user_id будет в сессии
            # Если не авторизован - работаем только с IP
            
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
        
        # РАЗДЕЛ 2: ПРОВЕРКА ЛИМИТОВ (разная логика для зарегистрированных и незарегистрированных)
        
        if is_authenticated:
            # ========== ЗАРЕГИСТРИРОВАННЫЙ ПОЛЬЗОВАТЕЛЬ ==========
            logger.info(f"👤 Обработка для ЗАРЕГИСТРИРОВАННОГО пользователя: {user_id}")
            
            # Получаем пользователя по user_id из сессии
            user = app.user_manager.get_user(user_id)
            if not user or not user.is_registered:
                logger.error(f"❌ Пользователь {user_id} не найден или не зарегистрирован!")
                return jsonify({
                    'success': False,
                    'error': 'Пользователь не найден. Пожалуйста, войдите заново.',
                    'login_required': True
                }), 401
            
            # Проверяем лимиты тарифа
            if not app.user_manager.can_analyze(user_id):
                plan = PLANS[user.plan]
                if user.plan == 'free':
                    # Для бесплатного тарифа - один анализ навсегда
                    return jsonify({
                        'success': False,
                        'error': '❌ Бесплатный анализ уже использован! Приобретите тариф для продолжения работы.',
                        'upgrade_required': True
                    }), 402
                else:
                    # Для платных тарифов - закончились анализы
                    return jsonify({
                        'success': False,
                        'error': f'❌ Анализы закончились! Доступно: {user.available_analyses or 0} анализов.',
                        'upgrade_required': True
                    }), 402
            
        else:
            # ========== НЕЗАРЕГИСТРИРОВАННЫЙ ПОЛЬЗОВАТЕЛЬ (ГОСТЬ) ==========
            logger.info(f"👥 Обработка для НЕЗАРЕГИСТРИРОВАННОГО пользователя (IP: {real_ip})")
            
            # Проверяем IP-лимиты (1 анализ в день)
            if not app.ip_limit_manager.can_analyze_by_ip(request, app.user_manager):
                # IP лимит превышен - обновляем флаг registration_prompted для гостя
                # Ищем существующего гостя с этим IP или создаем нового
                try:
                    guest = app.user_manager.get_or_create_guest(real_ip, user_agent)
                    guest.registration_prompted = True
                    # Если гость только что создан (analyses_count = 0), это странно, но логируем
                    if guest.analyses_count == 0:
                        logger.warning(f"⚠️ IP лимит превышен для IP {real_ip}, но у гостя 0 анализов. Возможно, IP изменился между запросами.")
                    from models.sqlite_users import db
                    db.session.commit()
                except Exception as e:
                    logger.error(f"❌ Ошибка обновления гостя при превышении лимита: {e}")
                
                return jsonify({
                    'success': False,
                    'error': '❌ Бесплатный анализ с этого IP уже использован. Зарегистрируйтесь для продолжения.',
                    'registration_required': True,
                    'ip_limit_exceeded': True
                }), 403
            
            # ВАЖНО: Увеличиваем счетчик СРАЗУ после проверки, ДО начала анализа
            # Это гарантирует, что второй запрос будет заблокирован даже если первый упадет с ошибкой
            app.ip_limit_manager.record_ip_usage(request, None)  # user_id=None для незарегистрированных
            logger.info(f"📊 Счетчик IP увеличен ДО анализа: IP={real_ip}")
            
            # user остается None для незарегистрированных
        
        # РАЗДЕЛ 3: ПРОВЕРКА ТАРИФА ДЛЯ ФОТО (только для зарегистрированных)
        if is_authenticated:
            plan_type = user.plan if user else 'free'
        else:
            plan_type = 'free'  # Для незарегистрированных - бесплатный тариф
        
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            if plan_type == 'free':
                logger.info(f"❌ Отказано в анализе фото для {'пользователя' if is_authenticated else 'гостя'}")
                return jsonify({
                    'success': False,
                    'error': '📸 Распознавание фото доступно только для платных тарифов!',
                    'upgrade_required': True,
                    'message': '💎 Зарегистрируйтесь и перейдите на Базовый тариф (10 анализов за 290₽) для анализа фото документов'
                }), 402
            
            logger.info(f"✅ Разрешено распознавание фото (тариф: {plan_type})")
        
        # РАЗДЕЛ 4: ИЗВЛЕЧЕНИЕ ТЕКСТА И АНАЛИЗ
        # Извлекаем текст
        text = extract_text_from_file(temp_path, filename)
        
        # Проверяем что текст извлекся
        if not text or len(text.strip()) < 10:
            # Если анализ не удался из-за ошибки файла, откатываем счетчик для незарегистрированных
            if not is_authenticated:
                try:
                    real_ip = app.ip_limit_manager.get_client_ip(request)
                    if real_ip in app.ip_limit_manager.ip_limits:
                        app.ip_limit_manager.ip_limits[real_ip]['used_today'] = max(0, app.ip_limit_manager.ip_limits[real_ip]['used_today'] - 1)
                        app.ip_limit_manager.save_ip_limits()
                        logger.info(f"🔄 Откат счетчика IP из-за ошибки файла: IP={real_ip}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отката счетчика IP: {e}")
            return jsonify({'error': 'Не удалось извлечь текст из файла'}), 400
        
        # Анализируем текст
        analysis_result = analyze_text(text, plan_type, is_authenticated=is_authenticated)
        
        logger.info(f"✅ АНАЛИЗ УСПЕШЕН для {'пользователя' if is_authenticated else 'гостя'}, IP: {real_ip}")
        
        # РАЗДЕЛ 5: ЗАПИСЬ ИСПОЛЬЗОВАНИЯ И ИСТОРИИ
        if is_authenticated:
            # Для зарегистрированных: записываем использование и историю
            app.user_manager.record_usage(user_id)
            try:
                app.user_manager.save_analysis_history(user_id, filename, analysis_result)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось сохранить историю анализа: {e}")
        else:
            # Для незарегистрированных: записываем только в guests
            # ВАЖНО: IP-лимиты уже обновлены ДО анализа (см. выше), здесь только обновляем guests
            guest = app.user_manager.record_guest_analysis(real_ip, user_agent)
            logger.info(f"👤 Гость записан: IP={real_ip}, analyses_count={guest.analyses_count}, registration_prompted={guest.registration_prompted}")
            # История анализов НЕ сохраняется для незарегистрированных
        
        # РАЗДЕЛ 6: ФОРМИРОВАНИЕ ОТВЕТА
        # Добавляем информацию о лимитах в ответ
        if is_authenticated:
            # Для зарегистрированных - получаем актуальные данные пользователя
            user = app.user_manager.get_user(user_id)
            plan = PLANS[user.plan] if user else PLANS['free']
            
            # Для бесплатного тарифа используем free_analysis_used (один анализ навсегда)
            if user and user.plan == 'free':
                remaining = 0 if user.free_analysis_used else 1
                analysis_result['usage_info'] = {
                    'free_analysis_used': user.free_analysis_used,
                    'remaining': remaining,
                    'plan_name': plan['name'],
                    'is_registered': True,
                    'available_analyses': 0
                }
            else:
                # Для платных тарифов используем available_analyses
                analysis_result['usage_info'] = {
                    'available_analyses': user.available_analyses if user else 0,
                    'plan_name': plan['name'],
                    'is_registered': True
                }
        else:
            # Для незарегистрированных показываем что бесплатный анализ использован
            analysis_result['usage_info'] = {
                'used_today': 1,
                'daily_limit': 1,
                'plan_name': 'Пробный',
                'remaining': 0,
                'free_analysis_used': True,
                'registration_required': True,
                'is_registered': False
            }
        
        # Добавляем флаг is_authenticated в результат для фронтенда
        analysis_result['is_authenticated'] = is_authenticated
        
        # Возвращаем результат (user_id только для зарегистрированных)
        response_data = {
            'success': True,
            'filename': filename,
            'result': analysis_result
        }
        
        # Добавляем user_id только если пользователь авторизован
        if is_authenticated:
            response_data['user_id'] = user_id
        
        return jsonify(response_data)

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
    
    # Проверяем авторизацию через сессию
    user_id = session.get('user_id')
    is_authenticated = bool(user_id)
    
    if not is_authenticated:
        # Для незарегистрированных: проверяем IP-лимиты
        real_ip = app.ip_limit_manager.get_client_ip(request)
        can_analyze = app.ip_limit_manager.can_analyze_by_ip(request, app.user_manager)
        used = 0 if can_analyze else 1
        
        return jsonify({
            'plan': 'free',
            'plan_name': 'Пробный',
            'used_today': used,
            'daily_limit': 1,
            'remaining': 1 - used,
            'total_used': 0,
            'is_registered': False
        })
    
    # Для зарегистрированных - получаем данные пользователя
    user = app.user_manager.get_user(user_id)
    if not user or not user.is_registered:
        return jsonify({
            'plan': 'free',
            'plan_name': 'Пробный',
            'used_today': 0,
            'daily_limit': 1,
            'remaining': 1,
            'is_registered': False
        }), 401
    
    plan = PLANS[user.plan]
    
    # Для бесплатного тарифа используем free_analysis_used (один анализ навсегда)
    if user.plan == 'free':
        remaining = 0 if user.free_analysis_used else 1
        return jsonify({
            'user_id': user_id,
            'plan': user.plan,
            'plan_name': plan['name'],
            'free_analysis_used': user.free_analysis_used,
            'remaining': remaining,
            'total_used': user.total_used,
            'is_registered': True,
            'available_analyses': 0
        })
    else:
        # Для платных тарифов используем available_analyses
        return jsonify({
            'user_id': user_id,
            'plan': user.plan,
            'plan_name': plan['name'],
            'available_analyses': user.available_analyses or 0,
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
        
        # Сначала проверяем сессию для авторизованных пользователей
        user_id = None
        if 'user_id' in session:
            user_id = session['user_id']
            logger.info(f"🔍 Calculator click: user_id из сессии = {user_id}")
        else:
            # Если нет в сессии, проверяем тело запроса
            data = request.json
            if data:
                user_id = data.get('user_id')
                logger.info(f"🔍 Calculator click: user_id из запроса = {user_id}")
        
        if user_id:
            # Используем менеджер для обновления счетчика зарегистрированного пользователя
            success = app.user_manager.record_calculator_use(user_id)
            if success:
                logger.info(f"✅ Calculator used by user {user_id}")
            else:
                logger.warning(f"⚠️ Unknown user {user_id} used calculator")
        else:
            # Записываем использование для гостя (по IP)
            real_ip = app.ip_limit_manager.get_client_ip(request)
            success = app.user_manager.record_guest_calculator_use(real_ip)
            if success:
                logger.info(f"🔸 Anonymous calculator use recorded for IP {real_ip}")
            else:
                logger.warning(f"⚠️ Failed to record calculator use for IP {real_ip}")
        
        return jsonify({'success': True, 'user_id': user_id})
        
    except Exception as e:
        logger.error(f"❌ Calculator click error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== API ДЛЯ ВОПРОСОВ И ОТВЕТОВ ==========

@api_bp.route('/questions', methods=['POST'])
def create_question():
    """Создать новый вопрос"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content') or not data.get('category'):
        return jsonify({'success': False, 'error': 'Заполните все поля'}), 400
    
    try:
        question = app.user_manager.create_question(
            user_id=session['user_id'],
            title=data['title'],
            content=data['content'],
            category=data['category']
        )
        
        return jsonify({'success': True, 'question_id': question.id, 'message': 'Вопрос создан'})
    except Exception as e:
        logger.error(f"❌ Ошибка создания вопроса: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/questions/<int:question_id>/answers', methods=['POST'])
@cross_origin(supports_credentials=True)
def create_answer(question_id):
    """Создать ответ на вопрос"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'Введите текст ответа'}), 400
    
    try:
        answer = app.user_manager.create_answer(
            question_id=question_id,
            user_id=session['user_id'],
            content=data['content']
        )
        
        return jsonify({'success': True, 'answer_id': answer.id, 'message': 'Ответ добавлен'})
    except Exception as e:
        logger.error(f"❌ Ошибка создания ответа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/answers/<int:answer_id>/like', methods=['POST'])
@cross_origin(supports_credentials=True)
def toggle_answer_like(answer_id):
    """Переключить лайк на ответе"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        result = app.user_manager.toggle_answer_like(
            answer_id=answer_id,
            user_id=session['user_id']
        )
        
        return jsonify({'success': True, **result})
    except Exception as e:
        logger.error(f"❌ Ошибка лайка: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/notifications', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_notifications():
    """Получить уведомления пользователя"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        
        notifications = app.user_manager.get_notifications(
            user_id=session['user_id'],
            limit=limit,
            unread_only=unread_only
        )
        
        unread_count = app.user_manager.get_unread_count(session['user_id'])
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'unread_count': unread_count
        })
    except Exception as e:
        logger.error(f"❌ Ошибка получения уведомлений: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@cross_origin(supports_credentials=True)
def mark_notification_read(notification_id):
    """Отметить уведомление как прочитанное"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        success = app.user_manager.mark_notification_read(notification_id, session['user_id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Уведомление не найдено'}), 404
    except Exception as e:
        logger.error(f"❌ Ошибка отметки уведомления: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/notifications/read-all', methods=['POST'])
@cross_origin(supports_credentials=True)
def mark_all_notifications_read():
    """Отметить все уведомления как прочитанные"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        count = app.user_manager.mark_all_notifications_read(session['user_id'])
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"❌ Ошибка отметки всех уведомлений: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@cross_origin(supports_credentials=True)
def delete_notification(notification_id):
    """Удалить уведомление"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        success = app.user_manager.delete_notification(notification_id, session['user_id'])
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Уведомление не найдено'}), 404
    except Exception as e:
        logger.error(f"❌ Ошибка удаления уведомления: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/questions/<int:question_id>/best-answer', methods=['POST'])
@cross_origin(supports_credentials=True)
def set_best_answer(question_id):
    """Установить лучший ответ"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    data = request.get_json()
    answer_id = data.get('answer_id')
    
    if not answer_id:
        return jsonify({'success': False, 'error': 'Укажите ID ответа'}), 400
    
    try:
        success = app.user_manager.set_best_answer(
            question_id=question_id,
            answer_id=answer_id,
            user_id=session['user_id']
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Лучший ответ установлен'})
        else:
            return jsonify({'success': False, 'error': 'Недостаточно прав или ответ не найден'}), 403
    except Exception as e:
        logger.error(f"❌ Ошибка установки лучшего ответа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/questions/<int:question_id>', methods=['PUT'])
def update_question():
    """Обновить вопрос"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    data = request.get_json()
    
    # Проверяем, что пользователь является автором вопроса
    question = app.user_manager.get_question(question_id)
    if not question or question.user_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Недостаточно прав'}), 403
    
    try:
        updated = app.user_manager.update_question(question_id, **data)
        if updated:
            return jsonify({'success': True, 'message': 'Вопрос обновлен'})
        else:
            return jsonify({'success': False, 'error': 'Вопрос не найден'}), 404
    except Exception as e:
        logger.error(f"❌ Ошибка обновления вопроса: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question():
    """Удалить вопрос"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем, что пользователь является автором вопроса
    question = app.user_manager.get_question(question_id)
    if not question or question.user_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Недостаточно прав'}), 403
    
    try:
        success = app.user_manager.delete_question(question_id)
        if success:
            return jsonify({'success': True, 'message': 'Вопрос удален'})
        else:
            return jsonify({'success': False, 'error': 'Вопрос не найден'}), 404
    except Exception as e:
        logger.error(f"❌ Ошибка удаления вопроса: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
