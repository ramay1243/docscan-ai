@echo off
chcp 65001 >nul
echo ========================================
echo Отправка SEO изменений на GitHub
echo ========================================
echo.

cd /d "C:\Users\Radmil\Desktop\docscan banner"

echo [1/3] Проверка изменений...
git status --short
echo.

echo [2/3] Создание коммита...
git commit -m "SEO: Добавлены Schema.org Article, BreadcrumbList и мета-теги для статей"

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА при создании коммита!
    pause
    exit /b 1
)

echo.
echo [3/3] Отправка на GitHub...
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

echo [1/3] Проверка изменений...
git status --short
echo.

echo [2/3] Создание коммита...
git commit -m "SEO: Добавлены Schema.org Article, BreadcrumbList и мета-теги для статей"

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА при создании коммита!
    pause
    exit /b 1
)

echo.
echo [3/3] Отправка на GitHub...
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


