#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Скрипт для получения всех URL страниц сайта для переобхода в Яндексе"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    from models.sqlite_users import Article, FullNews, Question, db
    
    base_url = "https://docscan-ai.ru"
    
    # Статические страницы
    static_pages = [
        '/',
        '/news',
        '/analiz-dokumentov',
        '/proverka-dogovorov',
        '/articles',
        '/questions',
        '/questions/ask',
        '/faq',
        '/calculator-penalty',
        '/mobile-app',
        '/proverka-dokumentov-onlayn',
        '/articles/nalogovaya-proverka',
        '/partners',
        '/tariffs',
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
        '/riski-dogovora-zayma',
        '/avtokredit-skrytye-usloviya',
        '/ii-dlya-proverki-dogovorov-onlayn-besplatno',
        '/medicinskie-dokumenty-analiz',
        '/contact',
        '/terms',
        '/privacy',
        '/offer',
        '/api',
        '/chat',
    ]
    
    with app.app_context():
        all_urls = []
        
        # Статические страницы
        print("📄 СТАТИЧЕСКИЕ СТРАНИЦЫ:")
        print("-" * 80)
        for page in static_pages:
            url = f"{base_url}{page}"
            print(url)
            all_urls.append(url)
        print()
        
        # Статьи из БД
        print("📝 СТАТЬИ ИЗ БАЗЫ ДАННЫХ:")
        print("-" * 80)
        try:
            articles = Article.query.filter_by(status='published').all()
            if articles:
                for article in articles:
                    url = f"{base_url}/articles/{article.slug}"
                    print(url)
                    all_urls.append(url)
            else:
                print("(Нет опубликованных статей)")
        except Exception as e:
            print(f"(Ошибка получения статей: {e})")
        print()
        
        # Новости из БД
        print("📰 НОВОСТИ ИЗ БАЗЫ ДАННЫХ:")
        print("-" * 80)
        try:
            news = FullNews.query.filter_by(is_published=True).all()
            if news:
                for n in news:
                    url = f"{base_url}/news/{n.slug}"
                    print(url)
                    all_urls.append(url)
            else:
                print("(Нет опубликованных новостей)")
        except Exception as e:
            print(f"(Ошибка получения новостей: {e})")
        print()
        
        # Вопросы из БД
        print("❓ ВОПРОСЫ ИЗ БАЗЫ ДАННЫХ:")
        print("-" * 80)
        try:
            questions = Question.query.all()
            if questions:
                for q in questions:
                    url = f"{base_url}/questions/{q.id}"
                    print(url)
                    all_urls.append(url)
            else:
                print("(Нет вопросов)")
        except Exception as e:
            print(f"(Ошибка получения вопросов: {e})")
        print()
        
        # Итого
        print("=" * 80)
        print(f"ИТОГО СТРАНИЦ: {len(all_urls)}")
        print(f"  - Статические: {len(static_pages)}")
        print(f"  - Статьи: {len([a for a in all_urls if '/articles/' in a and a not in [f'{base_url}{p}' for p in static_pages]])}")
        print(f"  - Новости: {len([a for a in all_urls if '/news/' in a])}")
        print(f"  - Вопросы: {len([a for a in all_urls if '/questions/' in a and '/ask' not in a])}")
        print("=" * 80)
        print()
        
        # Сохраняем в файл
        with open('ALL_URLS_FOR_YANDEX.txt', 'w', encoding='utf-8') as f:
            f.write("ВСЕ URL ДЛЯ ПЕРЕОБХОДА В ЯНДЕКСЕ\n")
            f.write("=" * 80 + "\n\n")
            for url in all_urls:
                f.write(url + "\n")
        
        print("✅ Список сохранен в файл: ALL_URLS_FOR_YANDEX.txt")
        print()
        print("💡 Для отправки в Яндекс:")
        print("   1. Откройте файл ALL_URLS_FOR_YANDEX.txt")
        print("   2. Скопируйте все URL")
        print("   3. Перейдите в Яндекс.Вебмастер: https://webmaster.yandex.ru")
        print("   4. Раздел 'Индексирование' -> 'Переобход страниц'")
        print("   5. Вставьте список URL и отправьте на переобход")
        print()
        print("📋 Или используйте sitemap.xml:")
        print(f"   {base_url}/sitemap.xml")

except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()

