import logging
from services.yandex_gpt import detect_document_type, analyze_with_yandexgpt
from config import PLANS, SMART_ANALYSIS_CONFIG, RISK_LEVELS

logger = logging.getLogger(__name__)

def analyze_text(text, user_plan='free'):
    """Умная функция анализа с определением типа документа"""
    
    # Определяем тип документа
    document_type = detect_document_type(text)
    doc_config = SMART_ANALYSIS_CONFIG[document_type]
    
    logger.info(f"🔍 Анализируем документ типа: {doc_config['name']}, план пользователя: {user_plan}")
    
    # Проверяем доступ к AI по тарифу
    if PLANS[user_plan]['ai_access']:
        result = analyze_with_yandexgpt(text, document_type)
        if result['ai_used']:
            return result
    
    # Если AI недоступен, используем улучшенный локальный анализ
    return create_basic_analysis(text, document_type)

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

def get_decision_support(risk_level):
    """Предоставляет поддержку для принятия решений"""
    decisions = {
        'CRITICAL': "НЕ РЕКОМЕНДУЕТСЯ к подписанию. Требуется существенная доработка с юристом.",
        'HIGH': "Требует серьезной доработки. Консультация с юристом обязательна.",
        'MEDIUM': "Может быть подписан после устранения основных замечаний.",
        'LOW': "Может быть подписан. Рекомендуется учесть выявленные рекомендации."
    }
    return decisions.get(risk_level, "Требуется дополнительный анализ.")
