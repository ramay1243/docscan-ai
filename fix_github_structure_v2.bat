@echo off
chcp 65001 >nul
echo ========================================
echo Исправление структуры репозитория v2
echo ========================================
echo.

cd /d "C:\Users\Radmil\Desktop\docscan banner"

echo [1/6] Удаление старого .git...
if exist .git (
    rmdir /s /q .git
    echo Старый .git удален
)

echo.
echo [2/6] Инициализация нового репозитория...
git init
echo Репозиторий инициализирован

echo.
echo [3/6] Добавление удаленного репозитория...
git remote add origin https://github.com/ramay1243/docscan-ai.git
echo Удаленный репозиторий добавлен

echo.
echo [4/6] Добавление всех файлов проекта...
git add .
echo Файлы добавлены

echo.
echo [5/6] Создание коммита...
git commit -m "Fix: Правильная структура репозитория без вложенных папок"
echo Коммит создан

echo.
echo [6/6] Переименование ветки в main...
git branch -M main
echo Ветка переименована в main

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

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Готово! Структура исправлена на GitHub
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ОШИБКА при отправке на GitHub
    echo ========================================
    echo.
    echo Попробуйте выполнить вручную:
    echo git push -u origin main --force
)

echo.
pause

