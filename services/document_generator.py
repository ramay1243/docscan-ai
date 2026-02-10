"""
Модуль для генерации документов (договоры, акты, заявки) и конвертации в PDF
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import logging
import os
import platform

logger = logging.getLogger(__name__)

# Регистрируем шрифты с поддержкой кириллицы (используем те же, что в pdf_generator.py)
FONT_NAME = None
FONT_BOLD = None

def register_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    global FONT_NAME, FONT_BOLD
    
    font_paths = {
        'Windows': [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
        ],
        'Linux': [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        ],
        'Darwin': [
            '/Library/Fonts/Arial.ttf',
            '/Library/Fonts/Arial Bold.ttf',
        ]
    }
    
    system = platform.system()
    paths = font_paths.get(system, font_paths['Linux'])
    
    regular_font = None
    bold_font = None
    
    for path in paths:
        if os.path.exists(path):
            try:
                if 'bold' in path.lower() or 'bd' in path.lower() or 'Bold' in path:
                    if bold_font is None:
                        pdfmetrics.registerFont(TTFont('CyrillicBold', path))
                        bold_font = 'CyrillicBold'
                        logger.info(f"✅ Зарегистрирован жирный шрифт: {path}")
                else:
                    if regular_font is None:
                        pdfmetrics.registerFont(TTFont('CyrillicRegular', path))
                        regular_font = 'CyrillicRegular'
                        logger.info(f"✅ Зарегистрирован обычный шрифт: {path}")
                
                if regular_font and bold_font:
                    break
            except Exception as e:
                logger.warning(f"⚠️ Не удалось зарегистрировать шрифт {path}: {e}")
                continue
    
    if regular_font and bold_font:
        FONT_NAME = regular_font
        FONT_BOLD = bold_font
        logger.info("✅ TTF шрифты с поддержкой кириллицы успешно зарегистрированы")
        return True
    
    # Fallback на стандартные шрифты
    FONT_NAME = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
    logger.warning("⚠️ Используются стандартные шрифты (кириллица может отображаться некорректно)")
    return False

# Регистрируем шрифты при импорте
register_fonts()

def generate_service_contract_pdf(data):
    """Генерирует договор оказания услуг в PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=2*cm, leftMargin=2*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    # Создаем кастомные стили
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a202c'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName=FONT_BOLD
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=6,
        spaceBefore=12,
        fontName=FONT_BOLD
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#4a5568'),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName=FONT_NAME
    )
    
    story = []
    
    # Заголовок
    contract_number = data.get('contract_number', f"№ {datetime.now().strftime('%d/%m/%Y')}")
    city = data.get('city', 'г. Москва')
    date = data.get('date', datetime.now().strftime('«%d» %B %Y г.'))
    
    story.append(Paragraph("ДОГОВОР ОКАЗАНИЯ УСЛУГ", title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"{contract_number}", normal_style))
    story.append(Paragraph(f"{city}, {date}", normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Стороны
    executor_name = data.get('executor_name', '')
    executor_inn = data.get('executor_inn', '')
    executor_address = data.get('executor_address', '')
    executor_phone = data.get('executor_phone', '')
    executor_email = data.get('executor_email', '')
    
    customer_name = data.get('customer_name', '')
    customer_inn = data.get('customer_inn', '')
    customer_address = data.get('customer_address', '')
    customer_phone = data.get('customer_phone', '')
    customer_email = data.get('customer_email', '')
    
    parties_text = f"""
    {executor_name}, именуемый в дальнейшем «Исполнитель», с одной стороны, и {customer_name}, именуемый в дальнейшем «Заказчик», с другой стороны, совместно именуемые «Стороны», заключили настоящий Договор о нижеследующем:
    """
    story.append(Paragraph(parties_text.strip(), normal_style))
    story.append(Spacer(1, 0.3*cm))
    
    # 1. Предмет договора
    story.append(Paragraph("1. ПРЕДМЕТ ДОГОВОРА", heading_style))
    service_description = data.get('service_description', 'Услуги по настоящему договору')
    service_period = data.get('service_period', '')
    
    subject_text = f"""
    1.1. Исполнитель обязуется оказать Заказчику следующие услуги: {service_description}.
    """
    if service_period:
        subject_text += f"\n    1.2. Срок оказания услуг: {service_period}."
    
    story.append(Paragraph(subject_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 2. Права и обязанности сторон
    story.append(Paragraph("2. ПРАВА И ОБЯЗАННОСТИ СТОРОН", heading_style))
    
    obligations_text = """
    2.1. Исполнитель обязуется:
    - оказать услуги качественно и в полном объеме;
    - соблюдать сроки оказания услуг, установленные настоящим договором;
    - предоставить Заказчику необходимую информацию о ходе выполнения работ.
    
    2.2. Заказчик обязуется:
    - предоставить Исполнителю всю необходимую информацию и документы для оказания услуг;
    - принять оказанные услуги в установленные сроки;
    - оплатить услуги в порядке и размере, установленных настоящим договором.
    """
    story.append(Paragraph(obligations_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 3. Стоимость услуг и порядок расчетов
    story.append(Paragraph("3. СТОИМОСТЬ УСЛУГ И ПОРЯДОК РАСЧЕТОВ", heading_style))
    
    price = data.get('price', '0')
    payment_terms = data.get('payment_terms', '100% предоплата')
    
    price_text = f"""
    3.1. Стоимость услуг по настоящему договору составляет {price} рублей (включая НДС, если применимо).
    
    3.2. Оплата производится в следующем порядке: {payment_terms}.
    
    3.3. Расчеты между Сторонами производятся путем перечисления денежных средств на расчетный счет Исполнителя.
    """
    story.append(Paragraph(price_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 4. Ответственность сторон
    story.append(Paragraph("4. ОТВЕТСТВЕННОСТЬ СТОРОН", heading_style))
    
    penalty = data.get('penalty', '0.1%')
    
    responsibility_text = f"""
    4.1. За нарушение сроков оказания услуг Исполнитель уплачивает Заказчику неустойку в размере {penalty} от стоимости невыполненных в срок услуг за каждый день просрочки.
    
    4.2. За нарушение сроков оплаты Заказчик уплачивает Исполнителю неустойку в размере {penalty} от суммы просроченного платежа за каждый день просрочки.
    
    4.3. Стороны освобождаются от ответственности за частичное или полное неисполнение обязательств по настоящему договору, если это неисполнение явилось следствием обстоятельств непреодолимой силы.
    """
    story.append(Paragraph(responsibility_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 5. Срок действия договора
    story.append(Paragraph("5. СРОК ДЕЙСТВИЯ ДОГОВОРА", heading_style))
    
    contract_period = data.get('contract_period', 'до полного исполнения обязательств Сторонами')
    
    term_text = f"""
    5.1. Настоящий договор вступает в силу с момента подписания и действует {contract_period}.
    
    5.2. Договор может быть расторгнут по соглашению Сторон или в одностороннем порядке при существенном нарушении условий договора одной из Сторон.
    """
    story.append(Paragraph(term_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 6. Прочие условия
    story.append(Paragraph("6. ПРОЧИЕ УСЛОВИЯ", heading_style))
    
    other_text = """
    6.1. Все споры и разногласия, возникающие при исполнении настоящего договора, решаются путем переговоров, а при недостижении соглашения - в порядке, установленном законодательством Российской Федерации.
    
    6.2. Настоящий договор составлен в двух экземплярах, имеющих одинаковую юридическую силу, по одному для каждой из Сторон.
    """
    story.append(Paragraph(other_text.strip(), normal_style))
    story.append(Spacer(1, 0.3*cm))
    
    # 7. Реквизиты и подписи
    story.append(Paragraph("7. РЕКВИЗИТЫ И ПОДПИСИ СТОРОН", heading_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Таблица с реквизитами
    requisites_data = [
        ['', 'ИСПОЛНИТЕЛЬ', 'ЗАКАЗЧИК'],
        ['Наименование:', executor_name, customer_name],
        ['ИНН:', executor_inn or '—', customer_inn or '—'],
        ['Адрес:', executor_address or '—', customer_address or '—'],
        ['Телефон:', executor_phone or '—', customer_phone or '—'],
        ['E-mail:', executor_email or '—', customer_email or '—'],
    ]
    
    req_table = Table(requisites_data, colWidths=[3*cm, 7*cm, 7*cm])
    req_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a202c')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(req_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Подписи
    signature_text = """
    <b>Исполнитель:</b> _________________ / {executor_name} /
    
    <b>Заказчик:</b> _________________ / {customer_name} /
    """.format(executor_name=executor_name, customer_name=customer_name)
    
    story.append(Paragraph(signature_text.strip(), normal_style))
    
    # Генерируем PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_lease_contract_pdf(data):
    """Генерирует договор аренды в PDF"""
    # Аналогично generate_service_contract_pdf, но с полями для аренды
    # Пока используем базовую структуру, можно расширить позже
    return generate_service_contract_pdf(data)  # Временная заглушка

def generate_business_plan_pdf(data):
    """Генерирует бизнес-план в PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          rightMargin=2*cm, leftMargin=2*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a202c'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName=FONT_BOLD
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=6,
        spaceBefore=12,
        fontName=FONT_BOLD
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#4a5568'),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName=FONT_NAME
    )
    
    story = []
    
    # Заголовок
    project_name = data.get('project_name', 'Бизнес-план')
    story.append(Paragraph(project_name.upper(), title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 1. Описание проекта
    story.append(Paragraph("1. ОПИСАНИЕ ПРОЕКТА", heading_style))
    description = data.get('description', '')
    story.append(Paragraph(description or 'Описание проекта', normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 2. Целевая аудитория
    story.append(Paragraph("2. ЦЕЛЕВАЯ АУДИТОРИЯ", heading_style))
    target_audience = data.get('target_audience', '')
    story.append(Paragraph(target_audience or 'Целевая аудитория проекта', normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 3. План расходов и доходов
    story.append(Paragraph("3. ПЛАН РАСХОДОВ И ДОХОДОВ", heading_style))
    
    expenses = data.get('expenses', '')
    income = data.get('income', '')
    
    if expenses:
        story.append(Paragraph("<b>3.1. Расходы:</b>", normal_style))
        # Если expenses - строка, разбиваем по строкам
        if isinstance(expenses, str):
            for exp in expenses.split('\n'):
                if exp.strip():
                    story.append(Paragraph(f"• {exp.strip()}", normal_style))
        else:
            for exp in expenses:
                story.append(Paragraph(f"• {exp}", normal_style))
    
    if income:
        story.append(Paragraph("<b>3.2. Доходы:</b>", normal_style))
        # Если income - строка, разбиваем по строкам
        if isinstance(income, str):
            for inc in income.split('\n'):
                if inc.strip():
                    story.append(Paragraph(f"• {inc.strip()}", normal_style))
        else:
            for inc in income:
                story.append(Paragraph(f"• {inc}", normal_style))
    
    story.append(Spacer(1, 0.2*cm))
    
    # 4. План действий
    story.append(Paragraph("4. ПЛАН ДЕЙСТВИЙ", heading_style))
    action_plan = data.get('action_plan', '')
    story.append(Paragraph(action_plan or 'План действий по реализации проекта', normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # 5. Ожидаемые результаты
    story.append(Paragraph("5. ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ", heading_style))
    expected_results = data.get('expected_results', '')
    story.append(Paragraph(expected_results or 'Ожидаемые результаты проекта', normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

