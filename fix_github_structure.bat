@echo off
chcp 65001 >nul
echo ========================================
echo Исправление структуры репозитория
echo ========================================
echo.

cd /d "C:\Users\Radmil\Desktop\docscan banner"

echo [1/5] Удаление старого .git...
if exist .git (
    rmdir /s /q .git
    echo Старый .git удален
)

echo.
echo [2/5] Инициализация нового репозитория...
git init
echo Репозиторий инициализирован

echo.
echo [3/5] Добавление удаленного репозитория...
git remote add origin https://github.com/ramay1243/docscan-ai.git
echo Удаленный репозиторий добавлен

echo.
echo [4/5] Добавление всех файлов проекта...
git add .
echo Файлы добавлены

echo.
echo [5/5] Создание коммита...
git commit -m "Fix: Правильная структура репозитория без вложенных папок"
echo Коммит создан

echo.
echo ========================================
echo Готово к отправке на GitHub
echo ========================================
echo.
echo ВНИМАНИЕ: Будет выполнен force push!
echo Это перезапишет структуру на GitHub!
echo.
pause

echo.
echo Отправка на GitHub...
git push origin main --force

echo.
echo ========================================
echo Готово! Структура исправлена на GitHub
echo ========================================
echo.
pause

