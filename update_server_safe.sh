#!/bin/bash
# Безопасное обновление сервера с GitHub

echo "========================================"
echo "Безопасное обновление сервера"
echo "========================================"
echo ""

cd /var/www/docscan

# 1. Сохраняем важные файлы
echo "[1/5] Сохранение важных файлов..."
mkdir -p /var/www/backup
cp /var/www/data/.env /var/www/backup/.env.backup 2>/dev/null || echo "⚠️ .env не найден"
cp docscan.db /var/www/backup/docscan.db.backup 2>/dev/null || echo "⚠️ docscan.db не найден"
echo "✅ Резервные копии созданы"

# 2. Получаем обновления
echo ""
echo "[2/5] Получение обновлений с GitHub..."
git fetch origin
echo "✅ Обновления получены"

# 3. Настраиваем стратегию merge
echo ""
echo "[3/5] Настройка стратегии merge..."
git config pull.rebase false
echo "✅ Стратегия настроена"

# 4. Обновляем файлы (полная замена на версию с GitHub)
echo ""
echo "[4/5] Обновление файлов..."
git reset --hard origin/main
echo "✅ Файлы обновлены"

# 5. Восстанавливаем .env
echo ""
echo "[5/5] Восстановление конфигурации..."
if [ -f /var/www/backup/.env.backup ]; then
    cp /var/www/backup/.env.backup /var/www/data/.env
    echo "✅ .env восстановлен"
else
    echo "⚠️ .env.backup не найден, проверьте вручную"
fi

echo ""
echo "========================================"
echo "Обновление завершено!"
echo "========================================"
echo ""
echo "Следующие шаги:"
echo "1. Проверьте .env файл: nano /var/www/data/.env"
echo "2. Обновите зависимости: pip3 install -r requirements.txt"
echo "3. Перезапустите: sudo supervisorctl restart docscan"
echo "4. Проверьте логи: sudo supervisorctl tail -f docscan"
echo ""

