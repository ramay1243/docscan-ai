from flask import Blueprint, request, jsonify, session, send_file, redirect
from utils.logger import RussianLogger
from datetime import datetime
import tempfile
import os
import uuid
import logging
from urllib.parse import quote
from services.file_processing import extract_text_from_file, validate_file
from services.analysis import analyze_text
from services.pdf_generator import generate_analysis_pdf
from services.export_generator import generate_analysis_word, generate_analysis_excel
from services.contract_pdf_generator import generate_contract_pdf, generate_contract_pdf_from_data
from config import PLANS, CHAT_LIMITS
from flask_cors import cross_origin, CORS
from io import BytesIO

logger = logging.getLogger(__name__)

# Создаем Blueprint для API
api_bp = Blueprint('api', __name__)

def check_plan_feature(user_plan, feature_name):
    """Проверяет, доступна ли функция для тарифа пользователя"""
    from config import PLANS
    if user_plan not in PLANS:
        return False
    plan = PLANS[user_plan]
    return plan.get('features', {}).get(feature_name, False)

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
            
            # ========== ИЗМЕНЕННАЯ ЛОГИКА ==========
            # Если тариф бесплатный - сразу на покупку (без бесплатных анализов)
            if user.plan == 'free':
                return jsonify({
                    'success': False,
                    'error': '❌ Для продолжения работы необходимо приобрести тариф. Бесплатные анализы после регистрации не предоставляются.',
                    'upgrade_required': True
                }), 402
            
            # Для платных тарифов - проверяем лимиты
            if not app.user_manager.can_analyze(user_id):
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
        
        # РАЗДЕЛ 3: ПРОВЕРКА БЕЛОГО СПИСКА IP (для бизнес-тарифов)
        if is_authenticated and user:
            # Проверяем, есть ли у пользователя белый список IP
            whitelisted_ips = app.user_manager.get_whitelisted_ips(user_id)
            if whitelisted_ips:
                # Если белый список не пуст, проверяем IP
                if not app.user_manager.is_ip_whitelisted(user_id, real_ip):
                    logger.warning(f"🚫 IP {real_ip} не разрешен для пользователя {user_id} (белый список активен)")
                    return jsonify({
                        'success': False,
                        'error': '❌ Доступ разрешен только с корпоративных IP-адресов. Обратитесь к администратору для добавления вашего IP в белый список.',
                        'ip_whitelist_required': True,
                        'user_ip': real_ip
                    }), 403
        
        # РАЗДЕЛ 4: ПРОВЕРКА ТАРИФА ДЛЯ ФОТО (только для зарегистрированных)
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
                    'message': '💎 Зарегистрируйтесь и перейдите на тариф Стандарт (5 анализов за 590₽, 30 дней) или выше для анализа фото документов'
                }), 402
            
            logger.info(f"✅ Разрешено распознавание фото (тариф: {plan_type})")
        
        # РАЗДЕЛ 5: ИЗВЛЕЧЕНИЕ ТЕКСТА И АНАЛИЗ
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
        
        # Анализируем текст (передаем user_id для загрузки настроек анализа)
        analysis_result = analyze_text(
            text, 
            plan_type, 
            is_authenticated=is_authenticated,
            user_id=user_id if is_authenticated else None
        )
        
        logger.info(f"✅ АНАЛИЗ УСПЕШЕН для {'пользователя' if is_authenticated else 'гостя'}, IP: {real_ip}")
        
        # РАЗДЕЛ 6: ЗАПИСЬ ИСПОЛЬЗОВАНИЯ И ИСТОРИИ
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
        
        # РАЗДЕЛ 7: ФОРМИРОВАНИЕ ОТВЕТА
        # Добавляем информацию о лимитах в ответ
        if is_authenticated:
            # Для зарегистрированных - получаем актуальные данные пользователя
            user = app.user_manager.get_user(user_id)
            plan = PLANS[user.plan] if user else PLANS['free']
            
            # Для бесплатного тарифа используем free_analysis_used (но теперь он всегда 0 после регистрации)
            if user and user.plan == 'free':
                remaining = 0
                analysis_result['usage_info'] = {
                    'free_analysis_used': True,
                    'remaining': remaining,
                    'plan_name': plan['name'],
                    'is_registered': True,
                    'available_analyses': 0,
                    'upgrade_required': True
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
    
    # Для бесплатного тарифа - анализов нет
    if user.plan == 'free':
        return jsonify({
            'user_id': user_id,
            'plan': user.plan,
            'plan_name': plan['name'],
            'free_analysis_used': True,
            'remaining': 0,
            'total_used': user.total_used,
            'is_registered': True,
            'available_analyses': 0,
            'upgrade_required': True
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

@api_bp.route('/download-analysis', methods=['POST'])
def download_analysis():
    """Скачать анализ в PDF"""
    try:
        # Парсим JSON с обработкой ошибок
        try:
            data = request.get_json(force=True)
        except Exception as json_error:
            logger.error(f"❌ Ошибка парсинга JSON: {json_error}")
            return jsonify({'error': 'Неверный формат JSON данных'}), 400
        
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        analysis_data = data.get('analysis')
        filename = data.get('filename', 'document.pdf')
        export_format = data.get('format', 'pdf').lower()  # pdf, word, excel
        
        if not analysis_data:
            return jsonify({'error': 'Нет данных анализа'}), 400
        
        # Проверяем доступность экспорта для пользователя
        user_id = data.get('user_id') or session.get('user_id')
        if user_id:
            from app import app
            user = app.user_manager.get_user(user_id)
            if user:
                from config import PLANS
                plan = PLANS.get(user.plan, {})
                features = plan.get('features', {})
                
                # Проверяем доступность формата экспорта
                if export_format == 'pdf' and not features.get('export_pdf', False):
                    return jsonify({'error': 'Экспорт в PDF недоступен для вашего тарифа'}), 403
                elif export_format in ['word', 'docx'] and not features.get('export_word', False):
                    return jsonify({'error': 'Экспорт в Word недоступен для вашего тарифа'}), 403
                elif export_format in ['excel', 'xlsx'] and not features.get('export_excel', False):
                    return jsonify({'error': 'Экспорт в Excel недоступен для вашего тарифа'}), 403
        
        # Получаем настройки брендинга для пользователя (если авторизован)
        branding_settings = None
        try:
            user_id = data.get('user_id') or session.get('user_id')
            if user_id:
                from app import app
                try:
                    branding_settings = app.user_manager.get_branding_settings(user_id)
                except Exception as branding_error:
                    logger.warning(f"⚠️ Ошибка получения брендинга: {branding_error}")
                    branding_settings = None
        except Exception as user_error:
            logger.warning(f"⚠️ Ошибка получения user_id: {user_error}")
        
        # Генерируем файл в зависимости от формата
        file_content = None
        mime_type = None
        file_extension = None
        
        try:
            if export_format == 'word' or export_format == 'docx':
                logger.info(f"📄 Генерация Word: filename={filename}, branding={branding_settings is not None}")
                file_content = generate_analysis_word(analysis_data, filename, branding_settings)
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                file_extension = 'docx'
            elif export_format == 'excel' or export_format == 'xlsx':
                logger.info(f"📊 Генерация Excel: filename={filename}, branding={branding_settings is not None}")
                file_content = generate_analysis_excel(analysis_data, filename, branding_settings)
                mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                file_extension = 'xlsx'
            else:  # pdf по умолчанию
                logger.info(f"📄 Генерация PDF: filename={filename}, branding={branding_settings is not None}")
                file_content = generate_analysis_pdf(analysis_data, filename, branding_settings)
                mime_type = 'application/pdf'
                file_extension = 'pdf'
            
            # Проверяем, что файл был сгенерирован
            if file_content is None:
                logger.error(f"❌ Функция генерации вернула None для формата {export_format}")
                return jsonify({'error': 'Ошибка генерации файла: функция вернула пустой результат'}), 500
            
            # Проверяем тип данных
            if not isinstance(file_content, bytes):
                logger.error(f"❌ file_content не является bytes, тип: {type(file_content)}")
                # Пытаемся преобразовать в bytes
                if isinstance(file_content, BytesIO):
                    file_content = file_content.getvalue()
                elif hasattr(file_content, 'read'):
                    file_content = file_content.read()
                else:
                    return jsonify({'error': f'Ошибка: неправильный тип данных файла: {type(file_content)}'}), 500
                
        except TypeError as e:
            logger.error(f"❌ Ошибка типа при генерации {export_format}: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Трассировка: {error_trace}")
            return jsonify({'error': f'Ошибка генерации файла: неправильные аргументы функции. {str(e)}'}), 500
        except Exception as e:
            logger.error(f"❌ Ошибка при генерации {export_format}: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Трассировка: {error_trace}")
            return jsonify({'error': f'Ошибка генерации файла: {str(e)}'}), 500
        
        from flask import Response, make_response
        
        # Подготавливаем имя файла для заголовка Content-Disposition
        try:
            # Проверяем, что file_content - это bytes
            if not isinstance(file_content, bytes):
                logger.error(f"❌ file_content не является bytes, тип: {type(file_content)}")
                return jsonify({'error': 'Ошибка: файл не в правильном формате'}), 500
            
            # Создаем безопасное имя файла БЕЗ кириллицы для заголовка
            # Используем только латиницу, цифры и безопасные символы
            base_filename = filename.rsplit(".", 1)[0] if "." in filename else filename
            # Транслитерируем кириллицу в латиницу (простая замена)
            translit_map = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
                'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
                'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
                'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
                'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
                'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
                'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
                'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
                'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
                'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
            }
            safe_filename = ''.join(translit_map.get(c, c) if c.isalpha() else (c if c.isalnum() or c in (' ', '-', '_') else '_') for c in base_filename)
            safe_filename = safe_filename.strip()[:50] or "document"
            timestamp = datetime.now().strftime("%Y%m%d")
            download_filename = f"analysis_{safe_filename}_{timestamp}.{file_extension}"
            
            logger.info(f"📤 Отправка файла: формат={export_format}, размер={len(file_content)} bytes, имя={download_filename}")
            
            # Создаем Response с упрощенными заголовками (без кириллицы в имени)
            response = make_response(file_content)
            response.headers['Content-Type'] = mime_type
            response.headers['Content-Disposition'] = f'attachment; filename="{download_filename}"'
            response.headers['Content-Length'] = str(len(file_content))
            
            logger.info(f"✅ Файл экспортирован: формат={export_format}, файл={filename}")
            return response
            
        except Exception as response_error:
            logger.error(f"❌ Ошибка создания Response: {response_error}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Трассировка: {error_trace}")
            # ВАЖНО: возвращаем JSON, а не пробрасываем исключение
            return jsonify({'error': f'Ошибка создания ответа: {str(response_error)}'}), 500
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка экспорта: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Полная трассировка: {error_trace}")
        return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500


@api_bp.route('/contracts/generate-pdf', methods=['POST'])
@cross_origin()
def generate_contract_pdf_endpoint():
    """Генерация PDF договора (для конструктора /business-ip)."""
    try:
        data = request.get_json(force=True) or {}
        contract = data.get('contract')
        title = (data.get('title') or 'Договор').strip()
        text = (data.get('text') or '').strip()

        # Новый режим: структурные данные
        if isinstance(contract, dict):
            pdf_bytes = generate_contract_pdf_from_data(contract)
        else:
            # Legacy режим: текст
            if not text or len(text) < 20:
                return jsonify({'error': 'Нет текста договора для генерации PDF'}), 400

            pdf_bytes = generate_contract_pdf(title=title, text=text)

        from flask import make_response
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename="contract.pdf"'
        response.headers['Content-Length'] = str(len(pdf_bytes))
        return response

    except Exception as e:
        logger.error(f"❌ Ошибка генерации PDF договора: {e}")
        return jsonify({'error': f'Ошибка генерации PDF: {str(e)}'}), 500

@api_bp.route('/')
def api_info():
    """Информация о API"""
    return jsonify({
        'message': 'DocScan API работает!',
        'status': 'active',
        'ai_available': True,
        'pdf_export': True,
        'word_export': True,
        'excel_export': True,
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

@api_bp.route('/questions/<int:question_id>/mark-solved', methods=['POST'])
@cross_origin(supports_credentials=True)
def mark_question_solved(question_id):
    """Отметить вопрос как решенный"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        success = app.user_manager.mark_question_solved(
            question_id=question_id,
            user_id=session['user_id']
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Вопрос отмечен как решенный'})
        else:
            return jsonify({'success': False, 'error': 'Недостаточно прав или вопрос не найден'}), 403
    except Exception as e:
        logger.error(f"❌ Ошибка отметки вопроса как решенного: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/questions/<int:question_id>/mark-open', methods=['POST'])
@cross_origin(supports_credentials=True)
def mark_question_open(question_id):
    """Вернуть вопрос в статус открытого"""
    from app import app
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        success = app.user_manager.mark_question_open(
            question_id=question_id,
            user_id=session['user_id']
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Вопрос возвращен в статус открытого'})
        else:
            return jsonify({'success': False, 'error': 'Недостаточно прав или вопрос не найден'}), 403
    except Exception as e:
        logger.error(f"❌ Ошибка возврата вопроса в статус открытого: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id):
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
def delete_question(question_id):
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

# ========== API ДЛЯ КАСТОМНОГО БРЕНДИНГА (ПОЛЬЗОВАТЕЛИ) ==========

@api_bp.route('/user/branding', methods=['GET'])
def get_user_branding():
    """Получить настройки брендинга для текущего пользователя"""
    from app import app
    from config import PLANS
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем тариф (только premium/business)
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    # Проверяем доступность кастомного брендинга для тарифа
    if not check_plan_feature(user.plan, 'custom_branding'):
        return jsonify({'success': False, 'error': 'Кастомный брендинг доступен только для тарифа Премиум и выше'}), 403
    
    try:
        branding = app.user_manager.get_branding_settings(user_id)
        return jsonify({
            'success': True,
            'branding': branding
        })
    except Exception as e:
        logger.error(f"❌ Ошибка получения настроек брендинга: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/branding', methods=['POST'])
def save_user_branding():
    """Сохранить настройки брендинга для текущего пользователя"""
    from app import app
    from config import PLANS
    from werkzeug.utils import secure_filename
    import uuid
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем тариф (только premium/business)
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    # Проверяем доступность кастомного брендинга для тарифа
    if not check_plan_feature(user.plan, 'custom_branding'):
        return jsonify({'success': False, 'error': 'Кастомный брендинг доступен только для тарифа Премиум и выше'}), 403
    
    try:
        # Получаем данные формы
        primary_color = request.form.get('primary_color')
        secondary_color = request.form.get('secondary_color')
        company_name = request.form.get('company_name')
        
        # Обработка загрузки логотипа
        logo_path = None
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                # Проверяем расширение
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
                filename = secure_filename(logo_file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                if file_ext not in allowed_extensions:
                    return jsonify({'success': False, 'error': 'Недопустимый формат файла. Разрешены: PNG, JPG, JPEG, GIF, SVG'}), 400
                
                # Проверяем размер файла (макс. 2MB)
                logo_file.seek(0, os.SEEK_END)
                file_size = logo_file.tell()
                logo_file.seek(0)
                if file_size > 2 * 1024 * 1024:  # 2MB
                    return jsonify({'success': False, 'error': 'Размер файла превышает 2MB'}), 400
                
                # Создаем папку для логотипов, если её нет
                logos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logos')
                os.makedirs(logos_dir, exist_ok=True)
                
                # Генерируем уникальное имя файла
                unique_filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
                logo_path = os.path.join(logos_dir, unique_filename)
                
                # Сохраняем файл
                logo_file.save(logo_path)
                logger.info(f"✅ Логотип сохранен пользователем {user_id}: {logo_path}")
                
                # Удаляем старый логотип, если есть
                old_branding = app.user_manager.get_branding_settings(user_id)
                if old_branding and old_branding.get('logo_path') and os.path.exists(old_branding['logo_path']):
                    try:
                        os.remove(old_branding['logo_path'])
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось удалить старый логотип: {e}")
        
        # Сохраняем настройки
        result = app.user_manager.save_branding_settings(
            user_id=user_id,
            logo_path=logo_path,
            primary_color=primary_color,
            secondary_color=secondary_color,
            company_name=company_name
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения настроек брендинга: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/branding/toggle', methods=['POST'])
def toggle_user_branding():
    """Включить/выключить брендинг для текущего пользователя"""
    from app import app
    from config import PLANS
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем тариф (только premium/business)
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    # Проверяем доступность кастомного брендинга для тарифа
    if not check_plan_feature(user.plan, 'custom_branding'):
        return jsonify({'success': False, 'error': 'Кастомный брендинг доступен только для тарифа Премиум и выше'}), 403
    
    try:
        result = app.user_manager.toggle_branding(user_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"❌ Ошибка переключения брендинга: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/branding', methods=['DELETE'])
def delete_user_branding():
    """Удалить настройки брендинга для текущего пользователя"""
    from app import app
    from config import PLANS
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем тариф (только premium/business)
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    # Проверяем доступность кастомного брендинга для тарифа
    if not check_plan_feature(user.plan, 'custom_branding'):
        return jsonify({'success': False, 'error': 'Кастомный брендинг доступен только для тарифа Премиум и выше'}), 403
    
    try:
        result = app.user_manager.delete_branding(user_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"❌ Ошибка удаления брендинга: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/api-keys', methods=['GET'])
def get_user_api_keys():
    """Получить список API-ключей текущего пользователя"""
    from app import app
    from utils.api_key_manager import APIKeyManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем тариф (только premium/business)
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    if not check_plan_feature(user.plan, 'api_access'):
        return jsonify({'success': False, 'error': 'API-ключи доступны только для бизнес-тарифов'}), 403
    
    try:
        keys = APIKeyManager.get_user_api_keys(user_id)
        return jsonify({'success': True, 'keys': keys})
    except Exception as e:
        logger.error(f"❌ Ошибка получения API-ключей: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/api-keys/create', methods=['POST'])
def create_user_api_key():
    """Создать новый API-ключ для текущего пользователя"""
    from app import app
    from utils.api_key_manager import APIKeyManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем тариф (только premium/business)
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    if not check_plan_feature(user.plan, 'api_access'):
        return jsonify({'success': False, 'error': 'API-ключи доступны только для бизнес-тарифов'}), 403
    
    data = request.get_json()
    name = data.get('name') if data else None
    
    try:
        api_key, error = APIKeyManager.create_api_key(user_id, name)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({
            'success': True,
            'api_key': api_key,
            'message': 'API-ключ успешно создан'
        })
    except Exception as e:
        logger.error(f"❌ Ошибка создания API-ключа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/api-keys/<int:api_key_id>/deactivate', methods=['POST'])
def deactivate_user_api_key(api_key_id):
    """Деактивировать API-ключ текущего пользователя"""
    from app import app
    from utils.api_key_manager import APIKeyManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        success, error = APIKeyManager.deactivate_api_key(api_key_id, user_id)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'API-ключ деактивирован'})
    except Exception as e:
        logger.error(f"❌ Ошибка деактивации API-ключа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/api-keys/<int:api_key_id>/activate', methods=['POST'])
def activate_user_api_key(api_key_id):
    """Активировать API-ключ текущего пользователя"""
    from app import app
    from models.sqlite_users import APIKey, db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        key = APIKey.query.filter_by(id=api_key_id, user_id=user_id).first()
        if not key:
            return jsonify({'success': False, 'error': 'API-ключ не найден'}), 404
        
        key.is_active = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'API-ключ активирован'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Ошибка активации API-ключа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/api-keys/<int:api_key_id>/delete', methods=['POST'])
def delete_user_api_key(api_key_id):
    """Удалить API-ключ текущего пользователя"""
    from app import app
    from utils.api_key_manager import APIKeyManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        success, error = APIKeyManager.delete_api_key(api_key_id, user_id)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'API-ключ удален'})
    except Exception as e:
        logger.error(f"❌ Ошибка удаления API-ключа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/analysis-settings', methods=['GET'])
def get_user_analysis_settings():
    """Получить настройки анализа текущего пользователя"""
    from app import app
    from utils.analysis_settings_manager import AnalysisSettingsManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем тариф (только premium/business)
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    if not check_plan_feature(user.plan, 'advanced_settings'):
        return jsonify({'success': False, 'error': 'Расширенные настройки анализа доступны только для тарифа Премиум и выше'}), 403
    
    try:
        settings = AnalysisSettingsManager.get_user_settings(user_id)
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        logger.error(f"❌ Ошибка получения настроек анализа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/analysis-settings', methods=['POST'])
def save_user_analysis_settings():
    """Сохранить настройки анализа текущего пользователя"""
    from app import app
    from utils.analysis_settings_manager import AnalysisSettingsManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем тариф (только premium/business)
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    if not check_plan_feature(user.plan, 'advanced_settings'):
        return jsonify({'success': False, 'error': 'Расширенные настройки анализа доступны только для тарифа Премиум и выше'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Данные не предоставлены'}), 400
    
    try:
        success, error = AnalysisSettingsManager.save_user_settings(user_id, data)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'Настройки анализа сохранены'})
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения настроек анализа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/analysis-settings/reset', methods=['POST'])
def reset_user_analysis_settings():
    """Сбросить настройки анализа к умолчанию"""
    from app import app
    from utils.analysis_settings_manager import AnalysisSettingsManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        success, error = AnalysisSettingsManager.reset_to_default(user_id)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'Настройки сброшены к умолчанию'})
    except Exception as e:
        logger.error(f"❌ Ошибка сброса настроек: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/analysis-templates', methods=['GET'])
def get_user_analysis_templates():
    """Получить все шаблоны настроек анализа текущего пользователя"""
    from app import app
    from utils.analysis_settings_manager import AnalysisSettingsManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        templates = AnalysisSettingsManager.get_user_templates(user_id)
        return jsonify({'success': True, 'templates': templates})
    except Exception as e:
        logger.error(f"❌ Ошибка получения шаблонов: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/analysis-templates', methods=['POST'])
def create_user_analysis_template():
    """Создать шаблон настроек анализа"""
    from app import app
    from utils.analysis_settings_manager import AnalysisSettingsManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    data = request.get_json()
    template_name = data.get('name') if data else None
    settings_data = data.get('settings') if data else {}
    
    if not template_name:
        return jsonify({'success': False, 'error': 'Название шаблона не указано'}), 400
    
    try:
        success, error = AnalysisSettingsManager.create_template(user_id, template_name, settings_data)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'Шаблон создан'})
    except Exception as e:
        logger.error(f"❌ Ошибка создания шаблона: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/analysis-templates/<int:template_id>/apply', methods=['POST'])
def apply_user_analysis_template(template_id):
    """Применить шаблон настроек анализа"""
    from app import app
    from utils.analysis_settings_manager import AnalysisSettingsManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        success, error = AnalysisSettingsManager.apply_template(user_id, template_id)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'Шаблон применен'})
    except Exception as e:
        logger.error(f"❌ Ошибка применения шаблона: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/analysis-templates/<int:template_id>', methods=['DELETE'])
def delete_user_analysis_template(template_id):
    """Удалить шаблон настроек анализа"""
    from app import app
    from utils.analysis_settings_manager import AnalysisSettingsManager
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        success, error = AnalysisSettingsManager.delete_template(user_id, template_id)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'Шаблон удален'})
    except Exception as e:
        logger.error(f"❌ Ошибка удаления шаблона: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/batch-processing', methods=['POST'])
def create_batch_task():
    """Создать новую пакетную задачу обработки документов"""
    from app import app
    from utils.batch_processor import BatchProcessor
    import tempfile
    import uuid
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    # Проверяем тариф (только premium/business)
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    if not check_plan_feature(user.plan, 'batch_processing'):
        return jsonify({'success': False, 'error': 'Пакетная обработка доступна только для бизнес-тарифов'}), 403
    
    try:
        # Получаем файлы
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'Файлы не загружены'}), 400
        
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({'success': False, 'error': 'Не выбрано ни одного файла'}), 400
        
        # Проверяем лимит пакетной обработки для тарифа
        from config import PLANS
        plan = PLANS.get(user.plan, {})
        batch_limit = plan.get('features', {}).get('batch_limit', 0)
        if batch_limit == -1:
            # Безлимит
            pass
        elif len(files) > batch_limit:
            return jsonify({'success': False, 'error': f'Максимум {batch_limit} файлов за раз для вашего тарифа'}), 400
        
        task_name = request.form.get('task_name', f'Пакетная обработка {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        
        # Создаем задачу
        task_id, error = BatchProcessor.create_batch_task(user_id, task_name, len(files))
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        # Сохраняем файлы и добавляем в задачу
        saved_files = []
        temp_dir = os.path.join(tempfile.gettempdir(), f'batch_{task_id}')
        os.makedirs(temp_dir, exist_ok=True)
        
        for file in files:
            if file.filename == '':
                continue
            
            # Валидация файла
            is_valid, validation_message = validate_file(file)
            if not is_valid:
                # Добавляем файл с ошибкой валидации
                file_id, error = BatchProcessor.add_file_to_task(task_id, file.filename, None)
                if file_id:
                    # Обновляем статус файла на failed с сообщением об ошибке
                    from models.sqlite_users import BatchProcessingFile
                    file_record = BatchProcessingFile.query.get(file_id)
                    if file_record:
                        file_record.status = 'failed'
                        file_record.error_message = validation_message
                        db.session.commit()
                continue
            
            # Сохраняем файл
            file_ext = os.path.splitext(file.filename)[1]
            temp_filename = f"{uuid.uuid4()}{file_ext}"
            temp_path = os.path.join(temp_dir, temp_filename)
            file.save(temp_path)
            
            # Добавляем в задачу
            file_id, error = BatchProcessor.add_file_to_task(task_id, file.filename, temp_path)
            if file_id:
                saved_files.append(file_id)
        
        # Запускаем обработку в фоне
        BatchProcessor.process_batch_task_async(task_id, user_id, app)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Пакетная задача создана и запущена'
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания пакетной задачи: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/batch-processing/<int:task_id>', methods=['GET'])
def get_batch_task_status(task_id):
    """Получить статус пакетной задачи"""
    from app import app
    from utils.batch_processor import BatchProcessor
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        task_dict, error = BatchProcessor.get_task_status(task_id)
        if error:
            return jsonify({'success': False, 'error': error}), 404
        
        # Проверяем, что задача принадлежит пользователю
        if task_dict['user_id'] != user_id:
            return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
        
        # Получаем файлы задачи
        files = BatchProcessor.get_task_files(task_id)
        task_dict['files'] = files
        
        return jsonify({'success': True, 'task': task_dict})
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса задачи: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/batch-processing', methods=['GET'])
def get_user_batch_tasks():
    """Получить все пакетные задачи пользователя"""
    from app import app
    from utils.batch_processor import BatchProcessor
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        tasks = BatchProcessor.get_user_tasks(user_id)
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        logger.error(f"❌ Ошибка получения задач пользователя: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/document-comparison', methods=['POST'])
def create_document_comparison():
    """Создать задачу сравнения документов"""
    from app import app
    from utils.document_comparator import DocumentComparator
    import tempfile
    import uuid
    import os
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    user = app.user_manager.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
    
    if not check_plan_feature(user.plan, 'document_comparison'):
        return jsonify({'success': False, 'error': 'Сравнение документов доступно только для бизнес-тарифов'}), 403
    
    try:
        # Проверяем лимит сравнений для тарифа
        from config import PLANS
        plan = PLANS.get(user.plan, {})
        comparison_limit = plan.get('features', {}).get('comparison_limit', 0)
        if comparison_limit != -1:
            # Проверяем количество сравнений пользователя за текущий месяц
            from models.sqlite_users import DocumentComparison
            from datetime import datetime
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            comparisons_this_month = DocumentComparison.query.filter(
                DocumentComparison.user_id == user_id,
                DocumentComparison.created_at >= current_month_start.isoformat()
            ).count()
            if comparisons_this_month >= comparison_limit:
                return jsonify({'success': False, 'error': f'Достигнут лимит сравнений для вашего тарифа ({comparison_limit} в месяц)'}), 403
        
        # Проверяем наличие файлов
        if 'original_file' not in request.files or 'modified_file' not in request.files:
            return jsonify({'success': False, 'error': 'Необходимо загрузить оба файла'}), 400
        
        original_file = request.files['original_file']
        modified_file = request.files['modified_file']
        
        if original_file.filename == '' or modified_file.filename == '':
            return jsonify({'success': False, 'error': 'Оба файла должны быть выбраны'}), 400
        
        # Валидация файлов
        from services.file_processing import validate_file
        is_valid_orig, msg_orig = validate_file(original_file)
        if not is_valid_orig:
            return jsonify({'success': False, 'error': f'Ошибка валидации оригинального файла: {msg_orig}'}), 400
        
        is_valid_mod, msg_mod = validate_file(modified_file)
        if not is_valid_mod:
            return jsonify({'success': False, 'error': f'Ошибка валидации измененного файла: {msg_mod}'}), 400
        
        # Сохраняем файлы во временную директорию
        temp_dir = os.path.join(tempfile.gettempdir(), f'comparison_{uuid.uuid4()}')
        os.makedirs(temp_dir, exist_ok=True)
        
        original_ext = os.path.splitext(original_file.filename)[1]
        modified_ext = os.path.splitext(modified_file.filename)[1]
        
        original_path = os.path.join(temp_dir, f'original_{uuid.uuid4()}{original_ext}')
        modified_path = os.path.join(temp_dir, f'modified_{uuid.uuid4()}{modified_ext}')
        
        original_file.save(original_path)
        modified_file.save(modified_path)
        
        # Создаем задачу сравнения
        comparison_id, error = DocumentComparator.create_comparison(
            user_id=user_id,
            original_filename=original_file.filename,
            original_path=original_path,
            modified_filename=modified_file.filename,
            modified_path=modified_path
        )
        
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        # Запускаем сравнение в фоне
        import threading
        def compare_in_background():
            with app.app_context():
                DocumentComparator.compare_documents(comparison_id, user_id, app)
        
        thread = threading.Thread(target=compare_in_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'comparison_id': comparison_id,
            'message': 'Сравнение документов запущено'
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания сравнения: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/document-comparison', methods=['GET'])
def get_user_comparisons():
    """Получить все сравнения пользователя"""
    from app import app
    from utils.document_comparator import DocumentComparator
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        comparisons = DocumentComparator.get_user_comparisons(user_id)
        return jsonify({'success': True, 'comparisons': comparisons})
    except Exception as e:
        logger.error(f"❌ Ошибка получения сравнений: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/document-comparison/<int:comparison_id>', methods=['GET'])
def get_comparison(comparison_id):
    """Получить конкретное сравнение"""
    from app import app
    from utils.document_comparator import DocumentComparator
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Требуется авторизация'}), 401
    
    try:
        comparison, error = DocumentComparator.get_comparison(comparison_id, user_id)
        if error:
            return jsonify({'success': False, 'error': error}), 404
        
        return jsonify({'success': True, 'comparison': comparison})
    except Exception as e:
        logger.error(f"❌ Ошибка получения сравнения: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/chat/ask', methods=['POST'])
@cross_origin()
def chat_ask():
    """Обработка вопроса в юридическом чате"""
    from app import app
    from config import CHAT_LIMITS
    from datetime import datetime
    from models.sqlite_users import db
    from models.sqlite_users import ChatMessage
    
    try:
        # Проверка авторизации
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Для использования чата необходимо войти в аккаунт',
                'login_required': True
            }), 401
        
        # Получаем пользователя
        user = app.user_manager.get_user(user_id)
        if not user or not user.is_registered:
            return jsonify({
                'success': False,
                'error': 'Пользователь не найден. Пожалуйста, войдите заново.',
                'login_required': True
            }), 401
        
        # Проверка тарифа
        user_plan = user.plan
        if user_plan not in CHAT_LIMITS:
            user_plan = 'free'  # Fallback на бесплатный
        
        chat_limit = CHAT_LIMITS.get(user_plan, 1)  # По умолчанию 1 для free
        
        # Подсчитываем вопросы за сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        messages_today = ChatMessage.query.filter(
            ChatMessage.user_id == user_id,
            ChatMessage.created_at.like(f'{today}%')
        ).count()
        
        # Проверка лимита
        if messages_today >= chat_limit:
            return jsonify({
                'success': False,
                'error': f'Достигнут дневной лимит ({chat_limit} вопросов). Лимит обновится завтра в 00:00.',
                'limit_reached': True,
                'used': messages_today,
                'limit': chat_limit
            }), 429
        
        # Получаем вопрос
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Вопрос не может быть пустым'
            }), 400
        
        # Импортируем функцию для работы с Yandex GPT
        from services.yandex_gpt import ask_yandex_gpt
        
        # Получаем ответ от ИИ
        answer = ask_yandex_gpt(question)
        
        if not answer:
            return jsonify({
                'success': False,
                'error': 'Не удалось получить ответ от ИИ. Попробуйте еще раз.'
            }), 500
        
        # Сохраняем вопрос и ответ в БД
        try:
            chat_message = ChatMessage(
                user_id=user_id,
                question=question,
                answer=answer,
                is_legal=True,  # Пока считаем все вопросы юридическими
                created_at=datetime.now().isoformat()
            )
            db.session.add(chat_message)
            db.session.commit()
        except Exception as db_error:
            logger.error(f"❌ Ошибка сохранения сообщения в БД: {db_error}")
            # Не прерываем выполнение, просто логируем ошибку
        
        # Обновляем счетчик
        messages_today += 1
        remaining = chat_limit - messages_today
        
        logger.info(f"💬 Чат: пользователь {user_id} задал вопрос (использовано {messages_today}/{chat_limit})")
        
        return jsonify({
            'success': True,
            'answer': answer,
            'limits': {
                'used': messages_today,
                'limit': chat_limit,
                'remaining': remaining
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка в чате: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при обработке вопроса. Попробуйте еще раз.'
        }), 500

@api_bp.route('/chat/limits', methods=['GET'])
@cross_origin()
def chat_limits():
    """Получить информацию о лимитах чата для текущего пользователя"""
    from app import app
    from config import CHAT_LIMITS
    from datetime import datetime
    from models.sqlite_users import db
    from models.sqlite_users import ChatMessage
    
    try:
        # Проверка авторизации
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Для использования чата необходимо войти в аккаунт',
                'login_required': True
            }), 401
        
        # Получаем пользователя
        user = app.user_manager.get_user(user_id)
        if not user or not user.is_registered:
            return jsonify({
                'success': False,
                'error': 'Пользователь не найден',
                'login_required': True
            }), 401
        
        # Проверка тарифа
        user_plan = user.plan
        if user_plan not in CHAT_LIMITS:
            user_plan = 'free'
        
        chat_limit = CHAT_LIMITS.get(user_plan, 0)
        
        # Подсчитываем вопросы за сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        messages_today = ChatMessage.query.filter(
            ChatMessage.user_id == user_id,
            ChatMessage.created_at.like(f'{today}%')
        ).count()
        
        remaining = max(0, chat_limit - messages_today)
        
        return jsonify({
            'success': True,
            'plan': user_plan,
            'plan_name': PLANS.get(user_plan, {}).get('name', 'Неизвестный'),
            'used': messages_today,
            'limit': chat_limit,
            'remaining': remaining,
            'available': chat_limit > 0
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения лимитов чата: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения информации о лимитах'
        }), 500