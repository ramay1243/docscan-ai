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
                    <h3>👤 Всего гостей</h3>
                    <div id="totalGuests">0</div>
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
            
<h2>👤 Гости (незарегистрированные пользователи)</h2>
<p>Пользователи, которые сделали анализ без регистрации</p>

<div style="margin: 15px 0;">
    <input type="text" id="searchGuest" placeholder="🔍 Поиск по IP, браузеру..." 
           style="width: 300px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;"
           onkeyup="searchGuests()">
    <button onclick="clearGuestSearch()" style="margin-left: 10px; padding: 8px 15px; border: none; background: #e2e8f0; border-radius: 5px; cursor: pointer;">Очистить</button>
    <span id="guestSearchStatus" style="margin-left: 10px; color: #666; font-size: 14px;"></span>
</div>

<div id="guestsList"></div>

<h2>👥 Зарегистрированные пользователи</h2>

<h3>Управление пользователями:</h3>

<!-- ДОБАВЬТЕ ЭТОТ БЛОК -->
<div style="margin: 15px 0;">
    <input type="text" id="searchUser" placeholder="🔍 Поиск по ID, тарифу, IP..." 
           style="width: 300px; padding: 8px; border: 1px solid #cbd5e0; border-radius: 5px;"
           onkeyup="searchUsers()">
    <button onclick="clearSearch()" style="margin-left: 10px; padding: 8px 15px; border: none; background: #e2e8f0; border-radius: 5px; cursor: pointer;">Очистить</button>
    <span id="searchStatus" style="margin-left: 10px; color: #666; font-size: 14px;"></span>
</div>
<!-- КОНЕЦ БЛОКА -->

<div id="usersList"></div>
            
            <h3>Выдать тариф пользователю:</h3>
            <input type="text" id="userId" placeholder="ID пользователя">
            <select id="planSelect">
                <option value="free">Бесплатный (1 анализ)</option>
                <option value="basic">Базовый (Неограниченное количество анализов)</option>
                <option value="premium">Премиум (50 анализов)</option>
                <option value="unlimited">Безлимитный</option>
            </select>
            <button onclick="setUserPlan()">Выдать тариф</button>
            
            <h3>Статистика калькулятора:</h3>
            <button onclick="showCalculatorStats()">📊 Показать статистику калькулятора</button>
            <div id="calculatorStats" style="display: none; margin-top: 20px; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);"></div>
            
            <h3>Создать нового пользователя:</h3>
            <input type="text" id="newUserId" placeholder="Новый ID пользователя (опционально)">
            <button onclick="createUser()">Создать пользователя</button>
        </div>

        <!-- ========== РАЗДЕЛ EMAIL-РАССЫЛОК ========== -->
        <h2 style="margin-top: 50px; padding-top: 30px; border-top: 2px solid #e2e8f0;">📧 Email-рассылки</h2>
        
        <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
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
        
        <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3>История рассылок</h3>
            <button onclick="loadEmailCampaigns()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-bottom: 20px;">🔄 Обновить список</button>
            <div id="emailCampaignsList"></div>
        </div>

        <!-- TinyMCE CSS/JS -->
        <script src="https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js" referrerpolicy="origin"></script>
        
        <!-- ========== РАЗДЕЛ УПРАВЛЕНИЯ СТАТЬЯМИ ========== -->
        <h2 style="margin-top: 50px; padding-top: 30px; border-top: 2px solid #e2e8f0;">📝 Управление статьями</h2>
        
        <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
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
                    <button type="button" onclick="toggleEditorMode()" id="editorModeBtn" style="background: #4299e1; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem; margin-right: 10px;">📝 Визуальный редактор</button>
                    <button type="button" onclick="insertArticleTemplate()" style="background: #ed8936; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-size: 0.9rem;">📄 Вставить шаблон</button>
                    <span id="editorStatus" style="margin-left: 15px; color: #666; font-size: 0.9rem;">Режим: Визуальный редактор</span>
                </div>
                <!-- TinyMCE редактор -->
                <div id="tinymce-container" style="width: 100%; max-width: 1200px;">
                    <textarea id="articleHtmlContent" rows="20" placeholder="Начните писать статью здесь..."></textarea>
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
        
        <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
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
                        document.getElementById('totalGuests').textContent = stats.total_guests || 0;
                        document.getElementById('totalAnalyses').textContent = stats.total_analyses;
                        document.getElementById('todayAnalyses').textContent = stats.today_analyses;
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
                document.getElementById('searchGuest').value = '';
                searchGuests();
            }
            
            function showUser(userId) {
                // Прокручиваем к пользователям и подсвечиваем нужного
                document.getElementById('usersList').scrollIntoView({ behavior: 'smooth' });
                // Можно добавить подсветку нужной карточки пользователя
                alert('Пользователь: ' + userId);
            }

            function loadUsers() {
                // Очищаем поиск при новой загрузке
    document.getElementById('searchUser').value = '';
    document.getElementById('searchStatus').textContent = '';
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
                const limits = {free: 1, basic: 1000, premium: 50, unlimited: 1000};
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
    const userCards = document.querySelectorAll('.user-card');
    let foundCount = 0;
    
    userCards.forEach(card => {
        const cardText = card.textContent.toLowerCase();
        if (searchTerm === '' || cardText.includes(searchTerm)) {
            card.style.display = 'block';
            foundCount++;
        } else {
            card.style.display = 'none';
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

            // Загружаем при открытии
            loadStats();
            loadUsers();
            loadGuests();
            
            function showCalculatorStats() {
                fetch('/admin/calculator-stats-data', {credentials: 'include'})
                    .then(r => r.json())
                    .then(stats => {
                        let html = `
                            <h3>📊 Статистика калькулятора неустойки</h3>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0;">
                                <div style="background: #f0f7ff; padding: 15px; border-radius: 8px;">
                                    <div style="font-size: 0.9rem; color: #666;">Всего использований</div>
                                    <div style="font-size: 2rem; font-weight: bold; color: #4361ee;">${stats.total_calculator_uses}</div>
                                </div>
                                <div style="background: #f0f7ff; padding: 15px; border-radius: 8px;">
                                    <div style="font-size: 0.9rem; color: #666;">Пользователей использовали</div>
                                    <div style="font-size: 2rem; font-weight: bold; color: #4361ee;">${stats.users_with_calculator_use}/${stats.total_users}</div>
                                </div>
                            </div>
                        `;
                        
                        if (stats.top_users && stats.top_users.length > 0) {
                            html += `<h4>Топ пользователей:</h4><table style="width: 100%; border-collapse: collapse;"><thead><tr><th style="padding: 10px; background: #4361ee; color: white;">ID</th><th style="padding: 10px; background: #4361ee; color: white;">Использований</th><th style="padding: 10px; background: #4361ee; color: white;">Последнее</th></tr></thead><tbody>`;
                            
                            stats.top_users.forEach(user => {
                                html += `<tr><td style="padding: 10px; border-bottom: 1px solid #ddd;">${user[0]}</td><td style="padding: 10px; border-bottom: 1px solid #ddd;">${user[1]}</td><td style="padding: 10px; border-bottom: 1px solid #ddd;">${user[2] || 'Нет данных'}</td></tr>`;
                            });
                            
                            html += `</tbody></table>`;
                        }
                        
                        document.getElementById('calculatorStats').innerHTML = html;
                        document.getElementById('calculatorStats').style.display = 'block';
                    });
            }
            
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
            
            // Загружаем рассылки при открытии
            loadEmailCampaigns();
            
            // ========== ИНИЦИАЛИЗАЦИЯ TINYMCE РЕДАКТОРА ==========
            let tinymceEditor = null;
            let isHtmlMode = false;
            
            function initTinyMCE() {
                if (typeof tinymce !== 'undefined') {
                    tinymce.init({
                        selector: '#articleHtmlContent',
                        height: 600,
                        language: 'ru',
                        menubar: true,
                        plugins: [
                            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
                            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                            'insertdatetime', 'media', 'table', 'code', 'help', 'wordcount',
                            'emoticons', 'template', 'codesample', 'hr', 'pagebreak', 'nonbreaking',
                            'directionality', 'textcolor', 'colorpicker', 'textpattern', 'noneditable'
                        ],
                        toolbar: 'undo redo | blocks | ' +
                            'bold italic underline strikethrough forecolor backcolor | ' +
                            'alignleft aligncenter alignright alignjustify | ' +
                            'bullist numlist outdent indent | ' +
                            'removeformat | link image media table code | ' +
                            'insertdatetime charmap emoticons hr pagebreak | ' +
                            'visualblocks visualchars fullscreen preview | ' +
                            'fontfamily fontsize | ' +
                            'codesample template | ' +
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
                                console.log('✅ TinyMCE редактор загружен');
                            });
                        },
                        branding: false,
                        promotion: false
                    });
                } else {
                    console.error('❌ TinyMCE не загружен. Используйте HTML-режим.');
                }
            }
            
            function toggleEditorMode() {
                const container = document.getElementById('tinymce-container');
                const htmlContainer = document.getElementById('html-editor-container');
                const statusEl = document.getElementById('editorStatus');
                const btn = document.getElementById('editorModeBtn');
                
                if (isHtmlMode) {
                    // Переключаемся на визуальный режим
                    isHtmlMode = false;
                    const htmlContent = document.getElementById('articleHtmlContentRaw').value;
                    
                    if (tinymceEditor) {
                        tinymceEditor.setContent(htmlContent);
                        container.style.display = 'block';
                        htmlContainer.style.display = 'none';
                        statusEl.textContent = 'Режим: Визуальный редактор';
                        btn.textContent = '📝 Визуальный редактор';
                    }
                } else {
                    // Переключаемся на HTML-режим
                    isHtmlMode = true;
                    let htmlContent = '';
                    
                    if (tinymceEditor) {
                        htmlContent = tinymceEditor.getContent();
                    } else {
                        htmlContent = document.getElementById('articleHtmlContent').value;
                    }
                    
                    document.getElementById('articleHtmlContentRaw').value = htmlContent;
                    container.style.display = 'none';
                    htmlContainer.style.display = 'block';
                    statusEl.textContent = 'Режим: HTML-редактор';
                    btn.textContent = '</> HTML-редактор';
                }
            }
            
            function insertArticleTemplate() {
                const template = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #4361ee; border-bottom: 2px solid #4361ee; padding-bottom: 10px; }
        h2 { color: #7209b7; margin-top: 30px; }
        h3 { color: #4cc9f0; }
        .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .info { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .success { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 5px; }
        ul, ol { margin: 15px 0; padding-left: 30px; }
        li { margin: 8px 0; }
        strong { color: #4361ee; }
        blockquote { border-left: 4px solid #7209b7; padding-left: 20px; margin: 20px 0; color: #666; font-style: italic; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background: #4361ee; color: white; }
        tr:nth-child(even) { background: #f8f9fa; }
        img { max-width: 100%; height: auto; border-radius: 8px; margin: 20px 0; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
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
</body>
</html>`;
                
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
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initTinyMCE);
            } else {
                initTinyMCE();
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
        </script>
    </body>
    </html>
    """

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

@admin_bp.route('/stats')
@require_admin_auth
def admin_stats():
    """Статистика для админ-панели"""
    from app import app
    from models.sqlite_users import Guest
    
    stats = app.user_manager.get_stats()
    
    # Добавляем статистику по гостям
    total_guests = Guest.query.filter_by(registered_user_id=None).count()
    stats['total_guests'] = total_guests
    
    return jsonify(stats)

@admin_bp.route('/calculator-stats-data')
@require_admin_auth
def calculator_stats_data():
    """JSON данные статистики калькулятора"""
    from app import app
    
    stats = app.user_manager.get_calculator_stats()
    return jsonify(stats)

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
