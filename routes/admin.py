from flask import Blueprint, request, jsonify, session
import secrets
import uuid
import os
import subprocess
import sys
from datetime import datetime
from functools import wraps
from config import ADMINS
import logging
from models.limits import IPLimitManager

logger = logging.getLogger(__name__)

# Создаем Blueprint для админ-панели
admin_bp = Blueprint('admin', __name__)



def require_admin_auth(f):
    """Декоратор для проверки авторизации администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем специальную куку
        admin_cookie = request.cookies.get('admin_auth')
        if not admin_cookie or admin_cookie != 'authenticated':
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Страница входа в админ-панель"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in ADMINS and ADMINS[username] == password:  # ← ДОБАВИТЬ 4 ПРОБЕЛА
            response = jsonify({'success': True})
            response.set_cookie('admin_auth', 'authenticated', max_age=3600)
            return response                              # ← ДОБАВИТЬ 4 ПРОБЕЛА
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login - DocScan</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .login-box { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); width: 300px; }
            h2 { text-align: center; margin-bottom: 30px; color: #2d3748; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #cbd5e0; border-radius: 8px; box-sizing: border-box; }
            button { width: 100%; background: #667eea; color: white; border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-size: 16px; }
            button:hover { background: #5a67d8; }
            .error { color: #e53e3e; text-align: center; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>🔧 Вход в админ-панель</h2>
            <form id="loginForm">
                <input type="text" name="username" placeholder="Логин" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit">Войти</button>
            </form>
            <div class="error" id="error"></div>
        </div>
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                
                const response = await fetch('/admin/login', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    window.location.href = '/admin';
                } else {
                    document.getElementById('error').textContent = result.error;
                }
            });
        </script>
    </body>
    </html>
    """

@admin_bp.route('/')
@require_admin_auth
def admin_panel():
    """Защищенная админ-панель"""
    admin_info = {'username': session.get('admin_username', 'Unknown')}
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Panel - DocScan</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                background: #f7fafc; 
                color: #2d3748;
                overflow-x: hidden;
            }
            
            /* Боковое меню */
            .sidebar {
                position: fixed;
                left: 0;
                top: 0;
                width: 260px;
                height: 100vh;
                background: linear-gradient(180deg, #1a202c 0%, #2d3748 100%);
                color: white;
                overflow-y: auto;
                z-index: 1000;
                box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            }
            
            .sidebar-header {
                padding: 20px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                background: rgba(0,0,0,0.2);
            }
            
            .sidebar-header h1 {
                font-size: 1.3rem;
                margin-bottom: 5px;
            }
            
            .sidebar-header p {
                font-size: 0.85rem;
                opacity: 0.8;
            }
            
            .sidebar-menu {
                padding: 10px 0;
            }
            
            .menu-item {
                display: block;
                padding: 12px 20px;
                color: rgba(255,255,255,0.8);
                text-decoration: none;
                cursor: pointer;
                transition: all 0.2s;
                border-left: 3px solid transparent;
                user-select: none;
                -webkit-user-select: none;
                pointer-events: auto !important;
                position: relative;
                z-index: 100;
                background: transparent;
            }
            
            .menu-item:hover {
                background: rgba(255,255,255,0.1) !important;
                color: white;
            }
            
            .menu-item.active {
                background: rgba(102, 126, 234, 0.2) !important;
                border-left-color: #667eea;
                color: white;
                font-weight: 600;
            }
            
            .menu-item:active {
                transform: scale(0.98);
                opacity: 0.9;
            }
            
            .menu-item i {
                margin-right: 10px;
                font-size: 1.1rem;
            }
            
            /* Основной контент */
            .main-content {
                margin-left: 260px;
                min-height: 100vh;
                padding: 0;
                width: calc(100% - 260px);
                overflow-x: hidden;
            }
            
            .top-header {
                background: white;
                padding: 20px 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .top-header h2 {
                font-size: 1.5rem;
                color: #2d3748;
            }
            
            .top-header .user-info {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .content-area {
                padding: 30px;
            }
            
            /* Секции контента */
            .content-section {
                display: none;
            }
            
            .content-section.active {
                display: block;
            }
            
            /* Карточки */
            .user-card { 
                background: white; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 8px; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
            }
            
            .stat-card { 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                text-align: center; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            }
            
            .stats { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                margin: 20px 0; 
            }
            
            /* Кнопки */
            button { 
                background: #667eea; 
                color: white; 
                border: none; 
                padding: 10px 15px; 
                margin: 5px; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 0.9rem;
                transition: background 0.2s;
            }
            
            button:hover { 
                background: #5a67d8; 
            }
            
            .logout-btn { 
                background: #e53e3e; 
            }
            
            .logout-btn:hover { 
                background: #c53030; 
            }
            
            /* Кнопка меню для мобильных */
            .menu-toggle {
                display: none;
                position: fixed;
                top: 15px;
                left: 15px;
                z-index: 1001;
                background: #667eea;
                color: white;
                border: none;
                padding: 0;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1.2rem;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                width: 44px;
                height: 44px;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .menu-toggle:hover {
                background: #5a67d8;
            }
            
            /* Затемнение фона при открытом меню */
            .sidebar-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 999;
            }
            
            .sidebar-overlay.active {
                display: block;
            }
            
            /* Мобильная версия */
            @media (max-width: 768px) {
                .sidebar {
                    transform: translateX(-100%);
                    transition: transform 0.3s ease;
                    width: 280px;
                    z-index: 1000;
                }
                
                .sidebar.open {
                    transform: translateX(0);
                }
                
                .sidebar-overlay.active {
                    display: block;
                }
                
                .main-content {
                    margin-left: 0 !important;
                    width: 100% !important;
                }
                
                .menu-toggle {
                    display: block;
                }
                
                .top-header {
                    padding: 15px 20px;
                    flex-wrap: wrap;
                }
                
                .top-header h2 {
                    font-size: 1.2rem;
                    margin-bottom: 10px;
                }
                
                .top-header .user-info {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 10px;
                    width: 100%;
                }
                
                .content-area {
                    padding: 15px;
                }
                
                .stats {
                    grid-template-columns: 1fr;
                    gap: 15px;
                }
                
                .stat-card {
                    padding: 15px;
                }
                
                .card {
                    padding: 15px;
                    margin: 15px 0;
                }
                
                .section-header {
                    font-size: 1.2rem;
                    margin: 20px 0 15px 0;
                }
                
                button {
                    width: 100%;
                    margin: 5px 0;
                    padding: 12px;
                    font-size: 1rem;
                }
                
                input, select, textarea {
                    width: 100% !important;
                    max-width: 100% !important;
                    box-sizing: border-box;
                }
                
                .user-card {
                    padding: 12px;
                    margin: 8px 0;
                }
            }
            
            /* Заголовки секций */
            .section-header {
                margin: 30px 0 20px 0;
                padding-bottom: 15px;
                border-bottom: 2px solid #e2e8f0;
                font-size: 1.5rem;
                color: #2d3748;
            }
            
            .card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <!-- Затемнение фона для мобильных -->
        <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleMobileMenu()"></div>
        
        <!-- Кнопка меню для мобильных -->
        <button class="menu-toggle" id="menuToggle" onclick="toggleMobileMenu()">☰</button>
        
        <!-- Боковое меню -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h1>🔧 DocScan Admin</h1>
                <p>""" + admin_info.get('username', 'Unknown') + """</p>
            </div>
            <nav class="sidebar-menu" id="sidebarMenu">
                <a href="#" class="menu-item active" data-section="dashboard">
                    <span>📊</span> Главная
                </a>
                <a href="#" class="menu-item" data-section="users">
                    <span>👥</span> Пользователи
                </a>
                <a href="#" class="menu-item" data-section="guests">
                    <span>👤</span> Гости
                </a>
                <a href="#" class="menu-item" data-section="search-bots">
                    <span>🕷️</span> Поисковые боты
                </a>
                <a href="#" class="menu-item" data-section="campaigns">
                    <span>📧</span> Email-рассылки
                </a>
                <a href="#" class="menu-item" data-section="backups">
                    <span>💾</span> Резервные копии
                </a>
                <a href="#" class="menu-item" data-section="articles">
                    <span>📝</span> Статьи
                </a>
                <a href="#" class="menu-item" data-section="news">
                    <span>📰</span> Новости
                </a>
                <a href="#" class="menu-item" data-section="full-news">
                    <span>📄</span> Полные новости
                </a>
                <a href="#" class="menu-item" data-section="questions">
                    <span>❓</span> Вопросы и ответы
                </a>
                <a href="#" class="menu-item" data-section="notifications">
                    <span>🔔</span> Уведомления
                </a>
                <a href="#" class="menu-item" data-section="partners">
                    <span>🎁</span> Партнерская программа
                </a>
                <a href="#" class="menu-item" data-section="api-keys">
                    <span>🔑</span> API-ключи
                </a>
                <a href="#" class="menu-item" data-section="analysis-settings-admin">
                    <span>⚙️</span> Настройки анализа
                </a>
            </nav>
        </div>
        
        <!-- Основной контент -->
        <div class="main-content">
            <div class="top-header">
                <h2 id="pageTitle">📊 Главная</h2>
                <div class="user-info">
                    <span>Вошел как: <strong>""" + admin_info.get('username', 'Unknown') + """</strong></span>
                <button class="logout-btn" onclick="logout()">🚪 Выйти</button>
                </div>
            </div>
            
            <div class="content-area">
                <!-- Секция: Главная (Dashboard) -->
                <div id="section-dashboard" class="content-section active">
            <div class="stats">
                <div class="stat-card">
                    <h3>👥 Всего пользователей</h3>
                    <div id="totalUsers" style="font-size: 2rem; font-weight: bold; color: #667eea; margin-top: 10px;">0</div>
                </div>
                <div class="stat-card">
                    <h3>🆕 Новых пользователей за 24 часа</h3>
                    <div id="newUsers24h" style="font-size: 2rem; font-weight: bold; color: #48bb78; margin-top: 10px;">0</div>
                </div>
                <div class="stat-card">
                    <h3>🆕 Новых гостей за 24 часа</h3>
                    <div id="newGuests24h" style="font-size: 2rem; font-weight: bold; color: #ed8936; margin-top: 10px;">0</div>
                </div>
                <div class="stat-card">
                    <h3>👤 Всего гостей</h3>
                    <div id="totalGuests" style="font-size: 2rem; font-weight: bold; color: #667eea; margin-top: 10px;">0</div>
                </div>
                <div class="stat-card">
                    <h3>🕷️ Поисковых ботов за 24 часа</h3>
                    <div id="newBots24h" style="font-size: 2rem; font-weight: bold; color: #ed8936; margin-top: 10px;">0</div>
                </div>
                <div class="stat-card">
                    <h3>🕷️ Всего ботов</h3>
                    <div id="totalBots" style="font-size: 2rem; font-weight: bold; color: #667eea; margin-top: 10px;">0</div>
                </div>
                <div class="stat-card">
                    <h3>📊 Всего анализов</h3>
                    <div id="totalAnalyses" style="font-size: 2rem; font-weight: bold; color: #667eea; margin-top: 10px;">0</div>
                </div>
                <div class="stat-card">
                    <h3>📈 Анализов сегодня</h3>
                    <div id="todayAnalyses" style="font-size: 2rem; font-weight: bold; color: #667eea; margin-top: 10px;">0</div>
                </div>
                <div class="stat-card">
                    <h3>📄 /business-ip сегодня</h3>
                    <div id="businessIpViewsToday" style="font-size: 2rem; font-weight: bold; color: #667eea; margin-top: 10px;">0</div>
                    <div style="margin-top: 6px; color: #718096;">Уникальных: <span id="businessIpUniqueToday">0</span></div>
                </div>
                <div class="stat-card">
                    <h3>📄 /business-ip всего</h3>
                    <div id="businessIpViewsTotal" style="font-size: 2rem; font-weight: bold; color: #667eea; margin-top: 10px;">0</div>
                </div>
                <div class="stat-card">
                    <h3>💰 Доход сегодня</h3>
                    <div id="todayRevenue" style="font-size: 2rem; font-weight: bold; color: #48bb78; margin-top: 10px;">0 ₽</div>
                </div>
                <div class="stat-card">
                    <h3>💰 Доход за всё время</h3>
                    <div id="totalRevenue" style="font-size: 2rem; font-weight: bold; color: #48bb78; margin-top: 10px;">0 ₽</div>
                </div>
                <div class="stat-card">
                    <h3>🧾 Платежей сегодня</h3>
                    <div id="todayPayments" style="font-size: 2rem; font-weight: bold; color: #ed8936; margin-top: 10px;">0</div>
                </div>
            </div>
            
            <div class="card">
                <h3>🆕 Новые пользователи за последние 24 часа</h3>
                <button onclick="loadNewUsers()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px;">🔄 Обновить</button>
                <div id="newUsersList"></div>
            </div>
            
            <div class="card">
                <h3>💰 Последние платежи</h3>
                <div style="margin-bottom: 20px;">
                    <select id="paymentsFilter" onchange="loadPayments()" style="padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                        <option value="">Все платежи</option>
                        <option value="1">За сегодня</option>
                        <option value="7">За 7 дней</option>
                        <option value="30">За 30 дней</option>
                    </select>
                    <button onclick="loadPayments()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">🔄 Обновить</button>
                </div>
                <div id="paymentsList"></div>
            </div>
            
                    <div class="card">
                        <h3>Статистика калькулятора</h3>
                        <button onclick="showCalculatorStats()">📊 Показать статистику калькулятора</button>
                        <div id="calculatorStats" style="display: none; margin-top: 20px;"></div>
                    </div>
                </div>
                
                <!-- Секция: Пользователи -->
                <div id="section-users" class="content-section">
                    <h2 class="section-header">👥 Зарегистрированные пользователи</h2>
                    
                    <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: 2px solid #667eea;">
                        <h3 style="color: white; margin-bottom: 10px;">💎 Выдать тариф пользователю</h3>
                        <p style="color: rgba(255,255,255,0.9); font-size: 0.9rem; margin-bottom: 15px;">Выберите пользователя и тариф для выдачи. Для разовых тарифов (Стандарт, Премиум) анализы действуют 30-60 дней. Для бизнес-тарифов лимиты обновляются каждый месяц.</p>
                        <div style="margin: 15px 0; display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
                            <input type="text" id="userId" placeholder="ID пользователя" 
                                   style="width: 200px; padding: 10px; border: 2px solid rgba(255,255,255,0.3); border-radius: 8px; background: rgba(255,255,255,0.95); color: #2d3748; font-weight: 500;">
                            <select id="planSelect" style="padding: 10px; border: 2px solid rgba(255,255,255,0.3); border-radius: 8px; background: rgba(255,255,255,0.95); color: #2d3748; font-weight: 500; min-width: 300px;">
                                <optgroup label="Для физических лиц">
                                    <option value="free">Бесплатный (1 бесплатный анализ)</option>
                                    <option value="standard">Стандарт (5 анализов, 30 дней) - 590₽</option>
                                    <option value="premium">Премиум (15 анализов, 60 дней) - 1 350₽</option>
                                </optgroup>
                                <optgroup label="Для бизнеса (месячная подписка)">
                                    <option value="business_start">Бизнес Старт (10 анализов/мес) - 1 425₽/мес</option>
                                    <option value="business_pro">Бизнес Про (50 анализов/мес) - 4 500₽/мес</option>
                                    <option value="business_max">Бизнес Макс (100 анализов/мес) - 13 500₽/мес</option>
                                    <option value="business_unlimited">Бизнес Безлимит (безлимит) - 26 400₽/мес</option>
                                </optgroup>
                            </select>
                            <button onclick="setUserPlan()" style="padding: 10px 25px; background: white; color: #667eea; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: all 0.3s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.3)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(0,0,0,0.2)';">✅ Выдать тариф</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Создать нового пользователя</h3>
                        <div style="margin: 15px 0;">
                            <input type="text" id="newUserId" placeholder="Новый ID пользователя (опционально)" 
                                   style="width: 300px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <button onclick="createUser()">Создать пользователя</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Управление пользователями</h3>
<div style="margin: 15px 0;">
    <input type="text" id="searchUser" placeholder="🔍 Поиск по ID, тарифу, IP..." 
           style="width: 300px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;"
           onkeyup="searchUsers()">
                            <button onclick="clearSearch()" style="background: #e2e8f0; color: #2d3748;">Очистить</button>
    <span id="searchStatus" style="margin-left: 10px; color: #666; font-size: 14px;"></span>
</div>
<div id="usersList"></div>
                    </div>
                    
                    <div class="card">
                        <h3>🔒 Белый список IP (для бизнес-тарифов)</h3>
                        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
                            Управление разрешенными IP-адресами для пользователей. Если для пользователя добавлен хотя бы один IP, доступ будет разрешен только с этих адресов.
                        </p>
                        <div style="margin: 15px 0;">
                            <input type="text" id="whitelistUserId" placeholder="ID пользователя" 
                                   style="width: 200px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <input type="text" id="whitelistIP" placeholder="IP-адрес (например: 192.168.1.1 или 192.168.1.0/24)" 
                                   style="width: 300px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <input type="text" id="whitelistDescription" placeholder="Описание (например: Офис в Москве)" 
                                   style="width: 200px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <button onclick="addWhitelistedIP()" style="background: #48bb78; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer;">➕ Добавить IP</button>
                        </div>
                        <div id="whitelistStatus" style="margin: 10px 0; color: #666; font-size: 14px;"></div>
                        <div id="whitelistList" style="margin-top: 20px;"></div>
                    </div>
                    
                    <div class="card">
                        <h3>🎨 Кастомный брендинг (для бизнес-тарифов)</h3>
                        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
                            Настройка кастомного брендинга для пользователей. Логотип и цвета будут применяться ко всем отчетам (PDF, Word, Excel).
                        </p>
                        <div style="margin: 15px 0;">
                            <input type="text" id="brandingUserId" placeholder="ID пользователя" 
                                   style="width: 200px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <button onclick="loadBranding()" style="background: #667eea; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer;">📥 Загрузить настройки</button>
                        </div>
                        <div id="brandingStatus" style="margin: 10px 0; color: #666; font-size: 14px;"></div>
                        
                        <div id="brandingForm" style="display: none; margin-top: 20px; padding: 20px; background: #f7fafc; border-radius: 8px;">
                            <h4 style="margin-bottom: 15px;">Настройки брендинга</h4>
                            
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Название компании:</label>
                                <input type="text" id="brandingCompanyName" placeholder="Например: ООО Рога и Копыта" 
                                       style="width: 100%; max-width: 400px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Основной цвет (hex):</label>
                                <input type="color" id="brandingPrimaryColor" value="#4361ee" 
                                       style="width: 100px; height: 40px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                                <input type="text" id="brandingPrimaryColorText" value="#4361ee" placeholder="#4361ee" 
                                       style="width: 150px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Вторичный цвет (hex):</label>
                                <input type="color" id="brandingSecondaryColor" value="#764ba2" 
                                       style="width: 100px; height: 40px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                                <input type="text" id="brandingSecondaryColorText" value="#764ba2" placeholder="#764ba2" 
                                       style="width: 150px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Логотип (PNG, JPG, JPEG, GIF, SVG):</label>
                                <input type="file" id="brandingLogo" accept="image/png,image/jpeg,image/jpg,image/gif,image/svg+xml" 
                                       style="width: 100%; max-width: 400px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                                <small style="color: #666; font-size: 0.85rem;">Рекомендуемый размер: 200x80px. Максимальный размер: 2MB.</small>
                            </div>
                            
                            <div id="brandingLogoPreview" style="margin: 15px 0; display: none;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Текущий логотип:</label>
                                <img id="brandingLogoPreviewImg" src="" alt="Логотип" style="max-width: 200px; max-height: 80px; border: 1px solid #cbd5e0; border-radius: 5px; padding: 5px;">
                            </div>
                            
                            <div style="margin: 20px 0;">
                                <button onclick="saveBranding()" style="background: #48bb78; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">💾 Сохранить настройки</button>
                                <button onclick="toggleBrandingActive()" id="brandingToggleBtn" style="background: #ed8936; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">⏸️ Деактивировать</button>
                                <button onclick="deleteBranding()" style="background: #e53e3e; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">🗑️ Удалить брендинг</button>
                            </div>
                        </div>
                    </div>
                    
                </div>
                
                <!-- Секция: Гости -->
                <div id="section-guests" class="content-section">
                    <h2 class="section-header">👤 Гости (незарегистрированные пользователи)</h2>
                    <p>Пользователи, которые сделали анализ без регистрации</p>
                    
                    <div class="card">
                        <div style="margin: 15px 0;">
                            <input type="text" id="searchGuest" placeholder="🔍 Поиск по IP, браузеру..." 
                                   style="width: 300px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;"
                                   onkeyup="searchGuests()">
                            <button onclick="clearGuestSearch()" style="background: #e2e8f0; color: #2d3748;">Очистить</button>
                            <span id="guestSearchStatus" style="margin-left: 10px; color: #666; font-size: 14px;"></span>
                        </div>
                        <div id="guestsList"></div>
                    </div>
                </div>
                
                <!-- Секция: Поисковые боты -->
                <div id="section-search-bots" class="content-section">
                    <h2 class="section-header">🕷️ Поисковые боты</h2>
                    <p>Боты поисковых систем, которые индексируют сайт</p>
                    
                    <div class="stats" style="margin: 20px 0;">
                        <div class="stat-card">
                            <h3>🕷️ Новых ботов за 24 часа</h3>
                            <div id="newBots24hDetail" style="font-size: 2rem; font-weight: bold; color: #ed8936; margin-top: 10px;">0</div>
                        </div>
                        <div class="stat-card">
                            <h3>🕷️ Всего ботов</h3>
                            <div id="totalBotsDetail" style="font-size: 2rem; font-weight: bold; color: #667eea; margin-top: 10px;">0</div>
                        </div>
                        <div class="stat-card">
                            <h3>📊 Активность ботов сегодня</h3>
                            <div id="todayBotVisits" style="font-size: 2rem; font-weight: bold; color: #48bb78; margin-top: 10px;">0</div>
                        </div>
                        <div class="stat-card">
                            <h3>🌐 Типы ботов</h3>
                            <div id="uniqueBotTypes" style="font-size: 2rem; font-weight: bold; color: #667eea; margin-top: 10px;">0</div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div style="margin: 15px 0;">
                            <input type="text" id="searchBot" placeholder="🔍 Поиск по IP, типу бота..." 
                                   style="width: 300px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;"
                                   onkeyup="searchBots()">
                            <button onclick="clearBotSearch()" style="background: #e2e8f0; color: #2d3748;">Очистить</button>
                            <span id="botSearchStatus" style="margin-left: 10px; color: #666; font-size: 14px;"></span>
                        </div>
                        <div id="botsList"></div>
                    </div>
                </div>
                
                <!-- Секция: Email-рассылки -->
                <div id="section-campaigns" class="content-section">
                    <h2 class="section-header">📧 Email-рассылки</h2>
                    
                    <div class="card">
                        <h3>Создать новую рассылку</h3>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Название рассылки:</label>
                            <input type="text" id="campaignName" placeholder="Например: Приветственное письмо" 
                                   style="width: 100%; max-width: 500px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Тема письма:</label>
                            <input type="text" id="campaignSubject" placeholder="Например: Добро пожаловать в DocScan AI!" 
                                   style="width: 100%; max-width: 500px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Получатели:</label>
                            <select id="campaignRecipients" style="width: 100%; max-width: 500px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                                <option value="all">Все зарегистрированные пользователи</option>
                                <option value="free">Только бесплатный тариф</option>
                                <option value="paid">Только платные тарифы</option>
                                <option value="verified">Только верифицированные email</option>
                                <option value="manual">Выбрать вручную (по пользователям)</option>
            </select>
                        </div>

                        <div id="manualRecipientsBlock" style="display:none; margin: 15px 0; padding: 15px; background:#f7fafc; border-radius:10px; border: 1px solid #cbd5e0; max-width: 800px;">
                            <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                                <input type="text" id="manualRecipientSearch" placeholder="🔍 Поиск по email / user_id" style="width: 320px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                                <button onclick="selectAllManualRecipients(true)" style="background:#48bb78; color:white; border:none; padding:8px 12px; border-radius:5px; cursor:pointer;">✅ Выбрать всех</button>
                                <button onclick="selectAllManualRecipients(false)" style="background:#e2e8f0; color:#2d3748; border:none; padding:8px 12px; border-radius:5px; cursor:pointer;">✖ Снять выбор</button>
                                <span id="manualRecipientsCount" style="color:#666; font-size: 0.9rem;"></span>
                            </div>
                            <div id="manualRecipientsList" style="margin-top: 12px; background:white; padding:12px; border-radius:8px; max-height: 320px; overflow:auto;"></div>
                            <p style="margin-top:10px; font-size:12px; color:#666;">
                                Отправка пойдет только выбранным пользователям. У отписавшихся (email_subscribed=false) письма не отправляются.
                            </p>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">HTML-содержимое письма:</label>
                            <p style="font-size: 12px; color: #666; margin-bottom: 5px;">
                                Доступные переменные: {email}, {user_id}, {plan}, {plan_name}
                            </p>
                            <textarea id="campaignHtmlContent" rows="15" placeholder="Введите HTML-код письма..."
                                      style="width: 100%; max-width: 800px; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px; font-family: monospace;"></textarea>
                            <button onclick="insertEmailTemplate()" style="background: #4299e1; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; margin-top: 10px; font-size: 0.9rem;">📄 Вставить базовый шаблон</button>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Текстовая версия (опционально):</label>
                            <textarea id="campaignTextContent" rows="8" placeholder="Текстовая версия письма..."
                                      style="width: 100%; max-width: 800px; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px;"></textarea>
        </div>

                        <div style="margin: 20px 0;">
                            <button onclick="previewCampaign()" style="background: #4299e1; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">👁️ Предпросмотр</button>
                            <button onclick="createCampaign()" style="background: #48bb78; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">💾 Создать рассылку</button>
                            <button onclick="loadRecipientsPreview()" style="background: #ed8936; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-left: 10px;">👥 Предпросмотр получателей</button>
                        </div>
                        
                        <div id="campaignPreview" style="display: none; margin-top: 20px; padding: 20px; background: #f7fafc; border-radius: 10px; border: 1px solid #cbd5e0;">
                            <h4>Предпросмотр письма:</h4>
                            <div id="previewContent" style="background: white; padding: 20px; border-radius: 5px; margin-top: 10px;"></div>
                        </div>
                        
                        <div id="recipientsPreview" style="display: none; margin-top: 20px; padding: 20px; background: #f7fafc; border-radius: 10px; border: 1px solid #cbd5e0;">
                            <h4>Получатели рассылки:</h4>
                            <div id="recipientsList" style="background: white; padding: 20px; border-radius: 5px; margin-top: 10px; max-height: 400px; overflow-y: auto;"></div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>История рассылок</h3>
                        <button onclick="loadEmailCampaigns()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px;">🔄 Обновить список</button>
                        <div id="emailCampaignsList"></div>
                    </div>
                </div>
                
                <!-- Секция: Резервные копии -->
                <div id="section-backups" class="content-section">
                    <h2 class="section-header">💾 Резервные копии базы данных</h2>
                    <p style="color: #666; margin-bottom: 20px;">
                        Управление резервными копиями базы данных. Рекомендуется создавать бэкапы регулярно для защиты данных.
                    </p>
                    
                    <div class="card">
                        <h3>Создать резервную копию</h3>
                        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
                            Создает полную резервную копию базы данных в сжатом формате. Бэкап будет сохранен в папке backups/.
                        </p>
                        <button onclick="createBackup()" style="background: #48bb78; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-weight: 600; font-size: 1rem;">
                            💾 Создать бэкап сейчас
                        </button>
                        <div id="backupStatus" style="margin-top: 15px; color: #666; font-size: 14px;"></div>
                    </div>
                    
                    <div class="card">
                        <h3>Управление бэкапами</h3>
                        <div style="margin: 15px 0;">
                            <button onclick="loadBackups()" style="background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">
                                🔄 Обновить список
                            </button>
                            <button onclick="cleanOldBackups()" style="background: #ed8936; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
                                🧹 Удалить старые бэкапы (старше 30 дней)
                            </button>
                        </div>
                        <div id="backupsList" style="margin-top: 20px;"></div>
                    </div>
                    
                    <div class="card" style="background: #fff5f5; border-left: 4px solid #fc8181;">
                        <h3 style="color: #c53030;">⚠️ Восстановление базы данных</h3>
                        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
                            Для восстановления базы данных из бэкапа используйте скрипт на сервере:
                        </p>
                        <code style="background: #f7fafc; padding: 10px; border-radius: 5px; display: block; margin: 10px 0; font-family: monospace;">
                            python restore_database.py
                        </code>
                        <p style="color: #666; font-size: 0.9rem; margin-top: 10px;">
                            Это безопаснее, чем восстановление через веб-интерфейс, так как создается резервная копия текущей БД перед восстановлением.
                        </p>
                    </div>
                </div>
                
                <!-- Секция: API-ключи -->
                <div id="section-api-keys" class="content-section">
                    <h2 class="section-header">🔑 API-ключи</h2>
                    <p style="color: #666; margin-bottom: 20px;">
                        Управление API-ключами для интеграции с внешними системами. API-ключи позволяют автоматизировать анализ документов через API. Доступны только для бизнес-тарифов (premium).
                    </p>
                    
                    <div class="card">
                        <h3>Все API-ключи</h3>
                        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
                            Полный список всех API-ключей всех пользователей с полной информацией.
                        </p>
                        <div style="margin: 15px 0;">
                            <button onclick="loadAllAPIKeys()" style="background: #667eea; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">🔄 Обновить список</button>
                            <button onclick="loadAPIKeys()" style="background: #ed8936; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer;">🔍 Поиск по пользователю</button>
                        </div>
                        <div id="allApiKeysList" style="margin-top: 20px;"></div>
                    </div>
                    
                    <div class="card">
                        <h3>Просмотр API-ключей конкретного пользователя</h3>
                        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
                            Введите ID пользователя для просмотра всех его API-ключей.
                        </p>
                        <div style="margin: 15px 0;">
                            <input type="text" id="apiKeyUserId" placeholder="ID пользователя" 
                                   style="width: 200px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <button onclick="loadAPIKeys()" style="background: #667eea; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer;">📥 Загрузить ключи</button>
                        </div>
                        <div id="apiKeyStatus" style="margin: 10px 0; color: #666; font-size: 14px;"></div>
                        <div id="apiKeysList" style="margin-top: 20px;"></div>
                    </div>
                    
                    <div class="card">
                        <h3>Создать новый API-ключ</h3>
                        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
                            Создайте новый API-ключ для пользователя. Ключ будет показан только один раз при создании.
                        </p>
                        <div style="margin: 15px 0;">
                            <input type="text" id="newApiKeyUserId" placeholder="ID пользователя" 
                                   style="width: 200px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <input type="text" id="newApiKeyName" placeholder="Название ключа (опционально)" 
                                   style="width: 250px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <button onclick="createAPIKey()" style="background: #48bb78; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer;">➕ Создать ключ</button>
                        </div>
                        <div id="newApiKeyResult" style="margin-top: 15px; padding: 15px; background: #edf2f7; border-radius: 5px; display: none;">
                            <p style="margin: 0 0 10px 0; font-weight: 600; color: #ed8936;">⚠️ ВАЖНО: Сохраните этот ключ! Он больше не будет показан:</p>
                            <code id="newApiKeyValue" style="display: block; padding: 10px; background: #2d3748; color: #48bb78; border-radius: 5px; font-family: monospace; word-break: break-all;"></code>
                        </div>
                    </div>
                </div>
                
                <!-- Секция: Настройки анализа -->
                <div id="section-analysis-settings-admin" class="content-section">
                    <h2 class="section-header">⚙️ Настройки анализа документов</h2>
                    <p style="color: #666; margin-bottom: 20px;">
                        Управление настройками анализа для бизнес-пользователей. Позволяет настраивать приоритеты областей экспертизы, уровень детализации и кастомные проверки.
                    </p>
                    
                    <div class="card">
                        <h3>Просмотр и редактирование настроек пользователя</h3>
                        <p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">
                            Введите ID пользователя для просмотра и редактирования его настроек анализа.
                        </p>
                        <div style="margin: 15px 0;">
                            <input type="text" id="adminAnalysisSettingsUserId" placeholder="ID пользователя" 
                                   style="width: 200px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <button onclick="loadAdminAnalysisSettings()" style="background: #667eea; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer;">📥 Загрузить настройки</button>
                        </div>
                        <div id="adminAnalysisSettingsStatus" style="margin: 10px 0; color: #666; font-size: 14px;"></div>
                        <div id="adminAnalysisSettingsContent" style="margin-top: 20px;"></div>
                    </div>
                </div>
                
                <!-- Секция: Статьи -->
                <div id="section-articles" class="content-section">
                    <h2 class="section-header">📝 Управление статьями</h2>
                    
                    <div class="card">
                        <h3>Создать новую статью</h3>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Заголовок статьи:</label>
                            <input type="text" id="articleTitle" placeholder="Например: Как проверить договор аренды" 
                                   style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">URL статьи (slug):</label>
                            <input type="text" id="articleSlug" placeholder="kak-proverit-dogovor-arendy" 
                                   style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; font-family: monospace;">
                            <p style="font-size: 12px; color: #666; margin-top: 5px;">Только латинские буквы, цифры, дефисы и подчеркивания</p>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Краткое описание:</label>
                            <textarea id="articleDescription" rows="3" placeholder="Краткое описание для карточки на странице /articles..."
                                      style="width: 100%; max-width: 800px; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px;"></textarea>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Иконка (эмодзи):</label>
                            <input type="text" id="articleIcon" placeholder="🏠" 
                                   style="width: 100px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; font-size: 1.5rem; text-align: center;">
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Категория (опционально):</label>
                            <input type="text" id="articleCategory" placeholder="Например: Договоры аренды" 
                                   style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Содержимое статьи:</label>
                            <div style="margin-bottom: 10px;">
                                <button type="button" onclick="toggleEditorMode()" id="editorModeBtn" style="background: #4299e1; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem; margin-right: 10px;"></> Переключить в HTML</button>
                                <button type="button" onclick="insertArticleTemplate()" style="background: #ed8936; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">📄 Вставить шаблон</button>
                                <span id="editorStatus" style="margin-left: 15px; color: #666; font-size: 0.9rem;">Режим: Визуальный редактор</span>
                            </div>
                            <!-- TinyMCE редактор -->
                            <div id="tinymce-container" style="width: 100%; max-width: 1200px;">
                                <textarea id="articleHtmlContent" rows="20" placeholder="Начните писать статью здесь..."></textarea>
                                <p id="tinymce-loading" style="font-size: 12px; color: #666; margin-top: 5px;">⏳ Загрузка визуального редактора...</p>
                            </div>
                            <!-- Fallback HTML редактор (скрыт по умолчанию) -->
                            <div id="html-editor-container" style="display: none;">
                                <textarea id="articleHtmlContentRaw" rows="20" placeholder="Введите HTML-код статьи..."
                                          style="width: 100%; max-width: 1200px; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px; font-family: monospace; font-size: 12px;"></textarea>
                                <p style="font-size: 12px; color: #666; margin-top: 5px;">💡 Совет: Используйте визуальный редактор для удобного форматирования</p>
                            </div>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">SEO мета-ключевые слова (опционально):</label>
                            <input type="text" id="articleMetaKeywords" placeholder="проверка договоров, анализ документов" 
                                   style="width: 100%; max-width: 800px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">SEO мета-описание (опционально):</label>
                            <textarea id="articleMetaDescription" rows="2" placeholder="Краткое описание для поисковых систем..."
                                      style="width: 100%; max-width: 800px; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px;"></textarea>
                        </div>
                        
                        <div style="margin: 20px 0;">
                            <button onclick="createArticle()" style="background: #48bb78; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">💾 Создать статью</button>
                            <button onclick="clearArticleForm()" style="background: #a0aec0; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">🗑️ Очистить форму</button>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Все статьи</h3>
                        <div style="margin-bottom: 20px;">
                            <select id="articleStatusFilter" onchange="loadArticles()" style="padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                                <option value="">Все статьи</option>
                                <option value="published">Опубликованные</option>
                                <option value="draft">Черновики</option>
                                <option value="archived">В архиве</option>
                            </select>
                            <button onclick="loadArticles()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">🔄 Обновить список</button>
                        </div>
                        <div id="articlesList"></div>
                    </div>
                </div>
                
                <!-- Секция: Новости -->
                <div id="section-news" class="content-section">
                    <h2 class="section-header">📰 Управление новостями</h2>
                    <p>Добавляйте и редактируйте новости для раздела "Обновления сайта" и "Новости"</p>
                    
                    <div class="card">
                        <div style="margin-bottom: 20px;">
                            <button onclick="showNewsForm()" style="background: #48bb78; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 1rem; margin-right: 10px;">➕ Добавить новость</button>
                            <select id="newsCategoryFilter" onchange="loadNews()" style="padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                                <option value="">Все новости</option>
                                <option value="updates">🔄 Обновления сайта</option>
                                <option value="news">📰 Новости</option>
                            </select>
                        </div>
                        
                        <!-- Форма добавления/редактирования новости -->
                        <div id="newsFormContainer" style="display: none; background: #f7fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h3 id="newsFormTitle">Добавить новость</h3>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Раздел:</label>
                                <select id="newsCategory" style="width: 100%; max-width: 400px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                                    <option value="updates">🔄 Обновления сайта</option>
                                    <option value="news">📰 Новости</option>
                                </select>
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Заголовок:</label>
                                <input type="text" id="newsTitle" placeholder="Введите заголовок новости" 
                                       style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Дата публикации:</label>
                                <input type="date" id="newsDate" 
                                       style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Описание:</label>
                                <textarea id="newsDescription" rows="5" placeholder="Введите описание новости" 
                                          style="width: 100%; max-width: 800px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;"></textarea>
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Ссылка (опционально):</label>
                                <input type="text" id="newsLink" placeholder="https://example.com" 
                                       style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Текст ссылки (опционально):</label>
                                <input type="text" id="newsLinkText" placeholder="Читать статью →" 
                                       style="width: 100%; max-width: 400px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <button onclick="saveNews()" id="saveNewsBtn" style="background: #4299e1; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">💾 Сохранить</button>
                                <button onclick="cancelNewsForm()" style="background: #e2e8f0; color: #2d3748; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Отмена</button>
                            </div>
                        </div>
                        
                        <div id="newsList"></div>
                    </div>
                </div>
                
                <!-- Секция: Полные новости -->
                <div id="section-full-news" class="content-section">
                    <h2 class="section-header">📄 Управление полными новостями</h2>
                    <p>Создавайте и редактируйте полные новостные статьи с HTML-контентом</p>
                    
                    <div class="card">
                        <div style="margin-bottom: 20px;">
                            <button onclick="showFullNewsForm()" style="background: #48bb78; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 1rem; margin-right: 10px;">➕ Создать полную новость</button>
                            <select id="fullNewsCategoryFilter" onchange="loadFullNews()" style="padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                                <option value="">Все категории</option>
                                <option value="Недвижимость">Недвижимость</option>
                                <option value="Финансы">Финансы</option>
                                <option value="Юридические новости">Юридические новости</option>
                                <option value="Технологии">Технологии</option>
                                <option value="Общие новости">Общие новости</option>
                            </select>
                        </div>
                        
                        <!-- Форма добавления/редактирования полной новости -->
                        <div id="fullNewsFormContainer" style="display: none; background: #f7fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h3 id="fullNewsFormTitle">Создать полную новость</h3>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Slug (URL):</label>
                                <input type="text" id="fullNewsSlug" placeholder="kak-poluchit-semejnuyu-ipoteku" 
                                       style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                                <small style="color: #666;">Только латинские буквы, цифры и дефисы. URL будет: /news/[slug]</small>
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Заголовок:</label>
                                <input type="text" id="fullNewsTitle" placeholder="Введите заголовок новости" 
                                       style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Краткое описание (для карточки):</label>
                                <textarea id="fullNewsShortDescription" rows="3" placeholder="Краткое описание, которое будет отображаться в карточке новости..." 
                                          style="width: 100%; max-width: 800px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;"></textarea>
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Полный HTML-контент:</label>
                                <div style="margin-bottom: 10px;">
                                    <button type="button" onclick="toggleFullNewsEditorMode()" id="fullNewsEditorModeBtn" style="background: #4299e1; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem; margin-right: 10px;"></> Переключить в HTML</button>
                                    <span id="fullNewsEditorStatus" style="margin-left: 15px; color: #666; font-size: 0.9rem;">Режим: Визуальный редактор</span>
                                </div>
                                <!-- TinyMCE редактор -->
                                <div id="fullNews-tinymce-container" style="width: 100%; max-width: 1200px;">
                                    <textarea id="fullNewsContent" rows="20" placeholder="Начните писать новость здесь..."></textarea>
                                    <p id="fullNews-tinymce-loading" style="font-size: 12px; color: #666; margin-top: 5px;">⏳ Загрузка визуального редактора...</p>
                                </div>
                                <!-- Fallback HTML редактор (скрыт по умолчанию) -->
                                <div id="fullNews-html-editor-container" style="display: none;">
                                    <textarea id="fullNewsContentRaw" rows="20" placeholder="Введите HTML-код новости..."
                                              style="width: 100%; max-width: 1200px; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px; font-family: monospace; font-size: 12px;"></textarea>
                                    <p style="font-size: 12px; color: #666; margin-top: 5px;">💡 Совет: Используйте визуальный редактор для удобного форматирования</p>
                                </div>
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Категория:</label>
                                <select id="fullNewsCategory" style="width: 100%; max-width: 400px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                                    <option value="">Без категории</option>
                                    <option value="Недвижимость">Недвижимость</option>
                                    <option value="Финансы">Финансы</option>
                                    <option value="Юридические новости">Юридические новости</option>
                                    <option value="Технологии">Технологии</option>
                                    <option value="Общие новости">Общие новости</option>
                                </select>
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">URL изображения обложки:</label>
                                <input type="text" id="fullNewsImageUrl" placeholder="https://example.com/image.jpg" 
                                       style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Автор:</label>
                                <input type="text" id="fullNewsAuthor" placeholder="Редакция DocScan" 
                                       style="width: 100%; max-width: 400px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Meta Title (для SEO, опционально):</label>
                                <input type="text" id="fullNewsMetaTitle" placeholder="Если не указан, будет использован заголовок" 
                                       style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Meta Description (для SEO, опционально):</label>
                                <textarea id="fullNewsMetaDescription" rows="2" placeholder="Краткое описание для поисковых систем..." 
                                          style="width: 100%; max-width: 800px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;"></textarea>
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Meta Keywords (для SEO, опционально):</label>
                                <input type="text" id="fullNewsMetaKeywords" placeholder="ключевое слово 1, ключевое слово 2" 
                                       style="width: 100%; max-width: 600px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Дата публикации:</label>
                                <input type="date" id="fullNewsPublishedAt" 
                                       style="width: 100%; max-width: 300px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;">
                            </div>
                            <div style="margin: 15px 0;">
                                <label style="display: flex; align-items: center; gap: 10px;">
                                    <input type="checkbox" id="fullNewsIsPublished" checked style="width: 20px; height: 20px;">
                                    <span>Опубликовано (если снять галочку, новость будет в черновиках)</span>
                                </label>
                            </div>
                            <div style="margin: 15px 0;">
                                <button onclick="saveFullNews()" id="saveFullNewsBtn" style="background: #4299e1; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">💾 Сохранить</button>
                                <button onclick="cancelFullNewsForm()" style="background: #e2e8f0; color: #2d3748; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Отмена</button>
                            </div>
                        </div>
                        
                        <div id="fullNewsList"></div>
                    </div>
                </div>
                
                <!-- Секция: Вопросы и ответы -->
                <div id="section-questions" class="content-section">
                    <h2 class="section-header">❓ Управление вопросами и ответами</h2>
                    <p>Модерация вопросов и ответов пользователей</p>
                    
                    <div class="card">
                        <div style="margin-bottom: 20px;">
                            <select id="questionFilter" onchange="loadQuestions()" style="padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                                <option value="">Все вопросы</option>
                                <option value="open">Открытые</option>
                                <option value="answered">С ответами</option>
                                <option value="solved">Решенные</option>
                                <option value="closed">Закрытые</option>
                            </select>
                            <button onclick="loadQuestions()" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">🔄 Обновить</button>
                        </div>
                        <div id="questionsList"></div>
                    </div>
                </div>
                
                <!-- Секция: Уведомления -->
                <div id="section-notifications" class="content-section">
                    <h2 class="section-header">🔔 Отправка уведомлений пользователям</h2>
                    <p>Отправьте уведомление конкретному пользователю в личный кабинет</p>
                    
                    <div class="card">
                        <h3 style="margin-bottom: 20px; color: #2d3748;">Создать уведомление</h3>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #2d3748;">Пользователь (User ID или Email):</label>
                            <input type="text" id="notificationUserId" placeholder="Введите User ID или Email" style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px; font-size: 0.9rem;">
                            <small style="color: #666; font-size: 0.85rem;">Можно указать User ID (например: abc12345) или Email пользователя</small>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #2d3748;">Тип уведомления:</label>
                            <select id="notificationType" style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px; font-size: 0.9rem;">
                                <option value="admin">Административное</option>
                                <option value="info">Информационное</option>
                                <option value="warning">Предупреждение</option>
                                <option value="success">Успех</option>
                            </select>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #2d3748;">Заголовок уведомления:</label>
                            <input type="text" id="notificationTitle" placeholder="Например: Важное обновление" style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px; font-size: 0.9rem;">
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #2d3748;">Сообщение:</label>
                            <textarea id="notificationMessage" rows="4" placeholder="Текст уведомления..." style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px; font-size: 0.9rem; resize: vertical;"></textarea>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #2d3748;">Ссылка (опционально):</label>
                            <input type="text" id="notificationLink" placeholder="/cabinet или /questions/123" style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px; font-size: 0.9rem;">
                            <small style="color: #666; font-size: 0.85rem;">При клике на уведомление пользователь перейдет по этой ссылке</small>
                        </div>
                        
                        <button onclick="sendAdminNotification()" style="background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 1rem; font-weight: 600;">
                            📤 Отправить уведомление
                        </button>
                        
                        <div id="notificationMessageDiv" style="margin-top: 15px;"></div>
                    </div>
                    
                    <div class="card" style="margin-top: 20px;">
                        <h3 style="margin-bottom: 20px; color: #2d3748;">Последние отправленные уведомления</h3>
                        <div id="notificationsHistory" style="min-height: 100px;">
                            <p style="color: #999; padding: 20px; text-align: center;">Загрузка истории уведомлений...</p>
                        </div>
                    </div>
                </div>
                
                <!-- Секция: Партнерская программа -->
                <div id="section-partners" class="content-section">
                    <div class="card">
                        <h2 class="section-header">🎁 Партнеры</h2>
                        <p>Пользователи, которые сгенерировали реферальные ссылки</p>
                        <button onclick="loadPartners()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px;">🔄 Обновить</button>
                        <div id="partnersList"></div>
                    </div>
                    
                    <div class="card">
                        <h2 class="section-header">📋 Приглашения</h2>
                        <p>Список всех приглашений пользователей</p>
                        <button onclick="loadReferrals()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px;">🔄 Обновить</button>
                        <div id="referralsList"></div>
                    </div>
                    
                    <div class="card">
                        <h2 class="section-header">💰 Вознаграждения к выплате</h2>
                        <p>Список вознаграждений, ожидающих выплаты</p>
                        <button onclick="loadRewards()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px;">🔄 Обновить</button>
                        <div id="rewardsList"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- TinyMCE CSS/JS -->
        <script src="https://cdn.jsdelivr.net/npm/tinymce@6/tinymce.min.js"></script>
        <!-- Admin Panel JavaScript -->
        <script src="/static/js/admin.js"></script>
        <!-- Original inline script removed and moved to admin.js -->
        <!--
        <script>
            // Функция переключения между секциями
            function showSection(sectionName) {
                try {
                    console.log('🔄 Переключение на секцию:', sectionName);
                    
                    // Закрываем меню на мобильных после выбора
                    if (window.innerWidth <= 768) {
                        const sidebar = document.getElementById('sidebar');
                        const overlay = document.getElementById('sidebarOverlay');
                        if (sidebar) {
                            sidebar.classList.remove('open');
                        }
                        if (overlay) {
                            overlay.classList.remove('active');
                        }
                    }
                    
                    // Скрываем все секции
                    const sections = document.querySelectorAll('.content-section');
                    console.log('📦 Найдено секций:', sections.length);
                    sections.forEach(section => {
                        section.classList.remove('active');
                    });
                    
                    // Показываем выбранную секцию
                    const targetSection = document.getElementById('section-' + sectionName);
                    if (!targetSection) {
                        console.error('❌ Секция не найдена: section-' + sectionName);
                        alert('Секция не найдена: ' + sectionName);
                        return;
                    }
                    targetSection.classList.add('active');
                    console.log('✅ Секция показана: section-' + sectionName);
                    
                    // Обновляем активный пункт меню
                    document.querySelectorAll('.menu-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    const menuItem = document.querySelector(`[data-section="${sectionName}"]`);
                    if (menuItem) {
                        menuItem.classList.add('active');
                        console.log('✅ Меню обновлено');
                    } else {
                        console.warn('⚠️ Пункт меню не найден:', sectionName);
                    }
                    
                    // Обновляем заголовок страницы
                    const titles = {
                        'dashboard': '📊 Главная',
                        'users': '👥 Пользователи',
                        'guests': '👤 Гости',
                        'search-bots': '🕷️ Поисковые боты',
                        'campaigns': '📧 Email-рассылки',
                        'backups': '💾 Резервные копии',
                        'articles': '📝 Статьи',
                        'news': '📰 Новости',
                        'full-news': '📄 Полные новости',
                        'questions': '❓ Вопросы и ответы',
                        'notifications': '🔔 Уведомления',
                        'partners': '🎁 Партнерская программа'
                    };
                    const pageTitle = document.getElementById('pageTitle');
                    if (pageTitle) {
                        pageTitle.textContent = titles[sectionName] || 'Админ-панель';
                    }
                    
                    // Загружаем данные секции при первом открытии
                    // Используем отложенную загрузку для всех функций, так как они могут быть определены в другом script блоке
                    function tryLoadFunction(funcName, delay) {
                        delay = delay || 0;
                        setTimeout(function() {
                            if (typeof window[funcName] === 'function') {
                                try {
                                    window[funcName]();
                                } catch(e) {
                                    console.error('❌ Ошибка при вызове ' + funcName + ':', e);
                                }
                            } else {
                                // Пробуем еще раз через небольшую задержку
                                if (delay < 500) {
                                    tryLoadFunction(funcName, delay + 100);
                                } else {
                                    console.error('❌ Функция ' + funcName + ' не найдена после всех попыток');
                                }
                            }
                        }, delay);
                    }
                    
                    if (sectionName === 'users') {
                        const usersList = document.getElementById('usersList');
                        if (usersList && usersList.innerHTML === '') {
                            console.log('📥 Загрузка пользователей...');
                            tryLoadFunction('loadUsers', 0);
                            tryLoadFunction('loadUsers', 100);
                            tryLoadFunction('loadUsers', 300);
                        }
                    } else if (sectionName === 'guests') {
                        const guestsList = document.getElementById('guestsList');
                        if (guestsList && guestsList.innerHTML === '') {
                            console.log('📥 Загрузка гостей...');
                            tryLoadFunction('loadGuests', 0);
                            tryLoadFunction('loadGuests', 100);
                            tryLoadFunction('loadGuests', 300);
                        }
                    } else if (sectionName === 'search-bots') {
                        const botsList = document.getElementById('botsList');
                        if (botsList && botsList.innerHTML === '') {
                            console.log('📥 Загрузка ботов...');
                            tryLoadFunction('loadBots', 0);
                            tryLoadFunction('loadBots', 100);
                            tryLoadFunction('loadBots', 300);
                        }
                        // Обновляем статистику ботов
                        tryLoadFunction('loadStats', 0);
                        tryLoadFunction('loadStats', 100);
                    } else if (sectionName === 'news') {
                        const newsList = document.getElementById('newsList');
                        if (newsList && newsList.innerHTML === '') {
                            console.log('📥 Загрузка новостей...');
                            tryLoadFunction('loadNews', 0);
                            tryLoadFunction('loadNews', 100);
                            tryLoadFunction('loadNews', 300);
                        }
                    } else if (sectionName === 'full-news') {
                        const fullNewsList = document.getElementById('fullNewsList');
                        if (fullNewsList && fullNewsList.innerHTML === '') {
                            console.log('📥 Загрузка полных новостей...');
                            tryLoadFunction('loadFullNews', 0);
                            tryLoadFunction('loadFullNews', 100);
                            tryLoadFunction('loadFullNews', 300);
                        }
                        // Инициализируем TinyMCE при открытии секции полных новостей
                        tryLoadFunction('initFullNewsEditorOnShow', 500);
                    } else if (sectionName === 'backups') {
                        const backupsList = document.getElementById('backupsList');
                        if (backupsList && backupsList.innerHTML === '') {
                            console.log('📥 Загрузка бэкапов...');
                            tryLoadFunction('loadBackups', 0);
                            tryLoadFunction('loadBackups', 100);
                            tryLoadFunction('loadBackups', 300);
                        }
                    } else if (sectionName === 'questions') {
                        const questionsList = document.getElementById('questionsList');
                        if (questionsList && questionsList.innerHTML === '') {
                            console.log('📥 Загрузка вопросов...');
                            tryLoadFunction('loadQuestions', 0);
                            tryLoadFunction('loadQuestions', 100);
                            tryLoadFunction('loadQuestions', 300);
                        }
                    } else if (sectionName === 'campaigns') {
                        const campaignsList = document.getElementById('emailCampaignsList');
                        if (campaignsList && campaignsList.innerHTML === '') {
                            console.log('📥 Загрузка рассылок...');
                            tryLoadFunction('loadEmailCampaigns', 0);
                            tryLoadFunction('loadEmailCampaigns', 100);
                            tryLoadFunction('loadEmailCampaigns', 300);
                        }
                    } else if (sectionName === 'articles') {
                        const articlesList = document.getElementById('articlesList');
                        if (articlesList && articlesList.innerHTML === '') {
                            console.log('📥 Загрузка статей...');
                            tryLoadFunction('loadArticles', 0);
                            tryLoadFunction('loadArticles', 100);
                            tryLoadFunction('loadArticles', 300);
                        }
                    } else if (sectionName === 'notifications') {
                        const notificationsHistory = document.getElementById('notificationsHistory');
                        if (notificationsHistory) {
                            console.log('📥 Загрузка истории уведомлений...');
                            tryLoadFunction('loadNotificationsHistory', 0);
                            tryLoadFunction('loadNotificationsHistory', 100);
                            tryLoadFunction('loadNotificationsHistory', 300);
                        }
                    } else if (sectionName === 'partners') {
                        tryLoadFunction('loadPartners', 0);
                        tryLoadFunction('loadPartners', 100);
                        tryLoadFunction('loadPartners', 300);
                        tryLoadFunction('loadReferrals', 0);
                        tryLoadFunction('loadReferrals', 100);
                        tryLoadFunction('loadReferrals', 300);
                        tryLoadFunction('loadRewards', 0);
                        tryLoadFunction('loadRewards', 100);
                        tryLoadFunction('loadRewards', 300);
                    }
                    
                    console.log('✅ Переключение завершено успешно');
                } catch (error) {
                    console.error('❌ Ошибка при переключении секции:', error);
                    alert('Ошибка переключения: ' + error.message);
                }
            }
            
            // Проверяем доступность функции showSection
            console.log('✅ Функция showSection определена:', typeof showSection);
            
            // Регистрируем функцию глобально для доступа из onclick
            window.showSection = showSection;
            console.log('✅ showSection зарегистрирована глобально:', typeof window.showSection);
            
            function logout() {
                try {
                    document.cookie = "admin_auth=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                window.location.href = "/admin/login";
                } catch (error) {
                    console.error('Ошибка выхода:', error);
                    alert('Ошибка выхода: ' + error.message);
                }
            }
            
            // Функция для открытия/закрытия меню на мобильных
            function toggleMobileMenu() {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebarOverlay');
                if (sidebar && overlay) {
                    sidebar.classList.toggle('open');
                    overlay.classList.toggle('active');
                }
            }
            
            // Закрываем меню при клике вне его на мобильных
            document.addEventListener('click', function(event) {
                const sidebar = document.getElementById('sidebar');
                const menuToggle = document.getElementById('menuToggle');
                const overlay = document.getElementById('sidebarOverlay');
                
                if (window.innerWidth <= 768 && sidebar && menuToggle && overlay) {
                    // Если клик не по меню и не по кнопке, закрываем меню
                    if (!sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
                        sidebar.classList.remove('open');
                        overlay.classList.remove('active');
                    }
                }
            });
            
            // Регистрируем ВСЕ функции глобально для доступа из onclick
            window.showSection = showSection;
            window.logout = logout;
            window.toggleMobileMenu = toggleMobileMenu;
            
            // Регистрируем функции после их определения (будет сделано позже)
            function registerGlobalFunctions() {
                if (typeof loadStats === 'function') window.loadStats = loadStats;
                if (typeof loadUsers === 'function') window.loadUsers = loadUsers;
                if (typeof loadGuests === 'function') window.loadGuests = loadGuests;
                if (typeof loadArticles === 'function') window.loadArticles = loadArticles;
                if (typeof showCalculatorStats === 'function') window.showCalculatorStats = showCalculatorStats;
                if (typeof setUserPlan === 'function') window.setUserPlan = setUserPlan;
                if (typeof createUser === 'function') window.createUser = createUser;
                if (typeof searchUsers === 'function') window.searchUsers = searchUsers;
                if (typeof clearSearch === 'function') window.clearSearch = clearSearch;
                if (typeof searchGuests === 'function') window.searchGuests = searchGuests;
                if (typeof clearGuestSearch === 'function') window.clearGuestSearch = clearGuestSearch;
                if (typeof createCampaign === 'function') window.createCampaign = createCampaign;
                if (typeof loadEmailCampaigns === 'function') window.loadEmailCampaigns = loadEmailCampaigns;
                if (typeof createArticle === 'function') window.createArticle = createArticle;
                if (typeof clearArticleForm === 'function') window.clearArticleForm = clearArticleForm;
                console.log('✅ Все функции зарегистрированы глобально');
            }
            
            console.log('✅ Основные функции зарегистрированы глобально');
            
            // Инициализация при загрузке страницы
            function initAdminPanel() {
                console.log('🚀 Инициализация админ-панели...');
                try {
                    // Загружаем статистику
                    if (typeof loadStats === 'function') {
                        loadStats();
                        console.log('✅ Статистика загружена');
                    }
                    
                    // Убеждаемся, что главная секция видна
                    const dashboardSection = document.getElementById('section-dashboard');
                    if (dashboardSection) {
                        dashboardSection.classList.add('active');
                        console.log('✅ Dashboard секция активирована');
                    }
                    
                    // Проверяем доступность элементов меню
                    const menuItems = document.querySelectorAll('.menu-item');
                    console.log('📦 Найдено пунктов меню:', menuItems.length);
                    menuItems.forEach((item, index) => {
                        console.log(`  ${index + 1}. ${item.textContent.trim()}`);
                    });
                    
                    console.log('✅ Админ-панель инициализирована');
                } catch (error) {
                    console.error('❌ Ошибка инициализации:', error);
                    alert('Ошибка инициализации: ' + error.message);
                }
            }
            
            // Привязываем обработчики событий к пунктам меню
            function attachMenuHandlers() {
                console.log('🔗 Привязка обработчиков меню...');
                const menuItems = document.querySelectorAll('.menu-item');
                console.log('📦 Найдено пунктов меню:', menuItems.length);
                
                menuItems.forEach((item, index) => {
                    const sectionName = item.getAttribute('data-section');
                    console.log(`  Обработка пункта ${index + 1}: ${sectionName}`);
                    
                    if (sectionName) {
                        // Удаляем все старые обработчики
                        item.onclick = null;
                        item.removeEventListener('click', function(){});
                        
                        // Добавляем новый обработчик
                        item.addEventListener('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            console.log('🖱️ Клик по меню:', sectionName);
                            
                            try {
                                if (typeof window.showSection === 'function') {
                                    window.showSection(sectionName);
                                } else if (typeof showSection === 'function') {
                                    showSection(sectionName);
                                } else {
                                    console.error('❌ showSection не определена!');
                                    alert('Ошибка: функция showSection не найдена. Проверьте консоль.');
                                }
                            } catch (error) {
                                console.error('❌ Ошибка при клике:', error);
                                alert('Ошибка: ' + error.message);
                            }
                            
                            return false;
                        });
                        
                        // Также добавляем onclick для совместимости
                        item.onclick = function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            if (typeof window.showSection === 'function') {
                                window.showSection(sectionName);
                            }
                            return false;
                        };
                        
                        console.log(`✅ Обработчик привязан для: ${sectionName}`);
                    } else {
                        console.warn(`⚠️ Нет data-section для пункта ${index + 1}`);
                    }
                });
                console.log('✅ Все обработчики меню привязаны');
            }
            
            // Инициализируем при загрузке DOM
            function initAll() {
                console.log('🚀 Полная инициализация...');
                attachMenuHandlers();
                initAdminPanel();
            }
            
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(initAll, 100);
                });
            } else {
                setTimeout(initAll, 100);
            }
            
            // Проверяем загрузку TinyMCE
            let tinyMCELoaded = false;
            
            function checkTinyMCELoad() {
                if (typeof tinymce !== 'undefined') {
                    tinyMCELoaded = true;
                    console.log('✅ TinyMCE загружен успешно');
                } else {
                    console.warn('⏳ Ожидание загрузки TinyMCE...');
                    setTimeout(checkTinyMCELoad, 500);
                }
            }
            
            window.addEventListener('load', function() {
                checkTinyMCELoad();
            });
            
            // Альтернативная загрузка если основной CDN не работает
            setTimeout(function() {
                if (!tinyMCELoaded && typeof tinymce === 'undefined') {
                    console.warn('⚠️ Основной CDN не загрузился, пробую альтернативный...');
                    const script = document.createElement('script');
                    script.src = 'https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js';
                    script.referrerPolicy = 'origin';
                    script.onload = function() {
                        console.log('✅ TinyMCE загружен с альтернативного CDN');
                        tinyMCELoaded = true;
                    };
                    script.onerror = function() {
                        console.error('❌ Не удалось загрузить TinyMCE с обоих CDN');
                        const loadingEl = document.getElementById('tinymce-loading');
                        if (loadingEl) {
                            loadingEl.textContent = '❌ Визуальный редактор недоступен. Используйте HTML-режим.';
                            loadingEl.style.color = '#f56565';
                        }
                    };
                    document.head.appendChild(script);
                }
            }, 3000);
        </script>
        -->
        
        <!-- Second script block removed and moved to admin.js -->
        <!--
        <script>
            // НЕМЕДЛЕННАЯ РЕГИСТРАЦИЯ ВСЕХ ФУНКЦИЙ В WINDOW ПРИ ОПРЕДЕЛЕНИИ
            // Это гарантирует, что функции будут доступны глобально сразу после определения
            
            // Функция для автоматической регистрации функций в window
            function registerFunction(funcName, func) {
                if (typeof func === 'function') {
                    window[funcName] = func;
                    console.log('✅ ' + funcName + ' зарегистрирована глобально');
                }
            }
            
            // Загружаем статистику и пользователей
            function loadStats() {
                fetch('/admin/stats', {credentials: 'include'})
                    .then(r => r.json())
                    .then(stats => {
                        document.getElementById('totalUsers').textContent = stats.total_users;
                        document.getElementById('newUsers24h').textContent = stats.new_users_24h || 0;
                        document.getElementById('newGuests24h').textContent = stats.new_guests_24h || 0;
                        document.getElementById('totalGuests').textContent = stats.total_guests || 0;
                        document.getElementById('newBots24h').textContent = stats.new_bots_24h || 0;
                        document.getElementById('totalBots').textContent = stats.total_bots || 0;
                        // Обновляем статистику в секции ботов, если она открыта
                        if (document.getElementById('newBots24hDetail')) {
                            document.getElementById('newBots24hDetail').textContent = stats.new_bots_24h || 0;
                            document.getElementById('totalBotsDetail').textContent = stats.total_bots || 0;
                            document.getElementById('todayBotVisits').textContent = stats.today_visits || 0;
                            document.getElementById('uniqueBotTypes').textContent = stats.unique_bot_types || 0;
                        }
                        document.getElementById('totalAnalyses').textContent = stats.total_analyses;
                        document.getElementById('todayAnalyses').textContent = stats.today_analyses;
                        document.getElementById('todayRevenue').textContent = (stats.today_revenue || 0).toFixed(2) + ' ₽';
                        document.getElementById('totalRevenue').textContent = (stats.total_revenue || 0).toFixed(2) + ' ₽';
                        document.getElementById('todayPayments').textContent = stats.today_payments || 0;
                    });
            }
            // Регистрируем loadStats глобально сразу после определения
            if (typeof loadStats === 'function') {
                window.loadStats = loadStats;
                console.log('✅ loadStats зарегистрирована глобально');
            }
            
            function loadNewUsers() {
                fetch('/admin/new-users', {credentials: 'include'})
                    .then(r => r.json())
                    .then(users => {
                        let html = '';
                        if (!users || users.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет новых пользователей за последние 24 часа</p>';
                        } else {
                            html = '<div style="overflow-x: auto; -webkit-overflow-scrolling: touch; margin-top: 15px;"><table style="min-width: 700px; width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">ID</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Email</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата регистрации</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Тариф</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Сделал анализ</th></tr></thead><tbody>';
                            users.forEach(user => {
                                const createdDate = user.created_at ? (function() {
                                    try {
                                        return new Date(user.created_at).toLocaleString('ru-RU');
                                    } catch(e) {
                                        return user.created_at;
                                    }
                                })() : 'Неизвестно';
                                const planLimit = getPlanLimit(user.plan || 'free');
                                const hasAnalysis = user.has_analysis ? `1/${planLimit}` : `0/${planLimit}`;
                                html += `<tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 10px;">${user.user_id}</td><td style="padding: 10px;">${user.email || 'Не указан'}</td><td style="padding: 10px;">${createdDate}</td><td style="padding: 10px;">${getPlanName(user.plan || 'free')}</td><td style="padding: 10px;">${hasAnalysis}</td></tr>`;
                            });
                            html += '</tbody></table></div>';
                        }
                        const el = document.getElementById('newUsersList');
                        if (el) el.innerHTML = html;
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки новых пользователей:', err);
                        const el = document.getElementById('newUsersList');
                        if (el) el.innerHTML = '<p style="color: #f56565; padding: 20px;">Ошибка загрузки данных</p>';
                    });
            }
            
            function loadPayments() {
                const days = document.getElementById('paymentsFilter') ? document.getElementById('paymentsFilter').value : '';
                let url = '/admin/payments';
                if (days) {
                    url += '?days=' + days;
                }
                
                fetch(url, {credentials: 'include'})
                    .then(r => r.json())
                    .then(payments => {
                        let html = '';
                        if (!payments || payments.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет платежей</p>';
                        } else {
                            html = '<div style="overflow-x: auto; -webkit-overflow-scrolling: touch; margin-top: 15px;"><table style="min-width: 700px; width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Email</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Тариф</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Сумма</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Статус</th></tr></thead><tbody>';
                            payments.forEach(payment => {
                                const date = payment.created_at ? (function() {
                                    try {
                                        return new Date(payment.created_at).toLocaleString('ru-RU');
                                    } catch(e) {
                                        return payment.created_at;
                                    }
                                })() : 'Неизвестно';
                                const amount = payment.amount ? payment.amount.toFixed(2) : '0.00';
                                html += `<tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 10px;">${date}</td><td style="padding: 10px;">${payment.email || 'Не указан'}</td><td style="padding: 10px;">${getPlanName(payment.plan_type || 'basic')}</td><td style="padding: 10px; font-weight: bold; color: #48bb78;">${amount} ${payment.currency || 'RUB'}</td><td style="padding: 10px;"><span style="color: #48bb78;">✅ ${payment.status || 'success'}</span></td></tr>`;
                            });
                            html += '</tbody></table></div>';
                        }
                        const el = document.getElementById('paymentsList');
                        if (el) el.innerHTML = html;
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки платежей:', err);
                        const el = document.getElementById('paymentsList');
                        if (el) el.innerHTML = '<p style="color: #f56565; padding: 20px;">Ошибка загрузки данных</p>';
                    });
            }
            
            function loadGuests() {
                fetch('/admin/guests', {credentials: 'include'})
                    .then(r => r.json())
                    .then(guests => {
                        let html = '';
                        if (!guests || guests.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет незарегистрированных гостей</p>';
                        } else {
                            guests.forEach(guest => {
                                const registeredLink = guest.registered_user_id 
                                    ? `<a href="#" onclick="showUser('${guest.registered_user_id}'); return false;" style="color: #667eea; text-decoration: underline;">Перейти к пользователю ${guest.registered_user_id}</a>`
                                    : '<span style="color: #999;">Не зарегистрирован</span>';
                                
                                html += `
                                    <div class="user-card guest-card">
                                        <strong>IP:</strong> ${guest.ip_address}<br>
                                        <strong>Браузер:</strong> ${guest.user_agent ? (guest.user_agent.substring(0, 50) + (guest.user_agent.length > 50 ? '...' : '')) : 'Не определен'}<br>
                                        <strong>Анализов сделано:</strong> ${guest.analyses_count}<br>
                                        <strong>Первый визит:</strong> ${new Date(guest.first_seen).toLocaleString('ru-RU')}<br>
                                        <strong>Последний визит:</strong> ${new Date(guest.last_seen).toLocaleString('ru-RU')}<br>
                                        <strong>Предложение регистрации:</strong> ${guest.registration_prompted ? '✅ Да' : '❌ Нет'}<br>
                                        <strong>Статус:</strong> ${registeredLink}
                                    </div>
                                `;
                            });
                        }
                        document.getElementById('guestsList').innerHTML = html;
                    });
            }
            // Регистрируем loadGuests глобально сразу после определения
            if (typeof loadGuests === 'function') {
                window.loadGuests = loadGuests;
                console.log('✅ loadGuests зарегистрирована глобально');
            }
            
            function searchGuests() {
                const searchTerm = document.getElementById('searchGuest').value.toLowerCase().trim();
                const guestCards = document.querySelectorAll('.guest-card');
                let foundCount = 0;
                
                guestCards.forEach(card => {
                    const cardText = card.textContent.toLowerCase();
                    if (searchTerm === '' || cardText.includes(searchTerm)) {
                        card.style.display = 'block';
                        foundCount++;
                    } else {
                        card.style.display = 'none';
                    }
                });
                
                const statusEl = document.getElementById('guestSearchStatus');
                if (searchTerm) {
                    statusEl.textContent = `Найдено: ${foundCount}`;
                    statusEl.style.color = '#2d3748';
                    statusEl.style.fontWeight = 'bold';
                } else {
                    statusEl.textContent = '';
                }
            }
            
            function clearGuestSearch() {
                // Регистрируем глобально при первом вызове
                if (!window.clearGuestSearch) window.clearGuestSearch = clearGuestSearch;
                
                document.getElementById('searchGuest').value = '';
                searchGuests();
            }
            
            // Регистрируем функции поиска гостей глобально
            window.searchGuests = searchGuests;
            window.clearGuestSearch = clearGuestSearch;
            
            // ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ПОИСКОВЫМИ БОТАМИ ==========
            function loadBots() {
                fetch('/admin/search-bots', {credentials: 'include'})
                    .then(r => r.json())
                    .then(bots => {
                        let html = '';
                        if (!bots || bots.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет записей о поисковых ботах</p>';
                        } else {
                            bots.forEach(bot => {
                                html += `
                                    <div class="user-card bot-card">
                                        <strong>IP:</strong> ${bot.ip_address}<br>
                                        <strong>Тип бота:</strong> ${bot.bot_type}<br>
                                        <strong>User-Agent:</strong> ${bot.user_agent ? (bot.user_agent.substring(0, 80) + (bot.user_agent.length > 80 ? '...' : '')) : 'Не определен'}<br>
                                        <strong>Первый визит:</strong> ${new Date(bot.first_seen).toLocaleString('ru-RU')}<br>
                                        <strong>Последний визит:</strong> ${new Date(bot.last_seen).toLocaleString('ru-RU')}<br>
                                        <strong>Количество визитов:</strong> ${bot.visits_count}
                                    </div>
                                `;
                            });
                        }
                        document.getElementById('botsList').innerHTML = html;
                    });
            }
            // Регистрируем loadBots глобально сразу после определения
            if (typeof loadBots === 'function') {
                window.loadBots = loadBots;
                console.log('✅ loadBots зарегистрирована глобально');
            }
            
            function searchBots() {
                const searchTerm = document.getElementById('searchBot').value.toLowerCase().trim();
                const botCards = document.querySelectorAll('.bot-card');
                let foundCount = 0;
                
                botCards.forEach(card => {
                    const cardText = card.textContent.toLowerCase();
                    if (searchTerm === '' || cardText.includes(searchTerm)) {
                        card.style.display = 'block';
                        foundCount++;
                    } else {
                        card.style.display = 'none';
                    }
                });
                
                const statusEl = document.getElementById('botSearchStatus');
                if (searchTerm) {
                    statusEl.textContent = `Найдено: ${foundCount}`;
                    statusEl.style.color = '#2d3748';
                    statusEl.style.fontWeight = 'bold';
                } else {
                    statusEl.textContent = '';
                }
            }
            
            function clearBotSearch() {
                document.getElementById('searchBot').value = '';
                if (!window.clearBotSearch) window.clearBotSearch = clearBotSearch;
                searchBots();
            }
            
            // Регистрируем функции для ботов глобально
            window.loadBots = loadBots;
            window.searchBots = searchBots;
            window.clearBotSearch = clearBotSearch;
            
            // ========== ФУНКЦИИ ДЛЯ РАБОТЫ С НОВОСТЯМИ ==========
            let editingNewsId = null;
            
            function loadNews() {
                const categoryFilter = document.getElementById('newsCategoryFilter') ? document.getElementById('newsCategoryFilter').value : '';
                let url = '/admin/news';
                if (categoryFilter) {
                    url += '?category=' + categoryFilter;
                }
                
                fetch(url, {credentials: 'include'})
                    .then(r => r.json())
                    .then(news => {
                        const newsListEl = document.getElementById('newsList');
                        if (!newsListEl) return;
                        
                        let html = '';
                        if (!news || news.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет новостей</p>';
                        } else {
                            // Группируем по категориям
                            const updates = news.filter(n => n.category === 'updates');
                            const newsItems = news.filter(n => n.category === 'news');
                            
                            if (categoryFilter === '' || categoryFilter === 'updates') {
                                if (updates.length > 0) {
                                    html += '<h3 style="margin-top: 20px; color: #667eea;">🔄 Обновления сайта</h3>';
                                    updates.forEach(item => {
                                        html += createNewsCard(item);
                                    });
                                }
                            }
                            
                            if (categoryFilter === '' || categoryFilter === 'news') {
                                if (newsItems.length > 0) {
                                    html += '<h3 style="margin-top: 30px; color: #667eea;">📰 Новости</h3>';
                                    newsItems.forEach(item => {
                                        html += createNewsCard(item);
                                    });
                                }
                            }
                        }
                        newsListEl.innerHTML = html;
                    });
            }
            
            function createNewsCard(item) {
                const categoryName = item.category === 'updates' ? '🔄 Обновления сайта' : '📰 Новости';
                const linkHtml = item.link ? `<a href="${item.link}" target="_blank" style="color: #667eea; text-decoration: underline;">${item.link_text || 'Читать →'}</a>` : '';
                
                return `
                    <div class="user-card" style="margin: 10px 0; border-left: 4px solid ${item.category === 'updates' ? '#48bb78' : '#ed8936'};">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 5px;">${categoryName}</div>
                                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 5px;">${item.title}</div>
                                <div style="color: #666; font-size: 0.9rem; margin-bottom: 10px;">📅 ${formatNewsDate(item.date)}</div>
                                <div style="color: #2d3748; margin-bottom: 10px;">${item.description}</div>
                                ${linkHtml ? `<div style="margin-top: 10px;">${linkHtml}</div>` : ''}
                            </div>
                            <div style="display: flex; gap: 5px;">
                                <button onclick="editNews(${item.id})" style="background: #4299e1; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">✏️ Редактировать</button>
                                <button onclick="deleteNews(${item.id})" style="background: #f56565; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">🗑️ Удалить</button>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            function formatNewsDate(dateStr) {
                if (!dateStr) return '';
                try {
                    const date = new Date(dateStr);
                    return date.toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' });
                } catch {
                    return dateStr;
                }
            }
            
            function showNewsForm() {
                editingNewsId = null;
                document.getElementById('newsFormTitle').textContent = 'Добавить новость';
                document.getElementById('saveNewsBtn').textContent = '💾 Сохранить';
                document.getElementById('newsFormContainer').style.display = 'block';
                
                // Очищаем форму
                document.getElementById('newsCategory').value = 'updates';
                document.getElementById('newsTitle').value = '';
                document.getElementById('newsDate').value = new Date().toISOString().split('T')[0];
                document.getElementById('newsDescription').value = '';
                document.getElementById('newsLink').value = '';
                document.getElementById('newsLinkText').value = '';
                
                // Прокручиваем к форме
                document.getElementById('newsFormContainer').scrollIntoView({ behavior: 'smooth' });
            }
            
            function editNews(newsId) {
                fetch(`/admin/news/${newsId}`, {credentials: 'include'})
                    .then(r => r.json())
                    .then(result => {
                        if (result.success) {
                            const item = result.news;
                            editingNewsId = newsId;
                            
                            document.getElementById('newsFormTitle').textContent = 'Редактировать новость';
                            document.getElementById('saveNewsBtn').textContent = '💾 Сохранить изменения';
                            document.getElementById('newsFormContainer').style.display = 'block';
                            
                            document.getElementById('newsCategory').value = item.category;
                            document.getElementById('newsTitle').value = item.title;
                            document.getElementById('newsDate').value = item.date.split(' ')[0] || item.date;
                            document.getElementById('newsDescription').value = item.description;
                            document.getElementById('newsLink').value = item.link || '';
                            document.getElementById('newsLinkText').value = item.link_text || '';
                            
                            document.getElementById('newsFormContainer').scrollIntoView({ behavior: 'smooth' });
                        } else {
                            alert('❌ Ошибка загрузки новости');
                        }
                    });
            }
            
            function saveNews() {
                const category = document.getElementById('newsCategory').value;
                const title = document.getElementById('newsTitle').value.trim();
                const date = document.getElementById('newsDate').value;
                const description = document.getElementById('newsDescription').value.trim();
                const link = document.getElementById('newsLink').value.trim();
                const linkText = document.getElementById('newsLinkText').value.trim();
                
                if (!title || !description || !date) {
                    alert('Заполните все обязательные поля! (заголовок, дата, описание)');
                    return;
                }
                
                const data = {
                    category: category,
                    title: title,
                    date: date,
                    description: description,
                    link: link || null,
                    link_text: linkText || null
                };
                
                const url = editingNewsId ? `/admin/news/${editingNewsId}` : '/admin/news';
                const method = editingNewsId ? 'PUT' : 'POST';
                
                fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify(data)
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert(editingNewsId ? '✅ Новость обновлена!' : '✅ Новость создана!');
                        cancelNewsForm();
                        loadNews();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('❌ Ошибка сохранения: ' + err);
                });
            }
            
            function cancelNewsForm() {
                editingNewsId = null;
                document.getElementById('newsFormContainer').style.display = 'none';
            }
            
            function deleteNews(newsId) {
                if (!confirm('Удалить новость? Это действие нельзя отменить!')) return;
                
                fetch(`/admin/news/${newsId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Новость удалена!');
                        loadNews();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            // Регистрируем функции для новостей глобально СРАЗУ после определения
            if (typeof loadNews === 'function') window.loadNews = loadNews;
            if (typeof showNewsForm === 'function') window.showNewsForm = showNewsForm;
            if (typeof editNews === 'function') window.editNews = editNews;
            if (typeof saveNews === 'function') window.saveNews = saveNews;
            if (typeof cancelNewsForm === 'function') window.cancelNewsForm = cancelNewsForm;
            if (typeof deleteNews === 'function') window.deleteNews = deleteNews;
                console.log('✅ Функции для новостей зарегистрированы глобально');
            
            // ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛНЫМИ НОВОСТЯМИ ==========
            let editingFullNewsId = null;
            let fullNewsTinyMCEEditor = null;
            let isFullNewsHtmlMode = false;
            
            function loadFullNews() {
                const categoryFilter = document.getElementById('fullNewsCategoryFilter') ? document.getElementById('fullNewsCategoryFilter').value : '';
                let url = '/admin/full-news';
                if (categoryFilter) {
                    url += '?category=' + categoryFilter;
                }
                
                fetch(url, {credentials: 'include'})
                    .then(r => r.json())
                    .then(news => {
                        const newsListEl = document.getElementById('fullNewsList');
                        if (!newsListEl) return;
                        
                        let html = '';
                        if (!news || news.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет полных новостей</p>';
                        } else {
                            news.forEach(item => {
                                html += createFullNewsCard(item);
                            });
                        }
                        newsListEl.innerHTML = html;
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки полных новостей:', err);
                        const newsListEl = document.getElementById('fullNewsList');
                        if (newsListEl) newsListEl.innerHTML = '<p style="color: #f56565; padding: 20px;">Ошибка загрузки данных</p>';
                    });
            }
            
            function createFullNewsCard(item) {
                const statusBadge = item.is_published ? '<span style="background: #48bb78; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; margin-left: 10px;">Опубликовано</span>' : '<span style="background: #cbd5e0; color: #2d3748; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; margin-left: 10px;">Черновик</span>';
                const categoryBadge = item.category ? `<span style="background: #667eea; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; margin-right: 10px;">${item.category}</span>` : '';
                const viewsCount = item.views_count || 0;
                
                return `
                    <div class="user-card" style="margin: 10px 0; border-left: 4px solid #667eea;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 5px;">
                                    ${categoryBadge}
                                    ${statusBadge}
                                    <span style="color: #999;">👁️ ${viewsCount} просмотров</span>
                                </div>
                                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 5px;">
                                    <a href="/news/${item.slug}" target="_blank" style="color: #667eea; text-decoration: none;">${item.title}</a>
                                </div>
                                <div style="color: #666; font-size: 0.9rem; margin-bottom: 10px;">
                                    📅 ${item.published_at ? item.published_at.substring(0, 10) : 'Не указана'} | 
                                    ✍️ ${item.author || 'Редакция DocScan'} | 
                                    🔗 /news/${item.slug}
                                </div>
                                <div style="color: #2d3748; margin-bottom: 10px; line-height: 1.5;">
                                    ${item.short_description.substring(0, 200)}${item.short_description.length > 200 ? '...' : ''}
                                </div>
                            </div>
                            <div style="display: flex; gap: 5px; flex-direction: column;">
                                <button onclick="editFullNews(${item.id})" style="background: #4299e1; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.85rem;">✏️ Редактировать</button>
                                <button onclick="deleteFullNews(${item.id})" style="background: #e53e3e; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.85rem;">🗑️ Удалить</button>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            function showFullNewsForm() {
                editingFullNewsId = null;
                document.getElementById('fullNewsFormTitle').textContent = 'Создать полную новость';
                document.getElementById('saveFullNewsBtn').textContent = '💾 Создать';
                document.getElementById('fullNewsFormContainer').style.display = 'block';
                
                // Очищаем форму
                document.getElementById('fullNewsSlug').value = '';
                document.getElementById('fullNewsTitle').value = '';
                document.getElementById('fullNewsShortDescription').value = '';
                document.getElementById('fullNewsCategory').value = '';
                document.getElementById('fullNewsImageUrl').value = '';
                document.getElementById('fullNewsAuthor').value = 'Редакция DocScan';
                document.getElementById('fullNewsMetaTitle').value = '';
                document.getElementById('fullNewsMetaDescription').value = '';
                document.getElementById('fullNewsMetaKeywords').value = '';
                const today = new Date().toISOString().split('T')[0];
                document.getElementById('fullNewsPublishedAt').value = today;
                document.getElementById('fullNewsIsPublished').checked = true;
                
                // Очищаем редактор
                if (fullNewsTinyMCEEditor) {
                    fullNewsTinyMCEEditor.setContent('');
                } else {
                    document.getElementById('fullNewsContent').value = '';
                    document.getElementById('fullNewsContentRaw').value = '';
                }
                
                // Инициализируем TinyMCE если еще не инициализирован
                setTimeout(() => {
                    if (!fullNewsTinyMCEEditor && typeof tinymce !== 'undefined') {
                        initFullNewsTinyMCE();
                    }
                }, 300);
                
                document.getElementById('fullNewsFormContainer').scrollIntoView({ behavior: 'smooth' });
            }
            
            function editFullNews(newsId) {
                fetch(`/admin/full-news/${newsId}`, {credentials: 'include'})
                    .then(r => r.json())
                    .then(result => {
                        if (result.success) {
                            const item = result.news;
                            editingFullNewsId = newsId;
                            
                            document.getElementById('fullNewsFormTitle').textContent = 'Редактировать полную новость';
                            document.getElementById('saveFullNewsBtn').textContent = '💾 Сохранить изменения';
                            document.getElementById('fullNewsFormContainer').style.display = 'block';
                            
                            document.getElementById('fullNewsSlug').value = item.slug;
                            document.getElementById('fullNewsTitle').value = item.title;
                            document.getElementById('fullNewsShortDescription').value = item.short_description;
                            document.getElementById('fullNewsCategory').value = item.category || '';
                            document.getElementById('fullNewsImageUrl').value = item.image_url || '';
                            document.getElementById('fullNewsAuthor').value = item.author || 'Редакция DocScan';
                            document.getElementById('fullNewsMetaTitle').value = item.meta_title || '';
                            document.getElementById('fullNewsMetaDescription').value = item.meta_description || '';
                            document.getElementById('fullNewsMetaKeywords').value = item.meta_keywords || '';
                            document.getElementById('fullNewsPublishedAt').value = item.published_at ? item.published_at.substring(0, 10) : new Date().toISOString().split('T')[0];
                            document.getElementById('fullNewsIsPublished').checked = item.is_published !== false;
                            
                            // Загружаем контент в редактор
                            if (fullNewsTinyMCEEditor) {
                                fullNewsTinyMCEEditor.setContent(item.full_content || '');
                            } else {
                                document.getElementById('fullNewsContent').value = item.full_content || '';
                                document.getElementById('fullNewsContentRaw').value = item.full_content || '';
                                // Инициализируем TinyMCE если еще не инициализирован
                                if (typeof tinymce !== 'undefined') {
                                    initFullNewsTinyMCE();
                                    // После инициализации загрузим контент
                                    setTimeout(() => {
                                        if (fullNewsTinyMCEEditor) {
                                            fullNewsTinyMCEEditor.setContent(item.full_content || '');
                                        }
                                    }, 1000);
                                }
                            }
                            
                            document.getElementById('fullNewsFormContainer').scrollIntoView({ behavior: 'smooth' });
                        } else {
                            alert('❌ Ошибка загрузки новости');
                        }
                    });
            }
            
            function saveFullNews() {
                const slug = document.getElementById('fullNewsSlug').value.trim();
                const title = document.getElementById('fullNewsTitle').value.trim();
                const shortDescription = document.getElementById('fullNewsShortDescription').value.trim();
                
                // Получаем контент из редактора
                let fullContent = '';
                if (isFullNewsHtmlMode) {
                    fullContent = document.getElementById('fullNewsContentRaw').value.trim();
                } else if (fullNewsTinyMCEEditor) {
                    fullContent = fullNewsTinyMCEEditor.getContent();
                } else {
                    fullContent = document.getElementById('fullNewsContent').value.trim();
                }
                
                const category = document.getElementById('fullNewsCategory').value;
                const imageUrl = document.getElementById('fullNewsImageUrl').value.trim();
                const author = document.getElementById('fullNewsAuthor').value.trim();
                const metaTitle = document.getElementById('fullNewsMetaTitle').value.trim();
                const metaDescription = document.getElementById('fullNewsMetaDescription').value.trim();
                const metaKeywords = document.getElementById('fullNewsMetaKeywords').value.trim();
                const publishedAt = document.getElementById('fullNewsPublishedAt').value;
                const isPublished = document.getElementById('fullNewsIsPublished').checked;
                
                if (!slug || !title || !shortDescription || !fullContent) {
                    alert('❌ Заполните все обязательные поля (slug, заголовок, краткое описание, полный контент)');
                    return;
                }
                
                const data = {
                    slug: slug,
                    title: title,
                    short_description: shortDescription,
                    full_content: fullContent,
                    category: category || null,
                    image_url: imageUrl || null,
                    author: author || 'Редакция DocScan',
                    meta_title: metaTitle || null,
                    meta_description: metaDescription || null,
                    meta_keywords: metaKeywords || null,
                    published_at: publishedAt ? publishedAt + 'T00:00:00' : null,
                    is_published: isPublished
                };
                
                const url = editingFullNewsId ? `/admin/full-news/${editingFullNewsId}` : '/admin/full-news';
                const method = editingFullNewsId ? 'PUT' : 'POST';
                
                fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify(data)
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert(editingFullNewsId ? '✅ Полная новость обновлена!' : '✅ Полная новость создана!');
                        cancelFullNewsForm();
                        loadFullNews();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('❌ Ошибка сохранения: ' + err);
                });
            }
            
            function cancelFullNewsForm() {
                editingFullNewsId = null;
                document.getElementById('fullNewsFormContainer').style.display = 'none';
                
                // Очищаем редактор
                if (fullNewsTinyMCEEditor) {
                    fullNewsTinyMCEEditor.setContent('');
                }
                document.getElementById('fullNewsContent').value = '';
                document.getElementById('fullNewsContentRaw').value = '';
                
                // Возвращаемся в визуальный режим
                isFullNewsHtmlMode = false;
                const container = document.getElementById('fullNews-tinymce-container');
                const htmlContainer = document.getElementById('fullNews-html-editor-container');
                const statusEl = document.getElementById('fullNewsEditorStatus');
                const btn = document.getElementById('fullNewsEditorModeBtn');
                if (container && htmlContainer && statusEl && btn) {
                    container.style.display = 'block';
                    htmlContainer.style.display = 'none';
                    statusEl.textContent = 'Режим: Визуальный редактор';
                    btn.textContent = '</> Переключить в HTML';
                }
            }
            
            function deleteFullNews(newsId) {
                if (!confirm('Удалить полную новость? Это действие нельзя отменить!')) return;
                
                fetch(`/admin/full-news/${newsId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Полная новость удалена!');
                        loadFullNews();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            // ========== ИНИЦИАЛИЗАЦИЯ TINYMCE ДЛЯ ПОЛНЫХ НОВОСТЕЙ ==========
            function initFullNewsTinyMCE() {
                const loadingEl = document.getElementById('fullNews-tinymce-loading');
                if (loadingEl) {
                    loadingEl.textContent = '⏳ Инициализация редактора...';
                }
                
                if (typeof tinymce !== 'undefined') {
                    // Удаляем предыдущий редактор если он существует
                    if (fullNewsTinyMCEEditor) {
                        tinymce.remove('#fullNewsContent');
                        fullNewsTinyMCEEditor = null;
                    }
                    
                    console.log('🚀 Инициализация TinyMCE для полных новостей...');
                    tinymce.init({
                        selector: '#fullNewsContent',
                        height: 600,
                        menubar: true,
                        plugins: [
                            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
                            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                            'insertdatetime', 'media', 'table', 'help', 'wordcount',
                            'emoticons', 'codesample', 'pagebreak', 'nonbreaking',
                            'directionality'
                        ],
                        toolbar: 'undo redo | blocks | ' +
                            'bold italic underline strikethrough forecolor backcolor | ' +
                            'alignleft aligncenter alignright alignjustify | ' +
                            'bullist numlist outdent indent | ' +
                            'removeformat | link image media table code | ' +
                            'insertdatetime charmap emoticons pagebreak | ' +
                            'visualblocks visualchars fullscreen preview | ' +
                            'fontfamily fontsize | ' +
                            'codesample | ' +
                            'searchreplace help',
                        content_style: 'body { font-family: Inter, Arial, sans-serif; font-size: 16px; line-height: 1.6; }',
                        font_family_formats: 'Inter=Inter, sans-serif; Arial=Arial, sans-serif; Times New Roman=Times New Roman, serif; Courier New=Courier New, monospace;',
                        font_size_formats: '8pt 10pt 12pt 14pt 16pt 18pt 24pt 36pt 48pt',
                        block_formats: 'Параграф=p; Заголовок 1=h1; Заголовок 2=h2; Заголовок 3=h3; Заголовок 4=h4; Заголовок 5=h5; Заголовок 6=h6; Предформатированный=pre',
                        image_advtab: true,
                        file_picker_types: 'image',
                        automatic_uploads: true,
                        images_upload_url: '/admin/articles/upload-image',
                        images_upload_handler: function (blobInfo, progress) {
                            return new Promise(function (resolve, reject) {
                                var xhr = new XMLHttpRequest();
                                xhr.withCredentials = true;
                                xhr.open('POST', '/admin/articles/upload-image');
                                
                                xhr.upload.onprogress = function (e) {
                                    progress(e.loaded / e.total * 100);
                                };
                                
                                xhr.onload = function () {
                                    if (xhr.status === 403) {
                                        reject({ message: 'HTTP Error: ' + xhr.status, remove: true });
                                        return;
                                    }
                                    
                                    if (xhr.status < 200 || xhr.status >= 300) {
                                        reject('HTTP Error: ' + xhr.status);
                                        return;
                                    }
                                    
                                    var json = JSON.parse(xhr.responseText);
                                    
                                    if (!json || typeof json.location != 'string') {
                                        reject('Invalid JSON: ' + xhr.responseText);
                                        return;
                                    }
                                    
                                    resolve(json.location);
                                };
                                
                                xhr.onerror = function () {
                                    reject('Image upload failed due to a XHR Transport error. Code: ' + xhr.status);
                                };
                                
                                var formData = new FormData();
                                formData.append('file', blobInfo.blob(), blobInfo.filename());
                                
                                xhr.send(formData);
                            });
                        },
                        setup: function (editor) {
                            fullNewsTinyMCEEditor = editor;
                            editor.on('init', function () {
                                console.log('✅ TinyMCE редактор для полных новостей инициализирован успешно');
                                const loadingEl = document.getElementById('fullNews-tinymce-loading');
                                if (loadingEl) {
                                    loadingEl.textContent = '✅ Визуальный редактор готов!';
                                    setTimeout(function() {
                                        loadingEl.style.display = 'none';
                                    }, 2000);
                                }
                                // Убеждаемся, что визуальный редактор видим
                                document.getElementById('fullNews-tinymce-container').style.display = 'block';
                                document.getElementById('fullNews-html-editor-container').style.display = 'none';
                            });
                            
                            editor.on('error', function(e) {
                                console.error('❌ Ошибка TinyMCE для полных новостей:', e);
                                const loadingEl = document.getElementById('fullNews-tinymce-loading');
                                if (loadingEl) {
                                    loadingEl.textContent = '❌ Ошибка загрузки редактора. Используйте HTML-режим.';
                                    loadingEl.style.color = '#f56565';
                                }
                            });
                        },
                        branding: false,
                        promotion: false
                    });
                } else {
                    console.error('❌ TinyMCE не загружен. Используйте HTML-режим.');
                    const loadingEl = document.getElementById('fullNews-tinymce-loading');
                    if (loadingEl) {
                        loadingEl.textContent = '❌ Визуальный редактор не загрузился. Используйте HTML-режим.';
                        loadingEl.style.color = '#f56565';
                    }
                }
            }
            
            function toggleFullNewsEditorMode() {
                const container = document.getElementById('fullNews-tinymce-container');
                const htmlContainer = document.getElementById('fullNews-html-editor-container');
                const statusEl = document.getElementById('fullNewsEditorStatus');
                const btn = document.getElementById('fullNewsEditorModeBtn');
                
                if (!container || !htmlContainer || !statusEl || !btn) {
                    console.error('❌ Не найдены элементы для переключения режима');
                    return;
                }
                
                if (isFullNewsHtmlMode) {
                    // Переключаемся на визуальный режим
                    console.log('🔄 Переключение на визуальный режим...');
                    isFullNewsHtmlMode = false;
                    const htmlContent = document.getElementById('fullNewsContentRaw').value;
                    
                    if (fullNewsTinyMCEEditor) {
                        fullNewsTinyMCEEditor.setContent(htmlContent || '');
                        container.style.display = 'block';
                        htmlContainer.style.display = 'none';
                        statusEl.textContent = 'Режим: Визуальный редактор';
                        btn.textContent = '</> Переключить в HTML';
                        console.log('✅ Визуальный режим включен');
                    } else {
                        console.warn('⚠️ TinyMCE редактор не инициализирован, пробую инициализировать...');
                        if (typeof tinymce !== 'undefined') {
                            initFullNewsTinyMCE();
                            setTimeout(() => {
                                if (fullNewsTinyMCEEditor) {
                                    fullNewsTinyMCEEditor.setContent(htmlContent || '');
                                    container.style.display = 'block';
                                    htmlContainer.style.display = 'none';
                                    statusEl.textContent = 'Режим: Визуальный редактор';
                                    btn.textContent = '</> Переключить в HTML';
                                }
                            }, 1000);
                        } else {
                            alert('⚠️ Визуальный редактор не загружен. Используйте HTML-режим.');
                        }
                    }
                } else {
                    // Переключаемся на HTML режим
                    console.log('🔄 Переключение на HTML режим...');
                    isFullNewsHtmlMode = true;
                    let htmlContent = '';
                    
                    if (fullNewsTinyMCEEditor) {
                        htmlContent = fullNewsTinyMCEEditor.getContent();
                    } else {
                        htmlContent = document.getElementById('fullNewsContent').value;
                    }
                    
                    document.getElementById('fullNewsContentRaw').value = htmlContent;
                    container.style.display = 'none';
                    htmlContainer.style.display = 'block';
                    statusEl.textContent = 'Режим: HTML редактор';
                    btn.textContent = '👁️ Переключить в визуальный';
                    console.log('✅ HTML режим включен');
                }
            }
            
            // Инициализируем TinyMCE для полных новостей при открытии формы
            function initFullNewsEditorOnShow() {
                // Проверяем, видна ли форма
                const formContainer = document.getElementById('fullNewsFormContainer');
                if (formContainer && formContainer.style.display !== 'none') {
                    if (typeof tinymce !== 'undefined' && !fullNewsTinyMCEEditor) {
                        setTimeout(() => {
                            initFullNewsTinyMCE();
                        }, 500);
                    }
                }
            }
            
            // Регистрируем функции для полных новостей глобально сразу после определения
            if (typeof loadFullNews === 'function') window.loadFullNews = loadFullNews;
            if (typeof showFullNewsForm === 'function') window.showFullNewsForm = showFullNewsForm;
            if (typeof editFullNews === 'function') window.editFullNews = editFullNews;
            if (typeof saveFullNews === 'function') window.saveFullNews = saveFullNews;
            if (typeof cancelFullNewsForm === 'function') window.cancelFullNewsForm = cancelFullNewsForm;
            if (typeof deleteFullNews === 'function') window.deleteFullNews = deleteFullNews;
            if (typeof initFullNewsTinyMCE === 'function') window.initFullNewsTinyMCE = initFullNewsTinyMCE;
            if (typeof toggleFullNewsEditorMode === 'function') window.toggleFullNewsEditorMode = toggleFullNewsEditorMode;
            if (typeof initFullNewsEditorOnShow === 'function') window.initFullNewsEditorOnShow = initFullNewsEditorOnShow;
                console.log('✅ Функции для полных новостей зарегистрированы глобально');
            
            // ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ВОПРОСАМИ ==========
            function loadQuestions() {
                const statusFilter = document.getElementById('questionFilter') ? document.getElementById('questionFilter').value : '';
                let url = '/admin/questions';
                if (statusFilter) {
                    url += '?status=' + statusFilter;
                }
                
                fetch(url, {credentials: 'include'})
                    .then(r => r.json())
                    .then(questions => {
                        const questionsListEl = document.getElementById('questionsList');
                        if (!questionsListEl) return;
                        
                        let html = '';
                        if (!questions || questions.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет вопросов</p>';
                        } else {
                            questions.forEach(q => {
                                const statusBadge = q.status === 'solved' ? '✅ Решен' : 
                                                   q.status === 'answered' ? '💬 Есть ответы' : 
                                                   q.status === 'closed' ? '🔒 Закрыт' : '❓ Открыт';
                                const statusColor = q.status === 'solved' ? '#48bb78' : 
                                                   q.status === 'answered' ? '#ed8936' : 
                                                   q.status === 'closed' ? '#999' : '#667eea';
                                
                                html += `
                                    <div class="user-card" style="margin: 10px 0; border-left: 4px solid ${statusColor};">
                                        <div style="display: flex; justify-content: space-between; align-items: start;">
                                            <div style="flex: 1;">
                                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 5px;">
                                                    <span style="background: ${statusColor}; color: white; padding: 3px 8px; border-radius: 3px; margin-right: 10px;">${statusBadge}</span>
                                                    ${q.category}
                                                </div>
                                                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 5px;">
                                                    <a href="/questions/${q.id}" target="_blank" style="color: #667eea; text-decoration: none;">${q.title}</a>
                                                </div>
                                                <div style="color: #666; font-size: 0.9rem; margin-bottom: 10px;">
                                                    ${q.content.substring(0, 150)}${q.content.length > 150 ? '...' : ''}
                                                </div>
                                                <div style="color: #999; font-size: 0.85rem;">
                                                    👁️ ${q.views_count} | 💬 ${q.answers_count} | 📅 ${new Date(q.created_at).toLocaleDateString('ru-RU')}
                                                </div>
                                            </div>
                                            <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                                                <button onclick="viewAdminQuestion(${q.id})" style="background: #667eea; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">👁️ Просмотр</button>
                                                ${q.status !== 'closed' ? `<button onclick="closeAdminQuestion(${q.id})" style="background: #ed8936; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">🔒 Закрыть</button>` : `<button onclick="openAdminQuestion(${q.id})" style="background: #48bb78; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">🔓 Открыть</button>`}
                                                ${q.status !== 'solved' ? `<button onclick="solveAdminQuestion(${q.id})" style="background: #48bb78; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">✅ Решен</button>` : ''}
                                                <button onclick="deleteAdminQuestion(${q.id})" style="background: #f56565; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">🗑️ Удалить</button>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            });
                        }
                        questionsListEl.innerHTML = html;
                    });
            }
            
            function viewAdminQuestion(questionId) {
                // Показываем модальное окно с ответами
                showQuestionAnswers(questionId);
            }
            
            function showQuestionAnswers(questionId) {
                fetch(`/admin/questions/${questionId}/answers`, {credentials: 'include'})
                    .then(r => r.json())
                    .then(answers => {
                        let html = '<div style="max-height: 70vh; overflow-y: auto; padding: 20px;">';
                        html += '<h3 style="margin-bottom: 20px;">Ответы на вопрос</h3>';
                        
                        if (!answers || answers.length === 0) {
                            html += '<p style="color: #999; padding: 20px;">Нет ответов</p>';
                        } else {
                            answers.forEach(answer => {
                                const bestBadge = answer.is_best ? '<span style="background: #48bb78; color: white; padding: 3px 8px; border-radius: 3px; margin-right: 10px; font-size: 0.85rem;">⭐ Лучший ответ</span>' : '';
                                html += `
                                    <div class="user-card" style="margin: 10px 0; border-left: 4px solid ${answer.is_best ? '#48bb78' : '#667eea'};">
                                        <div style="display: flex; justify-content: space-between; align-items: start;">
                                            <div style="flex: 1;">
                                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 5px;">
                                                    ${bestBadge}
                                                    Автор: ${answer.author_email || 'Неизвестно'} | 👍 ${answer.likes_count || 0}
                                                </div>
                                                <div style="color: #2d3748; margin-bottom: 10px;">
                                                    ${answer.content}
                                                </div>
                                                <div style="color: #999; font-size: 0.85rem;">
                                                    📅 ${new Date(answer.created_at).toLocaleString('ru-RU')}
                                                </div>
                                            </div>
                                            <div style="display: flex; gap: 5px;">
                                                <button onclick="deleteAdminAnswer(${answer.id}, ${questionId})" style="background: #f56565; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">🗑️ Удалить</button>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            });
                        }
                        
                        html += '</div>';
                        html += '<div style="text-align: right; padding: 15px; border-top: 1px solid #e2e8f0;">';
                        html += '<button onclick="closeModal()" style="background: #e2e8f0; color: #2d3748; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Закрыть</button>';
                        html += '</div>';
                        
                        showModal('Ответы на вопрос', html);
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки ответов:', err);
                        alert('Ошибка загрузки ответов');
                    });
            }
            
            function deleteAdminAnswer(answerId, questionId) {
                if (!confirm('Удалить ответ? Это действие нельзя отменить!')) return;
                
                fetch(`/admin/answers/${answerId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Ответ удален!');
                        showQuestionAnswers(questionId); // Обновляем список
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('❌ Ошибка соединения: ' + err);
                });
            }
            
            function showModal(title, content) {
                // Создаем модальное окно если его нет
                let modal = document.getElementById('adminModal');
                if (!modal) {
                    modal = document.createElement('div');
                    modal.id = 'adminModal';
                    modal.style.cssText = 'display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 10000; align-items: center; justify-content: center;';
                    document.body.appendChild(modal);
                    
                    const modalContent = document.createElement('div');
                    modalContent.id = 'adminModalContent';
                    modalContent.style.cssText = 'background: white; border-radius: 10px; max-width: 800px; width: 90%; max-height: 90vh; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.2);';
                    modal.appendChild(modalContent);
                }
                
                const modalContent = document.getElementById('adminModalContent');
                modalContent.innerHTML = `
                    <div style="padding: 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
                        <h2 style="margin: 0; color: #2d3748;">${title}</h2>
                        <button onclick="closeModal()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #999;">&times;</button>
                    </div>
                    ${content}
                `;
                
                modal.style.display = 'flex';
            }
            
            function closeModal() {
                const modal = document.getElementById('adminModal');
                if (modal) {
                    modal.style.display = 'none';
                }
            }
            
            // ========== ФУНКЦИИ ДЛЯ РАБОТЫ С УВЕДОМЛЕНИЯМИ ==========
            
            function sendAdminNotification() {
                const userIdOrEmail = document.getElementById('notificationUserId').value.trim();
                const type = document.getElementById('notificationType').value;
                const title = document.getElementById('notificationTitle').value.trim();
                const message = document.getElementById('notificationMessage').value.trim();
                const link = document.getElementById('notificationLink').value.trim();
                
                if (!userIdOrEmail || !title) {
                    document.getElementById('notificationMessageDiv').innerHTML = 
                        '<div style="color: #f56565; padding: 10px; background: #fed7d7; border-radius: 5px;">❌ Заполните User ID/Email и заголовок!</div>';
                    return;
                }
                
                fetch('/admin/notifications/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({
                        user_id_or_email: userIdOrEmail,
                        type: type,
                        title: title,
                        message: message,
                        link: link || null
                    })
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        document.getElementById('notificationMessageDiv').innerHTML = 
                            '<div style="color: #48bb78; padding: 10px; background: #c6f6d5; border-radius: 5px;">✅ Уведомление отправлено!</div>';
                        
                        // Очищаем форму
                        document.getElementById('notificationUserId').value = '';
                        document.getElementById('notificationTitle').value = '';
                        document.getElementById('notificationMessage').value = '';
                        document.getElementById('notificationLink').value = '';
                        
                        // Обновляем историю
                        loadNotificationsHistory();
                    } else {
                        document.getElementById('notificationMessageDiv').innerHTML = 
                            '<div style="color: #f56565; padding: 10px; background: #fed7d7; border-radius: 5px;">❌ Ошибка: ' + (result.error || 'Неизвестная ошибка') + '</div>';
                    }
                })
                .catch(err => {
                    document.getElementById('notificationMessageDiv').innerHTML = 
                        '<div style="color: #f56565; padding: 10px; background: #fed7d7; border-radius: 5px;">❌ Ошибка соединения: ' + err.message + '</div>';
                });
            }
            
            function loadNotificationsHistory() {
                fetch('/admin/notifications/history', {
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    const historyEl = document.getElementById('notificationsHistory');
                    if (!historyEl) return;
                    
                    if (!result.success || !result.notifications || result.notifications.length === 0) {
                        historyEl.innerHTML = '<p style="color: #999; padding: 20px; text-align: center;">Нет отправленных уведомлений</p>';
                        return;
                    }
                    
                    html = '<div style="overflow-x: auto; -webkit-overflow-scrolling: touch;"><table style="min-width: 600px; width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Пользователь</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Тип</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Заголовок</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата</th></tr></thead><tbody>';
                    
                    result.notifications.slice(0, 20).forEach(notif => {
                        const typeColors = {
                            'admin': '#667eea',
                            'info': '#4299e1',
                            'warning': '#ed8936',
                            'success': '#48bb78'
                        };
                        const typeColor = typeColors[notif.type] || '#cbd5e0';
                        const userId = notif.user_id || '';
                        const notifType = notif.type || '';
                        const notifTitle = (notif.title || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        const createdDate = new Date(notif.created_at).toLocaleString('ru-RU');
                        
                        html += '<tr style="border-bottom: 1px solid #e2e8f0;">';
                        html += '<td style="padding: 12px;">' + userId + '</td>';
                        html += '<td style="padding: 12px;"><span style="background: ' + typeColor + '; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">' + notifType + '</span></td>';
                        html += '<td style="padding: 12px;">' + notifTitle + '</td>';
                        html += '<td style="padding: 12px;">' + createdDate + '</td>';
                        html += '</tr>';
                    });
                    
                    html += '</tbody></table></div>';
                    historyEl.innerHTML = html;
                })
                .catch(err => {
                    const historyEl = document.getElementById('notificationsHistory');
                    if (historyEl) {
                        historyEl.innerHTML = '<p style="color: #f56565; padding: 20px;">Ошибка загрузки истории</p>';
                    }
                });
            }
            // Регистрируем loadNotificationsHistory глобально сразу после определения
            if (typeof loadNotificationsHistory === 'function') {
                window.loadNotificationsHistory = loadNotificationsHistory;
                console.log('✅ loadNotificationsHistory зарегистрирована глобально');
            }
            
            function closeAdminQuestion(questionId) {
                if (!confirm('Закрыть вопрос?')) return;
                
                fetch(`/admin/questions/${questionId}/status`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({status: 'closed'})
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Вопрос закрыт!');
                        loadQuestions();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            function openAdminQuestion(questionId) {
                fetch(`/admin/questions/${questionId}/status`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({status: 'open'})
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Вопрос открыт!');
                        loadQuestions();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            function solveAdminQuestion(questionId) {
                fetch(`/admin/questions/${questionId}/status`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({status: 'solved'})
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Вопрос отмечен как решенный!');
                        loadQuestions();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            function deleteAdminQuestion(questionId) {
                if (!confirm('Удалить вопрос? Это действие нельзя отменить!')) return;
                
                fetch(`/admin/questions/${questionId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Вопрос удален!');
                        loadQuestions();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            // Регистрируем функции для вопросов глобально
            if (typeof loadQuestions === 'function') window.loadQuestions = loadQuestions;
            if (typeof viewAdminQuestion === 'function') window.viewAdminQuestion = viewAdminQuestion;
            if (typeof closeAdminQuestion === 'function') window.closeAdminQuestion = closeAdminQuestion;
            if (typeof openAdminQuestion === 'function') window.openAdminQuestion = openAdminQuestion;
            if (typeof solveAdminQuestion === 'function') window.solveAdminQuestion = solveAdminQuestion;
            if (typeof deleteAdminQuestion === 'function') window.deleteAdminQuestion = deleteAdminQuestion;
            if (typeof showQuestionAnswers === 'function') window.showQuestionAnswers = showQuestionAnswers;
            if (typeof deleteAdminAnswer === 'function') window.deleteAdminAnswer = deleteAdminAnswer;
            if (typeof closeModal === 'function') window.closeModal = closeModal;
            
            function showUser(userId) {
                // Переключаемся на секцию пользователей
                showSection('users');
                // Прокручиваем к списку пользователей
                setTimeout(function() {
                    const usersList = document.getElementById('usersList');
                    if (usersList) {
                        usersList.scrollIntoView({ behavior: 'smooth' });
                        // Подсвечиваем нужную карточку пользователя
                        const userCards = usersList.querySelectorAll('.user-card');
                        userCards.forEach(card => {
                            if (card.textContent.includes(userId)) {
                                card.style.background = '#fff3cd';
                                card.style.border = '2px solid #ffc107';
                                setTimeout(function() {
                                    card.style.background = 'white';
                                    card.style.border = 'none';
                                }, 3000);
                            }
                        });
                    }
                }, 500);
            }

            function loadUsers() {
                // Очищаем поиск при новой загрузке
                document.getElementById('searchUser').value = '';
                document.getElementById('searchStatus').textContent = '';
                fetch('/admin/users', {credentials: 'include'})
                    .then(r => r.json())
                    .then(users => {
                        // Преобразуем объект в массив и сортируем по дате создания (новые сначала)
                        const usersArray = Object.entries(users).map(([userId, userData]) => ({
                            userId: userId,
                            ...userData
                        }));
                        
                        // Сортируем по created_at (новые сначала)
                        usersArray.sort((a, b) => {
                            if (!a.created_at && !b.created_at) return 0;
                            if (!a.created_at) return 1;
                            if (!b.created_at) return -1;
                            return new Date(b.created_at) - new Date(a.created_at);
                        });
                        
                        html = '<div style="overflow-x: auto; -webkit-overflow-scrolling: touch; margin-top: 15px;"><table style="min-width: 1000px; width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">ID</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Email</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата регистрации</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Тариф</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Тариф до</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Анализов всего</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Сегодня</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Действия</th></tr></thead><tbody>';
                        
                        usersArray.forEach(user => {
                            const createdDate = user.created_at ? (function() {
                                try {
                                    return new Date(user.created_at).toLocaleString('ru-RU');
                                } catch(e) {
                                    return user.created_at;
                                }
                            })() : 'Неизвестно';
                            const planExpires = user.plan_expires ? (function() {
                                try {
                                    return new Date(user.plan_expires).toLocaleDateString('ru-RU');
                                } catch(e) {
                                    return user.plan_expires;
                                }
                            })() : '—';
                            html += `
                                <tr style="border-bottom: 1px solid #e2e8f0;" class="user-card-row" data-user-id="${user.userId}">
                                    <td style="padding: 10px;"><strong>${user.userId}</strong></td>
                                    <td style="padding: 10px;">${user.email || 'Не указан'}</td>
                                    <td style="padding: 10px;">${createdDate}</td>
                                    <td style="padding: 10px;">${getPlanName(user.plan || 'free')}</td>
                                    <td style="padding: 10px;">${planExpires}</td>
                                    <td style="padding: 10px;">${user.total_used || 0}</td>
                                    <td style="padding: 10px;">${user.analyses_today !== undefined ? user.analyses_today : (user.used_today || 0)}/${getPlanLimit(user.plan || 'free')}</td>
                                    <td style="padding: 10px;">
                                        <button class="set-plan-btn" data-user-id="${user.userId || ''}" data-plan="standard" style="font-size: 0.85rem; padding: 5px 10px;">Стандарт</button>
                                        <button class="set-plan-btn" data-user-id="${user.userId || ''}" data-plan="premium" style="font-size: 0.85rem; padding: 5px 10px;">Премиум</button>
                                    </td>
                                </tr>
                            `;
                        });
                        html += '</tbody></table></div>';
                        document.getElementById('usersList').innerHTML = html;
                        
                        // Привязываем обработчики для кнопок быстрой установки тарифа
                        document.querySelectorAll('.set-plan-btn').forEach(btn => {
                            btn.addEventListener('click', function() {
                                const userId = this.getAttribute('data-user-id');
                                const plan = this.getAttribute('data-plan');
                                if (userId && plan && typeof setUserPlanQuick === 'function') {
                                    setUserPlanQuick(userId, plan);
                                }
                            });
                        });
                    });
            }
            // Регистрируем loadUsers глобально сразу после определения
            if (typeof loadUsers === 'function') {
                window.loadUsers = loadUsers;
                console.log('✅ loadUsers зарегистрирована глобально');
            }

            function getPlanName(plan) {
                const names = {
                    free: 'Бесплатный',
                    standard: 'Стандарт',
                    premium: 'Премиум',
                    business_start: 'Бизнес Старт',
                    business_pro: 'Бизнес Про',
                    business_max: 'Бизнес Макс',
                    business_unlimited: 'Бизнес Безлимит'
                };
                return names[plan] || plan;
            }
            
            function getPlanLimit(plan) {
                const limits = {
                    free: 1,
                    standard: 5,
                    premium: 15,
                    business_start: 10,
                    business_pro: 50,
                    business_max: 100,
                    business_unlimited: -1
                };
                return limits[plan] || 0;
            }

            function setUserPlan() {
                const userId = document.getElementById('userId').value;
                const plan = document.getElementById('planSelect').value;
                
                if (!userId) return alert('Введите ID пользователя');
                
                fetch('/admin/set-plan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId, plan: plan})
                })
                .then(r => r.json())
                .then(result => {
                    alert(result.success ? '✅ ' + result.message : '❌ ' + result.error);
                    loadUsers();
                    loadStats();
                });
            }

            function setUserPlanQuick(userId, plan) {
                fetch('/admin/set-plan', {credentials: 'include',
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId, plan: plan})
                })
                .then(r => r.json())
                .then(result => {
                    alert(result.success ? '✅ ' + result.message : '❌ ' + result.error);
                    if (typeof window.loadUsers === 'function') {
                        window.loadUsers();
                    } else if (typeof loadUsers === 'function') {
                    loadUsers();
                    }
                    if (typeof window.loadStats === 'function') {
                        window.loadStats();
                    } else if (typeof loadStats === 'function') {
                    loadStats();
                    }
                });
            }

            function createUser() {
                const userId = document.getElementById('newUserId').value;
                
                fetch('/admin/create-user', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId})
                })
                .then(r => r.json())
                .then(result => {
                    alert(result.success ? '✅ ' + result.message : '❌ ' + result.error);
                    loadUsers();
                    loadStats();
                });
            }
            
            // ========== ФУНКЦИИ ДЛЯ БЕЛОГО СПИСКА IP ==========
            
            function addWhitelistedIP() {
                const userId = document.getElementById('whitelistUserId').value.trim();
                const ipAddress = document.getElementById('whitelistIP').value.trim();
                const description = document.getElementById('whitelistDescription').value.trim();
                
                if (!userId || !ipAddress) {
                    document.getElementById('whitelistStatus').innerHTML = '<span style="color: #e53e3e;">❌ Заполните ID пользователя и IP-адрес</span>';
                    return;
                }
                
                fetch('/admin/add-whitelist-ip', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({
                        user_id: userId,
                        ip_address: ipAddress,
                        description: description || null
                    })
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        document.getElementById('whitelistStatus').innerHTML = '<span style="color: #48bb78;">✅ ' + result.message + '</span>';
                        document.getElementById('whitelistUserId').value = '';
                        document.getElementById('whitelistIP').value = '';
                        document.getElementById('whitelistDescription').value = '';
                        loadWhitelistedIPs();
                    } else {
                        document.getElementById('whitelistStatus').innerHTML = '<span style="color: #e53e3e;">❌ ' + result.error + '</span>';
                    }
                })
                .catch(error => {
                    document.getElementById('whitelistStatus').innerHTML = '<span style="color: #e53e3e;">❌ Ошибка: ' + error.message + '</span>';
                });
            }
            
            function loadWhitelistedIPs() {
                fetch('/admin/get-whitelist-ips', {
                    method: 'GET',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        const ips = result.ips || [];
                        let html = '<table style="width: 100%; border-collapse: collapse; margin-top: 15px;"><thead><tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0;"><th style="padding: 10px; text-align: left;">Пользователь</th><th style="padding: 10px; text-align: left;">IP-адрес</th><th style="padding: 10px; text-align: left;">Описание</th><th style="padding: 10px; text-align: left;">Статус</th><th style="padding: 10px; text-align: left;">Дата</th><th style="padding: 10px; text-align: left;">Действия</th></tr></thead><tbody>';
                        
                        if (ips.length === 0) {
                            html += '<tr><td colspan="6" style="padding: 20px; text-align: center; color: #666;">Нет IP-адресов в белом списке</td></tr>';
                        } else {
                            ips.forEach(ip => {
                                const statusBadge = ip.is_active 
                                    ? '<span style="background: #48bb78; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">Активен</span>'
                                    : '<span style="background: #cbd5e0; color: #4a5568; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">Неактивен</span>';
                                
                                html += `
                                    <tr style="border-bottom: 1px solid #e2e8f0;">
                                        <td style="padding: 10px;"><strong>${ip.user_id}</strong></td>
                                        <td style="padding: 10px;"><code style="background: #f7fafc; padding: 4px 8px; border-radius: 4px;">${ip.ip_address}</code></td>
                                        <td style="padding: 10px;">${ip.description || '—'}</td>
                                        <td style="padding: 10px;">${statusBadge}</td>
                                        <td style="padding: 10px;">${ip.created_at ? new Date(ip.created_at).toLocaleDateString('ru-RU') : '—'}</td>
                                        <td style="padding: 10px;">
                                            <button onclick="toggleWhitelistedIP(${ip.id})" style="font-size: 0.85rem; padding: 5px 10px; margin-right: 5px; background: ${ip.is_active ? '#ed8936' : '#48bb78'}; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                                ${ip.is_active ? '⏸️ Деактивировать' : '▶️ Активировать'}
                                            </button>
                                            <button onclick="removeWhitelistedIP(${ip.id})" style="font-size: 0.85rem; padding: 5px 10px; background: #e53e3e; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                                🗑️ Удалить
                                            </button>
                                        </td>
                                    </tr>
                                `;
                            });
                        }
                        
                        html += '</tbody></table>';
                        document.getElementById('whitelistList').innerHTML = html;
                    }
                })
                .catch(error => {
                    document.getElementById('whitelistList').innerHTML = '<div style="color: #e53e3e; padding: 20px;">❌ Ошибка загрузки: ' + error.message + '</div>';
                });
            }
            
            function removeWhitelistedIP(ipId) {
                if (!confirm('Удалить этот IP-адрес из белого списка?')) return;
                
                fetch('/admin/remove-whitelist-ip', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({ip_id: ipId})
                })
                .then(r => r.json())
                .then(result => {
                    alert(result.success ? '✅ ' + result.message : '❌ ' + result.error);
                    loadWhitelistedIPs();
                });
            }
            
            function toggleWhitelistedIP(ipId) {
                fetch('/admin/toggle-whitelist-ip', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({ip_id: ipId})
                })
                .then(r => r.json())
                .then(result => {
                    alert(result.success ? '✅ ' + result.message : '❌ ' + result.error);
                    loadWhitelistedIPs();
                });
            }
            // Регистрируем loadWhitelistedIPs глобально сразу после определения
            if (typeof loadWhitelistedIPs === 'function') {
                window.loadWhitelistedIPs = loadWhitelistedIPs;
                console.log('✅ loadWhitelistedIPs зарегистрирована глобально');
            }
            
            // Загружаем белый список IP при загрузке страницы
            document.addEventListener('DOMContentLoaded', function() {
                const userSection = document.getElementById('section-users');
                if (userSection) {
                    const observer = new MutationObserver(function(mutations) {
                        if (userSection.style.display !== 'none') {
                            if (typeof window.loadWhitelistedIPs === 'function') {
                                window.loadWhitelistedIPs();
                            }
                        }
                    });
                    observer.observe(userSection, { attributes: true, attributeFilter: ['style'] });
                }
            });
            
            // ========== ФУНКЦИИ ДЛЯ РЕЗЕРВНЫХ КОПИЙ ==========
            
            function createBackup() {
                const statusEl = document.getElementById('backupStatus');
                statusEl.innerHTML = '<span style="color: #667eea;">⏳ Создание бэкапа...</span>';
                
                fetch('/admin/create-backup', {
                    method: 'POST',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        statusEl.innerHTML = '<span style="color: #48bb78;">✅ ' + result.message + '</span>';
                        loadBackups();
                    } else {
                        statusEl.innerHTML = '<span style="color: #e53e3e;">❌ ' + result.error + '</span>';
                    }
                })
                .catch(error => {
                    statusEl.innerHTML = '<span style="color: #e53e3e;">❌ Ошибка: ' + error.message + '</span>';
                });
            }
            
            function loadBackups() {
                fetch('/admin/list-backups', {
                    method: 'GET',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        const backups = result.backups || [];
                        let html = '';
                        
                        if (result.total > 0) {
                            const totalSize = (result.total_size_mb !== undefined && result.total_size_mb !== null) ? result.total_size_mb : 0;
                            const totalCount = result.total || 0;
                            html += '<div style="margin-bottom: 15px; padding: 10px; background: #f7fafc; border-radius: 5px;">';
                            html += '<strong>Всего бэкапов:</strong> ' + totalCount + ' | ';
                            html += '<strong>Общий размер:</strong> ' + totalSize + ' MB';
                            html += '</div>';
                            
                            html += '<table style="width: 100%; border-collapse: collapse; margin-top: 15px;"><thead><tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0;"><th style="padding: 10px; text-align: left;">Дата создания</th><th style="padding: 10px; text-align: left;">Размер</th><th style="padding: 10px; text-align: left;">Имя файла</th><th style="padding: 10px; text-align: left;">Действия</th></tr></thead><tbody>';
                            
                            backups.forEach((backup, index) => {
                                const date = new Date(backup.date);
                                const dateStr = date.toLocaleString('ru-RU');
                                const sizeMb = backup.size_mb || 0;
                                const filename = backup.filename || '';
                                // Экранируем HTML специальные символы для безопасного отображения
                                const filenameEscaped = filename.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                                
                                html += '<tr style="border-bottom: 1px solid #e2e8f0;">';
                                html += '<td style="padding: 10px;">' + dateStr + '</td>';
                                html += '<td style="padding: 10px;">' + sizeMb + ' MB</td>';
                                html += '<td style="padding: 10px;"><code style="background: #f7fafc; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;">' + filenameEscaped + '</code></td>';
                                html += '<td style="padding: 10px;">';
                                // Используем JSON.stringify для безопасного экранирования в data-атрибуте
                                html += '<button class="delete-backup-btn" data-filename="' + filenameEscaped.replace(/"/g, '&quot;') + '" style="font-size: 0.85rem; padding: 5px 10px; background: #e53e3e; color: white; border: none; border-radius: 4px; cursor: pointer;">';
                                html += '🗑️ Удалить';
                                html += '</button>';
                                html += '</td>';
                                html += '</tr>';
                            });
                            
                            html += '</tbody></table>';
                        } else {
                            html = '<div style="padding: 20px; text-align: center; color: #666;">📦 Бэкапы не найдены. Создайте первый бэкап с помощью кнопки выше.</div>';
                        }
                        
                        document.getElementById('backupsList').innerHTML = html;
                        
                        // Привязываем обработчики для кнопок удаления
                        document.querySelectorAll('.delete-backup-btn').forEach(btn => {
                            btn.addEventListener('click', function() {
                                const filename = this.getAttribute('data-filename');
                                if (filename && typeof deleteBackup === 'function') {
                                    deleteBackup(filename);
                                }
                            });
                        });
                    } else {
                        document.getElementById('backupsList').innerHTML = '<div style="color: #e53e3e; padding: 20px;">❌ Ошибка загрузки: ' + result.error + '</div>';
                    }
                })
                .catch(error => {
                    document.getElementById('backupsList').innerHTML = '<div style="color: #e53e3e; padding: 20px;">❌ Ошибка соединения: ' + error.message + '</div>';
                });
            }
            // Регистрируем loadBackups глобально сразу после определения
            if (typeof loadBackups === 'function') {
                window.loadBackups = loadBackups;
                console.log('✅ loadBackups зарегистрирована глобально');
            }
            
            function deleteBackup(filename) {
                if (!confirm('Удалить бэкап ' + filename + '?')) return;
                
                fetch('/admin/delete-backup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({filename: filename})
                })
                .then(r => r.json())
                .then(result => {
                    alert(result.success ? '✅ ' + result.message : '❌ ' + result.error);
                    loadBackups();
                });
            }
            
            function cleanOldBackups() {
                if (!confirm('Удалить все бэкапы старше 30 дней?')) return;
                
                fetch('/admin/clean-old-backups', {
                    method: 'POST',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    alert(result.success ? '✅ ' + result.message : '❌ ' + result.error);
                    loadBackups();
                });
            }
            
            // ========== ФУНКЦИИ ДЛЯ КАСТОМНОГО БРЕНДИНГА ==========
            
            function loadBranding() {
                const userId = document.getElementById('brandingUserId').value.trim();
                if (!userId) {
                    document.getElementById('brandingStatus').innerHTML = '<span style="color: #e53e3e;">❌ Введите ID пользователя</span>';
                    return;
                }
                
                fetch(`/admin/get-branding?user_id=${userId}`, {
                    method: 'GET',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success && result.branding) {
                        const branding = result.branding;
                        document.getElementById('brandingCompanyName').value = branding.company_name || '';
                        document.getElementById('brandingPrimaryColor').value = branding.primary_color || '#4361ee';
                        document.getElementById('brandingPrimaryColorText').value = branding.primary_color || '#4361ee';
                        document.getElementById('brandingSecondaryColor').value = branding.secondary_color || '#764ba2';
                        document.getElementById('brandingSecondaryColorText').value = branding.secondary_color || '#764ba2';
                        
                        // Показываем логотип, если есть
                        if (branding.logo_path) {
                            // Заменяем обратные слеши на прямые для URL (безопасный способ)
                            const logoPath = branding.logo_path.split('\\\\').join('/').split('\\').join('/');
                            document.getElementById('brandingLogoPreviewImg').src = '/' + logoPath;
                            document.getElementById('brandingLogoPreview').style.display = 'block';
                        } else {
                            document.getElementById('brandingLogoPreview').style.display = 'none';
                        }
                        
                        // Обновляем кнопку активации
                        const toggleBtn = document.getElementById('brandingToggleBtn');
                        if (branding.is_active) {
                            toggleBtn.textContent = '⏸️ Деактивировать';
                            toggleBtn.style.background = '#ed8936';
                        } else {
                            toggleBtn.textContent = '▶️ Активировать';
                            toggleBtn.style.background = '#48bb78';
                        }
                        
                        document.getElementById('brandingForm').style.display = 'block';
                        document.getElementById('brandingStatus').innerHTML = '<span style="color: #48bb78;">✅ Настройки загружены</span>';
                    } else {
                        // Нет настроек, показываем форму для создания
                        document.getElementById('brandingForm').style.display = 'block';
                        document.getElementById('brandingStatus').innerHTML = '<span style="color: #667eea;">ℹ️ Настройки не найдены. Заполните форму для создания.</span>';
                    }
                })
                .catch(error => {
                    document.getElementById('brandingStatus').innerHTML = '<span style="color: #e53e3e;">❌ Ошибка: ' + error.message + '</span>';
                });
            }
            
            function saveBranding() {
                const userId = document.getElementById('brandingUserId').value.trim();
                if (!userId) {
                    alert('❌ Введите ID пользователя');
                    return;
                }
                
                const formData = new FormData();
                formData.append('user_id', userId);
                formData.append('company_name', document.getElementById('brandingCompanyName').value.trim());
                formData.append('primary_color', document.getElementById('brandingPrimaryColorText').value.trim());
                formData.append('secondary_color', document.getElementById('brandingSecondaryColorText').value.trim());
                
                const logoFile = document.getElementById('brandingLogo').files[0];
                if (logoFile) {
                    formData.append('logo', logoFile);
                }
                
                const statusEl = document.getElementById('brandingStatus');
                statusEl.innerHTML = '<span style="color: #667eea;">⏳ Сохранение...</span>';
                
                fetch('/admin/save-branding', {
                    method: 'POST',
                    credentials: 'include',
                    body: formData
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        statusEl.innerHTML = '<span style="color: #48bb78;">✅ Настройки сохранены!</span>';
                        loadBranding(); // Перезагружаем для обновления превью
                    } else {
                        statusEl.innerHTML = '<span style="color: #e53e3e;">❌ ' + result.error + '</span>';
                    }
                })
                .catch(error => {
                    statusEl.innerHTML = '<span style="color: #e53e3e;">❌ Ошибка: ' + error.message + '</span>';
                });
            }
            
            function toggleBrandingActive() {
                const userId = document.getElementById('brandingUserId').value.trim();
                if (!userId) {
                    alert('❌ Введите ID пользователя');
                    return;
                }
                
                fetch('/admin/toggle-branding', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({user_id: userId})
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Брендинг ' + (result.is_active ? 'активирован' : 'деактивирован'));
                        loadBranding(); // Перезагружаем для обновления кнопки
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                })
                .catch(error => {
                    alert('❌ Ошибка: ' + error.message);
                });
            }
            
            function deleteBranding() {
                const userId = document.getElementById('brandingUserId').value.trim();
                if (!userId) {
                    alert('❌ Введите ID пользователя');
                    return;
                }
                
                if (!confirm('Удалить настройки брендинга? Логотип также будет удален.')) return;
                
                fetch('/admin/delete-branding', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({user_id: userId})
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Брендинг удален');
                        document.getElementById('brandingForm').style.display = 'none';
                        document.getElementById('brandingStatus').innerHTML = '<span style="color: #48bb78;">✅ Брендинг удален</span>';
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                })
                .catch(error => {
                    alert('❌ Ошибка: ' + error.message);
                });
            }
            
            // Синхронизация color picker с текстовым полем
            document.addEventListener('DOMContentLoaded', function() {
                const primaryColorPicker = document.getElementById('brandingPrimaryColor');
                const primaryColorText = document.getElementById('brandingPrimaryColorText');
                const secondaryColorPicker = document.getElementById('brandingSecondaryColor');
                const secondaryColorText = document.getElementById('brandingSecondaryColorText');
                
                if (primaryColorPicker && primaryColorText) {
                    primaryColorPicker.addEventListener('input', function() {
                        primaryColorText.value = primaryColorPicker.value;
                    });
                    primaryColorText.addEventListener('input', function() {
                        if (/^#[0-9A-F]{6}$/i.test(primaryColorText.value)) {
                            primaryColorPicker.value = primaryColorText.value;
                        }
                    });
                }
                
                if (secondaryColorPicker && secondaryColorText) {
                    secondaryColorPicker.addEventListener('input', function() {
                        secondaryColorText.value = secondaryColorPicker.value;
                    });
                    secondaryColorText.addEventListener('input', function() {
                        if (/^#[0-9A-F]{6}$/i.test(secondaryColorText.value)) {
                            secondaryColorPicker.value = secondaryColorText.value;
                        }
                    });
                }
            });
            
            // Регистрируем функции глобально
            window.loadBranding = loadBranding;
            window.saveBranding = saveBranding;
            window.toggleBrandingActive = toggleBrandingActive;
            window.deleteBranding = deleteBranding;
            
            // Регистрируем функции глобально
            if (typeof createBackup === 'function') {
                window.createBackup = createBackup;
                window.loadBackups = loadBackups;
                window.deleteBackup = deleteBackup;
                window.cleanOldBackups = cleanOldBackups;
                
                // Загружаем бэкапы при переключении на секцию
                document.addEventListener('DOMContentLoaded', function() {
                    const backupsSection = document.getElementById('section-backups');
                    if (backupsSection) {
                        const observer = new MutationObserver(function(mutations) {
                            if (backupsSection.style.display !== 'none') {
                                loadBackups();
                            }
                        });
                        observer.observe(backupsSection, { attributes: true, attributeFilter: ['style'] });
                    }
                });
            }

// ========== ФУНКЦИИ ПОИСКА ==========
function searchUsers() {
    const searchTerm = document.getElementById('searchUser').value.toLowerCase().trim();
    const userRows = document.querySelectorAll('.user-card-row');
    let foundCount = 0;
    
    userRows.forEach(row => {
        const rowText = row.textContent.toLowerCase();
        if (searchTerm === '' || rowText.includes(searchTerm)) {
            row.style.display = '';
            foundCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Обновляем счетчик
    const statusEl = document.getElementById('searchStatus');
    if (searchTerm) {
        statusEl.textContent = `Найдено: ${foundCount}`;
        statusEl.style.color = '#2d3748';
        statusEl.style.fontWeight = 'bold';
    } else {
        statusEl.textContent = '';
    }
}

function clearSearch() {
    document.getElementById('searchUser').value = '';
    searchUsers(); // Это скроет сообщение о количестве
}
// ========== КОНЕЦ ФУНКЦИЙ ПОИСКА ==========

            // Регистрируем функции поиска глобально
window.searchUsers = searchUsers;
window.clearSearch = clearSearch;
window.loadNewUsers = loadNewUsers;
window.loadPayments = loadPayments;
if (typeof searchGuests === 'function') window.searchGuests = searchGuests;
if (typeof clearGuestSearch === 'function') window.clearGuestSearch = clearGuestSearch;

            // Загружаем при открытии
            loadStats();
            loadNewUsers();
            loadPayments();
            // loadUsers() и loadGuests() загружаются автоматически при переключении на соответствующие секции
            
            function showCalculatorStats() {
                try {
                    console.log('📊 Загрузка статистики калькулятора...');
                fetch('/admin/calculator-stats-data', {credentials: 'include'})
                        .then(function(r) { return r.json(); })
                        .then(function(stats) {
                            let html = '<h3>📊 Статистика калькулятора неустойки</h3>';
                            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0;">';
                            html += '<div style="background: #f0f7ff; padding: 15px; border-radius: 8px;">';
                            html += '<div style="font-size: 0.9rem; color: #666;">Всего использований</div>';
                            html += '<div style="font-size: 2rem; font-weight: bold; color: #4361ee;">' + stats.total_calculator_uses + '</div>';
                            html += '</div>';
                            html += '<div style="background: #f0f7ff; padding: 15px; border-radius: 8px;">';
                            html += '<div style="font-size: 0.9rem; color: #666;">Пользователей использовали</div>';
                            html += '<div style="font-size: 2rem; font-weight: bold; color: #4361ee;">' + stats.users_with_calculator_use + '/' + stats.total_users + '</div>';
                            html += '</div>';
                            html += '</div>';
                            
                            if (stats.top_users && stats.top_users.length > 0) {
                                html += '<h4>Топ пользователей:</h4>';
                                html += '<div style="overflow-x: auto; -webkit-overflow-scrolling: touch;"><table style="min-width: 500px; width: 100%; border-collapse: collapse;"><thead><tr>';
                                html += '<th style="padding: 10px; background: #4361ee; color: white;">ID</th>';
                                html += '<th style="padding: 10px; background: #4361ee; color: white;">Использований</th>';
                                html += '<th style="padding: 10px; background: #4361ee; color: white;">Последнее</th>';
                                html += '</tr></thead><tbody>';
                                
                                stats.top_users.forEach(function(user) {
                                    html += '<tr>';
                                    html += '<td style="padding: 10px; border-bottom: 1px solid #ddd;">' + user[0] + '</td>';
                                    html += '<td style="padding: 10px; border-bottom: 1px solid #ddd;">' + user[1] + '</td>';
                                    html += '<td style="padding: 10px; border-bottom: 1px solid #ddd;">' + (user[2] || 'Нет данных') + '</td>';
                                    html += '</tr>';
                                });
                                
                                html += '</tbody></table></div>';
                            }
                            
                            const statsEl = document.getElementById('calculatorStats');
                            if (statsEl) {
                                statsEl.innerHTML = html;
                                statsEl.style.display = 'block';
                                console.log('✅ Статистика калькулятора загружена');
                            } else {
                                console.error('❌ Элемент calculatorStats не найден');
                            }
                        })
                        .catch(function(error) {
                            console.error('❌ Ошибка загрузки статистики калькулятора:', error);
                            alert('Ошибка загрузки статистики: ' + error.message);
                        });
                } catch (error) {
                    console.error('❌ Ошибка в showCalculatorStats:', error);
                    alert('Ошибка: ' + error.message);
                }
            }
            
            // Регистрируем функцию глобально СРАЗУ после определения (ВАЖНО!)
            window.showCalculatorStats = showCalculatorStats;
            console.log('✅ showCalculatorStats зарегистрирована глобально:', typeof window.showCalculatorStats);
            
            // Проверка через 1 секунду, что функция действительно доступна
            setTimeout(function() {
                if (typeof window.showCalculatorStats === 'function') {
                    console.log('✅ Проверка: showCalculatorStats доступна глобально');
                } else {
                    console.error('❌ ОШИБКА: showCalculatorStats НЕ доступна глобально!');
                    // Повторная регистрация
                    window.showCalculatorStats = showCalculatorStats;
                }
            }, 1000);
            
            // ========== ФУНКЦИИ ДЛЯ EMAIL-РАССЫЛОК ==========
            function loadEmailCampaigns() {
                fetch('/admin/email-campaigns', {credentials: 'include'})
                    .then(r => r.json())
                    .then(campaigns => {
                        let html = '';
                        if (!campaigns || campaigns.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет созданных рассылок</p>';
                        } else {
                            campaigns.forEach(campaign => {
                                const statusColors = {
                                    'draft': '#a0aec0',
                                    'sending': '#ed8936',
                                    'sent': '#48bb78',
                                    'cancelled': '#f56565'
                                };
                                const statusText = {
                                    'draft': 'Черновик',
                                    'sending': 'Отправляется',
                                    'sent': 'Отправлено',
                                    'cancelled': 'Отменено'
                                };
                                
                                html += `
                                    <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 4px solid ${statusColors[campaign.status] || '#cbd5e0'};">
                                        <div style="display: flex; justify-content: space-between; align-items: start;">
                                            <div style="flex: 1;">
                                                <strong style="font-size: 1.1rem;">${campaign.name}</strong>
                                                <div style="margin-top: 5px; color: #666; font-size: 0.9rem;">
                                                    Тема: ${campaign.subject}
                                </div>
                                                <div style="margin-top: 5px; color: #666; font-size: 0.85rem;">
                                                    Получатели: ${getRecipientFilterText(campaign.recipient_filter)} | 
                                                    Статус: <span style="color: ${statusColors[campaign.status]}; font-weight: 600;">${statusText[campaign.status]}</span> |
                                                    Создано: ${new Date(campaign.created_at).toLocaleString('ru-RU')}
                                                    ${campaign.sent_at ? ' | Отправлено: ' + new Date(campaign.sent_at).toLocaleString('ru-RU') : ''}
                                                </div>
                                            </div>
                                            <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                                                ${campaign.status === 'draft' ? `
                                                    <button onclick="sendCampaign(${campaign.id})" style="background: #48bb78; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">📧 Отправить</button>
                                                    <button onclick="viewCampaignStats(${campaign.id})" style="background: #4299e1; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">📊 Статистика</button>
                                                ` : ''}
                                                ${campaign.status === 'sent' ? `
                                                    <button onclick="viewCampaignStats(${campaign.id})" style="background: #4299e1; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">📊 Статистика</button>
                                                ` : ''}
                                            </div>
                                </div>
                            </div>
                        `;
                            });
                        }
                        document.getElementById('emailCampaignsList').innerHTML = html;
                    });
            }
            // Регистрируем loadEmailCampaigns глобально сразу после определения
            if (typeof loadEmailCampaigns === 'function') {
                window.loadEmailCampaigns = loadEmailCampaigns;
                console.log('✅ loadEmailCampaigns зарегистрирована глобально');
            }
            
            function getRecipientFilterText(filter) {
                const filters = {
                    'all': 'Все зарегистрированные',
                    'free': 'Бесплатный тариф',
                    'paid': 'Платные тарифы',
                    'verified': 'Верифицированные email'
                };
                return filters[filter] || filter;
            }
            
            function createCampaign() {
                const name = document.getElementById('campaignName').value.trim();
                const subject = document.getElementById('campaignSubject').value.trim();
                const htmlContent = document.getElementById('campaignHtmlContent').value.trim();
                const textContent = document.getElementById('campaignTextContent').value.trim();
                const recipientFilter = document.getElementById('campaignRecipients').value;
                
                if (!name || !subject || !htmlContent) {
                    alert('Заполните все обязательные поля!');
                    return;
                }
                
                fetch('/admin/email-campaigns', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({
                        name: name,
                        subject: subject,
                        html_content: htmlContent,
                        text_content: textContent,
                        recipient_filter: recipientFilter
                    })
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Рассылка создана!');
                        // Очищаем форму
                        document.getElementById('campaignName').value = '';
                        document.getElementById('campaignSubject').value = '';
                        document.getElementById('campaignHtmlContent').value = '';
                        document.getElementById('campaignTextContent').value = '';
                        // Обновляем список
                        loadEmailCampaigns();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('❌ Ошибка создания рассылки: ' + err);
                });
            }
            
            function sendCampaign(campaignId) {
                if (!confirm('Отправить рассылку? Это может занять некоторое время.')) {
                    return;
                }
                
                fetch(`/admin/email-campaigns/${campaignId}/send`, {
                    method: 'POST',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert(`✅ Рассылка отправлена!\\nОтправлено: ${result.stats.sent}\\nОшибок: ${result.stats.failed}`);
                        loadEmailCampaigns();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('❌ Ошибка отправки: ' + err);
                });
            }
            
            function viewCampaignStats(campaignId) {
                fetch(`/admin/email-campaigns/${campaignId}/stats`, {credentials: 'include'})
                    .then(r => r.json())
                    .then(stats => {
                        alert(`📊 Статистика рассылки:\\n\\nВсего: ${stats.total}\\nОтправлено: ${stats.sent}\\nОшибок: ${stats.failed}\\nОжидает: ${stats.pending}\\n\\nУспешность: ${stats.success_rate.toFixed(1)}%`);
                    });
            }
            
            function previewCampaign() {
                const htmlContent = document.getElementById('campaignHtmlContent').value.trim();
                if (!htmlContent) {
                    alert('Введите HTML-содержимое письма!');
                    return;
                }
                document.getElementById('previewContent').innerHTML = htmlContent;
                document.getElementById('campaignPreview').style.display = 'block';
            }
            
            function loadRecipientsPreview() {
                const recipientFilter = document.getElementById('campaignRecipients').value;
                if (!recipientFilter) return;
                
                fetch('/admin/email-campaigns/recipients-preview?filter=' + recipientFilter, {credentials: 'include'})
                    .then(r => r.json())
                    .then(result => {
                        if (result && result.success) {
                            let html = `<p><strong>Количество получателей: ${result.count}</strong></p>`;
                            if (result.recipients && result.recipients.length > 0) {
                                html += '<ul style="list-style: none; padding: 0;">';
                                result.recipients.slice(0, 20).forEach(recipient => {
                                    html += `<li style="padding: 5px; border-bottom: 1px solid #eee;">${recipient.email} (${recipient.plan || 'free'})</li>`;
                                });
                                if (result.recipients.length > 20) {
                                    html += `<li style="padding: 5px; color: #666;">... и еще ${result.recipients.length - 20}</li>`;
                                }
                                html += '</ul>';
                            } else {
                                html += '<p style="color: #999;">Нет получателей для выбранного фильтра.</p>';
                            }
                            document.getElementById('recipientsList').innerHTML = html;
                            document.getElementById('recipientsPreview').style.display = 'block';
                        } else {
                            document.getElementById('recipientsList').innerHTML = '<p style="color: #999;">Ошибка загрузки получателей.</p>';
                            document.getElementById('recipientsPreview').style.display = 'block';
                        }
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки получателей:', err);
                        document.getElementById('recipientsList').innerHTML = '<p style="color: #999;">Не удалось загрузить список получателей. Проверьте фильтр.</p>';
                        document.getElementById('recipientsPreview').style.display = 'block';
                    });
            }
            
            function insertEmailTemplate() {
                const template = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4361ee, #7209b7); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #4361ee; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 DocScan AI</h1>
            <p>Заголовок письма</p>
                                </div>
        <div class="content">
            <p>Здравствуйте, {email}!</p>
            
            <p>Текст вашего письма здесь. Используйте переменные {user_id}, {plan}, {plan_name} для персонализации.</p>
            
            <div style="text-align: center;">
                <a href="https://docscan-ai.ru" class="button">Перейти на сайт</a>
            </div>
            
            <p>С уважением,<br>Команда DocScan AI</p>
        </div>
        <div class="footer">
            <p>© 2025 DocScan AI. Все права защищены.</p>
            <p><a href="https://docscan-ai.ru/unsubscribe" style="color: #666;">Отписаться от рассылок</a></p>
        </div>
    </div>
</body>
</html>`;
                document.getElementById('campaignHtmlContent').value = template;
            }
            
            // Загружаем данные при открытии
            loadStats();
            loadNewUsers();
            loadPayments();
            
            // Загружаем историю уведомлений при открытии секции
            if (document.getElementById('notificationsHistory')) {
                loadNotificationsHistory();
            }
            
            // Инициализируем TinyMCE для статей при загрузке страницы (если раздел статей доступен)
            
            // ========== ИНИЦИАЛИЗАЦИЯ TINYMCE РЕДАКТОРА ==========
            let tinymceEditor = null;
            let isHtmlMode = false;
            
            function initTinyMCE() {
                const loadingEl = document.getElementById('tinymce-loading');
                if (loadingEl) {
                    loadingEl.textContent = '⏳ Инициализация редактора...';
                }
                
                if (typeof tinymce !== 'undefined') {
                    console.log('🚀 Инициализация TinyMCE...');
                    tinymce.init({
                        selector: '#articleHtmlContent',
                        height: 600,
                        // Язык отключен, так как CDN не поддерживает русский язык
                        // language: 'ru',
                        menubar: true,
                        plugins: [
                            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
                            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                            'insertdatetime', 'media', 'table', 'help', 'wordcount',
                            'emoticons', 'codesample', 'pagebreak', 'nonbreaking',
                            'directionality'
                        ],
                        toolbar: 'undo redo | blocks | ' +
                            'bold italic underline strikethrough forecolor backcolor | ' +
                            'alignleft aligncenter alignright alignjustify | ' +
                            'bullist numlist outdent indent | ' +
                            'removeformat | link image media table code | ' +
                            'insertdatetime charmap emoticons pagebreak | ' +
                            'visualblocks visualchars fullscreen preview | ' +
                            'fontfamily fontsize | ' +
                            'codesample | ' +
                            'searchreplace help',
                        content_style: 'body { font-family: Inter, Arial, sans-serif; font-size: 16px; line-height: 1.6; }',
                        font_family_formats: 'Inter=Inter, sans-serif; Arial=Arial, sans-serif; Times New Roman=Times New Roman, serif; Courier New=Courier New, monospace;',
                        font_size_formats: '8pt 10pt 12pt 14pt 16pt 18pt 24pt 36pt 48pt',
                        block_formats: 'Параграф=p; Заголовок 1=h1; Заголовок 2=h2; Заголовок 3=h3; Заголовок 4=h4; Заголовок 5=h5; Заголовок 6=h6; Предформатированный=pre',
                        image_advtab: true,
                        file_picker_types: 'image',
                        automatic_uploads: true,
                        images_upload_url: '/admin/articles/upload-image',
                        images_upload_handler: function (blobInfo, progress) {
                            return new Promise(function (resolve, reject) {
                                var xhr = new XMLHttpRequest();
                                xhr.withCredentials = true;
                                xhr.open('POST', '/admin/articles/upload-image');
                                
                                xhr.upload.onprogress = function (e) {
                                    progress(e.loaded / e.total * 100);
                                };
                                
                                xhr.onload = function () {
                                    if (xhr.status === 403) {
                                        reject({ message: 'HTTP Error: ' + xhr.status, remove: true });
                                        return;
                                    }
                                    
                                    if (xhr.status < 200 || xhr.status >= 300) {
                                        reject('HTTP Error: ' + xhr.status);
                                        return;
                                    }
                                    
                                    var json = JSON.parse(xhr.responseText);
                                    
                                    if (!json || typeof json.location != 'string') {
                                        reject('Invalid JSON: ' + xhr.responseText);
                                        return;
                                    }
                                    
                                    resolve(json.location);
                                };
                                
                                xhr.onerror = function () {
                                    reject('Image upload failed due to a XHR Transport error. Code: ' + xhr.status);
                                };
                                
                                var formData = new FormData();
                                formData.append('file', blobInfo.blob(), blobInfo.filename());
                                
                                xhr.send(formData);
                            });
                        },
                        setup: function (editor) {
                            tinymceEditor = editor;
                            editor.on('init', function () {
                                console.log('✅ TinyMCE редактор инициализирован успешно');
                                const loadingEl = document.getElementById('tinymce-loading');
                                if (loadingEl) {
                                    loadingEl.textContent = '✅ Визуальный редактор готов!';
                                    setTimeout(function() {
                                        loadingEl.style.display = 'none';
                                    }, 2000);
                                }
                                // Убеждаемся, что визуальный редактор видим
                                document.getElementById('tinymce-container').style.display = 'block';
                                document.getElementById('html-editor-container').style.display = 'none';
                            });
                            
                            editor.on('error', function(e) {
                                console.error('❌ Ошибка TinyMCE:', e);
                                const loadingEl = document.getElementById('tinymce-loading');
                                if (loadingEl) {
                                    loadingEl.textContent = '❌ Ошибка загрузки редактора. Используйте HTML-режим.';
                                    loadingEl.style.color = '#f56565';
                                }
                            });
                        },
                        branding: false,
                        promotion: false
                    });
                } else {
                    console.error('❌ TinyMCE не загружен. Используйте HTML-режим.');
                    const loadingEl = document.getElementById('tinymce-loading');
                    if (loadingEl) {
                        loadingEl.textContent = '❌ Визуальный редактор не загрузился. Используйте HTML-режим.';
                        loadingEl.style.color = '#f56565';
                    }
                }
            }
            
            function toggleEditorMode() {
                const container = document.getElementById('tinymce-container');
                const htmlContainer = document.getElementById('html-editor-container');
                const statusEl = document.getElementById('editorStatus');
                const btn = document.getElementById('editorModeBtn');
                
                if (!container || !htmlContainer || !statusEl || !btn) {
                    console.error('❌ Не найдены элементы для переключения режима');
                    return;
                }
                
                if (isHtmlMode) {
                    // Переключаемся на визуальный режим
                    console.log('🔄 Переключение на визуальный режим...');
                    isHtmlMode = false;
                    const htmlContent = document.getElementById('articleHtmlContentRaw').value;
                    
                    if (tinymceEditor) {
                        tinymceEditor.setContent(htmlContent || '');
                        container.style.display = 'block';
                        htmlContainer.style.display = 'none';
                        statusEl.textContent = 'Режим: Визуальный редактор';
                        btn.textContent = '</> Переключить в HTML';
                        console.log('✅ Визуальный режим включен');
                    } else {
                        console.warn('⚠️ TinyMCE редактор не инициализирован, пробую инициализировать...');
                        initTinyMCE();
                        setTimeout(function() {
                            if (tinymceEditor) {
                                tinymceEditor.setContent(htmlContent || '');
                                container.style.display = 'block';
                                htmlContainer.style.display = 'none';
                                statusEl.textContent = 'Режим: Визуальный редактор';
                                btn.textContent = '</> Переключить в HTML';
                            } else {
                                alert('❌ Не удалось загрузить визуальный редактор. Используйте HTML-режим.');
                            }
                        }, 1500);
                    }
                } else {
                    // Переключаемся на HTML-режим
                    console.log('🔄 Переключение на HTML-режим...');
                    isHtmlMode = true;
                    let htmlContent = '';
                    
                    if (tinymceEditor) {
                        htmlContent = tinymceEditor.getContent();
                    } else {
                        htmlContent = document.getElementById('articleHtmlContent') ? document.getElementById('articleHtmlContent').value : '';
                    }
                    
                    document.getElementById('articleHtmlContentRaw').value = htmlContent;
                    container.style.display = 'none';
                    htmlContainer.style.display = 'block';
                    statusEl.textContent = 'Режим: HTML-редактор';
                    btn.textContent = '📝 Переключить в визуальный';
                    console.log('✅ HTML-режим включен');
                }
            }
            
            function insertArticleTemplate() {
                const template = `<style>
        .article-content h1 { color: #4361ee; border-bottom: 2px solid #4361ee; padding-bottom: 10px; margin-top: 0; }
        .article-content h2 { color: #7209b7; margin-top: 30px; }
        .article-content h3 { color: #4cc9f0; }
        .article-content .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .article-content .info { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .article-content .success { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .article-content ul, .article-content ol { margin: 15px 0; padding-left: 30px; }
        .article-content li { margin: 8px 0; }
        .article-content strong { color: #4361ee; }
        .article-content blockquote { border-left: 4px solid #7209b7; padding-left: 20px; margin: 20px 0; color: #666; font-style: italic; }
        .article-content table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .article-content th, .article-content td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .article-content th { background: #4361ee; color: white; }
        .article-content tr:nth-child(even) { background: #f8f9fa; }
        .article-content img { max-width: 100%; height: auto; border-radius: 8px; margin: 20px 0; }
        .article-content code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
    </style>
    
    <h1>Заголовок статьи</h1>
    
    <p>Введение к статье. Опишите, о чем пойдет речь в статье.</p>
    
    <h2>Первый раздел</h2>
    
    <p>Основной текст статьи. Здесь вы пишете основное содержание.</p>
    
    <div class="warning">
        <strong>⚠️ Важно:</strong> Важное предупреждение или информация.
    </div>
    
    <h3>Подраздел</h3>
    
    <ul>
        <li>Пункт списка 1</li>
        <li>Пункт списка 2</li>
        <li>Пункт списка 3</li>
    </ul>
    
    <h2>Второй раздел</h2>
    
    <div class="info">
        <strong>💡 Совет:</strong> Полезная информация для читателя.
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Колонка 1</th>
                <th>Колонка 2</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Данные 1</td>
                <td>Данные 2</td>
            </tr>
            <tr>
                <td>Данные 3</td>
                <td>Данные 4</td>
            </tr>
        </tbody>
    </table>
    
    <blockquote>
        Цитата или важное замечание в статье.
    </blockquote>
    
    <h2>Заключение</h2>
    
    <p>Подведение итогов статьи.</p>
    
    <div class="success">
        <strong>✅ Вывод:</strong> Основной вывод из статьи.
    </div>
    
    <div style="text-align: center; margin: 40px 0;">
        <a href="/articles" style="font-size: 1.1rem; padding: 15px 30px; background: #4361ee; color: white; border-radius: 50px; text-decoration: none; display: inline-block; transition: all 0.3s;">
            ← Вернуться к статьям
        </a>
    </div>`;
                
                if (tinymceEditor && !isHtmlMode) {
                    tinymceEditor.setContent(template);
                } else {
                    document.getElementById('articleHtmlContentRaw').value = template;
                }
                alert('✅ Шаблон статьи вставлен! Отредактируйте его под свою статью.');
            }
            
            function getArticleContent() {
                if (isHtmlMode) {
                    return document.getElementById('articleHtmlContentRaw').value;
                } else {
                    if (tinymceEditor) {
                        return tinymceEditor.getContent();
                    } else {
                        return document.getElementById('articleHtmlContent').value;
                    }
                }
            }
            
            function setArticleContent(content) {
                if (tinymceEditor && !isHtmlMode) {
                    tinymceEditor.setContent(content || '');
                } else {
                    document.getElementById('articleHtmlContentRaw').value = content || '';
                    if (document.getElementById('articleHtmlContent')) {
                        document.getElementById('articleHtmlContent').value = content || '';
                    }
                }
            }
            
            // Инициализируем редактор при загрузке
            let editorInitAttempts = 0;
            const maxAttempts = 20; // 10 секунд максимум
            
            function initEditorWhenReady() {
                editorInitAttempts++;
                
                if (typeof tinymce !== 'undefined' && typeof tinymce.init === 'function') {
                    console.log('✅ TinyMCE скрипт загружен, инициализирую редактор...');
                    try {
                        initTinyMCE();
                    } catch (e) {
                        console.error('❌ Ошибка инициализации TinyMCE:', e);
                        const loadingEl = document.getElementById('tinymce-loading');
                        if (loadingEl) {
                            loadingEl.textContent = '❌ Ошибка инициализации. Используйте HTML-режим.';
                            loadingEl.style.color = '#f56565';
                        }
                    }
                } else if (editorInitAttempts < maxAttempts) {
                    console.log('⏳ Ожидание загрузки TinyMCE... (попытка ' + editorInitAttempts + '/' + maxAttempts + ')');
                    setTimeout(initEditorWhenReady, 500);
                } else {
                    console.error('❌ TinyMCE не загрузился за отведенное время');
                    const loadingEl = document.getElementById('tinymce-loading');
                    if (loadingEl) {
                        loadingEl.textContent = '❌ Визуальный редактор не загрузился. Используйте HTML-режим.';
                        loadingEl.style.color = '#f56565';
                    }
                    // Автоматически переключаемся на HTML-режим
                    document.getElementById('tinymce-container').style.display = 'none';
                    document.getElementById('html-editor-container').style.display = 'block';
                    document.getElementById('editorStatus').textContent = 'Режим: HTML-редактор (визуальный недоступен)';
                    document.getElementById('editorModeBtn').textContent = '📝 Визуальный редактор недоступен';
                    document.getElementById('editorModeBtn').disabled = true;
                    isHtmlMode = true;
                }
            }
            
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(initEditorWhenReady, 1500);
                });
            } else {
                setTimeout(initEditorWhenReady, 1500);
            }
            
            // ========== ФУНКЦИИ ДЛЯ РАБОТЫ СО СТАТЬЯМИ ==========
            function loadArticles() {
                const statusFilter = document.getElementById('articleStatusFilter') ? document.getElementById('articleStatusFilter').value : '';
                let url = '/admin/articles';
                if (statusFilter) {
                    url += '?status=' + statusFilter;
                }
                
                fetch(url, {credentials: 'include'})
                    .then(r => r.json())
                    .then(articles => {
                        const articlesListEl = document.getElementById('articlesList');
                        if (!articlesListEl) return;
                        
                        let html = '';
                        if (!articles || articles.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет созданных статей</p>';
                        } else {
                            articles.forEach(article => {
                                const statusColors = {
                                    'draft': '#a0aec0',
                                    'published': '#48bb78',
                                    'archived': '#f56565'
                                };
                                const statusText = {
                                    'draft': 'Черновик',
                                    'published': 'Опубликована',
                                    'archived': 'В архиве'
                                };
                                
                                html += `
                                    <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 4px solid ${statusColors[article.status] || '#cbd5e0'};">
                                        <div style="display: flex; justify-content: space-between; align-items: start;">
                                            <div style="flex: 1;">
                                                <div style="font-size: 1.5rem; margin-bottom: 5px;">${article.icon || '📄'} <strong>${article.title}</strong></div>
                                                <div style="margin-top: 5px; color: #666; font-size: 0.9rem;">
                                                    URL: <code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">/articles/${article.slug}</code>
                                                </div>
                                                <div style="margin-top: 5px; color: #666; font-size: 0.85rem;">
                                                    Статус: <span style="color: ${statusColors[article.status]}; font-weight: 600;">${statusText[article.status]}</span> |
                                                    Просмотров: ${article.views_count || 0} |
                                                    Создано: ${new Date(article.created_at).toLocaleString('ru-RU')}
                                                    ${article.published_at ? ' | Опубликовано: ' + new Date(article.published_at).toLocaleString('ru-RU') : ''}
                                                </div>
                                                ${article.description ? `<div style="margin-top: 8px; color: #666; font-size: 0.9rem;">${article.description}</div>` : ''}
                                            </div>
                                            <div style="display: flex; gap: 5px; flex-wrap: wrap; align-items: start;">
                                                ${article.status === 'draft' ? `<button onclick="publishArticle(${article.id})" style="background: #48bb78; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">📢 Опубликовать</button>` : ''}
                                                ${article.status === 'published' ? `<button onclick="unpublishArticle(${article.id})" style="background: #ed8936; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">🔒 Снять</button>` : ''}
                                                <button onclick="editArticle(${article.id})" style="background: #4299e1; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">✏️ Редактировать</button>
                                                <button onclick="viewArticle('${article.slug}')" style="background: #667eea; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">👁️ Просмотр</button>
                                                <button onclick="deleteArticleConfirm(${article.id})" style="background: #f56565; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">🗑️ Удалить</button>
                                            </div>
                                </div>
                            </div>
                        `;
                            });
                        }
                        articlesListEl.innerHTML = html;
                    });
            }
            // Регистрируем loadArticles глобально сразу после определения
            if (typeof loadArticles === 'function') {
                window.loadArticles = loadArticles;
                console.log('✅ loadArticles зарегистрирована глобально');
            }
            
            function createArticle() {
                const title = document.getElementById('articleTitle').value.trim();
                const slug = document.getElementById('articleSlug').value.trim();
                const htmlContent = getArticleContent().trim();  // Используем функцию для получения контента
                const description = document.getElementById('articleDescription').value.trim();
                const icon = document.getElementById('articleIcon').value.trim();
                const category = document.getElementById('articleCategory').value.trim();
                const metaKeywords = document.getElementById('articleMetaKeywords').value.trim();
                const metaDescription = document.getElementById('articleMetaDescription').value.trim();
                
                if (!title || !slug || !htmlContent) {
                    alert('Заполните все обязательные поля! (заголовок, URL, содержимое)');
                    return;
                }
                
                fetch('/admin/articles', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({
                        title: title,
                        slug: slug,
                        html_content: htmlContent,
                        description: description,
                        icon: icon,
                        category: category,
                        meta_keywords: metaKeywords,
                        meta_description: metaDescription
                    })
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Статья создана!');
                        clearArticleForm();
                        loadArticles();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('❌ Ошибка создания статьи: ' + err);
                });
            }
            
            function clearArticleForm() {
                document.getElementById('articleTitle').value = '';
                document.getElementById('articleSlug').value = '';
                setArticleContent('');  // Используем функцию для очистки контента
                document.getElementById('articleDescription').value = '';
                document.getElementById('articleIcon').value = '';
                document.getElementById('articleCategory').value = '';
                document.getElementById('articleMetaKeywords').value = '';
                document.getElementById('articleMetaDescription').value = '';
                const updateBtn = document.getElementById('updateArticleBtn');
                if (updateBtn) updateBtn.remove();
                // Переключаемся на визуальный режим
                if (isHtmlMode) {
                    toggleEditorMode();
                }
            }
            
            function publishArticle(articleId) {
                if (!confirm('Опубликовать статью?')) return;
                
                fetch(`/admin/articles/${articleId}/publish`, {
                    method: 'POST',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Статья опубликована!');
                        loadArticles();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            function unpublishArticle(articleId) {
                if (!confirm('Снять статью с публикации?')) return;
                
                fetch(`/admin/articles/${articleId}/unpublish`, {
                    method: 'POST',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Статья снята с публикации!');
                        loadArticles();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            function editArticle(articleId) {
                fetch(`/admin/articles/${articleId}`, {credentials: 'include'})
                    .then(r => r.json())
                    .then(result => {
                        if (result.success) {
                            const article = result.article;
                            document.getElementById('articleTitle').value = article.title || '';
                            document.getElementById('articleSlug').value = article.slug || '';
                            setArticleContent(article.html_content || '');  // Используем функцию для установки контента
                            document.getElementById('articleDescription').value = article.description || '';
                            document.getElementById('articleIcon').value = article.icon || '';
                            document.getElementById('articleCategory').value = article.category || '';
                            document.getElementById('articleMetaKeywords').value = article.meta_keywords || '';
                            document.getElementById('articleMetaDescription').value = article.meta_description || '';
                            
                            // Переключаемся на визуальный режим если был HTML-режим
                            if (isHtmlMode) {
                                toggleEditorMode();
                            }
                            
                            const createBtn = document.querySelector('button[onclick="createArticle()"]');
                            if (createBtn && !document.getElementById('updateArticleBtn')) {
                                const btn = document.createElement('button');
                                btn.id = 'updateArticleBtn';
                                btn.textContent = '💾 Сохранить изменения';
                                btn.style.cssText = 'background: #4299e1; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;';
                                btn.onclick = () => updateArticle(articleId);
                                createBtn.parentElement.insertBefore(btn, createBtn);
                            }
                            
                            alert('Статья загружена в форму для редактирования. Нажмите "Сохранить изменения" после правок.');
                        } else {
                            alert('❌ Ошибка загрузки статьи');
                        }
                    });
            }
            
            function updateArticle(articleId) {
                const title = document.getElementById('articleTitle').value.trim();
                const slug = document.getElementById('articleSlug').value.trim();
                const htmlContent = getArticleContent().trim();  // Используем функцию для получения контента
                const description = document.getElementById('articleDescription').value.trim();
                const icon = document.getElementById('articleIcon').value.trim();
                const category = document.getElementById('articleCategory').value.trim();
                const metaKeywords = document.getElementById('articleMetaKeywords').value.trim();
                const metaDescription = document.getElementById('articleMetaDescription').value.trim();
                
                fetch(`/admin/articles/${articleId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({
                        title: title,
                        slug: slug,
                        html_content: htmlContent,
                        description: description,
                        icon: icon,
                        category: category,
                        meta_keywords: metaKeywords,
                        meta_description: metaDescription
                    })
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Статья обновлена!');
                        const btn = document.getElementById('updateArticleBtn');
                        if (btn) btn.remove();
                        clearArticleForm();
                        loadArticles();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            function deleteArticleConfirm(articleId) {
                if (!confirm('Удалить статью? Это действие нельзя отменить!')) return;
                
                fetch(`/admin/articles/${articleId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Статья удалена!');
                        loadArticles();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                });
            }
            
            function viewArticle(slug) {
                window.open(`/articles/${slug}`, '_blank');
            }
            
            // Загружаем статьи при открытии (если есть раздел)
            if (document.getElementById('articlesList')) {
                loadArticles();
            }
            
            // ========== ФУНКЦИИ ДЛЯ ПАРТНЕРСКОЙ ПРОГРАММЫ ==========
            function loadPartners() {
                fetch('/admin/partners', {credentials: 'include'})
                    .then(r => r.json())
                    .then(partners => {
                        const listEl = document.getElementById('partnersList');
                        if (!listEl) return;
                        
                        if (!partners || partners.length === 0) {
                            listEl.innerHTML = '<p style="color: #999; padding: 20px;">Нет партнеров</p>';
                            return;
                        }
                        
                        html = '<div style="overflow-x: auto; -webkit-overflow-scrolling: touch;"><table style="min-width: 900px; width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">ID</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Email</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Реферальный код</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Приглашено</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Покупок</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Ожидает выплаты</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Реквизиты</th></tr></thead><tbody>';
                        
                        partners.forEach(partner => {
                            const paymentDetails = partner.payment_details ? JSON.parse(partner.payment_details) : null;
                            html += `<tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 12px;">${partner.user_id}</td>
                                <td style="padding: 12px;">${partner.email || 'Нет email'}</td>
                                <td style="padding: 12px;"><code style="background: #f7fafc; padding: 4px 8px; border-radius: 4px;">${partner.referral_code || 'Не сгенерирован'}</code></td>
                                <td style="padding: 12px;">${partner.invited_count || 0}</td>
                                <td style="padding: 12px;">${partner.purchases_count || 0}</td>
                                <td style="padding: 12px; font-weight: 600; color: #48bb78;">${(partner.pending_amount || 0).toFixed(2)} ₽</td>
                                <td style="padding: 12px;">
                                    ${paymentDetails ? `
                                        <div style="font-size: 0.9rem;">
                                            <strong>Способ:</strong> ${paymentDetails.method || 'Не указан'}<br>
                                            <strong>Реквизиты:</strong> ${paymentDetails.details || 'Не указаны'}<br>
                                            <strong>Контакт:</strong> ${paymentDetails.contact || 'Не указан'}
                                        </div>
                                    ` : '<span style="color: #999;">Не указаны</span>'}
                                </td>
                            </tr>`;
                        });
                        
                        html += '</tbody></table></div>';
                        listEl.innerHTML = html;
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки партнеров:', err);
                        document.getElementById('partnersList').innerHTML = '<p style="color: #f56565;">Ошибка загрузки данных</p>';
                    });
            }
            // Регистрируем loadPartners глобально сразу после определения
            if (typeof loadPartners === 'function') {
                window.loadPartners = loadPartners;
                console.log('✅ loadPartners зарегистрирована глобально');
            }
            
            function loadReferrals() {
                fetch('/admin/referrals', {credentials: 'include'})
                    .then(r => r.json())
                    .then(referrals => {
                        const listEl = document.getElementById('referralsList');
                        if (!listEl) return;
                        
                        if (!referrals || referrals.length === 0) {
                            listEl.innerHTML = '<p style="color: #999; padding: 20px;">Нет приглашений</p>';
                            return;
                        }
                        
                        html = '<div style="overflow-x: auto; -webkit-overflow-scrolling: touch;"><table style="min-width: 600px; width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Кто пригласил</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Кого пригласили</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата приглашения</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата регистрации</th></tr></thead><tbody>';
                        
                        referrals.forEach(ref => {
                            html += `<tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 12px;">${ref.referrer_id}</td>
                                <td style="padding: 12px;">${ref.invited_user_id}</td>
                                <td style="padding: 12px;">${new Date(ref.created_at).toLocaleString('ru-RU')}</td>
                                <td style="padding: 12px;">${ref.registered_at ? new Date(ref.registered_at).toLocaleString('ru-RU') : 'Не зарегистрирован'}</td>
                            </tr>`;
                        });
                        
                        html += '</tbody></table></div>';
                        listEl.innerHTML = html;
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки приглашений:', err);
                        document.getElementById('referralsList').innerHTML = '<p style="color: #f56565;">Ошибка загрузки данных</p>';
                    });
            }
            // Регистрируем loadReferrals глобально сразу после определения
            if (typeof loadReferrals === 'function') {
                window.loadReferrals = loadReferrals;
                console.log('✅ loadReferrals зарегистрирована глобально');
            }
            
            function loadRewards() {
                fetch('/admin/rewards', {credentials: 'include'})
                    .then(r => r.json())
                    .then(rewards => {
                        const listEl = document.getElementById('rewardsList');
                        if (!listEl) return;
                        
                        if (!rewards || rewards.length === 0) {
                            listEl.innerHTML = '<p style="color: #999; padding: 20px;">Нет вознаграждений</p>';
                            return;
                        }
                        
                        html = '<div style="overflow-x: auto; -webkit-overflow-scrolling: touch;"><table style="min-width: 900px; width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Партнер</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Приглашенный</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Сумма покупки</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Вознаграждение</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Статус</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Действия</th></tr></thead><tbody>';
                        
                        rewards.forEach(reward => {
                            const statusColor = reward.status === 'paid' ? '#48bb78' : '#ed8936';
                            const statusText = reward.status === 'paid' ? 'Выплачено' : 'Ожидает выплаты';
                            html += `<tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 12px;">${reward.partner_id}</td>
                                <td style="padding: 12px;">${reward.invited_user_id}</td>
                                <td style="padding: 12px;">${reward.purchase_amount.toFixed(2)} ₽</td>
                                <td style="padding: 12px; font-weight: 600; color: #48bb78;">${reward.reward_amount.toFixed(2)} ₽ (${reward.reward_percent}%)</td>
                                <td style="padding: 12px; color: ${statusColor}; font-weight: 600;">${statusText}</td>
                                <td style="padding: 12px;">${new Date(reward.created_at).toLocaleString('ru-RU')}</td>
                                <td style="padding: 12px;">
                                    ${reward.status === 'pending' ? `<button onclick="markRewardPaid(${reward.id})" style="background: #48bb78; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">✅ Отметить как выплачено</button>` : reward.paid_at ? `Выплачено: ${new Date(reward.paid_at).toLocaleString('ru-RU')}` : ''}
                                </td>
                            </tr>`;
                        });
                        
                        html += '</tbody></table></div>';
                        listEl.innerHTML = html;
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки вознаграждений:', err);
                        document.getElementById('rewardsList').innerHTML = '<p style="color: #f56565;">Ошибка загрузки данных</p>';
                    });
            }
            // Регистрируем loadRewards глобально сразу после определения
            if (typeof loadRewards === 'function') {
                window.loadRewards = loadRewards;
                console.log('✅ loadRewards зарегистрирована глобально');
            }
            
            function markRewardPaid(rewardId) {
                if (!confirm('Отметить вознаграждение как выплаченное?')) return;
                
                fetch(`/admin/rewards/${rewardId}/mark-paid`, {
                    method: 'POST',
                    credentials: 'include'
                })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        alert('✅ Вознаграждение отмечено как выплаченное');
                        loadRewards();
                    } else {
                        alert('❌ Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('❌ Ошибка соединения');
                });
            }
            
            // Регистрируем все функции глобально после их определения
            if (typeof registerGlobalFunctions === 'function') {
                registerGlobalFunctions();
            } else {
                // Если функция еще не определена, регистрируем основные функции вручную
                if (typeof showCalculatorStats === 'function') {
                    window.showCalculatorStats = showCalculatorStats;
                }
                if (typeof loadStats === 'function') {
                    window.loadStats = loadStats;
                }
                if (typeof loadUsers === 'function') {
                    window.loadUsers = loadUsers;
                }
                if (typeof loadGuests === 'function') {
                    window.loadGuests = loadGuests;
                }
                if (typeof loadBots === 'function') {
                    window.loadBots = loadBots;
                }
                if (typeof searchBots === 'function') {
                    window.searchBots = searchBots;
                }
                if (typeof clearBotSearch === 'function') {
                    window.clearBotSearch = clearBotSearch;
                }
                if (typeof loadArticles === 'function') {
                    window.loadArticles = loadArticles;
                }
                if (typeof createArticle === 'function') {
                    window.createArticle = createArticle;
                }
                if (typeof loadNews === 'function') {
                    window.loadNews = loadNews;
                }
                if (typeof showNewsForm === 'function') {
                    window.showNewsForm = showNewsForm;
                }
                if (typeof editNews === 'function') {
                    window.editNews = editNews;
                }
                if (typeof saveNews === 'function') {
                    window.saveNews = saveNews;
                }
                if (typeof cancelNewsForm === 'function') {
                    window.cancelNewsForm = cancelNewsForm;
                }
                if (typeof deleteNews === 'function') {
                    window.deleteNews = deleteNews;
                }
                if (typeof createCampaign === 'function') {
                    window.createCampaign = createCampaign;
                }
                if (typeof sendAdminNotification === 'function') {
                    window.sendAdminNotification = sendAdminNotification;
                }
                if (typeof loadNotificationsHistory === 'function') {
                    window.loadNotificationsHistory = loadNotificationsHistory;
                }
                console.log('✅ Функции зарегистрированы глобально (fallback)');
            }
            
                // Финальная регистрация всех функций глобально
                setTimeout(function() {
                    const functionNames = [
                        'loadUsers', 'loadGuests', 'loadBots', 'loadEmailCampaigns', 
                        'loadArticles', 'loadPartners', 'loadReferrals', 'loadRewards',
                        'loadNews', 'loadFullNews', 'loadQuestions', 'loadBackups',
                        'loadNotificationsHistory', 'loadStats', 'loadWhitelistedIPs'
                    ];
                    
                    functionNames.forEach(funcName => {
                        try {
                            // Пытаемся получить функцию из локальной области видимости
                            const func = (function() {
                                try {
                                    return eval('typeof ' + funcName + ' !== "undefined" ? ' + funcName + ' : null');
                                } catch(e) {
                                    return null;
                                }
                            })();
                            
                            if (func && typeof func === 'function') {
                                window[funcName] = func;
                                console.log('✅ ' + funcName + ' зарегистрирована глобально');
                            }
                        } catch(e) {
                            console.warn('⚠️ Не удалось зарегистрировать ' + funcName + ':', e);
                        }
                    });
            
            console.log('✅ Все скрипты загружены и функции зарегистрированы');
                }, 100);
        </script>
        -->
    </body>
    </html>
    """

@admin_bp.route('/users')
@require_admin_auth
def get_all_users():
    """Получить всех пользователей (отсортированных по дате создания, новые сначала)"""
    from app import app
    from models.sqlite_users import AnalysisHistory
    from datetime import date
    
    # Получаем пользователей из SQLite (уже отсортированы по created_at DESC)
    users_list = app.user_manager.get_all_users()
    
    # Получаем сегодняшнюю дату для фильтрации анализов
    today = date.today().isoformat()
    
    # Конвертируем в dict для совместимости, сохраняя порядок
    users_dict = {}
    for user in users_list:
        users_dict[user.user_id] = user.to_dict()
    
    # Создаем менеджер IP-лимитов
    ip_manager = IPLimitManager()
    
    # Добавляем IP-адреса и анализы за сегодня к каждому пользователю
    for user_id, user_data in users_dict.items():
        user_ip = "Не определен"
        
        # Ищем IP пользователя в данных IP-лимитов
        for ip, ip_data in ip_manager.ip_limits.items():
            if (ip_data.get('user_id') == user_id or 
                ip_data.get('last_user') == user_id):
                user_ip = ip
                break
        
        user_data['ip_address'] = user_ip
        
        # Подсчитываем реальные анализы за сегодня из AnalysisHistory
        analyses_today = AnalysisHistory.query.filter(
            AnalysisHistory.user_id == user_id,
            AnalysisHistory.created_at.like(f'{today}%')
        ).count()
        
        user_data['analyses_today'] = analyses_today
    
    # Возвращаем словарь - порядок сохранится в Python 3.7+ и при использовании OrderedDict
    # Но для надежности также добавим сортировку на клиенте
    return jsonify(users_dict)

@admin_bp.route('/set-plan', methods=['POST'])
@require_admin_auth
def admin_set_plan():
    """Установить тариф пользователю"""
    from app import app
    
    try:
        data = request.json
        user_id = data.get('user_id')
        plan = data.get('plan')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Укажите ID пользователя'})
        
        result = app.user_manager.set_user_plan(user_id, plan)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Ошибка установки тарифа: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/create-user', methods=['POST'])
@require_admin_auth
def admin_create_user():
    """Создать нового пользователя"""
    from app import app
    
    try:
        data = request.json
        user_id = data.get('user_id')
        
        # Если ID не указан, генерируем случайный
        if not user_id:
            user_id = str(uuid.uuid4())[:8]
        
        # Проверяем существует ли пользователь
        existing_user = app.user_manager.get_user(user_id)
        if existing_user:
            return jsonify({'success': False, 'error': 'Пользователь уже существует'})
        
        # Создаем пользователя через SQLite
        user_data = {
            'user_id': user_id,
            'plan': 'free',
            'used_today': 0,
            'last_reset': datetime.now().date().isoformat(),
            'total_used': 0,
            'created_at': datetime.now().isoformat(),
            'plan_expires': None,
            'ip_address': 'Не определен'
        }
        app.user_manager.create_user(user_data)
        
        logger.info(f"👤 Администратор создал пользователя: {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Пользователь {user_id} создан с бесплатным тарифом',
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания пользователя: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/add-whitelist-ip', methods=['POST'])
@require_admin_auth
def admin_add_whitelist_ip():
    """Добавить IP-адрес в белый список для пользователя"""
    from app import app
    
    try:
        data = request.json
        user_id = data.get('user_id')
        ip_address = data.get('ip_address')
        description = data.get('description')
        
        if not user_id or not ip_address:
            return jsonify({'success': False, 'error': 'Укажите ID пользователя и IP-адрес'})
        
        # Получаем ID администратора из сессии (если есть)
        admin_user_id = session.get('user_id', 'admin')
        
        result = app.user_manager.add_whitelisted_ip(
            user_id=user_id,
            ip_address=ip_address,
            description=description,
            created_by=admin_user_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления IP в белый список: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/remove-whitelist-ip', methods=['POST'])
@require_admin_auth
def admin_remove_whitelist_ip():
    """Удалить IP-адрес из белого списка"""
    from app import app
    
    try:
        data = request.json
        ip_id = data.get('ip_id')
        
        if not ip_id:
            return jsonify({'success': False, 'error': 'Укажите ID IP-адреса'})
        
        result = app.user_manager.remove_whitelisted_ip(ip_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления IP из белого списка: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/toggle-whitelist-ip', methods=['POST'])
@require_admin_auth
def admin_toggle_whitelist_ip():
    """Включить/выключить IP-адрес в белом списке"""
    from app import app
    
    try:
        data = request.json
        ip_id = data.get('ip_id')
        
        if not ip_id:
            return jsonify({'success': False, 'error': 'Укажите ID IP-адреса'})
        
        result = app.user_manager.toggle_whitelisted_ip(ip_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Ошибка переключения статуса IP: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/get-whitelist-ips', methods=['GET'])
@require_admin_auth
def admin_get_whitelist_ips():
    """Получить все IP-адреса из белого списка"""
    from app import app
    from models.sqlite_users import WhitelistedIP
    
    try:
        # Получаем все IP из белого списка
        all_ips = WhitelistedIP.query.order_by(WhitelistedIP.created_at.desc()).all()
        
        ips_list = [ip.to_dict() for ip in all_ips]
        
        return jsonify({
            'success': True,
            'ips': ips_list
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения белого списка IP: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ========== API ДЛЯ УПРАВЛЕНИЯ БРЕНДИНГОМ ==========

@admin_bp.route('/get-branding', methods=['GET'])
@require_admin_auth
def admin_get_branding():
    """Получить настройки брендинга для пользователя"""
    from app import app
    
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Не указан user_id'}), 400
        
        branding = app.user_manager.get_branding_settings(user_id)
        
        return jsonify({
            'success': True,
            'branding': branding
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения настроек брендинга: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/save-branding', methods=['POST'])
@require_admin_auth
def admin_save_branding():
    """Сохранить настройки брендинга для пользователя"""
    from app import app
    from werkzeug.utils import secure_filename
    import uuid
    
    try:
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Не указан user_id'}), 400
        
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
                
                # Создаем папку для логотипов, если её нет
                logos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logos')
                os.makedirs(logos_dir, exist_ok=True)
                
                # Генерируем уникальное имя файла
                unique_filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
                logo_path = os.path.join(logos_dir, unique_filename)
                
                # Сохраняем файл
                logo_file.save(logo_path)
                logger.info(f"✅ Логотип сохранен: {logo_path}")
                
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
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/toggle-branding', methods=['POST'])
@require_admin_auth
def admin_toggle_branding():
    """Включить/выключить брендинг для пользователя"""
    from app import app
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        is_active = data.get('is_active')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Не указан user_id'}), 400
        
        result = app.user_manager.toggle_branding(user_id, is_active)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Ошибка переключения брендинга: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/delete-branding', methods=['POST'])
@require_admin_auth
def admin_delete_branding():
    """Удалить настройки брендинга для пользователя"""
    from app import app

@admin_bp.route('/api-keys', methods=['GET'])
@require_admin_auth
def admin_get_api_keys():
    """Получить список API-ключей пользователя или всех ключей"""
    from app import app
    from utils.api_key_manager import APIKeyManager
    from models.sqlite_users import APIKey, User, db
    
    user_id = request.args.get('user_id')
    
    # Если указан user_id - возвращаем ключи конкретного пользователя
    if user_id:
        try:
            keys = APIKeyManager.get_user_api_keys(user_id)
            return jsonify({'success': True, 'keys': keys})
        except Exception as e:
            logger.error(f"❌ Ошибка получения API-ключей: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Если user_id не указан - возвращаем все ключи со всей информацией
    try:
        all_keys = APIKey.query.order_by(APIKey.created_at.desc()).all()
        keys_with_user_info = []
        
        for key in all_keys:
            user = User.query.filter_by(user_id=key.user_id).first()
            key_info = {
                'id': key.id,
                'user_id': key.user_id,
                'user_email': user.email if user else 'Не найден',
                'api_key': key.api_key[:8] + '...' + key.api_key[-4:] if len(key.api_key) > 12 else '***',
                'name': key.name,
                'is_active': key.is_active,
                'last_used': key.last_used,
                'requests_count': key.requests_count,
                'created_at': key.created_at,
                'expires_at': key.expires_at,
                'user_plan': user.plan if user else 'unknown'
            }
            keys_with_user_info.append(key_info)
        
        return jsonify({'success': True, 'keys': keys_with_user_info})
    except Exception as e:
        logger.error(f"❌ Ошибка получения всех API-ключей: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api-keys/create', methods=['POST'])
@require_admin_auth
def admin_create_api_key():
    """Создать новый API-ключ для пользователя"""
    from app import app
    from utils.api_key_manager import APIKeyManager
    
    data = request.get_json()
    user_id = data.get('user_id')
    name = data.get('name')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'ID пользователя не указан'}), 400
    
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

@admin_bp.route('/api-keys/deactivate', methods=['POST'])
@require_admin_auth
def admin_deactivate_api_key():
    """Деактивировать API-ключ"""
    from app import app
    from utils.api_key_manager import APIKeyManager
    
    data = request.get_json()
    api_key_id = data.get('api_key_id')
    user_id = data.get('user_id')
    
    if not api_key_id or not user_id:
        return jsonify({'success': False, 'error': 'Не указаны обязательные параметры'}), 400
    
    try:
        success, error = APIKeyManager.deactivate_api_key(api_key_id, user_id)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'API-ключ деактивирован'})
    except Exception as e:
        logger.error(f"❌ Ошибка деактивации API-ключа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api-keys/activate', methods=['POST'])
@require_admin_auth
def admin_activate_api_key():
    """Активировать API-ключ"""
    from app import app
    from models.sqlite_users import APIKey, db
    
    data = request.get_json()
    api_key_id = data.get('api_key_id')
    user_id = data.get('user_id')
    
    if not api_key_id or not user_id:
        return jsonify({'success': False, 'error': 'Не указаны обязательные параметры'}), 400
    
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

@admin_bp.route('/api-keys/delete', methods=['POST'])
@require_admin_auth
def admin_delete_api_key():
    """Удалить API-ключ"""
    from app import app
    from utils.api_key_manager import APIKeyManager
    
    data = request.get_json()
    api_key_id = data.get('api_key_id')
    user_id = data.get('user_id')
    
    if not api_key_id or not user_id:
        return jsonify({'success': False, 'error': 'Не указаны обязательные параметры'}), 400
    
    try:
        success, error = APIKeyManager.delete_api_key(api_key_id, user_id)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'API-ключ удален'})
    except Exception as e:
        logger.error(f"❌ Ошибка удаления API-ключа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/analysis-settings', methods=['GET'])
@require_admin_auth
def admin_get_analysis_settings():
    """Получить настройки анализа пользователя"""
    from app import app
    from utils.analysis_settings_manager import AnalysisSettingsManager
    
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'ID пользователя не указан'}), 400
    
    try:
        settings = AnalysisSettingsManager.get_user_settings(user_id)
        templates = AnalysisSettingsManager.get_user_templates(user_id)
        return jsonify({
            'success': True,
            'settings': settings,
            'templates': templates
        })
    except Exception as e:
        logger.error(f"❌ Ошибка получения настроек анализа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/analysis-settings', methods=['POST'])
@require_admin_auth
def admin_save_analysis_settings():
    """Сохранить настройки анализа пользователя"""
    from app import app
    from utils.analysis_settings_manager import AnalysisSettingsManager
    
    data = request.get_json()
    user_id = data.get('user_id') if data else None
    
    if not user_id:
        return jsonify({'success': False, 'error': 'ID пользователя не указан'}), 400
    
    try:
        settings_data = data.get('settings', {})
        success, error = AnalysisSettingsManager.save_user_settings(user_id, settings_data)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({'success': True, 'message': 'Настройки анализа сохранены'})
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения настроек анализа: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Не указан user_id'}), 400
        
        result = app.user_manager.delete_branding(user_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления брендинга: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/create-backup', methods=['POST'])
@require_admin_auth
def admin_create_backup():
    """Создать резервную копию базы данных"""
    import subprocess
    import sys
    
    try:
        # Запускаем скрипт бэкапа
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backup_database.py')
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 минут максимум
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Резервная копия успешно создана',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Ошибка создания бэкапа: {result.stderr}'
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Таймаут создания бэкапа (превышено 5 минут)'
        })
    except Exception as e:
        logger.error(f"❌ Ошибка создания бэкапа: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/list-backups', methods=['GET'])
@require_admin_auth
def admin_list_backups():
    """Получить список всех бэкапов"""
    import os
    from datetime import datetime
    
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        
        if not os.path.exists(backup_dir):
            return jsonify({
                'success': True,
                'backups': [],
                'total': 0
            })
        
        backups = []
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            if os.path.isfile(file_path) and (filename.startswith('docscan_backup_') and filename.endswith('.db.gz')):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_size = os.path.getsize(file_path)
                size_mb = file_size / (1024 * 1024)
                backups.append({
                    'filename': filename,
                    'date': file_time.isoformat(),
                    'size_mb': round(size_mb, 2),
                    'size_bytes': file_size
                })
        
        # Сортируем по дате (новые первыми)
        backups.sort(key=lambda x: x['date'], reverse=True)
        
        # Подсчитываем общий размер
        total_size = sum(b['size_bytes'] for b in backups)
        
        return jsonify({
            'success': True,
            'backups': backups,
            'total': len(backups),
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка бэкапов: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/delete-backup', methods=['POST'])
@require_admin_auth
def admin_delete_backup():
    """Удалить бэкап"""
    import os
    
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'Укажите имя файла'})
        
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        file_path = os.path.join(backup_dir, filename)
        
        # Проверяем безопасность (только файлы бэкапов)
        if not filename.startswith('docscan_backup_') or not filename.endswith('.db.gz'):
            return jsonify({'success': False, 'error': 'Неверный формат имени файла'})
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Файл не найден'})
        
        os.remove(file_path)
        logger.info(f"🗑️ Бэкап удален администратором: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'Бэкап {filename} успешно удален'
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления бэкапа: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/clean-old-backups', methods=['POST'])
@require_admin_auth
def admin_clean_old_backups():
    """Удалить старые бэкапы"""
    import subprocess
    import sys
    
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backup_database.py')
        result = subprocess.run(
            [sys.executable, script_path, '--clean'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Старые бэкапы удалены',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Ошибка очистки: {result.stderr}'
            })
            
    except Exception as e:
        logger.error(f"❌ Ошибка очистки старых бэкапов: {e}")
        return jsonify({'success': False, 'error': str(e)})
        
        
@admin_bp.route('/guests')
@require_admin_auth
def get_all_guests():
    """Получить всех гостей (незарегистрированных пользователей)"""
    from app import app
    from models.sqlite_users import Guest
    
    # Получаем всех гостей
    guests_list = Guest.query.order_by(Guest.last_seen.desc()).limit(500).all()
    
    # Конвертируем в список словарей
    guests_dict_list = [guest.to_dict() for guest in guests_list]
    
    return jsonify(guests_dict_list)

@admin_bp.route('/search-bots')
@require_admin_auth
def get_all_search_bots():
    """Получить всех поисковых ботов"""
    from app import app
    
    # Получаем всех ботов через user_manager
    bots_list = app.user_manager.get_all_search_bots(limit=500)
    
    return jsonify(bots_list)

@admin_bp.route('/news')
@require_admin_auth
def get_news():
    """Получить список новостей"""
    from app import app
    from flask import request
    
    category = request.args.get('category', None)
    news_list = app.user_manager.get_news_items(category=category, limit=100)
    
    return jsonify(news_list)

@admin_bp.route('/news/<int:news_id>')
@require_admin_auth
def get_news_item(news_id):
    """Получить новость по ID"""
    from app import app
    
    news = app.user_manager.get_news_item(news_id)
    if not news:
        return jsonify({'success': False, 'error': 'Новость не найдена'}), 404
    
    return jsonify({'success': True, 'news': news.to_dict()})

@admin_bp.route('/news', methods=['POST'])
@require_admin_auth
def create_news():
    """Создать новую новость"""
    from app import app
    from flask import request, session
    
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('description') or not data.get('date'):
        return jsonify({'success': False, 'error': 'Заполните все обязательные поля'}), 400
    
    try:
        news = app.user_manager.create_news_item(
            category=data.get('category', 'updates'),
            title=data['title'],
            description=data['description'],
            date=data['date'],
            link=data.get('link'),
            link_text=data.get('link_text'),
            created_by=session.get('admin_username', 'admin')
        )
        
        return jsonify({'success': True, 'news': news.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/news/<int:news_id>', methods=['PUT'])
@require_admin_auth
def update_news(news_id):
    """Обновить новость"""
    from app import app
    from flask import request
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Нет данных для обновления'}), 400
    
    try:
        news = app.user_manager.update_news_item(news_id, **data)
        
        if not news:
            return jsonify({'success': False, 'error': 'Новость не найдена'}), 404
        
        return jsonify({'success': True, 'news': news.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/full-news')
@require_admin_auth
def get_full_news():
    """Получить список полных новостей"""
    from app import app
    from flask import request
    
    category = request.args.get('category', None)
    news_list = app.user_manager.get_all_full_news(category=category, limit=100)
    
    return jsonify(news_list)

@admin_bp.route('/full-news/<int:news_id>')
@require_admin_auth
def get_full_news_item(news_id):
    """Получить полную новость по ID"""
    from app import app
    
    news = app.user_manager.get_full_news(news_id)
    if not news:
        return jsonify({'success': False, 'error': 'Новость не найдена'}), 404
    
    return jsonify({'success': True, 'news': news.to_dict()})

@admin_bp.route('/full-news', methods=['POST'])
@require_admin_auth
def create_full_news():
    """Создать новую полную новость"""
    from app import app
    from flask import request, session
    
    data = request.get_json()
    
    if not data or not data.get('slug') or not data.get('title') or not data.get('short_description') or not data.get('full_content'):
        return jsonify({'success': False, 'error': 'Заполните все обязательные поля (slug, title, short_description, full_content)'}), 400
    
    try:
        news = app.user_manager.create_full_news(
            slug=data['slug'],
            title=data['title'],
            short_description=data['short_description'],
            full_content=data['full_content'],
            category=data.get('category'),
            image_url=data.get('image_url'),
            author=data.get('author'),
            meta_title=data.get('meta_title'),
            meta_description=data.get('meta_description'),
            meta_keywords=data.get('meta_keywords'),
            published_at=data.get('published_at'),
            created_by=session.get('admin_username', 'admin')
        )
        
        if not news:
            return jsonify({'success': False, 'error': 'Новость с таким slug уже существует'}), 400
        
        return jsonify({'success': True, 'news': news.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/full-news/<int:news_id>', methods=['PUT'])
@require_admin_auth
def update_full_news(news_id):
    """Обновить полную новость"""
    from app import app
    from flask import request
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Нет данных для обновления'}), 400
    
    try:
        news = app.user_manager.update_full_news(news_id, **data)
        
        if not news:
            return jsonify({'success': False, 'error': 'Новость не найдена'}), 404
        
        return jsonify({'success': True, 'news': news.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/full-news/<int:news_id>', methods=['DELETE'])
@require_admin_auth
def delete_full_news(news_id):
    """Удалить полную новость"""
    from app import app
    
    try:
        success = app.user_manager.delete_full_news(news_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Новость не найдена'}), 404
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/news/<int:news_id>', methods=['DELETE'])
@require_admin_auth
def delete_news(news_id):
    """Удалить новость"""
    from app import app
    
    try:
        success = app.user_manager.delete_news_item(news_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Новость не найдена'}), 404
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/stats')
@require_admin_auth
def admin_stats():
    """Статистика для админ-панели"""
    from app import app
    from models.sqlite_users import Guest, Payment, User, PageView
    from datetime import datetime, date, timedelta
    
    stats = app.user_manager.get_stats()
    
    # Добавляем статистику по гостям
    total_guests = Guest.query.filter_by(registered_user_id=None).count()
    stats['total_guests'] = total_guests
    
    # Новые пользователи за сегодня (с 0:00)
    today_str = date.today().isoformat()
    new_users_24h = User.query.filter(User.created_at.like(f'{today_str}%')).count()
    stats['new_users_24h'] = new_users_24h
    
    # Новые гости за сегодня (с 0:00) - только реальные пользователи, исключаем ботов
    new_guests_24h = Guest.query.filter(Guest.first_seen.like(f'{today_str}%')).count()
    stats['new_guests_24h'] = new_guests_24h
    
    # Статистика по поисковым ботам
    bots_stats = app.user_manager.get_search_bots_stats()
    stats.update(bots_stats)
    
    # Статистика доходов
    all_payments = Payment.query.filter_by(status='success').all()
    total_revenue = sum(p.amount for p in all_payments)
    stats['total_revenue'] = total_revenue
    
    # Доход за сегодня
    today_str = date.today().isoformat()
    today_payments = Payment.query.filter(
        Payment.status == 'success',
        Payment.created_at.like(f'{today_str}%')
    ).all()
    today_revenue = sum(p.amount for p in today_payments)
    stats['today_revenue'] = today_revenue
    
    # Доход за последние 7 дней
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    week_payments = Payment.query.filter(
        Payment.status == 'success',
        Payment.created_at >= week_ago
    ).all()
    week_revenue = sum(p.amount for p in week_payments)
    stats['week_revenue'] = week_revenue
    
    # Количество успешных платежей
    stats['total_payments'] = len(all_payments)
    stats['today_payments'] = len(today_payments)

    # ====== Статистика по /business-ip ======
    try:
        today_str = date.today().isoformat()
        business_total = PageView.query.filter(PageView.path == '/business-ip').count()
        business_today = PageView.query.filter(
            PageView.path == '/business-ip',
            PageView.created_at.like(f'{today_str}%')
        ).count()
        business_unique_today = PageView.query.filter(
            PageView.path == '/business-ip',
            PageView.created_at.like(f'{today_str}%')
        ).with_entities(PageView.ip_address).distinct().count()

        stats['business_ip_views_total'] = business_total
        stats['business_ip_views_today'] = business_today
        stats['business_ip_unique_today'] = business_unique_today
    except Exception:
        stats['business_ip_views_total'] = 0
        stats['business_ip_views_today'] = 0
        stats['business_ip_unique_today'] = 0
    
    return jsonify(stats)
        
@admin_bp.route('/calculator-stats-data')
@require_admin_auth
def calculator_stats_data():
    """JSON данные статистики калькулятора"""
    from app import app
    
    stats = app.user_manager.get_calculator_stats()
    return jsonify(stats)

@admin_bp.route('/payments')
@require_admin_auth
def get_payments():
    """Получить список всех платежей"""
    from models.sqlite_users import Payment
    from datetime import datetime, timedelta
    
    # Получаем параметры фильтрации
    days = request.args.get('days', type=int)  # За последние N дней
    limit = request.args.get('limit', type=int, default=100)  # Лимит записей
    
    query = Payment.query.filter_by(status='success')
    
    # Фильтр по дате
    if days:
        date_from = (datetime.now() - timedelta(days=days)).isoformat()
        query = query.filter(Payment.created_at >= date_from)
    
    # Сортировка по дате (новые сначала)
    payments = query.order_by(Payment.created_at.desc()).limit(limit).all()
    
    payments_list = [p.to_dict() for p in payments]
    return jsonify(payments_list)

@admin_bp.route('/new-users')
@require_admin_auth
def get_new_users():
    """Получить новых пользователей за сегодня (с 0:00)"""
    from models.sqlite_users import User, AnalysisHistory
    from datetime import datetime, timedelta, date
    
    today_str = date.today().isoformat()
    new_users = User.query.filter(User.created_at.like(f'{today_str}%')).order_by(User.created_at.desc()).all()
    
    users_list = []
    # Получаем сегодняшнюю дату для проверки анализов за сегодня
    today = date.today().isoformat()
    
    for user in new_users:
        user_dict = user.to_dict()
        
        # Проверяем, сделал ли пользователь анализ СЕГОДНЯ (не вообще когда-либо)
        has_analysis_today = AnalysisHistory.query.filter(
            AnalysisHistory.user_id == user.user_id,
            AnalysisHistory.created_at.like(f'{today}%')
        ).first() is not None
        user_dict['has_analysis'] = has_analysis_today
        
        users_list.append(user_dict)
    
    return jsonify(users_list)

# ========== МАРШРУТЫ ДЛЯ EMAIL-РАССЫЛОК ==========

@admin_bp.route('/email-campaigns', methods=['GET'])
@require_admin_auth
def get_email_campaigns():
    """Получить список всех рассылок"""
    from app import app
    
    campaigns = app.user_manager.get_email_campaigns(limit=100)
    return jsonify(campaigns)

@admin_bp.route('/email-campaigns', methods=['POST'])
@require_admin_auth
def create_email_campaign():
    """Создать новую email-рассылку"""
    from app import app
    from datetime import datetime
    
    try:
        data = request.get_json()
        
        name = data.get('name')
        subject = data.get('subject')
        html_content = data.get('html_content')
        text_content = data.get('text_content', '')
        recipient_filter = data.get('recipient_filter', 'all')
        recipient_list = data.get('recipient_list')  # для ручного выбора (manual)
        
        if not name or not subject or not html_content:
            return jsonify({'success': False, 'error': 'Заполните все обязательные поля'}), 400

        if recipient_filter == 'manual':
            if not recipient_list or (isinstance(recipient_list, list) and len(recipient_list) == 0):
                return jsonify({'success': False, 'error': 'Выберите хотя бы одного получателя'}), 400
        
        # Получаем имя админа из сессии или куки
        created_by = session.get('admin_username', request.cookies.get('admin_username', 'admin'))
        
        campaign = app.user_manager.create_email_campaign(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            recipient_filter=recipient_filter,
            created_by=created_by,
            recipient_list=json.dumps(recipient_list, ensure_ascii=False) if recipient_filter == 'manual' else None
        )
        
        logger.info(f"📧 Администратор создал рассылку: {name} (ID: {campaign.id})")
        
        return jsonify({
            'success': True,
            'message': 'Рассылка создана',
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания рассылки: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/email-campaigns/manual-users', methods=['GET'])
@require_admin_auth
def get_manual_users():
    """Список пользователей для ручного выбора получателей"""
    from app import app
    try:
        users = app.user_manager.get_registered_users_for_manual_selection()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        logger.error(f"❌ Ошибка получения пользователей для ручной рассылки: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/email-campaigns/<int:campaign_id>/send', methods=['POST'])
@require_admin_auth
def send_email_campaign(campaign_id):
    """Отправить email-рассылку"""
    from app import app
    from utils.email_service import send_email_campaign
    
    try:
        # Запускаем отправку рассылки в фоне (можно сделать через Celery в будущем)
        result = send_email_campaign(
            campaign_id=campaign_id,
            user_manager=app.user_manager,
            batch_size=10,
            delay_between_batches=1
        )
        
        if result['success']:
            logger.info(f"✅ Рассылка {campaign_id} отправлена: {result['sent']}/{result['total']}")
            return jsonify({
                'success': True,
                'message': f"Рассылка отправлена: {result['sent']} из {result['total']}",
                'stats': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Ошибка отправки')
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки рассылки {campaign_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/email-campaigns/<int:campaign_id>/stats', methods=['GET'])
@require_admin_auth
def get_campaign_stats(campaign_id):
    """Получить статистику по рассылке"""
    from app import app
    
    stats = app.user_manager.get_campaign_stats(campaign_id)
    return jsonify(stats)

@admin_bp.route('/email-campaigns/<int:campaign_id>/recipients', methods=['GET'])
@require_admin_auth
def get_campaign_recipients(campaign_id):
    """Получить список получателей для рассылки"""
    from app import app
    
    campaign = app.user_manager.get_email_campaign(campaign_id)
    if not campaign:
        return jsonify({'success': False, 'error': 'Рассылка не найдена'}), 404
    
    recipients = app.user_manager.get_recipients_for_campaign(campaign.recipient_filter)
    
    return jsonify({
        'success': True,
        'filter': campaign.recipient_filter,
        'count': len(recipients),
        'recipients': recipients
    })

@admin_bp.route('/email-campaigns/recipients-preview', methods=['GET'])
@require_admin_auth
def get_recipients_preview():
    """Получить предпросмотр получателей по фильтру"""
    from app import app
    
    recipient_filter = request.args.get('filter', 'all')
    
    recipients = app.user_manager.get_recipients_for_campaign(recipient_filter)
    
    return jsonify({
        'success': True,
        'filter': recipient_filter,
        'count': len(recipients),
        'recipients': recipients
    })

# ========== МАРШРУТЫ ДЛЯ УПРАВЛЕНИЯ СТАТЬЯМИ ==========

@admin_bp.route('/articles', methods=['GET'])
@require_admin_auth
def get_all_articles():
    """Получить список всех статей"""
    from app import app
    
    status_filter = request.args.get('status', None)
    articles = app.user_manager.get_all_articles(limit=200, status_filter=status_filter)
    
    return jsonify(articles)

@admin_bp.route('/articles', methods=['POST'])
@require_admin_auth
def create_article():
    """Создать новую статью"""
    from app import app
    import re
    
    try:
        data = request.get_json()
        
        title = data.get('title', '').strip()
        slug = data.get('slug', '').strip()
        html_content = data.get('html_content', '').strip()
        description = data.get('description', '').strip()
        icon = data.get('icon', '').strip()
        meta_keywords = data.get('meta_keywords', '').strip()
        meta_description = data.get('meta_description', '').strip()
        category = data.get('category', '').strip()
        
        if not title or not slug or not html_content:
            return jsonify({'success': False, 'error': 'Заполните все обязательные поля (заголовок, URL, содержимое)'}), 400
        
        # Проверяем формат slug (только латиница, цифры, дефисы и подчеркивания)
        if not re.match(r'^[a-z0-9_-]+$', slug.lower()):
            return jsonify({'success': False, 'error': 'URL может содержать только латинские буквы, цифры, дефисы и подчеркивания'}), 400
        
        # Приводим slug к нижнему регистру
        slug = slug.lower()
        
        # Получаем имя админа из сессии
        author = session.get('admin_username', request.cookies.get('admin_username', 'admin'))
        
        article = app.user_manager.create_article(
            title=title,
            slug=slug,
            html_content=html_content,
            description=description,
            icon=icon,
            meta_keywords=meta_keywords,
            meta_description=meta_description,
            author=author,
            category=category
        )
        
        logger.info(f"📝 Администратор создал статью: {title} (slug: {slug})")
        
        return jsonify({
            'success': True,
            'message': 'Статья создана',
            'article': article.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"❌ Ошибка создания статьи: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/articles/<int:article_id>', methods=['GET'])
@require_admin_auth
def get_article(article_id):
    """Получить статью по ID"""
    from app import app
    
    article = app.user_manager.get_article(article_id)
    if not article:
        return jsonify({'success': False, 'error': 'Статья не найдена'}), 404
    
    return jsonify({'success': True, 'article': article.to_dict()})

@admin_bp.route('/articles/<int:article_id>', methods=['PUT'])
@require_admin_auth
def update_article(article_id):
    """Обновить статью"""
    from app import app
    import re
    
    try:
        data = request.get_json()
        
        # Подготавливаем данные для обновления
        update_data = {}
        
        if 'title' in data:
            update_data['title'] = data['title'].strip()
        if 'slug' in data:
            slug = data['slug'].strip().lower()
            if not re.match(r'^[a-z0-9_-]+$', slug):
                return jsonify({'success': False, 'error': 'URL может содержать только латинские буквы, цифры, дефисы и подчеркивания'}), 400
            update_data['slug'] = slug
        if 'html_content' in data:
            update_data['html_content'] = data['html_content'].strip()
        if 'description' in data:
            update_data['description'] = data['description'].strip()
        if 'icon' in data:
            update_data['icon'] = data['icon'].strip()
        if 'meta_keywords' in data:
            update_data['meta_keywords'] = data['meta_keywords'].strip()
        if 'meta_description' in data:
            update_data['meta_description'] = data['meta_description'].strip()
        if 'status' in data:
            update_data['status'] = data['status']
        if 'category' in data:
            update_data['category'] = data['category'].strip()
        
        article = app.user_manager.update_article(article_id, **update_data)
        
        if not article:
            return jsonify({'success': False, 'error': 'Статья не найдена'}), 404
        
        logger.info(f"📝 Администратор обновил статью: {article.title} (ID: {article_id})")
        
        return jsonify({
            'success': True,
            'message': 'Статья обновлена',
            'article': article.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"❌ Ошибка обновления статьи: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/articles/<int:article_id>', methods=['DELETE'])
@require_admin_auth
def delete_article(article_id):
    """Удалить статью"""
    from app import app
    
    try:
        success = app.user_manager.delete_article(article_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Статья не найдена'}), 404
        
        logger.info(f"🗑️ Администратор удалил статью (ID: {article_id})")
        
        return jsonify({
            'success': True,
            'message': 'Статья удалена'
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления статьи: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/articles/<int:article_id>/publish', methods=['POST'])
@require_admin_auth
def publish_article(article_id):
    """Опубликовать статью"""
    from app import app
    
    try:
        article = app.user_manager.publish_article(article_id)
        
        if not article:
            return jsonify({'success': False, 'error': 'Статья не найдена'}), 404
        
        logger.info(f"📢 Администратор опубликовал статью: {article.title} (ID: {article_id})")
        
        return jsonify({
            'success': True,
            'message': 'Статья опубликована',
            'article': article.to_dict()
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка публикации статьи: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/articles/<int:article_id>/unpublish', methods=['POST'])
@require_admin_auth
def unpublish_article(article_id):
    """Снять статью с публикации"""
    from app import app
    
    try:
        article = app.user_manager.unpublish_article(article_id)
        
        if not article:
            return jsonify({'success': False, 'error': 'Статья не найдена'}), 404
        
        logger.info(f"🔒 Администратор снял с публикации статью: {article.title} (ID: {article_id})")
        
        return jsonify({
            'success': True,
            'message': 'Статья снята с публикации',
            'article': article.to_dict()
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка снятия с публикации: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/articles/upload-image', methods=['POST'])
@require_admin_auth
def upload_article_image():
    """Загрузить изображение для статьи"""
    import os
    from werkzeug.utils import secure_filename
    from datetime import datetime
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'}), 400
        
        # Проверяем расширение файла
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
        filename = file.filename
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'error': f'Разрешенные форматы: {", ".join(allowed_extensions)}'}), 400
        
        # Создаем безопасное имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = secure_filename(f"{timestamp}_{filename}")
        
        # Создаем директорию для изображений статей если её нет
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'articles')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Сохраняем файл
        filepath = os.path.join(upload_dir, safe_filename)
        file.save(filepath)
        
        # Возвращаем URL изображения
        image_url = f'/static/uploads/articles/{safe_filename}'
        
        logger.info(f"📷 Загружено изображение для статьи: {safe_filename}")
        
        return jsonify({
            'location': image_url
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки изображения: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/partners')
@require_admin_auth
def get_partners():
    """Получить список всех партнеров"""
    from models.sqlite_users import User, Referral, ReferralReward
    
    try:
        # Получаем всех пользователей с реферальными кодами
        partners = User.query.filter(User.referral_code.isnot(None)).all()
        
        partners_list = []
        for partner in partners:
            # Статистика партнера
            invited_count = Referral.query.filter_by(referrer_id=partner.user_id).count()
            rewards = ReferralReward.query.filter_by(partner_id=partner.user_id).all()
            purchases_count = len(rewards)
            pending_rewards = ReferralReward.query.filter_by(partner_id=partner.user_id, status='pending').all()
            pending_amount = sum(r.reward_amount for r in pending_rewards)
            
            partners_list.append({
                'user_id': partner.user_id,
                'email': partner.email,
                'referral_code': partner.referral_code,
                'invited_count': invited_count,
                'purchases_count': purchases_count,
                'pending_amount': pending_amount,
                'payment_details': partner.payment_details
            })
        
        return jsonify(partners_list)
    except Exception as e:
        logger.error(f"❌ Ошибка получения партнеров: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/referrals')
@require_admin_auth
def get_referrals():
    """Получить список всех приглашений"""
    from models.sqlite_users import Referral
    
    try:
        referrals = Referral.query.order_by(Referral.created_at.desc()).all()
        return jsonify([r.to_dict() for r in referrals])
    except Exception as e:
        logger.error(f"❌ Ошибка получения приглашений: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/rewards')
@require_admin_auth
def get_rewards():
    """Получить список всех вознаграждений"""
    from models.sqlite_users import ReferralReward
    
    try:
        rewards = ReferralReward.query.order_by(ReferralReward.created_at.desc()).all()
        return jsonify([r.to_dict() for r in rewards])
    except Exception as e:
        logger.error(f"❌ Ошибка получения вознаграждений: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/rewards/<int:reward_id>/mark-paid', methods=['POST'])
@require_admin_auth
def mark_reward_paid(reward_id):
    """Отметить вознаграждение как выплаченное"""
    from models.sqlite_users import ReferralReward, db
    from datetime import datetime
    
    try:
        reward = ReferralReward.query.filter_by(id=reward_id).first()
        if not reward:
            return jsonify({'success': False, 'error': 'Вознаграждение не найдено'}), 404
        
        reward.status = 'paid'
        reward.paid_at = datetime.now().isoformat()
        db.session.commit()
        
        logger.info(f"✅ Вознаграждение {reward_id} отмечено как выплаченное")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Ошибка обновления вознаграждения: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/notifications/send', methods=['POST'])
@require_admin_auth
def send_notification():
    """Отправить уведомление пользователю из админ панели"""
    from app import app
    from models.sqlite_users import User, Notification, db
    from datetime import datetime
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Отсутствуют данные'}), 400
        
        user_id_or_email = (data.get('user_id_or_email') or '').strip()
        type = data.get('type') or 'admin'
        title = (data.get('title') or '').strip()
        message = (data.get('message') or '').strip()
        link = (data.get('link') or '').strip()
        
        if not user_id_or_email or not title:
            return jsonify({'success': False, 'error': 'Укажите пользователя и заголовок'}), 400
        
        # Ищем пользователя по user_id или email
        user = None
        if '@' in user_id_or_email:
            # Это email
            user = User.query.filter_by(email=user_id_or_email).first()
        else:
            # Это user_id
            user = User.query.filter_by(user_id=user_id_or_email).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        # Создаем уведомление
        notification = Notification(
            user_id=user.user_id,
            type=type,
            question_id=None,
            answer_id=None,
            title=title,
            message=message,
            link=link if link else None,
            is_read=False,
            created_at=datetime.now().isoformat()
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logger.info(f"🔔 Админ отправил уведомление пользователю {user.user_id}: {title}")
        return jsonify({'success': True, 'message': 'Уведомление отправлено'})
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/notifications/history', methods=['GET'])
@require_admin_auth
def get_notifications_history():
    """Получить историю отправленных уведомлений"""
    from models.sqlite_users import Notification
    
    try:
        # Получаем последние 50 уведомлений, отсортированные по дате
        notifications = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
        
        notifications_list = []
        for notif in notifications:
            notifications_list.append({
                'id': notif.id,
                'user_id': notif.user_id,
                'type': notif.type,
                'title': notif.title,
                'message': notif.message,
                'link': notif.link,
                'is_read': notif.is_read,
                'created_at': notif.created_at
            })
        
        return jsonify({'success': True, 'notifications': notifications_list})
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения истории уведомлений: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/questions')
@require_admin_auth
def get_questions():
    """Получить список всех вопросов"""
    from app import app
    from flask import request
    from models.sqlite_users import Question
    
    try:
        status_filter = request.args.get('status', '')
        
        # Прямой запрос к базе для отладки
        query = Question.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        query = query.order_by(Question.created_at.desc())
        questions = query.limit(1000).all()
        
        # Преобразуем в словари
        questions_list = []
        for q in questions:
            q_dict = {
                'id': q.id,
                'user_id': q.user_id,
                'title': q.title,
                'content': q.content,
                'category': q.category,
                'status': q.status,
                'views_count': q.views_count or 0,
                'answers_count': q.answers_count or 0,
                'created_at': q.created_at,
                'updated_at': q.updated_at,
                'best_answer_id': q.best_answer_id,
                'author_email': q.user.email if hasattr(q, 'user') and q.user else 'Неизвестно'
            }
            questions_list.append(q_dict)
        
        logger.info(f"📋 Загружено вопросов: {len(questions_list)}")
        return jsonify(questions_list)
    except Exception as e:
        logger.error(f"❌ Ошибка получения вопросов: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/questions/<int:question_id>/status', methods=['POST'])
@require_admin_auth
def update_question_status(question_id):
    """Изменить статус вопроса"""
    from models.sqlite_users import db, Question
    from datetime import datetime
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['open', 'answered', 'solved', 'closed']:
            return jsonify({'success': False, 'error': 'Неверный статус'}), 400
        
        question = Question.query.filter_by(id=question_id).first()
        if not question:
            return jsonify({'success': False, 'error': 'Вопрос не найден'}), 404
        
        question.status = new_status
        question.updated_at = datetime.now().isoformat()
        db.session.commit()
        
        logger.info(f"✅ Статус вопроса {question_id} изменен на {new_status}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Ошибка изменения статуса вопроса: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@require_admin_auth
def delete_question(question_id):
    """Удалить вопрос"""
    from app import app
    from models.sqlite_users import db, Question
    
    try:
        question = Question.query.filter_by(id=question_id).first()
        if not question:
            return jsonify({'success': False, 'error': 'Вопрос не найден'}), 404
        
        db.session.delete(question)
        db.session.commit()
        
        logger.info(f"✅ Вопрос {question_id} удален администратором")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Ошибка удаления вопроса: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/answers/<int:answer_id>', methods=['DELETE'])
@require_admin_auth
def delete_answer(answer_id):
    """Удалить ответ на вопрос"""
    from models.sqlite_users import db, Answer, Question
    from datetime import datetime
    
    try:
        answer = Answer.query.filter_by(id=answer_id).first()
        if not answer:
            return jsonify({'success': False, 'error': 'Ответ не найден'}), 404
        
        question_id = answer.question_id
        db.session.delete(answer)
        db.session.commit()
        
        # Обновляем счетчик ответов и статус вопроса
        question = Question.query.filter_by(id=question_id).first()
        if question:
            # Пересчитываем количество ответов
            remaining_answers = Answer.query.filter_by(question_id=question_id).count()
            question.answers_count = remaining_answers
            
            # Если ответов не осталось, меняем статус на 'open'
            if remaining_answers == 0:
                if question.status == 'answered':
                    question.status = 'open'
                    logger.info(f"🔄 Статус вопроса {question_id} изменен на 'open' (ответов не осталось)")
            
            # Удаляем best_answer_id если удаляемый ответ был лучшим
            if question.best_answer_id == answer_id:
                question.best_answer_id = None
            
            question.updated_at = datetime.now().isoformat()
            db.session.commit()
        
        logger.info(f"✅ Ответ {answer_id} удален администратором")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Ошибка удаления ответа: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/questions/<int:question_id>/answers')
@require_admin_auth
def get_question_answers(question_id):
    """Получить все ответы на вопрос для админ-панели"""
    from models.sqlite_users import Answer, User
    
    try:
        answers = Answer.query.filter_by(question_id=question_id).order_by(Answer.created_at.desc()).all()
        
        answers_list = []
        for answer in answers:
            user = User.query.filter_by(user_id=answer.user_id).first()
            answer_dict = {
                'id': answer.id,
                'question_id': answer.question_id,
                'user_id': answer.user_id,
                'author_email': user.email if user else 'Неизвестно',
                'content': answer.content,
                'is_best': answer.is_best,
                'likes_count': answer.likes_count or 0,
                'created_at': answer.created_at
            }
            answers_list.append(answer_dict)
        
        return jsonify(answers_list)
    except Exception as e:
        logger.error(f"❌ Ошибка получения ответов: {e}")
        return jsonify({'error': str(e)}), 500
