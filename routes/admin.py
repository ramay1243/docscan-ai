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
        <style>
            body { font-family: Arial; margin: 40px; background: #f7fafc; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .user-card { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            button { background: #667eea; color: white; border: none; padding: 10px 15px; margin: 5px; border-radius: 5px; cursor: pointer; }
            button:hover { background: #5a67d8; }
            .logout-btn { background: #e53e3e; }
            .logout-btn:hover { background: #c53030; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 Админ-панель DocScan</h1>
                <p>Вошел как: <strong>""" + admin_info.get('username', 'Unknown') + """</strong></p>
                <button class="logout-btn" onclick="logout()">🚪 Выйти</button>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>👥 Всего пользователей</h3>
                    <div id="totalUsers">0</div>
                </div>
                <div class="stat-card">
                    <h3>📊 Всего анализов</h3>
                    <div id="totalAnalyses">0</div>
                </div>
                <div class="stat-card">
                    <h3>📈 Анализов сегодня</h3>
                    <div id="todayAnalyses">0</div>
                </div>
            </div>
            
            <h3>Управление пользователями:</h3>
            <div id="usersList"></div>
            
            <h3>Выдать тариф пользователю:</h3>
            <input type="text" id="userId" placeholder="ID пользователя">
            <select id="planSelect">
                <option value="free">Бесплатный (1 анализ)</option>
                <option value="basic">Базовый (10 анализов)</option>
                <option value="premium">Премиум (50 анализов)</option>
                <option value="unlimited">Безлимитный</option>
            </select>
            <button onclick="setUserPlan()">Выдать тариф</button>
            
            <h3>Создать нового пользователя:</h3>
            <input type="text" id="newUserId" placeholder="Новый ID пользователя (опционально)">
            <button onclick="createUser()">Создать пользователя</button>
        </div>

        <script>
            function logout() {
                document.cookie = "admin_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                window.location.href = "/admin/login";
            }

            // Загружаем статистику и пользователей
            function loadStats() {
                fetch('/admin/stats', {credentials: 'include'})
                    .then(r => r.json())
                    .then(stats => {
                        document.getElementById('totalUsers').textContent = stats.total_users;
                        document.getElementById('totalAnalyses').textContent = stats.total_analyses;
                        document.getElementById('todayAnalyses').textContent = stats.today_analyses;
                    });
            }

            function loadUsers() {
                    fetch('/admin/users', {credentials: 'include'})
                    .then(r => r.json())
                    .then(users => {
                        let html = '';
                        for (const [userId, userData] of Object.entries(users)) {
                            html += `
                                <div class="user-card">
                                    <strong>ID:</strong> ${userId}<br>
                                    <strong>Тариф:</strong> ${userData.plan} (${getPlanName(userData.plan)})<br>
                                    <strong>Использовано сегодня:</strong> ${userData.used_today}/${getPlanLimit(userData.plan)}<br>
                                    <strong>Всего анализов:</strong> ${userData.total_used}<br>
                                    <strong>Создан:</strong> ${userData.created_at || 'Неизвестно'}<br>
                                    <strong>IP-адрес:</strong> ${userData.ip_address || 'Не определен'}<br>
                                    <button onclick="setUserPlanQuick('${userId}', 'basic')">Выдать Базовый</button>
                                    <button onclick="setUserPlanQuick('${userId}', 'premium')">Выдать Премиум</button>
                                    <button onclick="setUserPlanQuick('${userId}', 'unlimited')">Выдать Безлимитный</button>
                                </div>
                            `;
                        }
                        document.getElementById('usersList').innerHTML = html;
                    });
            }

            function getPlanName(plan) {
                const names = {free: 'Бесплатный', basic: 'Базовый', premium: 'Премиум', unlimited: 'Безлимитный'};
                return names[plan] || plan;
            }

            function getPlanLimit(plan) {
                const limits = {free: 1, basic: 10, premium: 50, unlimited: 1000};
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

            // Загружаем при открытии
            loadStats();
            loadUsers();
        </script>
    </body>
    </html>
    """

@admin_bp.route('/stats')
@require_admin_auth
def admin_stats():
    """Статистика для админ-панели"""
    from app import app
    
    stats = app.user_manager.get_stats()
    return jsonify(stats)

@admin_bp.route('/users')
@require_admin_auth
def get_all_users():
    """Получить всех пользователей"""
    from app import app
    
    # Получаем пользователей из SQLite
    users_list = app.user_manager.get_all_users()
    
    # Конвертируем в dict для совместимости
    users_dict = {}
    for user in users_list:
        users_dict[user.user_id] = user.to_dict()
    
    # Создаем менеджер IP-лимитов
    ip_manager = IPLimitManager()
    
    # Добавляем IP-адреса к каждому пользователю
    for user_id, user_data in users_dict.items():
        user_ip = "Не определен"
        
        # Ищем IP пользователя в данных IP-лимитов
        for ip, ip_data in ip_manager.ip_limits.items():
            if (ip_data.get('user_id') == user_id or 
                ip_data.get('last_user') == user_id):
                user_ip = ip
                break
        
        user_data['ip_address'] = user_ip
    
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