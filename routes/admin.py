from flask import Blueprint, request, jsonify, session
import secrets
import uuid
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
                <a href="#" class="menu-item" data-section="articles">
                    <span>📝</span> Статьи
                </a>
                <a href="#" class="menu-item" data-section="partners">
                    <span>🎁</span> Партнерская программа
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
                    
                    <div class="card">
                        <h3>Выдать тариф пользователю</h3>
                        <div style="margin: 15px 0;">
                            <input type="text" id="userId" placeholder="ID пользователя" 
                                   style="width: 200px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                            <select id="planSelect" style="padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px; margin-right: 10px;">
                                <option value="free">Бесплатный (1 анализ)</option>
                                <option value="basic">Базовый (10 анализов за 290₽)</option>
                                <option value="premium">Премиум (30 анализов за 690₽)</option>
                            </select>
                            <button onclick="setUserPlan()">Выдать тариф</button>
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
            </select>
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
                        'articles': '📝 Статьи',
                        'partners': '🎁 Партнерская программа'
                    };
                    const pageTitle = document.getElementById('pageTitle');
                    if (pageTitle) {
                        pageTitle.textContent = titles[sectionName] || 'Админ-панель';
                    }
                    
                    // Загружаем данные секции при первом открытии
                    if (sectionName === 'users') {
                        const usersList = document.getElementById('usersList');
                        if (usersList && usersList.innerHTML === '') {
                            console.log('📥 Загрузка пользователей...');
                            loadUsers();
                        }
                    } else if (sectionName === 'guests') {
                        const guestsList = document.getElementById('guestsList');
                        if (guestsList && guestsList.innerHTML === '') {
                            console.log('📥 Загрузка гостей...');
                            loadGuests();
                        }
                    } else if (sectionName === 'search-bots') {
                        const botsList = document.getElementById('botsList');
                        if (botsList && botsList.innerHTML === '') {
                            console.log('📥 Загрузка ботов...');
                            loadBots();
                        }
                        // Обновляем статистику ботов
                        loadStats();
                    } else if (sectionName === 'campaigns') {
                        const campaignsList = document.getElementById('emailCampaignsList');
                        if (campaignsList && campaignsList.innerHTML === '') {
                            console.log('📥 Загрузка рассылок...');
                            loadEmailCampaigns();
                        }
                    } else if (sectionName === 'articles') {
                        const articlesList = document.getElementById('articlesList');
                        if (articlesList && articlesList.innerHTML === '') {
                            console.log('📥 Загрузка статей...');
                            loadArticles();
                        }
                    } else if (sectionName === 'partners') {
                        loadPartners();
                        loadReferrals();
                        loadRewards();
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
        
        <script>
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
            
            function loadNewUsers() {
                fetch('/admin/new-users', {credentials: 'include'})
                    .then(r => r.json())
                    .then(users => {
                        let html = '';
                        if (!users || users.length === 0) {
                            html = '<p style="color: #999; padding: 20px;">Нет новых пользователей за последние 24 часа</p>';
                        } else {
                            html = '<table style="width: 100%; border-collapse: collapse; margin-top: 15px;"><thead><tr style="background: #f7fafc;"><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">ID</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Email</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата регистрации</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Тариф</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Сделал анализ</th></tr></thead><tbody>';
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
                            html += '</tbody></table>';
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
                            html = '<table style="width: 100%; border-collapse: collapse; margin-top: 15px;"><thead><tr style="background: #f7fafc;"><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Email</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Тариф</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Сумма</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Статус</th></tr></thead><tbody>';
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
                            html += '</tbody></table>';
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
                        
                        let html = '<table style="width: 100%; border-collapse: collapse; margin-top: 15px;"><thead><tr style="background: #f7fafc;"><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">ID</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Email</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата регистрации</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Тариф</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Тариф до</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Анализов всего</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Сегодня</th><th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0;">Действия</th></tr></thead><tbody>';
                        
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
                                        <button onclick="setUserPlanQuick('${user.userId}', 'basic')" style="font-size: 0.85rem; padding: 5px 10px;">Базовый</button>
                                        <button onclick="setUserPlanQuick('${user.userId}', 'premium')" style="font-size: 0.85rem; padding: 5px 10px;">Премиум</button>
                                    </td>
                                </tr>
                            `;
                        });
                        html += '</tbody></table>';
                        document.getElementById('usersList').innerHTML = html;
                    });
            }

            function getPlanName(plan) {
                const names = {free: 'Бесплатный', basic: 'Базовый', premium: 'Премиум'};
                return names[plan] || plan;
            }
            
            function getPlanLimit(plan) {
                const limits = {free: 1, basic: 10, premium: 30};
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
                    loadUsers();
                    loadStats();
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
                                html += '<table style="width: 100%; border-collapse: collapse;"><thead><tr>';
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
                                
                                html += '</tbody></table>';
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
                        
                        let html = '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">ID</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Email</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Реферальный код</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Приглашено</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Покупок</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Ожидает выплаты</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Реквизиты</th></tr></thead><tbody>';
                        
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
                        
                        html += '</tbody></table>';
                        listEl.innerHTML = html;
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки партнеров:', err);
                        document.getElementById('partnersList').innerHTML = '<p style="color: #f56565;">Ошибка загрузки данных</p>';
                    });
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
                        
                        let html = '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Кто пригласил</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Кого пригласили</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата приглашения</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата регистрации</th></tr></thead><tbody>';
                        
                        referrals.forEach(ref => {
                            html += `<tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 12px;">${ref.referrer_id}</td>
                                <td style="padding: 12px;">${ref.invited_user_id}</td>
                                <td style="padding: 12px;">${new Date(ref.created_at).toLocaleString('ru-RU')}</td>
                                <td style="padding: 12px;">${ref.registered_at ? new Date(ref.registered_at).toLocaleString('ru-RU') : 'Не зарегистрирован'}</td>
                            </tr>`;
                        });
                        
                        html += '</tbody></table>';
                        listEl.innerHTML = html;
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки приглашений:', err);
                        document.getElementById('referralsList').innerHTML = '<p style="color: #f56565;">Ошибка загрузки данных</p>';
                    });
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
                        
                        let html = '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #f7fafc;"><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Партнер</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Приглашенный</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Сумма покупки</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Вознаграждение</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Статус</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Дата</th><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Действия</th></tr></thead><tbody>';
                        
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
                        
                        html += '</tbody></table>';
                        listEl.innerHTML = html;
                    })
                    .catch(err => {
                        console.error('Ошибка загрузки вознаграждений:', err);
                        document.getElementById('rewardsList').innerHTML = '<p style="color: #f56565;">Ошибка загрузки данных</p>';
                    });
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
                if (typeof createCampaign === 'function') {
                    window.createCampaign = createCampaign;
                }
                console.log('✅ Функции зарегистрированы глобально (fallback)');
            }
            
            console.log('✅ Все скрипты загружены и функции зарегистрированы');
        </script>
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

@admin_bp.route('/stats')
@require_admin_auth
def admin_stats():
    """Статистика для админ-панели"""
    from app import app
    from models.sqlite_users import Guest, Payment, User
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
        
        if not name or not subject or not html_content:
            return jsonify({'success': False, 'error': 'Заполните все обязательные поля'}), 400
        
        # Получаем имя админа из сессии или куки
        created_by = session.get('admin_username', request.cookies.get('admin_username', 'admin'))
        
        campaign = app.user_manager.create_email_campaign(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            recipient_filter=recipient_filter,
            created_by=created_by
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
