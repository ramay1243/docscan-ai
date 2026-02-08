// Универсальная функция checkAuth для всех страниц
// Добавить в каждый HTML файл в секцию <script>
function checkAuthUniversal() {
    return new Promise(async (resolve) => {
        try {
            const response = await fetch('/api/check-auth', {
                credentials: 'include',
                cache: 'no-cache'
            });
            
            if (!response.ok) {
                console.error('Auth check failed:', response.status);
                resolve(false);
                return;
            }
            
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
                console.log('✅ User authenticated:', data.email);
            } else {
                if (authButtons) authButtons.style.display = 'flex';
                if (userMenu) userMenu.style.display = 'none';
                if (mobileAuth) mobileAuth.style.display = 'block';
                if (mobileUser) mobileUser.style.display = 'none';
                console.log('❌ User not authenticated');
            }
            
            resolve(data.authenticated);
        } catch (error) {
            console.error('Auth check error:', error);
            // При ошибке показываем кнопки авторизации
            const authButtons = document.getElementById('authButtons');
            const userMenu = document.getElementById('userMenu');
            const mobileAuth = document.getElementById('mobileAuthButtons');
            const mobileUser = document.getElementById('mobileUserMenu');
            if (authButtons) authButtons.style.display = 'flex';
            if (userMenu) userMenu.style.display = 'none';
            if (mobileAuth) mobileAuth.style.display = 'block';
            if (mobileUser) mobileUser.style.display = 'none';
            resolve(false);
        }
    });
}

// Вызываем при загрузке и после небольших задержек для надежности
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        checkAuthUniversal();
        setTimeout(checkAuthUniversal, 300);
        setTimeout(checkAuthUniversal, 1000);
    });
} else {
    // DOM уже загружен
    checkAuthUniversal();
    setTimeout(checkAuthUniversal, 300);
    setTimeout(checkAuthUniversal, 1000);
}


