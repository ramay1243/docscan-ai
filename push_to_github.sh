#!/bin/bash
# Скрипт для отправки изменений на GitHub

echo "========================================"
echo "Отправка изменений на GitHub"
echo "========================================"
echo ""

cd "c:\Users\Radmil\Desktop\docscan lk" || exit

echo "[1/4] Добавление файлов..."
git add static/templates/proverka-dogovorov.html
git add static/templates/articles.html
git add static/templates/*.html

echo ""
echo "[2/4] Проверка статуса..."
git status --short

echo ""
echo "[3/4] Создание коммита..."
git commit -m "Fix: checkAuth function - get DOM elements once before if/else block"

echo ""
echo "[4/4] Отправка на GitHub..."
git push origin main

echo ""
echo "========================================"
echo "Готово! Изменения отправлены на GitHub"
echo "========================================"


