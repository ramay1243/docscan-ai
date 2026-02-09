@echo off
chcp 65001 >nul
echo ========================================
echo ПОЛНОЕ УДАЛЕНИЕ И ЗАГРУЗКА НОВЫХ ФАЙЛОВ
echo ========================================
echo.
echo ВНИМАНИЕ: Это УДАЛИТ ВСЕ файлы на GitHub
echo и загрузит ВСЕ локальные файлы!
echo.
echo Убедитесь что локальные файлы правильные!
echo.
pause

cd /d "C:\Users\Radmil\Desktop\docscan banner"

echo.
echo [1/6] Проверка локальных файлов...
if exist routes\main.py (
    echo Файл routes\main.py найден
    findstr /i "Биржа Аудитории" routes\main.py >nul
    if %ERRORLEVEL% EQU 0 (
        echo Баннер найден в файле - OK
    ) else (
        echo ВНИМАНИЕ: Баннер НЕ найден в файле!
        pause
    )
) else (
    echo ОШИБКА: routes\main.py не найден!
    pause
    exit /b 1
)

echo.
echo [2/6] Добавление ВСЕХ файлов...
git add -A
echo Все файлы добавлены

echo.
echo [3/6] Проверка что будет закоммичено...
git status --short
echo.
pause

echo.
echo [4/6] Создание коммита...
git commit -m "Complete: Полная замена всех файлов проекта"
if %ERRORLEVEL% NEQ 0 (
    echo ВНИМАНИЕ: Коммит не создан (возможно нет изменений)
    echo Продолжаем...
)

echo.
echo [5/6] Проверка текущей ветки...
git branch
echo.

echo.
echo [6/6] Отправка на GitHub (FORCE PUSH)...
echo.
echo ВНИМАНИЕ: Это полностью перезапишет GitHub!
echo Все старые файлы будут удалены!
echo.
pause

git push origin main --force

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Готово! Все файлы заменены на GitHub
    echo ========================================
    echo.
    echo Теперь на сервере выполните:
    echo cd /var/www/docscan
    echo git fetch origin
    echo git reset --hard origin/main
    echo cp /var/www/backup/.env.backup /var/www/data/.env
    echo pip3 install -r requirements.txt
    echo sudo supervisorctl restart docscan
) else (
    echo.
    echo ========================================
    echo ОШИБКА при отправке на GitHub
    echo ========================================
    echo.
    echo Попробуйте выполнить вручную:
    echo git push origin main --force
)

echo.
pause



chcp 65001 >nul
echo ========================================
echo ПОЛНОЕ УДАЛЕНИЕ И ЗАГРУЗКА НОВЫХ ФАЙЛОВ
echo ========================================
echo.
echo ВНИМАНИЕ: Это УДАЛИТ ВСЕ файлы на GitHub
echo и загрузит ВСЕ локальные файлы!
echo.
echo Убедитесь что локальные файлы правильные!
echo.
pause

cd /d "C:\Users\Radmil\Desktop\docscan banner"

echo.
echo [1/6] Проверка локальных файлов...
if exist routes\main.py (
    echo Файл routes\main.py найден
    findstr /i "Биржа Аудитории" routes\main.py >nul
    if %ERRORLEVEL% EQU 0 (
        echo Баннер найден в файле - OK
    ) else (
        echo ВНИМАНИЕ: Баннер НЕ найден в файле!
        pause
    )
) else (
    echo ОШИБКА: routes\main.py не найден!
    pause
    exit /b 1
)

echo.
echo [2/6] Добавление ВСЕХ файлов...
git add -A
echo Все файлы добавлены

echo.
echo [3/6] Проверка что будет закоммичено...
git status --short
echo.
pause

echo.
echo [4/6] Создание коммита...
git commit -m "Complete: Полная замена всех файлов проекта"
if %ERRORLEVEL% NEQ 0 (
    echo ВНИМАНИЕ: Коммит не создан (возможно нет изменений)
    echo Продолжаем...
)

echo.
echo [5/6] Проверка текущей ветки...
git branch
echo.

echo.
echo [6/6] Отправка на GitHub (FORCE PUSH)...
echo.
echo ВНИМАНИЕ: Это полностью перезапишет GitHub!
echo Все старые файлы будут удалены!
echo.
pause

git push origin main --force

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Готово! Все файлы заменены на GitHub
    echo ========================================
    echo.
    echo Теперь на сервере выполните:
    echo cd /var/www/docscan
    echo git fetch origin
    echo git reset --hard origin/main
    echo cp /var/www/backup/.env.backup /var/www/data/.env
    echo pip3 install -r requirements.txt
    echo sudo supervisorctl restart docscan
) else (
    echo.
    echo ========================================
    echo ОШИБКА при отправке на GitHub
    echo ========================================
    echo.
    echo Попробуйте выполнить вручную:
    echo git push origin main --force
)

echo.
pause


