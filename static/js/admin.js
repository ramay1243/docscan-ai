// Admin Panel JavaScript
// Extracted from routes/admin.py

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
            } else if (sectionName === 'api-keys') {
                console.log('📥 Секция API-ключей открыта');
                // Очищаем форму при открытии секции
                if (document.getElementById('apiKeyUserId')) {
                    document.getElementById('apiKeyUserId').value = '';
                }
                if (document.getElementById('newApiKeyUserId')) {
                    document.getElementById('newApiKeyUserId').value = '';
                }
                if (document.getElementById('newApiKeyName')) {
                    document.getElementById('newApiKeyName').value = '';
                }
                if (document.getElementById('apiKeysList')) {
                    document.getElementById('apiKeysList').innerHTML = '';
                }
                if (document.getElementById('apiKeyStatus')) {
                    document.getElementById('apiKeyStatus').textContent = '';
                }
                if (document.getElementById('newApiKeyResult')) {
                    document.getElementById('newApiKeyResult').style.display = 'none';
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
                                <button class="set-plan-btn" data-user-id="${user.userId || ''}" data-plan="basic" style="font-size: 0.85rem; padding: 5px 10px;">Базовый</button>
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
        
        // Функции для управления API-ключами
        function loadAPIKeys() {
            const userId = document.getElementById('apiKeyUserId').value.trim();
            if (!userId) {
                alert('Введите ID пользователя');
                return;
            }
            
            fetch(`/admin/api-keys?user_id=${userId}`)
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        const listDiv = document.getElementById('apiKeysList');
                        if (result.keys.length === 0) {
                            listDiv.innerHTML = '<p style="color: #666;">У пользователя нет API-ключей</p>';
                            return;
                        }
                        
                        let html = '<h4 style="margin-bottom: 15px;">API-ключи пользователя:</h4>';
                        html += '<table style="width: 100%; border-collapse: collapse;">';
                        html += '<thead><tr style="background: #edf2f7; border-bottom: 2px solid #cbd5e0;">';
                        html += '<th style="padding: 10px; text-align: left;">Название</th>';
                        html += '<th style="padding: 10px; text-align: left;">Ключ</th>';
                        html += '<th style="padding: 10px; text-align: left;">Запросов</th>';
                        html += '<th style="padding: 10px; text-align: left;">Последнее использование</th>';
                        html += '<th style="padding: 10px; text-align: left;">Статус</th>';
                        html += '<th style="padding: 10px; text-align: left;">Действия</th>';
                        html += '</tr></thead><tbody>';
                        
                        result.keys.forEach(key => {
                            html += '<tr style="border-bottom: 1px solid #e2e8f0;">';
                            html += `<td style="padding: 10px;">${key.name || 'Без названия'}</td>`;
                            html += `<td style="padding: 10px; font-family: monospace; font-size: 0.85rem;">${key.api_key}</td>`;
                            html += `<td style="padding: 10px;">${key.requests_count || 0}</td>`;
                            html += `<td style="padding: 10px;">${key.last_used || 'Никогда'}</td>`;
                            html += `<td style="padding: 10px;">${key.is_active ? '<span style="color: #48bb78;">Активен</span>' : '<span style="color: #e53e3e;">Неактивен</span>'}</td>`;
                            html += '<td style="padding: 10px;">';
                            if (key.is_active) {
                                html += `<button onclick="deactivateAPIKey(${key.id}, '${userId}')" style="background: #ed8936; color: white; padding: 5px 10px; border: none; border-radius: 3px; cursor: pointer; margin-right: 5px;">Деактивировать</button>`;
                            }
                            html += `<button onclick="deleteAPIKey(${key.id}, '${userId}')" style="background: #e53e3e; color: white; padding: 5px 10px; border: none; border-radius: 3px; cursor: pointer;">Удалить</button>`;
                            html += '</td></tr>';
                        });
                        
                        html += '</tbody></table>';
                        listDiv.innerHTML = html;
                        document.getElementById('apiKeyStatus').textContent = `Найдено ключей: ${result.keys.length}`;
                    } else {
                        alert('Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('Ошибка соединения');
                });
        }
        
        function createAPIKey() {
            const userId = document.getElementById('newApiKeyUserId').value.trim();
            const name = document.getElementById('newApiKeyName').value.trim();
            
            if (!userId) {
                alert('Введите ID пользователя');
                return;
            }
            
            fetch('/admin/api-keys/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_id: userId, name: name || null})
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        document.getElementById('newApiKeyValue').textContent = result.api_key;
                        document.getElementById('newApiKeyResult').style.display = 'block';
                        document.getElementById('newApiKeyUserId').value = '';
                        document.getElementById('newApiKeyName').value = '';
                        if (document.getElementById('apiKeyUserId').value === userId) {
                            loadAPIKeys();
                        }
                    } else {
                        alert('Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('Ошибка соединения');
                });
        }
        
        function deactivateAPIKey(apiKeyId, userId) {
            if (!confirm('Вы уверены, что хотите деактивировать этот API-ключ?')) {
                return;
            }
            
            fetch('/admin/api-keys/deactivate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({api_key_id: apiKeyId, user_id: userId})
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        loadAPIKeys();
                    } else {
                        alert('Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('Ошибка соединения');
                });
        }
        
        function deleteAPIKey(apiKeyId, userId) {
            if (!confirm('Вы уверены, что хотите удалить этот API-ключ? Это действие нельзя отменить!')) {
                return;
            }
            
            fetch('/admin/api-keys/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({api_key_id: apiKeyId, user_id: userId})
            })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        loadAPIKeys();
                    } else {
                        alert('Ошибка: ' + result.error);
                    }
                })
                .catch(err => {
                    alert('Ошибка соединения');
                });
        }
        
        // Регистрируем функции API-ключей глобально
        if (typeof loadAPIKeys === 'function') {
            window.loadAPIKeys = loadAPIKeys;
        }
        if (typeof createAPIKey === 'function') {
            window.createAPIKey = createAPIKey;
        }
        if (typeof deactivateAPIKey === 'function') {
            window.deactivateAPIKey = deactivateAPIKey;
        }
        if (typeof deleteAPIKey === 'function') {
            window.deleteAPIKey = deleteAPIKey;
        }

// Глобальная регистрация всех функций для доступа из onclick атрибутов
(function() {
    'use strict';
    
    // Список всех функций, которые должны быть глобально доступны
    const globalFunctions = [
        'showSection', 'logout', 'toggleMobileMenu',
        'loadStats', 'loadUsers', 'loadGuests', 'loadBots', 'loadNews', 'loadFullNews',
        'loadQuestions', 'loadArticles', 'loadEmailCampaigns', 'loadBackups',
        'loadNotificationsHistory', 'loadPartners', 'loadReferrals', 'loadRewards',
        'loadWhitelistedIPs', 'setUserPlan', 'setUserPlanQuick', 'createUser',
        'searchUsers', 'clearSearch', 'searchGuests', 'clearGuestSearch',
        'searchBots', 'clearBotSearch', 'createCampaign', 'createArticle',
        'clearArticleForm', 'showNewsForm', 'editNews', 'saveNews', 'cancelNewsForm',
        'deleteNews', 'showFullNewsForm', 'editFullNews', 'saveFullNews',
        'cancelFullNewsForm', 'deleteFullNews', 'initFullNewsTinyMCE',
        'toggleFullNewsEditorMode', 'initFullNewsEditorOnShow',
        'viewAdminQuestion', 'closeAdminQuestion', 'openAdminQuestion',
        'solveAdminQuestion', 'deleteAdminQuestion', 'showQuestionAnswers',
        'deleteAdminAnswer', 'closeModal', 'sendAdminNotification',
        'addWhitelistedIP', 'removeWhitelistedIP', 'toggleWhitelistedIP',
        'loadBranding', 'saveBranding', 'toggleBrandingActive', 'deleteBranding',
        'createBackup', 'deleteBackup', 'cleanOldBackups', 'showUser',
        'loadNewUsers', 'loadPayments', 'showCalculatorStats'
    ];
    
    // Регистрируем все функции
    globalFunctions.forEach(funcName => {
        try {
            if (typeof window[funcName] === 'undefined' && typeof eval(funcName) === 'function') {
                window[funcName] = eval(funcName);
            }
        } catch(e) {
            // Игнорируем ошибки для функций, которые еще не определены
        }
    });
    
    console.log('✅ Все функции зарегистрированы глобально');
})();