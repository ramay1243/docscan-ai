from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from utils.logger import RussianLogger
import logging
from flask import send_file

logger = logging.getLogger(__name__)

# Создаем Blueprint для главных маршрутов
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Главная страница с интерфейсом"""
    return render_template('index.html')

# ... (остальные функции routes остаются БЕЗ ИЗМЕНЕНИЙ)
@main_bp.route('/terms')
def terms():
    """Страница пользовательского соглашения"""
    RussianLogger.log_page_view("Пользовательское соглашение")
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    """Страница политики конфиденциальности"""
    RussianLogger.log_page_view("Политика конфиденциальности")
    return render_template('privacy.html')

@main_bp.route('/offer')
def offer():
    """Страница публичной оферты"""
    RussianLogger.log_page_view("Публичная оферта")
    return render_template('offer.html')

@main_bp.route('/tariffs')
def tariffs():
    """Страница тарифов"""
    RussianLogger.log_page_view("Тарифы")
    return render_template('tariffs.html')

@main_bp.route('/sitemap.xml')
def sitemap():
    """Sitemap для SEO с динамическими датами"""
    from datetime import datetime
    base_url = "https://docscan-ai.ru"
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Приоритетные страницы (обновляются часто)
    priority_pages = [
        ('/', 'daily', '1.0'),
        ('/news', 'weekly', '0.9'),
        ('/analiz-dokumentov', 'weekly', '0.9'),
        ('/proverka-dogovorov', 'weekly', '0.9'),
        ('/articles', 'weekly', '0.9'),
        ('/faq', 'monthly', '0.8'),
        ('/calculator-penalty', 'monthly', '0.8'),
        ('/mobile-app', 'weekly', '0.8'),
        ('/proverka-dokumentov-onlayn', 'weekly', '0.9'),
        ('/articles/nalogovaya-proverka', 'monthly', '0.8'),
        ('/partners', 'weekly', '0.8'),
        ('/tariffs', 'weekly', '0.9'),
    ]
    
    # Статьи (обновляются реже)
    articles = [
        '/articles/about',
        '/articles/guide',
        '/articles/tech',
        '/articles/rent',
        '/articles/labor',
        '/articles/tax',
        '/articles/business-protection',
        '/articles/freelance-gph',
        '/articles/ipoteka-2025',
        '/articles/lizing',
        '/articles/strahovanie',
        '/articles/okazanie-uslug',
    ]
    
    # Дополнительные страницы
    additional_pages = [
        ('/riski-dogovora-zayma', 'weekly', '0.9'),
        ('/avtokredit-skrytye-usloviya', 'monthly', '0.8'),
        ('/ii-dlya-proverki-dogovorov-onlayn-besplatno', 'monthly', '0.8'),
        ('/medicinskie-dokumenty-analiz', 'monthly', '0.8'),
        ('/contact', 'monthly', '0.7'),
    ]
    
    # Служебные страницы (низкий приоритет)
    service_pages = [
        ('/terms', 'yearly', '0.3'),
        ('/privacy', 'yearly', '0.3'),
        ('/offer', 'yearly', '0.3'),
    ]
    
    sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'''
    
    # Приоритетные страницы
    for url, changefreq, priority in priority_pages:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}{url}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{changefreq}</changefreq>
        <priority>{priority}</priority>
    </url>'''
    
    # Статьи
    for article in articles:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}{article}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>'''
    
    # Дополнительные страницы
    for url, changefreq, priority in additional_pages:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}{url}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{changefreq}</changefreq>
        <priority>{priority}</priority>
    </url>'''
    
    # Служебные страницы
    for url, changefreq, priority in service_pages:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}{url}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{changefreq}</changefreq>
        <priority>{priority}</priority>
    </url>'''
    
    sitemap_xml += '''
</urlset>'''
    
    return sitemap_xml, 200, {'Content-Type': 'application/xml'}

@main_bp.route('/robots.txt')
def robots():
    """Robots.txt для SEO - отдает статический файл"""
    from flask import send_from_directory
    import os
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    return send_from_directory(static_folder, 'robots.txt', mimetype='text/plain')

@main_bp.route('/articles')
def articles():
    """Страница со списком всех статей"""
    from app import app
    
    # Получаем опубликованные статьи из БД
    articles_list = app.user_manager.get_published_articles(limit=100)
    
    return render_template('articles.html', articles=articles_list)

@main_bp.route('/articles/<slug>')
def article_detail(slug):
    """Страница отдельной статьи"""
    from app import app
    from flask import abort
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Получаем опубликованную статью по slug
    article = app.user_manager.get_published_article_by_slug(slug)
    
    if not article:
        logger.warning(f"❌ Статья не найдена или не опубликована: slug={slug}")
        abort(404)
    
    # Получаем список всех опубликованных статей для навигации
    all_articles = app.user_manager.get_published_articles(limit=50)
    
    # Находим текущую статью в списке для навигации (предыдущая/следующая)
    current_index = next((i for i, a in enumerate(all_articles) if a.get('id') == article.id), None)
    prev_article = all_articles[current_index - 1] if current_index is not None and current_index > 0 else None
    next_article = all_articles[current_index + 1] if current_index is not None and current_index < len(all_articles) - 1 else None
    
    logger.info(f"✅ Просмотр статьи: {article.title} (slug: {slug})")
    
    return render_template('article_detail.html', 
                         article=article.to_dict(),
                         prev_article=prev_article,
                         next_article=next_article)

@main_bp.route('/articles/about')
def article_about():
    """Статья 'О проекте'"""
    return render_template('article_about.html')

@main_bp.route('/articles/guide')
def article_guide():
    """Статья 'Как пользоваться сервисом'"""
    return render_template('article_guide.html')

@main_bp.route('/articles/tech')
def article_tech():
    """Статья 'Технологии и AI'"""
    return render_template('article_tech.html')

@main_bp.route('/contact')
def contact():
    """Страница контактов"""
    return render_template('contact.html')
    
@main_bp.route('/articles/rent')
def article_rent():
    """Статья 'Как проверить договор аренды'"""
    return render_template('article_rent.html')
    
@main_bp.route('/articles/labor')
def article_labor():
    """Статья 'Топ-5 ошибок в трудовых договорах'"""
    return render_template('article_labor.html')
    
@main_bp.route('/articles/tax')
def article_tax():
    """Статья 'Финансовые риски в договорах'"""
    return render_template('article_tax.html')

@main_bp.route('/articles/nalogovaya-proverka')
def article_nalogovaya_proverka():
    """Статья 'Документ налоговой проверки'"""
    return render_template('article_nalogovaya-proverka.html')
    
@main_bp.route('/articles/business_protection')
def redirect_business_protection():
    """Редирект со старого URL (с подчёркиванием) на новый (с дефисом)"""
    return redirect('/articles/business-protection', code=301)
    
@main_bp.route('/articles/business-protection')
def article_business_protection():
    return render_template('article_business_protection.html')
    
@main_bp.route('/articles/freelance-gph')
def article_freelance_gph():
    return render_template('article_freelance_gph.html')

@main_bp.route('/articles/article_freelance_gph')
def redirect_article_freelance():
    """Редирект со старого URL на новый"""
    return redirect('/articles/freelance-gph', code=301)

@main_bp.route('/news')
def news():
    """Страница новостей и обновлений"""
    from app import app
    RussianLogger.log_page_view("Новости и обновления")
    
    # Загружаем новости из базы данных
    updates = app.user_manager.get_news_items(category='updates', limit=50)
    news_items = app.user_manager.get_news_items(category='news', limit=50)
    
    return render_template('news.html', updates=updates, news_items=news_items)

@main_bp.route('/analiz-dokumentov')
def analiz_dokumentov():
    return render_template('analiz-dokumentov.html')
    
@main_bp.route('/proverka-dogovorov')
def proverka_dogovorov():
    """Страница проверки договоров"""
    return render_template('proverka-dogovorov.html')

@main_bp.route('/proverka-dokumentov-onlayn')
def proverka_dokumentov_onlayn():
    """Страница проверки документов онлайн"""
    return render_template('proverka-dokumentov-onlayn.html')

@main_bp.route('/riski-dogovora-zayma')
def riski_dogovora_zayma():
    """Страница с статьей о рисках договора займа"""
    return render_template('riski-dogovora-zayma.html')
    
@main_bp.route('/avtokredit-skrytye-usloviya')
def avtokredit_skrytye_usloviya():
    """Статья про скрытые условия в автокредитах"""
    return render_template('avtokredit-skrytye-usloviya.html')
    
@main_bp.route('/ii-dlya-proverki-dogovorov-onlayn-besplatno')
def ii_dlya_proverki_dogovorov():
    return render_template('ii-dlya-proverki-dogovorov-onlayn-besplatno.html')

@main_bp.route('/medicinskie-dokumenty-analiz')
def medicinskie_dokumenty_analiz():
    return render_template('medicinskie-dokumenty-analiz.html')
    
@main_bp.route('/faq')
def faq_page():
    return render_template('faq.html')
    
@main_bp.route('/articles/rent-check')
def redirect_rent_check():
    return redirect('/articles/rent', code=301)
    
@main_bp.route('/=')
def redirect_root_equals():
    """Редирект странного URL на главную"""
    return redirect('/', code=301)
    
@main_bp.route('/articles/ipoteka-2025')
def article_ipoteka():
    return render_template('article_ipoteka_2025.html')

@main_bp.route('/articles/lizing')
def article_lizing():
    """Статья 'Проверка договора лизинга'"""
    return render_template('article_lizing.html')

@main_bp.route('/articles/strahovanie')
def article_strahovanie():
    """Статья 'Договор страхования: что проверить перед подписанием'"""
    return render_template('article_strahovanie.html')

@main_bp.route('/articles/okazanie-uslug')
def article_okazanie_uslug():
    """Статья 'Проверка договора оказания услуг'"""
    return render_template('article_okazanie-uslug.html')
    
@main_bp.route('/calculator-penalty')
def calculator_penalty():
    """Страница калькулятора неустойки"""
    return render_template('calculator_penalty.html')

@main_bp.route('/mobile-app')
def mobile_app_page():
    return render_template('mobile_app.html')
    
@main_bp.route('/telderi5f932e1d02880a7a361463d87d31d143.txt')
def telderi_verification():
    return "Telderi", 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
@main_bp.route('/send-telegram', methods=['POST'])
def send_telegram():
    """Отправка сообщения в Telegram"""
    import requests
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    data = request.json
    
    # Новый токен бота
    bot_token = "8112079604:AAHzzoB53c7FIo-fs4gvpWUzAdmtW1YF9Z8"
    
    # Функция для получения chat_id из последних обновлений (автоматически)
    def get_chat_id_from_updates(bot_token):
        """Получает chat_id из последних обновлений бота"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                updates = response.json()
                if updates.get('ok') and updates.get('result'):
                    # Берем chat_id из последнего сообщения
                    for update in reversed(updates['result']):
                        if 'message' in update:
                            chat_id = update['message']['chat']['id']
                            logger.info(f"✅ Найден chat_id из обновлений: {chat_id}")
                            return str(chat_id)
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения chat_id: {e}")
            return None
    
    # Автоматически получаем chat_id из обновлений бота
    chat_id = get_chat_id_from_updates(bot_token)
    
    # Если не удалось получить, пробуем из переменной окружения (для обратной совместимости)
    if not chat_id:
        import os
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    # Если все еще не найден, возвращаем ошибку с инструкцией
    if not chat_id:
        logger.error("❌ chat_id не найден. Нужно чтобы кто-то написал боту /start")
        return jsonify({
            'success': False, 
            'error': 'Бот не настроен. Пожалуйста, напишите боту @helpdocscanbot команду /start, затем повторите отправку формы.'
        }), 400
    
    # Формируем текст сообщения
    subject_names = {
        'technical': 'Техническая проблема',
        'billing': 'Вопросы по оплате',
        'feature': 'Предложение по улучшению',
        'partnership': 'Сотрудничество',
        'other': 'Другое'
    }
    
    subject_display = subject_names.get(data.get('subject', ''), data.get('subject', 'Не указано'))
    
    text = f"""
📨 *НОВОЕ СООБЩЕНИЕ С САЙТА*

*👤 Имя:* {data.get('name', 'Не указано')}
*📧 Email:* {data.get('email', 'Не указано')}
*🎯 Тема:* {subject_display}

*💬 Сообщение:*
{data.get('message', 'Пустое сообщение')}
    """
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Сообщение успешно отправлено в Telegram (chat_id: {chat_id})")
            return jsonify({'success': True})
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('description', 'Ошибка отправки в Telegram')
            logger.error(f"❌ Ошибка отправки в Telegram: {response.status_code} - {error_msg}")
            return jsonify({'success': False, 'error': f'Ошибка отправки: {error_msg}'}), response.status_code
            
    except Exception as e:
        logger.error(f"❌ Исключение при отправке в Telegram: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/favicon.ico')
def favicon():
    """Отдает фавикон для браузеров и поисковых систем"""
    return send_file('static/favicon.ico', mimetype='image/x-icon')
