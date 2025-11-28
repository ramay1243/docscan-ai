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
});