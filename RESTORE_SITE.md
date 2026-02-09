# Восстановление сломанного сайта

## Способ 1: Через Git (если файлы на GitHub)

### На сервере выполните:

```bash
# 1. Перейдите в папку проекта
cd /var/www/docscan

# 2. Сохраните важные файлы
mkdir -p /var/www/backup
cp /var/www/data/.env /var/www/backup/.env.backup 2>/dev/null || echo ".env не найден"
cp docscan.db /var/www/backup/docscan.db.backup 2>/dev/null || echo "docscan.db не найден"

# 3. Получите последнюю версию с GitHub
git fetch origin
git reset --hard origin/main

# 4. Восстановите .env
if [ -f /var/www/backup/.env.backup ]; then
    cp /var/www/backup/.env.backup /var/www/data/.env
    echo ".env восстановлен"
fi

# 5. Обновите зависимости
pip3 install -r requirements.txt

# 6. Проверьте права доступа
sudo chown -R www-data:www-data /var/www/docscan
sudo chmod -R 755 /var/www/docscan

# 7. Перезапустите
sudo supervisorctl restart docscan

# 8. Проверьте логи
sudo supervisorctl tail -f docscan
```

---

## Способ 2: Через SCP (прямая загрузка с локального компьютера)

### На вашем компьютере (Windows):

```powershell
# Установите WinSCP или используйте команду scp через Git Bash

# Через PowerShell (если установлен OpenSSH):
scp -r "C:\Users\Radmil\Desktop\docscan banner\*" root@ваш_сервер:/var/www/docscan/
```

### Или через WinSCP:
1. Откройте WinSCP
2. Подключитесь к серверу
3. Перетащите все файлы из `C:\Users\Radmil\Desktop\docscan banner\` в `/var/www/docscan/`

---

## Способ 3: Полное пересоздание на сервере

```bash
# 1. Сохраните важные файлы
mkdir -p /var/www/backup
cp /var/www/data/.env /var/www/backup/.env.backup
cp /var/www/docscan/docscan.db /var/www/backup/docscan.db.backup 2>/dev/null || true

# 2. Удалите старую папку
cd /var/www
rm -rf docscan

# 3. Клонируйте заново с GitHub
git clone https://github.com/ramay1243/docscan-ai.git docscan

# 4. Восстановите .env
cp /var/www/backup/.env.backup /var/www/data/.env

# 5. Восстановите базу данных (если нужно)
cp /var/www/backup/docscan.db.backup /var/www/docscan/docscan.db 2>/dev/null || true

# 6. Установите зависимости
cd docscan
pip3 install -r requirements.txt

# 7. Настройте права
sudo chown -R www-data:www-data /var/www/docscan
sudo chmod -R 755 /var/www/docscan
sudo chmod 664 /var/www/docscan/docscan.db 2>/dev/null || true

# 8. Перезапустите
sudo supervisorctl restart docscan
```

---

## Проверка после восстановления

```bash
# 1. Проверьте что сайт работает
curl http://localhost:5000

# 2. Проверьте логи
sudo supervisorctl tail -f docscan

# 3. Проверьте наличие .env
ls -la /var/www/data/.env

# 4. Проверьте базу данных
ls -la /var/www/docscan/docscan.db

# 5. Проверьте что баннер есть
grep -i "Биржа Аудитории" /var/www/docscan/routes/main.py
```

---

## Если сайт все еще не работает

### Проверьте ошибки:

```bash
# Логи приложения
sudo supervisorctl tail -100 docscan

# Логи системы
journalctl -u docscan -n 50

# Проверьте что Python работает
cd /var/www/docscan
python3 -c "import flask; print('Flask OK')"

# Проверьте что все зависимости установлены
pip3 list | grep -i flask
```

### Восстановите .env вручную:

```bash
nano /var/www/data/.env
```

Добавьте:
```env
YANDEX_API_KEY=ваш_ключ
YANDEX_FOLDER_ID=ваш_folder_id
YOOMONEY_CLIENT_ID=ваш_client_id
YOOMONEY_CLIENT_SECRET=ваш_secret
SECRET_KEY=ваш_секретный_ключ
SESSION_COOKIE_SECURE=True
```




## Способ 1: Через Git (если файлы на GitHub)

### На сервере выполните:

```bash
# 1. Перейдите в папку проекта
cd /var/www/docscan

# 2. Сохраните важные файлы
mkdir -p /var/www/backup
cp /var/www/data/.env /var/www/backup/.env.backup 2>/dev/null || echo ".env не найден"
cp docscan.db /var/www/backup/docscan.db.backup 2>/dev/null || echo "docscan.db не найден"

# 3. Получите последнюю версию с GitHub
git fetch origin
git reset --hard origin/main

# 4. Восстановите .env
if [ -f /var/www/backup/.env.backup ]; then
    cp /var/www/backup/.env.backup /var/www/data/.env
    echo ".env восстановлен"
fi

# 5. Обновите зависимости
pip3 install -r requirements.txt

# 6. Проверьте права доступа
sudo chown -R www-data:www-data /var/www/docscan
sudo chmod -R 755 /var/www/docscan

# 7. Перезапустите
sudo supervisorctl restart docscan

# 8. Проверьте логи
sudo supervisorctl tail -f docscan
```

---

## Способ 2: Через SCP (прямая загрузка с локального компьютера)

### На вашем компьютере (Windows):

```powershell
# Установите WinSCP или используйте команду scp через Git Bash

# Через PowerShell (если установлен OpenSSH):
scp -r "C:\Users\Radmil\Desktop\docscan banner\*" root@ваш_сервер:/var/www/docscan/
```

### Или через WinSCP:
1. Откройте WinSCP
2. Подключитесь к серверу
3. Перетащите все файлы из `C:\Users\Radmil\Desktop\docscan banner\` в `/var/www/docscan/`

---

## Способ 3: Полное пересоздание на сервере

```bash
# 1. Сохраните важные файлы
mkdir -p /var/www/backup
cp /var/www/data/.env /var/www/backup/.env.backup
cp /var/www/docscan/docscan.db /var/www/backup/docscan.db.backup 2>/dev/null || true

# 2. Удалите старую папку
cd /var/www
rm -rf docscan

# 3. Клонируйте заново с GitHub
git clone https://github.com/ramay1243/docscan-ai.git docscan

# 4. Восстановите .env
cp /var/www/backup/.env.backup /var/www/data/.env

# 5. Восстановите базу данных (если нужно)
cp /var/www/backup/docscan.db.backup /var/www/docscan/docscan.db 2>/dev/null || true

# 6. Установите зависимости
cd docscan
pip3 install -r requirements.txt

# 7. Настройте права
sudo chown -R www-data:www-data /var/www/docscan
sudo chmod -R 755 /var/www/docscan
sudo chmod 664 /var/www/docscan/docscan.db 2>/dev/null || true

# 8. Перезапустите
sudo supervisorctl restart docscan
```

---

## Проверка после восстановления

```bash
# 1. Проверьте что сайт работает
curl http://localhost:5000

# 2. Проверьте логи
sudo supervisorctl tail -f docscan

# 3. Проверьте наличие .env
ls -la /var/www/data/.env

# 4. Проверьте базу данных
ls -la /var/www/docscan/docscan.db

# 5. Проверьте что баннер есть
grep -i "Биржа Аудитории" /var/www/docscan/routes/main.py
```

---

## Если сайт все еще не работает

### Проверьте ошибки:

```bash
# Логи приложения
sudo supervisorctl tail -100 docscan

# Логи системы
journalctl -u docscan -n 50

# Проверьте что Python работает
cd /var/www/docscan
python3 -c "import flask; print('Flask OK')"

# Проверьте что все зависимости установлены
pip3 list | grep -i flask
```

### Восстановите .env вручную:

```bash
nano /var/www/data/.env
```

Добавьте:
```env
YANDEX_API_KEY=ваш_ключ
YANDEX_FOLDER_ID=ваш_folder_id
YOOMONEY_CLIENT_ID=ваш_client_id
YOOMONEY_CLIENT_SECRET=ваш_secret
SECRET_KEY=ваш_секретный_ключ
SESSION_COOKIE_SECURE=True
```


