@echo off
chcp 65001 >nul
echo ========================================
echo ПОЛНАЯ ЗАМЕНА ВСЕХ ФАЙЛОВ НА GITHUB
echo ========================================
echo.
echo ВНИМАНИЕ: Это удалит ВСЕ файлы на GitHub
echo и заменит их на локальные файлы!
echo.
pause

cd /d "C:\Users\Radmil\Desktop\docscan banner"

echo.
echo [1/5] Проверка текущей версии...
git log --oneline -1
echo.

echo [2/5] Добавление ВСЕХ файлов проекта...
git add .
echo Файлы добавлены

echo.
echo [3/5] Проверка что будет закоммичено...
git status --short
echo.

echo [4/5] Создание коммита...
git commit -m "Update: Полное обновление всех файлов проекта с баннером"
echo Коммит создан

echo.
echo [5/5] Отправка на GitHub (FORCE PUSH)...
echo ВНИМАНИЕ: Это перезапишет ВСЕ на GitHub!
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
    echo sudo supervisorctl restart docscan
) else (
    echo.
    echo ========================================
    echo ОШИБКА при отправке на GitHub
    echo ========================================
)

echo.
pause

