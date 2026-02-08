@echo off
chcp 65001 >nul
echo ========================================
echo Загрузка всех файлов на GitHub
echo ========================================
echo.

cd /d "C:\Users\Radmil\Desktop\docscan banner"

echo [1/4] Добавление всех файлов...
git add app.py
git add config.py
git add requirements.txt
git add runtime.txt
git add *.py
git add *.md
git add *.js
git add *.sh
git add *.bat
git add routes/
git add models/
git add services/
git add utils/
git add static/

echo.
echo [2/4] Проверка статуса...
git status --short

echo.
echo [3/4] Создание коммита...
git commit -m "Update: Обновление всех файлов проекта с баннером"

echo.
echo [4/4] Отправка на GitHub...
echo ВНИМАНИЕ: Будет выполнен force push!
git push origin main --force

echo.
echo ========================================
echo Готово! Все файлы отправлены на GitHub
echo ========================================
echo.
pause

