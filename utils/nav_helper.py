"""Утилита для генерации навигационного меню"""
from flask import session

def get_nav_html(current_page=''):
    """
    Генерирует HTML для навигационного меню
    
    Args:
        current_page: название текущей страницы для активной ссылки
    
    Returns:
        tuple: (nav_html, nav_style, nav_script)
    """
    user_id = session.get('user_id')
    is_authenticated = bool(user_id)
    
    nav_style = """
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }
        .nav-link {
            color: var(--gray);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
            position: relative;
            font-size: 0.9rem;
            white-space: nowrap;
        }
        .nav-link:hover { color: var(--primary); }
        .nav-link.active {
            color: var(--primary);
        }
        .nav-link.active::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--primary);
            border-radius: 2px;
        }
        .cta-button {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 10px 20px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 15px rgba(67, 97, 238, 0.3);
            font-size: 0.85rem;
        }
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(67, 97, 238, 0.4);
        }
        .burger-menu {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: none;
        }
        .burger-icon {
            background: white;
            padding: 15px 12px;
            border-radius: 50%;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            cursor: pointer;
            transition: all 0.3s ease;
            width: 50px;
            height: 50px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }
        .burger-icon:hover {
            background: var(--primary);
            transform: scale(1.1);
        }
        .burger-line {
            width: 20px;
            height: 2px;
            background: var(--dark);
            transition: all 0.3s ease;
        }
        .burger-icon:hover .burger-line {
            background: white;
        }
        .menu-dropdown {
            display: none;
            position: absolute;
            top: 60px;
            right: 0;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            padding: 15px 0;
            min-width: 200px;
            animation: slideDown 0.3s ease;
        }
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .menu-dropdown a {
            display: block;
            padding: 12px 20px;
            text-decoration: none;
            color: var(--dark);
            transition: all 0.2s ease;
            border-bottom: 1px solid var(--border);
        }
        .menu-dropdown a:hover {
            background: var(--primary);
            color: white;
        }
        .menu-dropdown a:last-child {
            border-bottom: none;
        }
        .menu-dropdown.show {
            display: block;
        }
        #mobileAuthButtons, #mobileUserMenu {
            border-top: 1px solid var(--border);
            margin-top: 10px;
            padding-top: 10px;
        }
        #mobileAuthButtons a, #mobileUserMenu a {
            display: block;
        }
        @media (max-width: 768px) {
            .nav-links { display: none; }
            .burger-menu { display: block; }
        }
    """
    
    nav_html = f"""
        <nav class="nav-links">
            <a href="/" class="nav-link {'active' if current_page == 'home' else ''}">Главная</a>
            <a href="/analiz-dokumentov" class="nav-link {'active' if current_page == 'analiz' else ''}">Анализ документов</a>
            <a href="/calculator-penalty" class="nav-link {'active' if current_page == 'calculator' else ''}">Калькулятор</a>
            <a href="/mobile-app" class="nav-link {'active' if current_page == 'mobile' else ''}">Мобильное приложение</a>
            <a href="/articles" class="nav-link {'active' if current_page == 'articles' else ''}">Статьи</a>
            <a href="/faq" class="nav-link {'active' if current_page == 'faq' else ''}">FAQ</a>
            <a href="/contact" class="nav-link {'active' if current_page == 'contact' else ''}">Контакты</a>
            <span id="authButtons" style="display: {'none' if is_authenticated else 'flex'}; gap: 10px; align-items: center;">
                <a href="/login" class="nav-link">Войти</a>
                <a href="/register" class="cta-button">Регистрация</a>
            </span>
            <span id="userMenu" style="display: {'flex' if is_authenticated else 'none'}; gap: 10px; align-items: center;">
                <a href="/cabinet" class="nav-link">Личный кабинет</a>
                <a href="/logout" class="cta-button">Выход</a>
            </span>
        </nav>
        
        <!-- Burger Menu (Mobile) -->
        <div class="burger-menu">
            <div class="burger-icon" onclick="toggleMenu()">
                <div class="burger-line"></div>
                <div class="burger-line"></div>
                <div class="burger-line"></div>
            </div>
            <div class="menu-dropdown" id="menuDropdown">
                <a href="/">🏠 Главная</a>
                <a href="/analiz-dokumentov">📄 Анализ документов</a>
                <a href="/calculator-penalty">🧮 Калькулятор</a>
                <a href="/mobile-app">📱 Приложение</a>
                <a href="/articles">📚 Статьи</a>
                <a href="/faq">❓ FAQ</a>
                <a href="/contact">📞 Контакты</a>
                <div id="mobileAuthButtons" style="display: {'none' if is_authenticated else 'block'};">
                    <a href="/login">🔐 Войти</a>
                    <a href="/register" style="background: var(--primary); color: white; font-weight: 600;">📝 Регистрация</a>
                </div>
                <div id="mobileUserMenu" style="display: {'block' if is_authenticated else 'none'};">
                    <a href="/cabinet">👤 Личный кабинет</a>
                    <a href="/logout" style="color: var(--danger);">🚪 Выход</a>
                </div>
                <a href="https://t.me/docscan_ai" target="_blank">📢 Telegram</a>
            </div>
        </div>
    """
    
    nav_script = """
        function toggleMenu() {
            const dropdown = document.getElementById('menuDropdown');
            dropdown.classList.toggle('show');
        }
        document.addEventListener('click', function(event) {
            const menu = document.querySelector('.burger-menu');
            const dropdown = document.getElementById('menuDropdown');
            if (menu && dropdown && !menu.contains(event.target)) {
                dropdown.classList.remove('show');
            }
        });
        // Проверяем авторизацию для обновления меню
        async function checkAuth() {
            try {
                const response = await fetch('/api/check-auth');
                const data = await response.json();
                const authButtons = document.getElementById('authButtons');
                const userMenu = document.getElementById('userMenu');
                const mobileAuth = document.getElementById('mobileAuthButtons');
                const mobileUser = document.getElementById('mobileUserMenu');
                if (data.authenticated) {
                    if (authButtons) authButtons.style.display = 'none';
                    if (userMenu) userMenu.style.display = 'flex';
                    if (mobileAuth) mobileAuth.style.display = 'none';
                    if (mobileUser) mobileUser.style.display = 'block';
                } else {
                    if (authButtons) authButtons.style.display = 'flex';
                    if (userMenu) userMenu.style.display = 'none';
                    if (mobileAuth) mobileAuth.style.display = 'block';
                    if (mobileUser) mobileUser.style.display = 'none';
                }
            } catch (e) {}
        }
        document.addEventListener('DOMContentLoaded', checkAuth);
    """
    
    return nav_html, nav_style, nav_script

