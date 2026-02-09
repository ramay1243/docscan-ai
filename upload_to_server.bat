@echo off
chcp 65001 >nul
echo ========================================
echo Загрузка файлов на сервер через SCP
echo ========================================
echo.
echo ВАЖНО: Убедитесь что у вас установлен OpenSSH
echo или используйте WinSCP для загрузки файлов
echo.
echo Введите данные сервера:
echo.
set /p SERVER="IP или домен сервера: "
set /p USER="Пользователь (обычно root): "

if "%USER%"=="" set USER=root

echo.
echo Загрузка файлов на сервер...
echo Сервер: %USER%@%SERVER%
echo Папка: /var/www/docscan
echo.
pause

echo.
echo Загрузка через SCP...
scp -r "C:\Users\Radmil\Desktop\docscan banner\*" %USER%@%SERVER%:/var/www/docscan/

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Файлы загружены!
    echo ========================================
    echo.
    echo Теперь на сервере выполните:
    echo cd /var/www/docscan
    echo cp /var/www/backup/.env.backup /var/www/data/.env
    echo pip3 install -r requirements.txt
    echo sudo supervisorctl restart docscan
) else (
    echo.
    echo ========================================
    echo ОШИБКА при загрузке
    echo ========================================
    echo.
    echo Используйте WinSCP для загрузки файлов вручную:
    echo 1. Откройте WinSCP
    echo 2. Подключитесь к серверу
    echo 3. Перетащите файлы из папки проекта в /var/www/docscan
)

echo.
pause



chcp 65001 >nul
echo ========================================
echo Загрузка файлов на сервер через SCP
echo ========================================
echo.
echo ВАЖНО: Убедитесь что у вас установлен OpenSSH
echo или используйте WinSCP для загрузки файлов
echo.
echo Введите данные сервера:
echo.
set /p SERVER="IP или домен сервера: "
set /p USER="Пользователь (обычно root): "

if "%USER%"=="" set USER=root

echo.
echo Загрузка файлов на сервер...
echo Сервер: %USER%@%SERVER%
echo Папка: /var/www/docscan
echo.
pause

echo.
echo Загрузка через SCP...
scp -r "C:\Users\Radmil\Desktop\docscan banner\*" %USER%@%SERVER%:/var/www/docscan/

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Файлы загружены!
    echo ========================================
    echo.
    echo Теперь на сервере выполните:
    echo cd /var/www/docscan
    echo cp /var/www/backup/.env.backup /var/www/data/.env
    echo pip3 install -r requirements.txt
    echo sudo supervisorctl restart docscan
) else (
    echo.
    echo ========================================
    echo ОШИБКА при загрузке
    echo ========================================
    echo.
    echo Используйте WinSCP для загрузки файлов вручную:
    echo 1. Откройте WinSCP
    echo 2. Подключитесь к серверу
    echo 3. Перетащите файлы из папки проекта в /var/www/docscan
)

echo.
pause


