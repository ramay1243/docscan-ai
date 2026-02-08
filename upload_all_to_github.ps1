# Скрипт для загрузки всех файлов на GitHub
# Использование: .\upload_all_to_github.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Загрузка всех файлов на GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectPath = "C:\Users\Radmil\Desktop\docscan banner"
$repoUrl = "https://github.com/ramay1243/docscan-ai.git"

# Переходим в папку проекта
Set-Location $projectPath

Write-Host "`n[1/4] Добавление всех файлов..." -ForegroundColor Yellow

# Добавляем все файлы проекта (исключая .git, базы данных, и т.д.)
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

Write-Host "[2/4] Проверка статуса..." -ForegroundColor Yellow
git status --short

Write-Host "`n[3/4] Создание коммита..." -ForegroundColor Yellow
$commitMessage = "Update: Обновление всех файлов проекта с баннером"
git commit -m $commitMessage

Write-Host "`n[4/4] Отправка на GitHub..." -ForegroundColor Yellow
Write-Host "ВНИМАНИЕ: Будет выполнен force push!" -ForegroundColor Red
$confirm = Read-Host "Продолжить? (y/n)"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    git push origin main --force
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "Готово! Все файлы отправлены на GitHub" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "Отменено." -ForegroundColor Yellow
}

Write-Host "`nДля продолжения нажмите любую клавишу..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

