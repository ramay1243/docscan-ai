// Функции для бургер-меню
function toggleMenu() {
    const dropdown = document.getElementById('menuDropdown');
    dropdown.classList.toggle('show');
}

// Закрывать меню при клике вне его
document.addEventListener('click', function(event) {
    const menu = document.querySelector('.burger-menu');
    const dropdown = document.getElementById('menuDropdown');
    
    if (!menu.contains(event.target)) {
        dropdown.classList.remove('show');
    }
    // Добавляем активный класс текущей странице
const currentPath = window.location.pathname;
document.querySelectorAll('.menu-dropdown a').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
        link.style.background = '#667eea';
        link.style.color = 'white';
    }
});
