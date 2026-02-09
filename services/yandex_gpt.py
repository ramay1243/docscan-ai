import requests
import logging
from config import Config, SMART_ANALYSIS_CONFIG, RISK_LEVELS

logger = logging.getLogger(__name__)

def detect_document_type(text):
    """Умное определение типа документа по ключевым словам"""
    text_lower = text.lower()
    
    # Приоритетный порядок проверки - сначала более специфичные типы
    # Судебные документы проверяем первыми, так как они могут содержать слова "займ", "кредит" и т.д.
    # Затем документы с уникальными ключевыми словами, потом общие
    priority_order = [
        'court',           # Судебные документы (самые специфичные)
        'invoice',         # Счет-фактура (уникальные слова)
        'waybill',         # Накладная (уникальные слова)
        'act',             # Акт (уникальные слова)
        'power_of_attorney', # Доверенность (уникальные слова)
        'loan',            # Договор займа/кредита
        'insurance',       # Страхование (уникальные слова)
        'lease',           # Договор аренды
        'employment',      # Трудовой договор
        'contract',        # Договор подряда
        'supply',          # Договор поставки
        'nda',             # Соглашение о конфиденциальности
        'partnership',     # Договор партнерства
        'service',         # Договор оказания услуг
        'commission',      # Договор комиссии
        'agency',          # Договор агентирования
        'mandate',         # Договор поручения
        'gift',            # Договор дарения
        'exchange',        # Договор мены
        'sale',            # Договор купли-продажи
        'general'         # Общий договор (fallback)
    ]
    
    # Сначала проверяем приоритетные типы
    for doc_type in priority_order:
        if doc_type not in SMART_ANALYSIS_CONFIG:
            continue
            
        config = SMART_ANALYSIS_CONFIG[doc_type]
        
        # Проверяем все ключевые слова
        for keyword in config['keywords']:
            if keyword in text_lower:
                logger.info(f"📄 Определен тип документа: {config['name']} (по ключевому слову: '{keyword}')")
                return doc_type
    
    logger.info("📄 Документ определен как: Общий договор")
    return 'general'

def analyze_with_yandexgpt(text, document_type='general'):
    """Умный комплексный анализ документа с расширенной экспертизой"""
    # Проверяем наличие API ключей
    if not Config.YANDEX_API_KEY or not Config.YANDEX_FOLDER_ID:
        error_msg = "API ключи Yandex Cloud не настроены"
        logger.error(error_msg)
        return create_fallback_analysis(document_type, error_msg)
    try:
        doc_config = SMART_ANALYSIS_CONFIG[document_type]
        
        # Умный промпт для комплексного анализа
        system_prompt = f"""Ты - ведущий юридический эксперт с многолетним опытом. Проведи комплексный анализ документа и предоставь развернутую экспертизу.

ВАЖНО: Для договоров займа/кредита обязательно анализируй процентную ставку. Ставка выше 30% годовых - это HIGH риск, выше 40% - CRITICAL риск.

ЭКСПЕРТНАЯ ОЦЕНКА ДОКУМЕНТА:

1. ЮРИДИЧЕСКАЯ ЭКСПЕРТИЗА:
Дай развернутую оценку (минимум 2-3 предложения):
- Соответствие законодательству РФ
- Полнота существенных условий
- Ясность формулировок
- Сбалансированность прав сторон

2. ФИНАНСОВЫЙ АНАЛИЗ:
Дай развернутую оценку (минимум 2-3 предложения):
- Прозрачность финансовых условий
- Справедливость расчетов
- Риски финансовых потерь
- ОБЯЗАТЕЛЬНО укажи процентную ставку и оцени её справедливость

3. ОПЕРАЦИОННЫЕ РИСКИ:
Дай развернутую оценку (минимум 2-3 предложения):
- Реализуемость условий на практике
- Возможности для злоупотреблений

4. СТРАТЕГИЧЕСКАЯ ОЦЕНКА:
Дай развернутую оценку (минимум 2-3 предложения):
- Соответствие бизнес-целям
- Гибкость при изменении обстоятельств

Требования к ответу:
- Будь конкретен и ссылайся на конкретные пункты договора
- ОБЯЗАТЕЛЬНО выяви ВСЕ риски, особенно финансовые
- Для договоров займа: если процентная ставка выше 30% - это ВСЕГДА риск
- Предлагай практические решения

Формат ответа СТРОГО (соблюдай точно):
ЮРИДИЧЕСКАЯ ЭКСПЕРТИЗА:
[развернутая оценка минимум 2-3 предложения]

ФИНАНСОВЫЙ АНАЛИЗ: 
[развернутая оценка минимум 2-3 предложения, обязательно укажи процентную ставку]

ОПЕРАЦИОННЫЕ РИСКИ:
[развернутая оценка минимум 2-3 предложения]

СТРАТЕГИЧЕСКАЯ ОЦЕНКА:
[развернутая оценка минимум 2-3 предложения]

КЛЮЧЕВЫЕ РИСКИ:
[ОБЯЗАТЕЛЬНО укажи хотя бы 3-5 рисков в формате ниже]
CRITICAL|Название риска|Детальное описание риска
HIGH|Название риска|Детальное описание риска
MEDIUM|Название риска|Детальное описание риска

ПРАКТИЧЕСКИЕ РЕКОМЕНДАЦИИ:
- Конкретное действие|Ожидаемый эффект|Срочность
- Конкретное действие|Ожидаемый эффект|Срочность

АЛЬТЕРНАТИВНЫЕ РЕШЕНИИ:
- Вариант решения|Преимущества|Недостатки

ЭКСПЕРТНОЕ ЗАКЛЮЧЕНИЕ:
[общая оценка и выводы]"""

        headers = {
            "Authorization": f"Api-Key {Config.YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "modelUri": f"gpt://{Config.YANDEX_FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.1,
                "maxTokens": 4000
            },
            "messages": [
                {
                    "role": "system", 
                    "text": system_prompt
                },
                {
                    "role": "user",
                    "text": f"""Проведи комплексный экспертный анализ этого {doc_config['name']}:

{text[:50000]}

ВАЖНО: Проанализируй ВЕСЬ документ, включая все страницы и все условия.
Проанализируй с позиций: {', '.join(doc_config['expert_areas'])}.
Будь максимально конкретен и практичен в рекомендациях.
Обрати особое внимание на финансовые условия, процентные ставки, сроки, штрафы и неустойки."""
                }
            ]
        }
        
        logger.info(f"🧠 Запускаем умный анализ для {doc_config['name']}")
        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['result']['alternatives'][0]['message']['text']
            
            logger.info(f"✅ Получен развернутый анализ от YandexGPT")
            return parse_smart_analysis(ai_response, document_type)
        else:
            error_msg = f"Ошибка YandexGPT: {response.status_code}"
            logger.error(error_msg)
            return create_fallback_analysis(document_type, error_msg)
            
    except Exception as e:
        error_msg = f"Ошибка соединения: {str(e)}"
        logger.error(error_msg)
        return create_fallback_analysis(document_type, error_msg)

def parse_smart_analysis(ai_response, document_type):
    """Парсинг комплексного анализа от AI"""
    doc_config = SMART_ANALYSIS_CONFIG[document_type]
    
    sections = {
        'legal_expertise': '',
        'financial_analysis': '', 
        'operational_risks': '',
        'strategic_assessment': '',
        'key_risks': [],
        'practical_recommendations': [],
        'alternative_solutions': [],
        'expert_conclusion': ''
    }
    
    current_section = None
    lines = [line.strip() for line in ai_response.split('\n') if line.strip()]
    
    for line in lines:
        line_lower = line.lower()
        
        # Определяем разделы
        if 'юридическая экспертиза' in line_lower:
            current_section = 'legal_expertise'
            continue
        elif 'финансовый анализ' in line_lower:
            current_section = 'financial_analysis'
            continue
        elif 'операционные риски' in line_lower:
            current_section = 'operational_risks'
            continue
        elif 'стратегическая оценка' in line_lower:
            current_section = 'strategic_assessment'
            continue
        elif 'ключевые риски' in line_lower:
            current_section = 'key_risks'
            continue
        elif 'практические рекомендации' in line_lower:
            current_section = 'practical_recommendations'
            continue
        elif 'альтернативные решения' in line_lower:
            current_section = 'alternative_solutions'
            continue
        elif 'экспертное заключение' in line_lower:
            current_section = 'expert_conclusion'
            continue
        
        # Обрабатываем содержимое разделов
        if current_section:
            if current_section in ['legal_expertise', 'financial_analysis', 'operational_risks', 
                                 'strategic_assessment', 'expert_conclusion']:
                # Пропускаем только заголовки разделов и пустые строки
                if line and not line.startswith(('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'КЛЮЧЕВЫЕ', 'ПРАКТИЧЕСКИЕ', 'АЛЬТЕРНАТИВНЫЕ', 'ЭКСПЕРТНОЕ')):
                    # Пропускаем строки, которые являются только заголовками без текста
                    if len(line) > 10:  # Минимальная длина для содержательного текста
                        if sections[current_section]:
                            sections[current_section] += ' ' + line
                        else:
                            sections[current_section] = line
            
            elif current_section == 'key_risks':
                # Пробуем разные форматы
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        risk_level = parts[0].strip().upper()
                        risk_title = parts[1].strip()
                        risk_description = parts[2].strip()
                        
                        if risk_level in RISK_LEVELS:
                            sections['key_risks'].append({
                                'level': risk_level,
                                'title': risk_title,
                                'description': risk_description,
                                'color': RISK_LEVELS[risk_level]['color'],
                                'icon': RISK_LEVELS[risk_level]['icon']
                            })
                # Альтернативный формат: CRITICAL: Название - Описание
                elif ':' in line and any(level in line.upper() for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']):
                    for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                        if level in line.upper():
                            parts = line.split(':', 1)
                            if len(parts) >= 2:
                                title_desc = parts[1].strip()
                                if ' - ' in title_desc:
                                    title, desc = title_desc.split(' - ', 1)
                                else:
                                    title = title_desc[:50]
                                    desc = title_desc[50:] if len(title_desc) > 50 else title_desc
                                
                                sections['key_risks'].append({
                                    'level': level,
                                    'title': title.strip(),
                                    'description': desc.strip(),
                                    'color': RISK_LEVELS[level]['color'],
                                    'icon': RISK_LEVELS[level]['icon']
                                })
                            break
            
            elif current_section == 'practical_recommendations' and '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    sections['practical_recommendations'].append({
                        'action': parts[0].strip().lstrip('-• '),
                        'effect': parts[1].strip(),
                        'urgency': parts[2].strip()
                    })
            
            elif current_section == 'alternative_solutions' and '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    sections['alternative_solutions'].append({
                        'solution': parts[0].strip().lstrip('-• '),
                        'advantages': parts[1].strip(),
                        'disadvantages': parts[2].strip()
                    })
    
    # Если для договора займа не найдено рисков, но есть процентная ставка - добавляем автоматически
    if document_type == 'loan' and len(sections['key_risks']) == 0:
        # Ищем процентную ставку в тексте
        import re
        rate_patterns = [
            r'(\d+[.,]\d+)\s*%?\s*процентов?\s*годовых',
            r'процентная\s*ставка[:\s]+(\d+[.,]\d+)',
            r'(\d+[.,]\d+)\s*%?\s*годовых',
            r'ПСК[:\s]+(\d+[.,]\d+)',
            r'полная\s*стоимость[:\s]+(\d+[.,]\d+)'
        ]
        
        for pattern in rate_patterns:
            matches = re.findall(pattern, ai_response, re.IGNORECASE)
            if matches:
                try:
                    rate = float(matches[0].replace(',', '.'))
                    if rate >= 40:
                        sections['key_risks'].append({
                            'level': 'CRITICAL',
                            'title': f'Критически высокая процентная ставка {rate}% годовых',
                            'description': f'Процентная ставка {rate}% годовых значительно превышает среднерыночные значения (обычно 15-25%). Это создает высокую финансовую нагрузку на заемщика и увеличивает риск невозврата.',
                            'color': RISK_LEVELS['CRITICAL']['color'],
                            'icon': RISK_LEVELS['CRITICAL']['icon']
                        })
                    elif rate >= 30:
                        sections['key_risks'].append({
                            'level': 'HIGH',
                            'title': f'Высокая процентная ставка {rate}% годовых',
                            'description': f'Процентная ставка {rate}% годовых выше среднерыночных значений. Рекомендуется сравнить с предложениями других кредиторов.',
                            'color': RISK_LEVELS['HIGH']['color'],
                            'icon': RISK_LEVELS['HIGH']['icon']
                        })
                    break
                except ValueError:
                    continue
    
    # Создаем итоговый результат
    return create_smart_analysis_result(sections, document_type)

def create_smart_analysis_result(sections, document_type):
    """Создает структурированный результат умного анализа"""
    doc_config = SMART_ANALYSIS_CONFIG[document_type]
    
    # Подсчитываем статистику рисков
    risk_stats = {
        'CRITICAL': 0,
        'HIGH': 0, 
        'MEDIUM': 0,
        'LOW': 0,
        'total': len(sections['key_risks'])
    }
    
    for risk in sections['key_risks']:
        if risk['level'] in risk_stats:
            risk_stats[risk['level']] += 1
    
    # Определяем общий уровень риска документа
    if risk_stats['CRITICAL'] > 0:
        overall_risk = 'CRITICAL'
    elif risk_stats['HIGH'] > 0:
        overall_risk = 'HIGH' 
    elif risk_stats['MEDIUM'] > 0:
        overall_risk = 'MEDIUM'
    else:
        overall_risk = 'LOW'
    
    return {
        # Основная информация
        'document_type': document_type,
        'document_type_name': doc_config['name'],
        'expert_areas': doc_config['expert_areas'],
        'ai_used': True,
        
        # Комплексная экспертиза
        'expert_analysis': {
            'legal_expertise': sections['legal_expertise'] or 'Юридический анализ не выявил критических нарушений',
            'financial_analysis': sections['financial_analysis'] or 'Финансовые условия требуют дополнительной проверки',
            'operational_risks': sections['operational_risks'] or 'Операционные риски находятся в допустимых пределах',
            'strategic_assessment': sections['strategic_assessment'] or 'Документ соответствует базовым стратегическим целям'
        },
        
        # Детализированные риски
        'risk_analysis': {
            'key_risks': sections['key_risks'][:10],
            'overall_risk_level': overall_risk,
            'risk_statistics': risk_stats,
            'risk_summary': f"Выявлено {risk_stats['total']} рисков: {risk_stats['CRITICAL']} критических, {risk_stats['HIGH']} высоких, {risk_stats['MEDIUM']} средних"
        },
        
        # Практические рекомендации
        'recommendations': {
            'practical_actions': sections['practical_recommendations'][:8],
            'alternative_solutions': sections['alternative_solutions'][:5],
            'priority_actions': [r for r in sections['practical_recommendations'] if 'срочн' in r.get('urgency', '').lower()][:3]
        },
        
        # Визуальная сводка
        'executive_summary': {
            'risk_level': overall_risk,
            'risk_color': RISK_LEVELS[overall_risk]['color'],
            'risk_icon': RISK_LEVELS[overall_risk]['icon'],
            'risk_description': RISK_LEVELS[overall_risk]['description'],
            'quick_facts': [
                f"Обнаружено {risk_stats['total']} рисков",
                f"Критических: {risk_stats['CRITICAL']}",
                f"Высоких: {risk_stats['HIGH']}",
                f"Требует доработки: {risk_stats['CRITICAL'] + risk_stats['HIGH'] > 0}"
            ],
            'decision_support': get_decision_support(overall_risk)
        }
    }

def get_decision_support(risk_level):
    """Предоставляет поддержку для принятия решений"""
    decisions = {
        'CRITICAL': "НЕ РЕКОМЕНДУЕТСЯ к подписанию. Требуется существенная доработка с юристом.",
        'HIGH': "Требует серьезной доработки. Консультация с юристом обязательна.",
        'MEDIUM': "Может быть подписан после устранения основных замечаний.",
        'LOW': "Может быть подписан. Рекомендуется учесть выявленные рекомендации."
    }
    return decisions.get(risk_level, "Требуется дополнительный анализ.")

def create_fallback_analysis(document_type, error_msg):
    """Создает базовый анализ при ошибках"""
    doc_config = SMART_ANALYSIS_CONFIG[document_type]
    
    return {
        'document_type': document_type,
        'document_type_name': doc_config['name'],
        'expert_areas': doc_config['expert_areas'],
        'ai_used': False,
        'expert_analysis': {
            'legal_expertise': f'Ошибка анализа: {error_msg}',
            'financial_analysis': 'Анализ недоступен',
            'operational_risks': 'Анализ недоступен',
            'strategic_assessment': 'Анализ недоступен'
        },
        'risk_analysis': {
            'key_risks': [{
                'level': 'INFO',
                'title': 'Ошибка анализа',
                'description': error_msg,
                'color': '#3182ce',
                'icon': '🔵'
            }],
            'overall_risk_level': 'INFO',
            'risk_statistics': {'total': 1, 'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'risk_summary': 'Анализ не выполнен'
        },
        'executive_summary': {
            'risk_level': 'INFO',
            'risk_color': '#3182ce',
            'risk_icon': '🔵',
            'risk_description': 'Ошибка анализа',
            'quick_facts': ['Анализ не выполнен', 'Попробуйте еще раз'],
            'decision_support': 'Недостаточно данных для принятия решения'
        }
    }

            'operational_risks': sections['operational_risks'] or 'Операционные риски находятся в допустимых пределах',
            'strategic_assessment': sections['strategic_assessment'] or 'Документ соответствует базовым стратегическим целям'
        },
        
        # Детализированные риски
        'risk_analysis': {
            'key_risks': sections['key_risks'][:10],
            'overall_risk_level': overall_risk,
            'risk_statistics': risk_stats,
            'risk_summary': f"Выявлено {risk_stats['total']} рисков: {risk_stats['CRITICAL']} критических, {risk_stats['HIGH']} высоких, {risk_stats['MEDIUM']} средних"
        },
        
        # Практические рекомендации
        'recommendations': {
            'practical_actions': sections['practical_recommendations'][:8],
            'alternative_solutions': sections['alternative_solutions'][:5],
            'priority_actions': [r for r in sections['practical_recommendations'] if 'срочн' in r.get('urgency', '').lower()][:3]
        },
        
        # Визуальная сводка
        'executive_summary': {
            'risk_level': overall_risk,
            'risk_color': RISK_LEVELS[overall_risk]['color'],
            'risk_icon': RISK_LEVELS[overall_risk]['icon'],
            'risk_description': RISK_LEVELS[overall_risk]['description'],
            'quick_facts': [
                f"Обнаружено {risk_stats['total']} рисков",
                f"Критических: {risk_stats['CRITICAL']}",
                f"Высоких: {risk_stats['HIGH']}",
                f"Требует доработки: {risk_stats['CRITICAL'] + risk_stats['HIGH'] > 0}"
            ],
            'decision_support': get_decision_support(overall_risk)
        }
    }

def get_decision_support(risk_level):
    """Предоставляет поддержку для принятия решений"""
    decisions = {
        'CRITICAL': "НЕ РЕКОМЕНДУЕТСЯ к подписанию. Требуется существенная доработка с юристом.",
        'HIGH': "Требует серьезной доработки. Консультация с юристом обязательна.",
        'MEDIUM': "Может быть подписан после устранения основных замечаний.",
        'LOW': "Может быть подписан. Рекомендуется учесть выявленные рекомендации."
    }
    return decisions.get(risk_level, "Требуется дополнительный анализ.")

def create_fallback_analysis(document_type, error_msg):
    """Создает базовый анализ при ошибках"""
    doc_config = SMART_ANALYSIS_CONFIG[document_type]
    
    return {
        'document_type': document_type,
        'document_type_name': doc_config['name'],
        'expert_areas': doc_config['expert_areas'],
        'ai_used': False,
        'expert_analysis': {
            'legal_expertise': f'Ошибка анализа: {error_msg}',
            'financial_analysis': 'Анализ недоступен',
            'operational_risks': 'Анализ недоступен',
            'strategic_assessment': 'Анализ недоступен'
        },
        'risk_analysis': {
            'key_risks': [{
                'level': 'INFO',
                'title': 'Ошибка анализа',
                'description': error_msg,
                'color': '#3182ce',
                'icon': '🔵'
            }],
            'overall_risk_level': 'INFO',
            'risk_statistics': {'total': 1, 'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'risk_summary': 'Анализ не выполнен'
        },
        'executive_summary': {
            'risk_level': 'INFO',
            'risk_color': '#3182ce',
            'risk_icon': '🔵',
            'risk_description': 'Ошибка анализа',
            'quick_facts': ['Анализ не выполнен', 'Попробуйте еще раз'],
            'decision_support': 'Недостаточно данных для принятия решения'
        }
    }
