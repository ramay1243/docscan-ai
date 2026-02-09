@echo off
chcp 65001 >nul
echo ========================================
echo Отправка SEO изменений на GitHub
echo ========================================
echo.

cd /d "C:\Users\Radmil\Desktop\docscan banner"

echo [1/4] Добавление файлов...
git add static/templates/login.html
git add static/templates/register.html
git add static/templates/cabinet.html
git add static/templates/message.html
git add static/templates/forgot_password.html
git add static/templates/reset_password.html
git add static/templates/article_detail.html

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА при добавлении файлов!
    pause
    exit /b 1
)

echo.
echo [2/4] Проверка статуса...
git status --short

echo.
echo [3/4] Создание коммита...
git commit -m "SEO: Добавлены метатеги description и noindex на служебные страницы, fallback для article_detail"

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА при создании коммита!
    pause
    exit /b 1
)

echo.
echo [4/4] Отправка на GitHub...
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Готово! Изменения отправлены на GitHub
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ОШИБКА при отправке на GitHub
    echo ========================================
)

echo.
pause


chcp 65001 >nul
echo ========================================
echo Отправка SEO изменений на GitHub
echo ========================================
echo.

cd /d "C:\Users\Radmil\Desktop\docscan banner"

echo [1/4] Добавление файлов...
git add static/templates/login.html
git add static/templates/register.html
git add static/templates/cabinet.html
git add static/templates/message.html
git add static/templates/forgot_password.html
git add static/templates/reset_password.html
git add static/templates/article_detail.html

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА при добавлении файлов!
    pause
    exit /b 1
)

echo.
echo [2/4] Проверка статуса...
git status --short

echo.
echo [3/4] Создание коммита...
git commit -m "SEO: Добавлены метатеги description и noindex на служебные страницы, fallback для article_detail"

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА при создании коммита!
    pause
    exit /b 1
)

echo.
echo [4/4] Отправка на GitHub...
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Готово! Изменения отправлены на GitHub
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ОШИБКА при отправке на GitHub
    echo ========================================
)

echo.
pause

