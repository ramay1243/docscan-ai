from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import logging
import os
import platform

logger = logging.getLogger(__name__)

# Регистрируем шрифты с поддержкой кириллицы
# Пробуем использовать TTF шрифты из системы, которые точно поддерживают кириллицу
FONT_NAME = None
FONT_BOLD = None

def register_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    global FONT_NAME, FONT_BOLD
    
    # Список возможных путей к шрифтам с поддержкой кириллицы
    font_paths = {
        'Windows': [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/times.ttf',
            'C:/Windows/Fonts/timesbd.ttf',
            'C:/Windows/Fonts/calibri.ttf',
            'C:/Windows/Fonts/calibrib.ttf',
        ],
        'Linux': [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
        ],
        'Darwin': [  # macOS
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf',
            '/Library/Fonts/Arial Bold.ttf',
        ]
    }
    
    system = platform.system()
    paths = font_paths.get(system, font_paths['Linux'])
    
    # Пробуем найти и зарегистрировать TTF шрифты
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
    
    # Если нашли оба шрифта - используем их
    if regular_font and bold_font:
        FONT_NAME = regular_font
        FONT_BOLD = bold_font
        logger.info("✅ TTF шрифты с поддержкой кириллицы успешно зарегистрированы")
        return True
    
    # Если не нашли TTF шрифты - пробуем UnicodeCIDFont (японские шрифты)
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
        FONT_NAME = 'HeiseiMin-W3'
        FONT_BOLD = 'HeiseiKakuGo-W5'
        logger.warning("⚠️ Используются японские Unicode шрифты (могут плохо отображать кириллицу)")
        return True
    except Exception as e:
        logger.error(f"❌ Не удалось зарегистрировать Unicode шрифты: {e}")
        FONT_NAME = 'Helvetica'
        FONT_BOLD = 'Helvetica-Bold'
        logger.error("❌ ВНИМАНИЕ: Используются стандартные шрифты! Кириллица будет отображаться как ■■■")
        return False

# Регистрируем шрифты при импорте модуля
register_fonts()

def generate_analysis_pdf(analysis_data, filename="document.pdf", branding_settings=None):
    """Генерирует PDF файл с результатами анализа
    
    Args:
        analysis_data: Данные анализа
        filename: Имя файла
        branding_settings: Настройки брендинга (dict с logo_path, primary_color, secondary_color, company_name)
    """
    try:
        # Получаем настройки брендинга или используем значения по умолчанию
        if branding_settings and branding_settings.get('is_active'):
            primary_color = branding_settings.get('primary_color', '#4361ee')
            secondary_color = branding_settings.get('secondary_color', '#764ba2')
            company_name = branding_settings.get('company_name')
            logo_path = branding_settings.get('logo_path')
        else:
            primary_color = '#4361ee'
            secondary_color = '#764ba2'
            company_name = None
            logo_path = None
        
        # Проверяем, что шрифты зарегистрированы
        if FONT_NAME is None or FONT_BOLD is None:
            logger.error("❌ Шрифты не зарегистрированы! Пробуем зарегистрировать снова...")
            register_fonts()
            if FONT_NAME is None or FONT_BOLD is None:
                raise Exception("Не удалось зарегистрировать шрифты с поддержкой кириллицы!")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        # Стили
        styles = getSampleStyleSheet()
        story = []
        
        # Логотип (если есть)
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=2*inch, height=0.8*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                logger.warning(f"⚠️ Не удалось добавить логотип: {e}")
        
        # Заголовок
        title_text = company_name if company_name else "Анализ документа"
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(primary_color),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=FONT_BOLD
        )
        
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Информация о документе
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            fontName=FONT_NAME
        )
        
        story.append(Paragraph(f"<b>Файл:</b> {filename}", info_style))
        story.append(Paragraph(f"<b>Дата анализа:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", info_style))
        story.append(Paragraph(f"<b>Тип документа:</b> {analysis_data.get('document_type_name', 'Не определен')}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Общий уровень риска
        risk_level = analysis_data.get('executive_summary', {}).get('risk_level', 'LOW')
        risk_colors = {
            'CRITICAL': colors.HexColor('#e53e3e'),
            'HIGH': colors.HexColor('#dd6b20'),
            'MEDIUM': colors.HexColor('#d69e2e'),
            'LOW': colors.HexColor('#38a169')
        }
        risk_color = risk_colors.get(risk_level, colors.HexColor('#3182ce'))
        
        risk_style = ParagraphStyle(
            'RiskStyle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=risk_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName=FONT_BOLD
        )
        
        risk_icon = analysis_data.get('executive_summary', {}).get('risk_icon', '⚠️')
        risk_desc = analysis_data.get('executive_summary', {}).get('risk_description', 'Риск не определен')
        
        story.append(Paragraph(f"{risk_icon} <b>Уровень риска: {risk_level}</b>", risk_style))
        story.append(Paragraph(risk_desc, info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Решение
        decision_style = ParagraphStyle(
            'DecisionStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#212529'),
            alignment=TA_JUSTIFY,
            backColor=colors.HexColor('#f8f9fa'),
            borderPadding=10,
            spaceAfter=20,
            fontName=FONT_NAME
        )
        
        decision = analysis_data.get('executive_summary', {}).get('decision_support', '')
        if decision:
            story.append(Paragraph(f"<b>💡 Решение:</b> {decision}", decision_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Статистика рисков
        risk_stats = analysis_data.get('risk_analysis', {}).get('risk_statistics', {})
        if risk_stats:
            heading2_style = ParagraphStyle(
                'Heading2Custom',
                parent=styles['Heading2'],
                fontName=FONT_BOLD
            )
            story.append(Paragraph("<b>📊 Статистика рисков</b>", heading2_style))
            story.append(Spacer(1, 0.1*inch))
            
            stats_data = [
                ['Уровень риска', 'Количество'],
                ['Критических', str(risk_stats.get('CRITICAL', 0))],
                ['Высоких', str(risk_stats.get('HIGH', 0))],
                ['Средних', str(risk_stats.get('MEDIUM', 0))],
                ['Низких', str(risk_stats.get('LOW', 0))],
                ['<b>Всего</b>', f"<b>{risk_stats.get('total', 0)}</b>"]
            ]
            
            stats_table = Table(stats_data, colWidths=[4*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Создаем стили с поддержкой кириллицы
        normal_style = ParagraphStyle(
            'NormalCustom',
            parent=styles['Normal'],
            fontName=FONT_NAME
        )
        
        heading2_style_custom = ParagraphStyle(
            'Heading2Custom',
            parent=styles['Heading2'],
            fontName=FONT_BOLD
        )
        
        heading3_style_custom = ParagraphStyle(
            'Heading3Custom',
            parent=styles['Heading3'],
            fontName=FONT_BOLD
        )
        
        # Юридическая экспертиза
        legal = analysis_data.get('expert_analysis', {}).get('legal_expertise', '')
        if legal and legal != 'Юридический анализ не выявил критических нарушений':
            story.append(Paragraph("<b>🧑‍⚖️ Юридическая экспертиза</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(legal, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Финансовый анализ
        financial = analysis_data.get('expert_analysis', {}).get('financial_analysis', '')
        if financial and financial != 'Финансовые условия требуют дополнительной проверки':
            story.append(Paragraph("<b>💰 Финансовый анализ</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(financial, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Операционные риски
        operational = analysis_data.get('expert_analysis', {}).get('operational_risks', '')
        if operational and operational != 'Операционные риски находятся в допустимых пределах':
            story.append(Paragraph("<b>⚙️ Операционные риски</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(operational, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Стратегическая оценка
        strategic = analysis_data.get('expert_analysis', {}).get('strategic_assessment', '')
        if strategic and strategic != 'Документ соответствует базовым стратегическим целям':
            story.append(Paragraph("<b>🎯 Стратегическая оценка</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(strategic, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Ключевые риски
        key_risks = analysis_data.get('risk_analysis', {}).get('key_risks', [])
        if key_risks:
            story.append(PageBreak())
            story.append(Paragraph("<b>⚠️ Детальный анализ рисков</b>", heading2_style_custom))
            story.append(Spacer(1, 0.2*inch))
            
            for i, risk in enumerate(key_risks, 1):
                risk_level = risk.get('level', 'MEDIUM')
                risk_color = risk_colors.get(risk_level, colors.HexColor('#3182ce'))
                
                risk_title_style = ParagraphStyle(
                    'RiskTitle',
                    parent=styles['Heading3'],
                    fontSize=14,
                    textColor=risk_color,
                    fontName=FONT_BOLD,
                    spaceAfter=5
                )
                
                story.append(Paragraph(f"{i}. {risk.get('icon', '⚠️')} <b>{risk.get('title', 'Риск')}</b> ({risk_level})", risk_title_style))
                story.append(Paragraph(risk.get('description', ''), normal_style))
                story.append(Spacer(1, 0.15*inch))
        
        # Рекомендации
        recommendations = analysis_data.get('recommendations', {})
        if recommendations:
            story.append(PageBreak())
            story.append(Paragraph("<b>💡 Практические рекомендации</b>", heading2_style_custom))
            story.append(Spacer(1, 0.2*inch))
            
            practical_actions = recommendations.get('practical_actions', [])
            if practical_actions:
                story.append(Paragraph("<b>📋 Рекомендуемые действия:</b>", heading3_style_custom))
                story.append(Spacer(1, 0.1*inch))
                
                for i, action in enumerate(practical_actions, 1):
                    if isinstance(action, dict):
                        action_text = action.get('action', action.get('title', ''))
                        effect = action.get('effect', action.get('description', ''))
                        if effect:
                            story.append(Paragraph(f"{i}. <b>{action_text}</b> - {effect}", normal_style))
                        else:
                            story.append(Paragraph(f"{i}. {action_text}", normal_style))
                    else:
                        story.append(Paragraph(f"{i}. {action}", normal_style))
                    story.append(Spacer(1, 0.1*inch))
            
            priority_actions = recommendations.get('priority_actions', [])
            if priority_actions:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("<b>🚨 Срочные действия:</b>", heading3_style_custom))
                story.append(Spacer(1, 0.1*inch))
                
                for action in priority_actions:
                    if isinstance(action, dict):
                        action_text = action.get('action', action.get('title', ''))
                    else:
                        action_text = str(action)
                    story.append(Paragraph(f"• {action_text}", normal_style))
                    story.append(Spacer(1, 0.05*inch))
        
        # Футер
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            fontName=FONT_NAME
        )
        footer_text = f"Сгенерировано {company_name if company_name else 'DocScan AI'} - https://docscan-ai.ru"
        story.append(Paragraph(footer_text, footer_style))
        
        # Собираем PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"✅ PDF успешно сгенерирован для файла: {filename}")
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import logging
import os
import platform

logger = logging.getLogger(__name__)

# Регистрируем шрифты с поддержкой кириллицы
# Пробуем использовать TTF шрифты из системы, которые точно поддерживают кириллицу
FONT_NAME = None
FONT_BOLD = None

def register_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    global FONT_NAME, FONT_BOLD
    
    # Список возможных путей к шрифтам с поддержкой кириллицы
    font_paths = {
        'Windows': [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/times.ttf',
            'C:/Windows/Fonts/timesbd.ttf',
            'C:/Windows/Fonts/calibri.ttf',
            'C:/Windows/Fonts/calibrib.ttf',
        ],
        'Linux': [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
        ],
        'Darwin': [  # macOS
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf',
            '/Library/Fonts/Arial Bold.ttf',
        ]
    }
    
    system = platform.system()
    paths = font_paths.get(system, font_paths['Linux'])
    
    # Пробуем найти и зарегистрировать TTF шрифты
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
    
    # Если нашли оба шрифта - используем их
    if regular_font and bold_font:
        FONT_NAME = regular_font
        FONT_BOLD = bold_font
        logger.info("✅ TTF шрифты с поддержкой кириллицы успешно зарегистрированы")
        return True
    
    # Если не нашли TTF шрифты - пробуем UnicodeCIDFont (японские шрифты)
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
        FONT_NAME = 'HeiseiMin-W3'
        FONT_BOLD = 'HeiseiKakuGo-W5'
        logger.warning("⚠️ Используются японские Unicode шрифты (могут плохо отображать кириллицу)")
        return True
    except Exception as e:
        logger.error(f"❌ Не удалось зарегистрировать Unicode шрифты: {e}")
        FONT_NAME = 'Helvetica'
        FONT_BOLD = 'Helvetica-Bold'
        logger.error("❌ ВНИМАНИЕ: Используются стандартные шрифты! Кириллица будет отображаться как ■■■")
        return False

# Регистрируем шрифты при импорте модуля
register_fonts()

def generate_analysis_pdf(analysis_data, filename="document.pdf", branding_settings=None):
    """Генерирует PDF файл с результатами анализа
    
    Args:
        analysis_data: Данные анализа
        filename: Имя файла
        branding_settings: Настройки брендинга (dict с logo_path, primary_color, secondary_color, company_name)
    """
    try:
        # Получаем настройки брендинга или используем значения по умолчанию
        if branding_settings and branding_settings.get('is_active'):
            primary_color = branding_settings.get('primary_color', '#4361ee')
            secondary_color = branding_settings.get('secondary_color', '#764ba2')
            company_name = branding_settings.get('company_name')
            logo_path = branding_settings.get('logo_path')
        else:
            primary_color = '#4361ee'
            secondary_color = '#764ba2'
            company_name = None
            logo_path = None
        
        # Проверяем, что шрифты зарегистрированы
        if FONT_NAME is None or FONT_BOLD is None:
            logger.error("❌ Шрифты не зарегистрированы! Пробуем зарегистрировать снова...")
            register_fonts()
            if FONT_NAME is None or FONT_BOLD is None:
                raise Exception("Не удалось зарегистрировать шрифты с поддержкой кириллицы!")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        # Стили
        styles = getSampleStyleSheet()
        story = []
        
        # Логотип (если есть)
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=2*inch, height=0.8*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                logger.warning(f"⚠️ Не удалось добавить логотип: {e}")
        
        # Заголовок
        title_text = company_name if company_name else "Анализ документа"
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(primary_color),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=FONT_BOLD
        )
        
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Информация о документе
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            fontName=FONT_NAME
        )
        
        story.append(Paragraph(f"<b>Файл:</b> {filename}", info_style))
        story.append(Paragraph(f"<b>Дата анализа:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", info_style))
        story.append(Paragraph(f"<b>Тип документа:</b> {analysis_data.get('document_type_name', 'Не определен')}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Общий уровень риска
        risk_level = analysis_data.get('executive_summary', {}).get('risk_level', 'LOW')
        risk_colors = {
            'CRITICAL': colors.HexColor('#e53e3e'),
            'HIGH': colors.HexColor('#dd6b20'),
            'MEDIUM': colors.HexColor('#d69e2e'),
            'LOW': colors.HexColor('#38a169')
        }
        risk_color = risk_colors.get(risk_level, colors.HexColor('#3182ce'))
        
        risk_style = ParagraphStyle(
            'RiskStyle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=risk_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName=FONT_BOLD
        )
        
        risk_icon = analysis_data.get('executive_summary', {}).get('risk_icon', '⚠️')
        risk_desc = analysis_data.get('executive_summary', {}).get('risk_description', 'Риск не определен')
        
        story.append(Paragraph(f"{risk_icon} <b>Уровень риска: {risk_level}</b>", risk_style))
        story.append(Paragraph(risk_desc, info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Решение
        decision_style = ParagraphStyle(
            'DecisionStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#212529'),
            alignment=TA_JUSTIFY,
            backColor=colors.HexColor('#f8f9fa'),
            borderPadding=10,
            spaceAfter=20,
            fontName=FONT_NAME
        )
        
        decision = analysis_data.get('executive_summary', {}).get('decision_support', '')
        if decision:
            story.append(Paragraph(f"<b>💡 Решение:</b> {decision}", decision_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Статистика рисков
        risk_stats = analysis_data.get('risk_analysis', {}).get('risk_statistics', {})
        if risk_stats:
            heading2_style = ParagraphStyle(
                'Heading2Custom',
                parent=styles['Heading2'],
                fontName=FONT_BOLD
            )
            story.append(Paragraph("<b>📊 Статистика рисков</b>", heading2_style))
            story.append(Spacer(1, 0.1*inch))
            
            stats_data = [
                ['Уровень риска', 'Количество'],
                ['Критических', str(risk_stats.get('CRITICAL', 0))],
                ['Высоких', str(risk_stats.get('HIGH', 0))],
                ['Средних', str(risk_stats.get('MEDIUM', 0))],
                ['Низких', str(risk_stats.get('LOW', 0))],
                ['<b>Всего</b>', f"<b>{risk_stats.get('total', 0)}</b>"]
            ]
            
            stats_table = Table(stats_data, colWidths=[4*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Создаем стили с поддержкой кириллицы
        normal_style = ParagraphStyle(
            'NormalCustom',
            parent=styles['Normal'],
            fontName=FONT_NAME
        )
        
        heading2_style_custom = ParagraphStyle(
            'Heading2Custom',
            parent=styles['Heading2'],
            fontName=FONT_BOLD
        )
        
        heading3_style_custom = ParagraphStyle(
            'Heading3Custom',
            parent=styles['Heading3'],
            fontName=FONT_BOLD
        )
        
        # Юридическая экспертиза
        legal = analysis_data.get('expert_analysis', {}).get('legal_expertise', '')
        if legal and legal != 'Юридический анализ не выявил критических нарушений':
            story.append(Paragraph("<b>🧑‍⚖️ Юридическая экспертиза</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(legal, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Финансовый анализ
        financial = analysis_data.get('expert_analysis', {}).get('financial_analysis', '')
        if financial and financial != 'Финансовые условия требуют дополнительной проверки':
            story.append(Paragraph("<b>💰 Финансовый анализ</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(financial, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Операционные риски
        operational = analysis_data.get('expert_analysis', {}).get('operational_risks', '')
        if operational and operational != 'Операционные риски находятся в допустимых пределах':
            story.append(Paragraph("<b>⚙️ Операционные риски</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(operational, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Стратегическая оценка
        strategic = analysis_data.get('expert_analysis', {}).get('strategic_assessment', '')
        if strategic and strategic != 'Документ соответствует базовым стратегическим целям':
            story.append(Paragraph("<b>🎯 Стратегическая оценка</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(strategic, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Ключевые риски
        key_risks = analysis_data.get('risk_analysis', {}).get('key_risks', [])
        if key_risks:
            story.append(PageBreak())
            story.append(Paragraph("<b>⚠️ Детальный анализ рисков</b>", heading2_style_custom))
            story.append(Spacer(1, 0.2*inch))
            
            for i, risk in enumerate(key_risks, 1):
                risk_level = risk.get('level', 'MEDIUM')
                risk_color = risk_colors.get(risk_level, colors.HexColor('#3182ce'))
                
                risk_title_style = ParagraphStyle(
                    'RiskTitle',
                    parent=styles['Heading3'],
                    fontSize=14,
                    textColor=risk_color,
                    fontName=FONT_BOLD,
                    spaceAfter=5
                )
                
                story.append(Paragraph(f"{i}. {risk.get('icon', '⚠️')} <b>{risk.get('title', 'Риск')}</b> ({risk_level})", risk_title_style))
                story.append(Paragraph(risk.get('description', ''), normal_style))
                story.append(Spacer(1, 0.15*inch))
        
        # Рекомендации
        recommendations = analysis_data.get('recommendations', {})
        if recommendations:
            story.append(PageBreak())
            story.append(Paragraph("<b>💡 Практические рекомендации</b>", heading2_style_custom))
            story.append(Spacer(1, 0.2*inch))
            
            practical_actions = recommendations.get('practical_actions', [])
            if practical_actions:
                story.append(Paragraph("<b>📋 Рекомендуемые действия:</b>", heading3_style_custom))
                story.append(Spacer(1, 0.1*inch))
                
                for i, action in enumerate(practical_actions, 1):
                    if isinstance(action, dict):
                        action_text = action.get('action', action.get('title', ''))
                        effect = action.get('effect', action.get('description', ''))
                        if effect:
                            story.append(Paragraph(f"{i}. <b>{action_text}</b> - {effect}", normal_style))
                        else:
                            story.append(Paragraph(f"{i}. {action_text}", normal_style))
                    else:
                        story.append(Paragraph(f"{i}. {action}", normal_style))
                    story.append(Spacer(1, 0.1*inch))
            
            priority_actions = recommendations.get('priority_actions', [])
            if priority_actions:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("<b>🚨 Срочные действия:</b>", heading3_style_custom))
                story.append(Spacer(1, 0.1*inch))
                
                for action in priority_actions:
                    if isinstance(action, dict):
                        action_text = action.get('action', action.get('title', ''))
                    else:
                        action_text = str(action)
                    story.append(Paragraph(f"• {action_text}", normal_style))
                    story.append(Spacer(1, 0.05*inch))
        
        # Футер
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            fontName=FONT_NAME
        )
        footer_text = f"Сгенерировано {company_name if company_name else 'DocScan AI'} - https://docscan-ai.ru"
        story.append(Paragraph(footer_text, footer_style))
        
        # Собираем PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"✅ PDF успешно сгенерирован для файла: {filename}")
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import logging
import os
import platform

logger = logging.getLogger(__name__)

# Регистрируем шрифты с поддержкой кириллицы
# Пробуем использовать TTF шрифты из системы, которые точно поддерживают кириллицу
FONT_NAME = None
FONT_BOLD = None

def register_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    global FONT_NAME, FONT_BOLD
    
    # Список возможных путей к шрифтам с поддержкой кириллицы
    font_paths = {
        'Windows': [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/times.ttf',
            'C:/Windows/Fonts/timesbd.ttf',
            'C:/Windows/Fonts/calibri.ttf',
            'C:/Windows/Fonts/calibrib.ttf',
        ],
        'Linux': [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
        ],
        'Darwin': [  # macOS
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf',
            '/Library/Fonts/Arial Bold.ttf',
        ]
    }
    
    system = platform.system()
    paths = font_paths.get(system, font_paths['Linux'])
    
    # Пробуем найти и зарегистрировать TTF шрифты
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
    
    # Если нашли оба шрифта - используем их
    if regular_font and bold_font:
        FONT_NAME = regular_font
        FONT_BOLD = bold_font
        logger.info("✅ TTF шрифты с поддержкой кириллицы успешно зарегистрированы")
        return True
    
    # Если не нашли TTF шрифты - пробуем UnicodeCIDFont (японские шрифты)
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
        FONT_NAME = 'HeiseiMin-W3'
        FONT_BOLD = 'HeiseiKakuGo-W5'
        logger.warning("⚠️ Используются японские Unicode шрифты (могут плохо отображать кириллицу)")
        return True
    except Exception as e:
        logger.error(f"❌ Не удалось зарегистрировать Unicode шрифты: {e}")
        FONT_NAME = 'Helvetica'
        FONT_BOLD = 'Helvetica-Bold'
        logger.error("❌ ВНИМАНИЕ: Используются стандартные шрифты! Кириллица будет отображаться как ■■■")
        return False

# Регистрируем шрифты при импорте модуля
register_fonts()

def generate_analysis_pdf(analysis_data, filename="document.pdf", branding_settings=None):
    """Генерирует PDF файл с результатами анализа
    
    Args:
        analysis_data: Данные анализа
        filename: Имя файла
        branding_settings: Настройки брендинга (dict с logo_path, primary_color, secondary_color, company_name)
    """
    try:
        # Получаем настройки брендинга или используем значения по умолчанию
        if branding_settings and branding_settings.get('is_active'):
            primary_color = branding_settings.get('primary_color', '#4361ee')
            secondary_color = branding_settings.get('secondary_color', '#764ba2')
            company_name = branding_settings.get('company_name')
            logo_path = branding_settings.get('logo_path')
        else:
            primary_color = '#4361ee'
            secondary_color = '#764ba2'
            company_name = None
            logo_path = None
        
        # Проверяем, что шрифты зарегистрированы
        if FONT_NAME is None or FONT_BOLD is None:
            logger.error("❌ Шрифты не зарегистрированы! Пробуем зарегистрировать снова...")
            register_fonts()
            if FONT_NAME is None or FONT_BOLD is None:
                raise Exception("Не удалось зарегистрировать шрифты с поддержкой кириллицы!")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        # Стили
        styles = getSampleStyleSheet()
        story = []
        
        # Логотип (если есть)
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=2*inch, height=0.8*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                logger.warning(f"⚠️ Не удалось добавить логотип: {e}")
        
        # Заголовок
        title_text = company_name if company_name else "Анализ документа"
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(primary_color),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=FONT_BOLD
        )
        
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Информация о документе
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            fontName=FONT_NAME
        )
        
        story.append(Paragraph(f"<b>Файл:</b> {filename}", info_style))
        story.append(Paragraph(f"<b>Дата анализа:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", info_style))
        story.append(Paragraph(f"<b>Тип документа:</b> {analysis_data.get('document_type_name', 'Не определен')}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Общий уровень риска
        risk_level = analysis_data.get('executive_summary', {}).get('risk_level', 'LOW')
        risk_colors = {
            'CRITICAL': colors.HexColor('#e53e3e'),
            'HIGH': colors.HexColor('#dd6b20'),
            'MEDIUM': colors.HexColor('#d69e2e'),
            'LOW': colors.HexColor('#38a169')
        }
        risk_color = risk_colors.get(risk_level, colors.HexColor('#3182ce'))
        
        risk_style = ParagraphStyle(
            'RiskStyle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=risk_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName=FONT_BOLD
        )
        
        risk_icon = analysis_data.get('executive_summary', {}).get('risk_icon', '⚠️')
        risk_desc = analysis_data.get('executive_summary', {}).get('risk_description', 'Риск не определен')
        
        story.append(Paragraph(f"{risk_icon} <b>Уровень риска: {risk_level}</b>", risk_style))
        story.append(Paragraph(risk_desc, info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Решение
        decision_style = ParagraphStyle(
            'DecisionStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#212529'),
            alignment=TA_JUSTIFY,
            backColor=colors.HexColor('#f8f9fa'),
            borderPadding=10,
            spaceAfter=20,
            fontName=FONT_NAME
        )
        
        decision = analysis_data.get('executive_summary', {}).get('decision_support', '')
        if decision:
            story.append(Paragraph(f"<b>💡 Решение:</b> {decision}", decision_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Статистика рисков
        risk_stats = analysis_data.get('risk_analysis', {}).get('risk_statistics', {})
        if risk_stats:
            heading2_style = ParagraphStyle(
                'Heading2Custom',
                parent=styles['Heading2'],
                fontName=FONT_BOLD
            )
            story.append(Paragraph("<b>📊 Статистика рисков</b>", heading2_style))
            story.append(Spacer(1, 0.1*inch))
            
            stats_data = [
                ['Уровень риска', 'Количество'],
                ['Критических', str(risk_stats.get('CRITICAL', 0))],
                ['Высоких', str(risk_stats.get('HIGH', 0))],
                ['Средних', str(risk_stats.get('MEDIUM', 0))],
                ['Низких', str(risk_stats.get('LOW', 0))],
                ['<b>Всего</b>', f"<b>{risk_stats.get('total', 0)}</b>"]
            ]
            
            stats_table = Table(stats_data, colWidths=[4*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Создаем стили с поддержкой кириллицы
        normal_style = ParagraphStyle(
            'NormalCustom',
            parent=styles['Normal'],
            fontName=FONT_NAME
        )
        
        heading2_style_custom = ParagraphStyle(
            'Heading2Custom',
            parent=styles['Heading2'],
            fontName=FONT_BOLD
        )
        
        heading3_style_custom = ParagraphStyle(
            'Heading3Custom',
            parent=styles['Heading3'],
            fontName=FONT_BOLD
        )
        
        # Юридическая экспертиза
        legal = analysis_data.get('expert_analysis', {}).get('legal_expertise', '')
        if legal and legal != 'Юридический анализ не выявил критических нарушений':
            story.append(Paragraph("<b>🧑‍⚖️ Юридическая экспертиза</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(legal, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Финансовый анализ
        financial = analysis_data.get('expert_analysis', {}).get('financial_analysis', '')
        if financial and financial != 'Финансовые условия требуют дополнительной проверки':
            story.append(Paragraph("<b>💰 Финансовый анализ</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(financial, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Операционные риски
        operational = analysis_data.get('expert_analysis', {}).get('operational_risks', '')
        if operational and operational != 'Операционные риски находятся в допустимых пределах':
            story.append(Paragraph("<b>⚙️ Операционные риски</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(operational, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Стратегическая оценка
        strategic = analysis_data.get('expert_analysis', {}).get('strategic_assessment', '')
        if strategic and strategic != 'Документ соответствует базовым стратегическим целям':
            story.append(Paragraph("<b>🎯 Стратегическая оценка</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(strategic, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Ключевые риски
        key_risks = analysis_data.get('risk_analysis', {}).get('key_risks', [])
        if key_risks:
            story.append(PageBreak())
            story.append(Paragraph("<b>⚠️ Детальный анализ рисков</b>", heading2_style_custom))
            story.append(Spacer(1, 0.2*inch))
            
            for i, risk in enumerate(key_risks, 1):
                risk_level = risk.get('level', 'MEDIUM')
                risk_color = risk_colors.get(risk_level, colors.HexColor('#3182ce'))
                
                risk_title_style = ParagraphStyle(
                    'RiskTitle',
                    parent=styles['Heading3'],
                    fontSize=14,
                    textColor=risk_color,
                    fontName=FONT_BOLD,
                    spaceAfter=5
                )
                
                story.append(Paragraph(f"{i}. {risk.get('icon', '⚠️')} <b>{risk.get('title', 'Риск')}</b> ({risk_level})", risk_title_style))
                story.append(Paragraph(risk.get('description', ''), normal_style))
                story.append(Spacer(1, 0.15*inch))
        
        # Рекомендации
        recommendations = analysis_data.get('recommendations', {})
        if recommendations:
            story.append(PageBreak())
            story.append(Paragraph("<b>💡 Практические рекомендации</b>", heading2_style_custom))
            story.append(Spacer(1, 0.2*inch))
            
            practical_actions = recommendations.get('practical_actions', [])
            if practical_actions:
                story.append(Paragraph("<b>📋 Рекомендуемые действия:</b>", heading3_style_custom))
                story.append(Spacer(1, 0.1*inch))
                
                for i, action in enumerate(practical_actions, 1):
                    if isinstance(action, dict):
                        action_text = action.get('action', action.get('title', ''))
                        effect = action.get('effect', action.get('description', ''))
                        if effect:
                            story.append(Paragraph(f"{i}. <b>{action_text}</b> - {effect}", normal_style))
                        else:
                            story.append(Paragraph(f"{i}. {action_text}", normal_style))
                    else:
                        story.append(Paragraph(f"{i}. {action}", normal_style))
                    story.append(Spacer(1, 0.1*inch))
            
            priority_actions = recommendations.get('priority_actions', [])
            if priority_actions:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("<b>🚨 Срочные действия:</b>", heading3_style_custom))
                story.append(Spacer(1, 0.1*inch))
                
                for action in priority_actions:
                    if isinstance(action, dict):
                        action_text = action.get('action', action.get('title', ''))
                    else:
                        action_text = str(action)
                    story.append(Paragraph(f"• {action_text}", normal_style))
                    story.append(Spacer(1, 0.05*inch))
        
        # Футер
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            fontName=FONT_NAME
        )
        footer_text = f"Сгенерировано {company_name if company_name else 'DocScan AI'} - https://docscan-ai.ru"
        story.append(Paragraph(footer_text, footer_style))
        
        # Собираем PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"✅ PDF успешно сгенерирован для файла: {filename}")
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import logging
import os
import platform

logger = logging.getLogger(__name__)

# Регистрируем шрифты с поддержкой кириллицы
# Пробуем использовать TTF шрифты из системы, которые точно поддерживают кириллицу
FONT_NAME = None
FONT_BOLD = None

def register_fonts():
    """Регистрирует шрифты с поддержкой кириллицы"""
    global FONT_NAME, FONT_BOLD
    
    # Список возможных путей к шрифтам с поддержкой кириллицы
    font_paths = {
        'Windows': [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/times.ttf',
            'C:/Windows/Fonts/timesbd.ttf',
            'C:/Windows/Fonts/calibri.ttf',
            'C:/Windows/Fonts/calibrib.ttf',
        ],
        'Linux': [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
        ],
        'Darwin': [  # macOS
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial.ttf',
            '/Library/Fonts/Arial Bold.ttf',
        ]
    }
    
    system = platform.system()
    paths = font_paths.get(system, font_paths['Linux'])
    
    # Пробуем найти и зарегистрировать TTF шрифты
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
    
    # Если нашли оба шрифта - используем их
    if regular_font and bold_font:
        FONT_NAME = regular_font
        FONT_BOLD = bold_font
        logger.info("✅ TTF шрифты с поддержкой кириллицы успешно зарегистрированы")
        return True
    
    # Если не нашли TTF шрифты - пробуем UnicodeCIDFont (японские шрифты)
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
        FONT_NAME = 'HeiseiMin-W3'
        FONT_BOLD = 'HeiseiKakuGo-W5'
        logger.warning("⚠️ Используются японские Unicode шрифты (могут плохо отображать кириллицу)")
        return True
    except Exception as e:
        logger.error(f"❌ Не удалось зарегистрировать Unicode шрифты: {e}")
        FONT_NAME = 'Helvetica'
        FONT_BOLD = 'Helvetica-Bold'
        logger.error("❌ ВНИМАНИЕ: Используются стандартные шрифты! Кириллица будет отображаться как ■■■")
        return False

# Регистрируем шрифты при импорте модуля
register_fonts()

def generate_analysis_pdf(analysis_data, filename="document.pdf", branding_settings=None):
    """Генерирует PDF файл с результатами анализа
    
    Args:
        analysis_data: Данные анализа
        filename: Имя файла
        branding_settings: Настройки брендинга (dict с logo_path, primary_color, secondary_color, company_name)
    """
    try:
        # Получаем настройки брендинга или используем значения по умолчанию
        if branding_settings and branding_settings.get('is_active'):
            primary_color = branding_settings.get('primary_color', '#4361ee')
            secondary_color = branding_settings.get('secondary_color', '#764ba2')
            company_name = branding_settings.get('company_name')
            logo_path = branding_settings.get('logo_path')
        else:
            primary_color = '#4361ee'
            secondary_color = '#764ba2'
            company_name = None
            logo_path = None
        
        # Проверяем, что шрифты зарегистрированы
        if FONT_NAME is None or FONT_BOLD is None:
            logger.error("❌ Шрифты не зарегистрированы! Пробуем зарегистрировать снова...")
            register_fonts()
            if FONT_NAME is None or FONT_BOLD is None:
                raise Exception("Не удалось зарегистрировать шрифты с поддержкой кириллицы!")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        # Стили
        styles = getSampleStyleSheet()
        story = []
        
        # Логотип (если есть)
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=2*inch, height=0.8*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                logger.warning(f"⚠️ Не удалось добавить логотип: {e}")
        
        # Заголовок
        title_text = company_name if company_name else "Анализ документа"
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(primary_color),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=FONT_BOLD
        )
        
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Информация о документе
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            fontName=FONT_NAME
        )
        
        story.append(Paragraph(f"<b>Файл:</b> {filename}", info_style))
        story.append(Paragraph(f"<b>Дата анализа:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", info_style))
        story.append(Paragraph(f"<b>Тип документа:</b> {analysis_data.get('document_type_name', 'Не определен')}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Общий уровень риска
        risk_level = analysis_data.get('executive_summary', {}).get('risk_level', 'LOW')
        risk_colors = {
            'CRITICAL': colors.HexColor('#e53e3e'),
            'HIGH': colors.HexColor('#dd6b20'),
            'MEDIUM': colors.HexColor('#d69e2e'),
            'LOW': colors.HexColor('#38a169')
        }
        risk_color = risk_colors.get(risk_level, colors.HexColor('#3182ce'))
        
        risk_style = ParagraphStyle(
            'RiskStyle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=risk_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName=FONT_BOLD
        )
        
        risk_icon = analysis_data.get('executive_summary', {}).get('risk_icon', '⚠️')
        risk_desc = analysis_data.get('executive_summary', {}).get('risk_description', 'Риск не определен')
        
        story.append(Paragraph(f"{risk_icon} <b>Уровень риска: {risk_level}</b>", risk_style))
        story.append(Paragraph(risk_desc, info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Решение
        decision_style = ParagraphStyle(
            'DecisionStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#212529'),
            alignment=TA_JUSTIFY,
            backColor=colors.HexColor('#f8f9fa'),
            borderPadding=10,
            spaceAfter=20,
            fontName=FONT_NAME
        )
        
        decision = analysis_data.get('executive_summary', {}).get('decision_support', '')
        if decision:
            story.append(Paragraph(f"<b>💡 Решение:</b> {decision}", decision_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Статистика рисков
        risk_stats = analysis_data.get('risk_analysis', {}).get('risk_statistics', {})
        if risk_stats:
            heading2_style = ParagraphStyle(
                'Heading2Custom',
                parent=styles['Heading2'],
                fontName=FONT_BOLD
            )
            story.append(Paragraph("<b>📊 Статистика рисков</b>", heading2_style))
            story.append(Spacer(1, 0.1*inch))
            
            stats_data = [
                ['Уровень риска', 'Количество'],
                ['Критических', str(risk_stats.get('CRITICAL', 0))],
                ['Высоких', str(risk_stats.get('HIGH', 0))],
                ['Средних', str(risk_stats.get('MEDIUM', 0))],
                ['Низких', str(risk_stats.get('LOW', 0))],
                ['<b>Всего</b>', f"<b>{risk_stats.get('total', 0)}</b>"]
            ]
            
            stats_table = Table(stats_data, colWidths=[4*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Создаем стили с поддержкой кириллицы
        normal_style = ParagraphStyle(
            'NormalCustom',
            parent=styles['Normal'],
            fontName=FONT_NAME
        )
        
        heading2_style_custom = ParagraphStyle(
            'Heading2Custom',
            parent=styles['Heading2'],
            fontName=FONT_BOLD
        )
        
        heading3_style_custom = ParagraphStyle(
            'Heading3Custom',
            parent=styles['Heading3'],
            fontName=FONT_BOLD
        )
        
        # Юридическая экспертиза
        legal = analysis_data.get('expert_analysis', {}).get('legal_expertise', '')
        if legal and legal != 'Юридический анализ не выявил критических нарушений':
            story.append(Paragraph("<b>🧑‍⚖️ Юридическая экспертиза</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(legal, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Финансовый анализ
        financial = analysis_data.get('expert_analysis', {}).get('financial_analysis', '')
        if financial and financial != 'Финансовые условия требуют дополнительной проверки':
            story.append(Paragraph("<b>💰 Финансовый анализ</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(financial, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Операционные риски
        operational = analysis_data.get('expert_analysis', {}).get('operational_risks', '')
        if operational and operational != 'Операционные риски находятся в допустимых пределах':
            story.append(Paragraph("<b>⚙️ Операционные риски</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(operational, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Стратегическая оценка
        strategic = analysis_data.get('expert_analysis', {}).get('strategic_assessment', '')
        if strategic and strategic != 'Документ соответствует базовым стратегическим целям':
            story.append(Paragraph("<b>🎯 Стратегическая оценка</b>", heading2_style_custom))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(strategic, normal_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Ключевые риски
        key_risks = analysis_data.get('risk_analysis', {}).get('key_risks', [])
        if key_risks:
            story.append(PageBreak())
            story.append(Paragraph("<b>⚠️ Детальный анализ рисков</b>", heading2_style_custom))
            story.append(Spacer(1, 0.2*inch))
            
            for i, risk in enumerate(key_risks, 1):
                risk_level = risk.get('level', 'MEDIUM')
                risk_color = risk_colors.get(risk_level, colors.HexColor('#3182ce'))
                
                risk_title_style = ParagraphStyle(
                    'RiskTitle',
                    parent=styles['Heading3'],
                    fontSize=14,
                    textColor=risk_color,
                    fontName=FONT_BOLD,
                    spaceAfter=5
                )
                
                story.append(Paragraph(f"{i}. {risk.get('icon', '⚠️')} <b>{risk.get('title', 'Риск')}</b> ({risk_level})", risk_title_style))
                story.append(Paragraph(risk.get('description', ''), normal_style))
                story.append(Spacer(1, 0.15*inch))
        
        # Рекомендации
        recommendations = analysis_data.get('recommendations', {})
        if recommendations:
            story.append(PageBreak())
            story.append(Paragraph("<b>💡 Практические рекомендации</b>", heading2_style_custom))
            story.append(Spacer(1, 0.2*inch))
            
            practical_actions = recommendations.get('practical_actions', [])
            if practical_actions:
                story.append(Paragraph("<b>📋 Рекомендуемые действия:</b>", heading3_style_custom))
                story.append(Spacer(1, 0.1*inch))
                
                for i, action in enumerate(practical_actions, 1):
                    if isinstance(action, dict):
                        action_text = action.get('action', action.get('title', ''))
                        effect = action.get('effect', action.get('description', ''))
                        if effect:
                            story.append(Paragraph(f"{i}. <b>{action_text}</b> - {effect}", normal_style))
                        else:
                            story.append(Paragraph(f"{i}. {action_text}", normal_style))
                    else:
                        story.append(Paragraph(f"{i}. {action}", normal_style))
                    story.append(Spacer(1, 0.1*inch))
            
            priority_actions = recommendations.get('priority_actions', [])
            if priority_actions:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("<b>🚨 Срочные действия:</b>", heading3_style_custom))
                story.append(Spacer(1, 0.1*inch))
                
                for action in priority_actions:
                    if isinstance(action, dict):
                        action_text = action.get('action', action.get('title', ''))
                    else:
                        action_text = str(action)
                    story.append(Paragraph(f"• {action_text}", normal_style))
                    story.append(Spacer(1, 0.05*inch))
        
        # Футер
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            fontName=FONT_NAME
        )
        footer_text = f"Сгенерировано {company_name if company_name else 'DocScan AI'} - https://docscan-ai.ru"
        story.append(Paragraph(footer_text, footer_style))
        
        # Собираем PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"✅ PDF успешно сгенерирован для файла: {filename}")
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
