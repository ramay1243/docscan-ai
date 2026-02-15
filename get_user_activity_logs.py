#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для получения логов поведения пользователей за последние 24 часа
"""

import sys
import os
from datetime import datetime, timedelta

# Исправление кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models.sqlite_users import db, User, AnalysisHistory, Guest, Payment, Referral, ReferralReward
from config import Config

def create_app():
    """Создаем минимальное Flask приложение для работы с БД"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def format_datetime(dt_str):
    """Форматирует строку даты для вывода"""
    try:
        if dt_str:
            # Пытаемся распарсить ISO формат
            if 'T' in dt_str:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_str
    return dt_str

def get_user_activity_logs():
    """Получает логи активности пользователей за последние 24 часа"""
    app = create_app()
    
    with app.app_context():
        # Вычисляем время 24 часа назад
        now = datetime.now()
        yesterday = now - timedelta(hours=24)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        print("=" * 80)
        print(f"📊 ЛОГИ ПОВЕДЕНИЯ ПОЛЬЗОВАТЕЛЕЙ ЗА ПОСЛЕДНИЕ 24 ЧАСА")
        print(f"Период: {yesterday_str} {yesterday.strftime('%H:%M:%S')} - {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # 1. НОВЫЕ ПОЛЬЗОВАТЕЛИ (зарегистрированные за 24 часа)
        print("👤 НОВЫЕ ПОЛЬЗОВАТЕЛИ (зарегистрированные за 24 часа):")
        print("-" * 80)
        new_users = User.query.filter(
            User.created_at >= yesterday_str
        ).order_by(User.created_at.desc()).all()
        
        if new_users:
            for user in new_users:
                email = user.email if user.email else "Не указан"
                plan = user.plan
                is_reg = "✅ Зарегистрирован" if user.is_registered else "❌ Не зарегистрирован"
                print(f"  • {format_datetime(user.created_at)} | ID: {user.user_id} | Email: {email} | Тариф: {plan} | {is_reg} | IP: {user.ip_address}")
        else:
            print("  Нет новых пользователей")
        print(f"Всего новых пользователей: {len(new_users)}")
        print()
        
        # 2. АНАЛИЗЫ ДОКУМЕНТОВ (за 24 часа)
        print("📄 АНАЛИЗЫ ДОКУМЕНТОВ (за 24 часа):")
        print("-" * 80)
        analyses = AnalysisHistory.query.filter(
            AnalysisHistory.created_at >= yesterday_str
        ).order_by(AnalysisHistory.created_at.desc()).all()
        
        if analyses:
            for analysis in analyses:
                user = User.query.filter_by(user_id=analysis.user_id).first()
                email = user.email if user and user.email else "Гость"
                print(f"  • {format_datetime(analysis.created_at)} | Пользователь: {analysis.user_id} ({email}) | Файл: {analysis.filename} | Тип: {analysis.document_type_name or 'Не определен'} | Риск: {analysis.risk_level or 'Не определен'}")
        else:
            print("  Нет анализов за этот период")
        print(f"Всего анализов: {len(analyses)}")
        print()
        
        # 3. ПЛАТЕЖИ (за 24 часа)
        print("💳 ПЛАТЕЖИ (за 24 часа):")
        print("-" * 80)
        payments = Payment.query.filter(
            Payment.created_at >= yesterday_str
        ).order_by(Payment.created_at.desc()).all()
        
        if payments:
            for payment in payments:
                user = User.query.filter_by(user_id=payment.user_id).first()
                email = payment.email if payment.email else (user.email if user else "Не указан")
                print(f"  • {format_datetime(payment.created_at)} | Пользователь: {payment.user_id} ({email}) | Тариф: {payment.plan_type} | Сумма: {payment.amount} {payment.currency} | Статус: {payment.status}")
        else:
            print("  Нет платежей за этот период")
        print(f"Всего платежей: {len(payments)}")
        print(f"Общая сумма: {sum(p.amount for p in payments):.2f} RUB")
        print()
        
        # 4. РЕФЕРАЛЫ (приглашения за 24 часа)
        print("🎁 РЕФЕРАЛЬНАЯ ПРОГРАММА (приглашения за 24 часа):")
        print("-" * 80)
        referrals = Referral.query.filter(
            Referral.created_at >= yesterday_str
        ).order_by(Referral.created_at.desc()).all()
        
        if referrals:
            for ref in referrals:
                referrer = User.query.filter_by(user_id=ref.referrer_id).first()
                invited = User.query.filter_by(user_id=ref.invited_user_id).first()
                referrer_email = referrer.email if referrer and referrer.email else "Не указан"
                invited_email = invited.email if invited and invited.email else "Не указан"
                registered = "✅ Зарегистрирован" if ref.registered_at else "⏳ Ожидает регистрации"
                print(f"  • {format_datetime(ref.created_at)} | Пригласил: {ref.referrer_id} ({referrer_email}) → Приглашен: {ref.invited_user_id} ({invited_email}) | {registered}")
        else:
            print("  Нет приглашений за этот период")
        print(f"Всего приглашений: {len(referrals)}")
        print()
        
        # 5. НАГРАДЫ ПАРТНЕРАМ (за 24 часа)
        print("💰 НАГРАДЫ ПАРТНЕРАМ (за 24 часа):")
        print("-" * 80)
        rewards = ReferralReward.query.filter(
            ReferralReward.created_at >= yesterday_str
        ).order_by(ReferralReward.created_at.desc()).all()
        
        if rewards:
            for reward in rewards:
                partner = User.query.filter_by(user_id=reward.partner_id).first()
                partner_email = partner.email if partner and partner.email else "Не указан"
                status = "✅ Выплачено" if reward.status == 'paid' else "⏳ Ожидает выплаты"
                print(f"  • {format_datetime(reward.created_at)} | Партнер: {reward.partner_id} ({partner_email}) | Покупка: {reward.purchase_amount} RUB | Награда: {reward.reward_amount} RUB | {status}")
        else:
            print("  Нет наград за этот период")
        print(f"Всего наград: {len(rewards)}")
        print(f"Общая сумма наград: {sum(r.reward_amount for r in rewards):.2f} RUB")
        print()
        
        # 6. АКТИВНОСТЬ ПО IP (гости)
        print("🌐 АКТИВНОСТЬ ГОСТЕЙ (по IP за 24 часа):")
        print("-" * 80)
        guests = Guest.query.filter(
            Guest.last_seen >= yesterday_str
        ).order_by(Guest.last_seen.desc()).all()
        
        if guests:
            for guest in guests:
                registered = f"→ Зарегистрирован: {guest.registered_user_id}" if guest.registered_user_id else "Не зарегистрирован"
                print(f"  • IP: {guest.ip_address} | Анализов: {guest.analyses_count} | Калькулятор: {guest.calculator_uses} | Последняя активность: {format_datetime(guest.last_seen)} | {registered}")
        else:
            print("  Нет активности гостей за этот период")
        print(f"Всего уникальных IP: {len(guests)}")
        print()
        
        # 7. СТАТИСТИКА ПО ТАРИФАМ
        print("📊 СТАТИСТИКА ПО ТАРИФАМ (активные пользователи):")
        print("-" * 80)
        free_users = User.query.filter_by(plan='free').count()
        basic_users = User.query.filter_by(plan='basic').count()
        premium_users = User.query.filter_by(plan='premium').count()
        total_users = User.query.count()
        
        print(f"  Бесплатный: {free_users} пользователей")
        print(f"  Базовый: {basic_users} пользователей")
        print(f"  Премиум: {premium_users} пользователей")
        print(f"  Всего пользователей: {total_users}")
        print()
        
        # 8. ИТОГОВАЯ СТАТИСТИКА ЗА 24 ЧАСА
        print("=" * 80)
        print("📈 ИТОГОВАЯ СТАТИСТИКА ЗА 24 ЧАСА:")
        print("=" * 80)
        print(f"  • Новых пользователей: {len(new_users)}")
        print(f"  • Анализов документов: {len(analyses)}")
        print(f"  • Платежей: {len(payments)}")
        print(f"  • Сумма платежей: {sum(p.amount for p in payments):.2f} RUB")
        print(f"  • Реферальных приглашений: {len(referrals)}")
        print(f"  • Наград партнерам: {len(rewards)}")
        print(f"  • Сумма наград: {sum(r.reward_amount for r in rewards):.2f} RUB")
        print(f"  • Уникальных IP (гостей): {len(guests)}")
        print("=" * 80)

if __name__ == '__main__':
    try:
        get_user_activity_logs()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

