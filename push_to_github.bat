@echo off
echo ========================================
echo Отправка изменений на GitHub
echo ========================================
echo.

cd /d "c:\Users\Radmil\Desktop\docscan lk"

echo [1/4] Добавление файлов...
git add -A

echo.
echo [2/4] Проверка статуса...
git status --short

echo.
echo [3/4] Создание коммита...
git commit -m "Fix: checkAuth function - get DOM elements once on all pages for consistent auth status"

echo.
echo [4/4] Отправка на GitHub...
git push origin main

echo.
echo ========================================
echo Готово! Изменения отправлены на GitHub
echo ========================================
pause

