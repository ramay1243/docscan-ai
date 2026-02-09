# Скрипт для исправления структуры репозитория на GitHub
# Этот скрипт создаст правильный репозиторий в папке проекта

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Исправление структуры репозитория" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectPath = "C:\Users\Radmil\Desktop\docscan banner"
$repoUrl = "https://github.com/ramay1243/docscan-ai.git"

# Переходим в папку проекта
Set-Location $projectPath

Write-Host "`n[1/5] Удаление старого .git (если есть)..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Remove-Item -Recurse -Force .git
    Write-Host "Старый .git удален" -ForegroundColor Green
}

Write-Host "`n[2/5] Инициализация нового репозитория..." -ForegroundColor Yellow
git init
Write-Host "Репозиторий инициализирован" -ForegroundColor Green

Write-Host "`n[3/5] Добавление удаленного репозитория..." -ForegroundColor Yellow
git remote add origin $repoUrl
Write-Host "Удаленный репозиторий добавлен" -ForegroundColor Green

Write-Host "`n[4/5] Добавление всех файлов проекта..." -ForegroundColor Yellow
git add .
Write-Host "Файлы добавлены" -ForegroundColor Green

Write-Host "`n[5/5] Создание коммита..." -ForegroundColor Yellow
$commitMessage = "Fix: Правильная структура репозитория без вложенных папок"
git commit -m $commitMessage
Write-Host "Коммит создан" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Готово к отправке на GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nВНИМАНИЕ: Будет выполнен force push!" -ForegroundColor Red
Write-Host "Это перезапишет структуру на GitHub!" -ForegroundColor Red
$confirm = Read-Host "`nПродолжить? (y/n)"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    Write-Host "`nОтправка на GitHub..." -ForegroundColor Yellow
    git push origin main --force
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "Готово! Структура исправлена на GitHub" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "Отменено." -ForegroundColor Yellow
}

Write-Host "`nДля продолжения нажмите любую клавишу..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")



# Этот скрипт создаст правильный репозиторий в папке проекта

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Исправление структуры репозитория" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectPath = "C:\Users\Radmil\Desktop\docscan banner"
$repoUrl = "https://github.com/ramay1243/docscan-ai.git"

# Переходим в папку проекта
Set-Location $projectPath

Write-Host "`n[1/5] Удаление старого .git (если есть)..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Remove-Item -Recurse -Force .git
    Write-Host "Старый .git удален" -ForegroundColor Green
}

Write-Host "`n[2/5] Инициализация нового репозитория..." -ForegroundColor Yellow
git init
Write-Host "Репозиторий инициализирован" -ForegroundColor Green

Write-Host "`n[3/5] Добавление удаленного репозитория..." -ForegroundColor Yellow
git remote add origin $repoUrl
Write-Host "Удаленный репозиторий добавлен" -ForegroundColor Green

Write-Host "`n[4/5] Добавление всех файлов проекта..." -ForegroundColor Yellow
git add .
Write-Host "Файлы добавлены" -ForegroundColor Green

Write-Host "`n[5/5] Создание коммита..." -ForegroundColor Yellow
$commitMessage = "Fix: Правильная структура репозитория без вложенных папок"
git commit -m $commitMessage
Write-Host "Коммит создан" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Готово к отправке на GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nВНИМАНИЕ: Будет выполнен force push!" -ForegroundColor Red
Write-Host "Это перезапишет структуру на GitHub!" -ForegroundColor Red
$confirm = Read-Host "`nПродолжить? (y/n)"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    Write-Host "`nОтправка на GitHub..." -ForegroundColor Yellow
    git push origin main --force
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "Готово! Структура исправлена на GitHub" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "Отменено." -ForegroundColor Yellow
}

Write-Host "`nДля продолжения нажмите любую клавишу..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


