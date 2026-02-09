import logging
from services.yandex_gpt import detect_document_type, analyze_with_yandexgpt
from config import PLANS, SMART_ANALYSIS_CONFIG, RISK_LEVELS

logger = logging.getLogger(__name__)

def analyze_text(text, user_plan='free', is_authenticated=False):
    """Умная функция анализа с определением типа документа"""
    
    # Определяем тип документа
    document_type = detect_document_type(text)
    doc_config = SMART_ANALYSIS_CONFIG[document_type]
    
    logger.info(f"🔍 Анализируем документ типа: {doc_config['name']}, план пользователя: {user_plan}, зарегистрирован: {is_authenticated}")
    
    # Проверяем доступ к AI по тарифу
    if PLANS[user_plan]['ai_access']:
        result = analyze_with_yandexgpt(text, document_type)
        if result['ai_used']:
            # Если пользователь не зарегистрирован - создаем краткую версию
            if not is_authenticated:
                return create_guest_analysis(result)
            return result
    
    # Если AI недоступен, используем улучшенный локальный анализ
    basic_result = create_basic_analysis(text, document_type)
    # Для незарегистрированных - создаем краткую версию
    if not is_authenticated:
        return create_guest_analysis(basic_result)
    return basic_result

def create_basic_analysis(text, document_type):
    """Базовый анализ для случаев когда AI недоступен"""
    doc_config = SMART_ANALYSIS_CONFIG[document_type]
    
    return {
        'document_type': document_type,
        'document_type_name': doc_config['name'],
        'expert_areas': doc_config['expert_areas'],
        'ai_used': False,
        'expert_analysis': {
            'legal_expertise': 'Для полного юридического анализа требуется AI-экспертиза',
            'financial_analysis': 'Активируйте платный тариф для финансового анализа',
            'operational_risks': 'Расширенный анализ рисков доступен в премиум-версии',
            'strategic_assessment': 'Стратегическая оценка требует AI-анализа'
        },
        'risk_analysis': {
            'key_risks': [{
                'level': 'INFO',
                'title': 'Ограниченный анализ',
                'description': 'Для полного анализа рисков активируйте платный тариф',
                'color': '#3182ce',
                'icon': '🔵'
            }],
            'overall_risk_level': 'INFO',
            'risk_statistics': {'total': 1, 'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'risk_summary': 'Требуется расширенный анализ'
        },
        'executive_summary': {
            'risk_level': 'INFO',
            'risk_color': '#3182ce',
            'risk_icon': '🔵',
            'risk_description': 'Требуется расширенный анализ',
            'quick_facts': ['Доступен только базовый анализ', 'Активируйте платный тариф для полной экспертизы'],
            'decision_support': 'Рекомендуется провести расширенный анализ перед принятием решения'
        }
    }

def parse_fallback_response(ai_response):
    """Резервный парсинг для неструктурированных ответов"""
    risks = []
    recommendations = []
    
    lines = [line.strip() for line in ai_response.split('\n') if line.strip()]
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Ищем риски по ключевым словам
        if any(word in line_lower for word in ['риск', 'опасность', 'проблема', 'недостаток', 'слабое место', 'угроза']):
            # Берем следующие несколько строк как описание риска
            for j in range(i+1, min(i+4, len(lines))):
                next_line = lines[j]
                if next_line and len(next_line) > 20 and not next_line.lower().startswith('рекомендац'):
                    risks.append(next_line)
                    break
        
        # Ищем рекомендации по ключевым словам
        elif any(word in line_lower for word in ['рекомендац', 'совет', 'следует', 'рекомендуется', 'улучшить', 'добавить']):
            # Берем следующие несколько строк как рекомендацию
            for j in range(i+1, min(i+4, len(lines))):
                next_line = lines[j]
                if next_line and len(next_line) > 20 and not next_line.lower().startswith('риск'):
                    recommendations.append(next_line)
                    break
    
    return risks, recommendations

def create_guest_analysis(full_analysis):
    """Создает краткую версию анализа для незарегистрированных пользователей"""
    # Берем только самые критичные риски (максимум 3)
    key_risks = full_analysis.get('risk_analysis', {}).get('key_risks', [])
    
    # Убеждаемся что key_risks это список
    if not isinstance(key_risks, list):
        key_risks = []
    
    # Фильтруем только CRITICAL и HIGH риски, берем первые 3
    critical_risks = [r for r in key_risks if isinstance(r, dict) and r.get('level') in ['CRITICAL', 'HIGH']][:3]
    
    # Если критичных рисков нет, берем первые 2 любых
    if not critical_risks:
        critical_risks = [r for r in key_risks if isinstance(r, dict)][:2]
    
    # Создаем краткое описание
    risk_stats = full_analysis.get('risk_analysis', {}).get('risk_statistics', {})
    total_risks = risk_stats.get('total', 0)
    critical_count = risk_stats.get('CRITICAL', 0)
    high_count = risk_stats.get('HIGH', 0)
    
    # Краткое описание на основе уровня риска
    risk_level = full_analysis.get('executive_summary', {}).get('risk_level', 'MEDIUM')
    if risk_level == 'CRITICAL':
        brief_description = f"⚠️ Обнаружено {total_risks} рисков, из них {critical_count} критических. Документ требует серьезной доработки."
    elif risk_level == 'HIGH':
        brief_description = f"⚠️ Обнаружено {total_risks} рисков, из них {high_count} высоких. Рекомендуется доработка."
    elif risk_level == 'MEDIUM':
        brief_description = f"ℹ️ Обнаружено {total_risks} рисков среднего уровня. Документ требует внимательного изучения."
    else:
        brief_description = f"✅ Обнаружено {total_risks} незначительных рисков. Документ в целом безопасен."
    
    # Создаем краткую версию
    guest_analysis = {
        'document_type': full_analysis.get('document_type'),
        'document_type_name': full_analysis.get('document_type_name'),
        'expert_areas': full_analysis.get('expert_areas'),
        'ai_used': full_analysis.get('ai_used', False),
        'is_guest': True,  # Флаг что это краткая версия
        
        # Краткая экспертиза (только общее описание)
        'expert_analysis': {
            'legal_expertise': brief_description,
            'financial_analysis': 'Для получения детального финансового анализа зарегистрируйтесь на сайте.',
            'operational_risks': None,
            'strategic_assessment': None
        },
        
        # Только критичные риски
        'risk_analysis': {
            'key_risks': critical_risks,
            'overall_risk_level': risk_level,
            'risk_statistics': risk_stats,
            'risk_summary': f"Выявлено {total_risks} рисков: {critical_count} критических, {high_count} высоких"
        },
        
        # Без рекомендаций для гостей
        'recommendations': None,
        
        # Краткая сводка
        'executive_summary': {
            'risk_level': risk_level,
            'risk_color': full_analysis.get('executive_summary', {}).get('risk_color', '#f8961e'),
            'risk_icon': full_analysis.get('executive_summary', {}).get('risk_icon', '⚠️'),
            'risk_description': brief_description,
            'quick_facts': [
                f"Обнаружено {total_risks} рисков",
                f"Критических: {critical_count}",
                f"Высоких: {high_count}"
            ],
            'decision_support': full_analysis.get('executive_summary', {}).get('decision_support', 'Требуется расширенный анализ')
        }
    }
    
    return guest_analysis

def get_decision_support(risk_level):
    """Предоставляет поддержку для принятия решений"""
    decisions = {
        'CRITICAL': "НЕ РЕКОМЕНДУЕТСЯ к подписанию. Требуется существенная доработка с юристом.",
        'HIGH': "Требует серьезной доработки. Консультация с юристом обязательна.",
        'MEDIUM': "Может быть подписан после устранения основных замечаний.",
        'LOW': "Может быть подписан. Рекомендуется учесть выявленные рекомендации."
    }
    return decisions.get(risk_level, "Требуется дополнительный анализ.")
