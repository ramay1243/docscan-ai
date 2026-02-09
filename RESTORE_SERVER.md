# Восстановление сервера до правильной версии

## Проблема
После `git reset --hard origin/main` на сервере загрузилась старая версия сайта.

## Решение: Обновить до последней версии с GitHub

### Шаг 1: Проверьте что на сервере

```bash
cd /var/www/docscan

# Проверьте текущий коммит
git log --oneline -1

# Проверьте есть ли баннер в routes/main.py
grep -i "ad-banner\|Биржа Аудитории" routes/main.py
```

Если баннера нет - значит старая версия.

### Шаг 2: Сохраните важные файлы

```bash
# Сохраните .env и базу данных
mkdir -p /var/www/backup
cp /var/www/data/.env /var/www/backup/.env.backup
cp docscan.db /var/www/backup/docscan.db.backup
```

### Шаг 3: Получите последнюю версию с GitHub

```bash
# Получите все обновления
git fetch origin

# Проверьте что есть на GitHub
git log origin/main --oneline -5

# Должен быть коммит: "Fix: Правильная структура репозитория без вложенных папок"
```

### Шаг 4: Обновите до последней версии

```bash
# Полностью замените на версию с GitHub
git reset --hard origin/main

# Проверьте что обновилось
git log --oneline -1
# Должен показать: b83a2ea Fix: Правильная структура репозитория...
```

### Шаг 5: Восстановите конфигурацию

```bash
# Восстановите .env
cp /var/www/backup/.env.backup /var/www/data/.env

# Проверьте что файл на месте
ls -la /var/www/data/.env
```

### Шаг 6: Обновите зависимости

```bash
# Установите зависимости
pip3 install -r requirements.txt
```

### Шаг 7: Проверьте что баннер есть

```bash
# Проверьте что баннер в файле
grep -i "Биржа Аудитории" routes/main.py

# Должно показать строки с баннером
```

### Шаг 8: Перезапустите приложение

```bash
# Перезапустите
sudo supervisorctl restart docscan

# Проверьте статус
sudo supervisorctl status docscan

# Проверьте логи
sudo supervisorctl tail -f docscan
```

### Шаг 9: Проверьте работу сайта

```bash
# Проверьте что сайт работает
curl http://localhost:5000

# Или откройте в браузере
# https://docscan-ai.ru
```

---

## Если все еще старая версия

### Вариант 1: Принудительное обновление

```bash
cd /var/www/docscan

# Удалите все локальные изменения
git fetch origin
git reset --hard origin/main
git clean -fd

# Восстановите .env
cp /var/www/backup/.env.backup /var/www/data/.env

# Перезапустите
sudo supervisorctl restart docscan
```

### Вариант 2: Пересоздать репозиторий на сервере

```bash
cd /var/www

# Сохраните важные файлы
mkdir -p backup
cp docscan/docscan.db backup/
cp data/.env backup/

# Удалите старый репозиторий
cd docscan
rm -rf .git

# Клонируйте заново
cd ..
rm -rf docscan
git clone https://github.com/ramay1243/docscan-ai.git docscan

# Восстановите файлы
cp backup/.env data/.env
cp backup/docscan.db docscan/docscan.db

# Установите зависимости
cd docscan
pip3 install -r requirements.txt

# Перезапустите
sudo supervisorctl restart docscan
```

---

## Проверка правильной версии

Правильная версия должна содержать в `routes/main.py`:
- CSS стили `.ad-banner` (около строки 804)
- JavaScript функции `closeAdBanner()`, `initAdBanner()` (около строки 1799)
- HTML разметку баннера с "Биржа Аудитории" (около строки 1950)

Если этого нет - версия старая, нужно обновить.




## Проблема
После `git reset --hard origin/main` на сервере загрузилась старая версия сайта.

## Решение: Обновить до последней версии с GitHub

### Шаг 1: Проверьте что на сервере

```bash
cd /var/www/docscan

# Проверьте текущий коммит
git log --oneline -1

# Проверьте есть ли баннер в routes/main.py
grep -i "ad-banner\|Биржа Аудитории" routes/main.py
```

Если баннера нет - значит старая версия.

### Шаг 2: Сохраните важные файлы

```bash
# Сохраните .env и базу данных
mkdir -p /var/www/backup
cp /var/www/data/.env /var/www/backup/.env.backup
cp docscan.db /var/www/backup/docscan.db.backup
```

### Шаг 3: Получите последнюю версию с GitHub

```bash
# Получите все обновления
git fetch origin

# Проверьте что есть на GitHub
git log origin/main --oneline -5

# Должен быть коммит: "Fix: Правильная структура репозитория без вложенных папок"
```

### Шаг 4: Обновите до последней версии

```bash
# Полностью замените на версию с GitHub
git reset --hard origin/main

# Проверьте что обновилось
git log --oneline -1
# Должен показать: b83a2ea Fix: Правильная структура репозитория...
```

### Шаг 5: Восстановите конфигурацию

```bash
# Восстановите .env
cp /var/www/backup/.env.backup /var/www/data/.env

# Проверьте что файл на месте
ls -la /var/www/data/.env
```

### Шаг 6: Обновите зависимости

```bash
# Установите зависимости
pip3 install -r requirements.txt
```

### Шаг 7: Проверьте что баннер есть

```bash
# Проверьте что баннер в файле
grep -i "Биржа Аудитории" routes/main.py

# Должно показать строки с баннером
```

### Шаг 8: Перезапустите приложение

```bash
# Перезапустите
sudo supervisorctl restart docscan

# Проверьте статус
sudo supervisorctl status docscan

# Проверьте логи
sudo supervisorctl tail -f docscan
```

### Шаг 9: Проверьте работу сайта

```bash
# Проверьте что сайт работает
curl http://localhost:5000

# Или откройте в браузере
# https://docscan-ai.ru
```

---

## Если все еще старая версия

### Вариант 1: Принудительное обновление

```bash
cd /var/www/docscan

# Удалите все локальные изменения
git fetch origin
git reset --hard origin/main
git clean -fd

# Восстановите .env
cp /var/www/backup/.env.backup /var/www/data/.env

# Перезапустите
sudo supervisorctl restart docscan
```

### Вариант 2: Пересоздать репозиторий на сервере

```bash
cd /var/www

# Сохраните важные файлы
mkdir -p backup
cp docscan/docscan.db backup/
cp data/.env backup/

# Удалите старый репозиторий
cd docscan
rm -rf .git

# Клонируйте заново
cd ..
rm -rf docscan
git clone https://github.com/ramay1243/docscan-ai.git docscan

# Восстановите файлы
cp backup/.env data/.env
cp backup/docscan.db docscan/docscan.db

# Установите зависимости
cd docscan
pip3 install -r requirements.txt

# Перезапустите
sudo supervisorctl restart docscan
```

---

## Проверка правильной версии

Правильная версия должна содержать в `routes/main.py`:
- CSS стили `.ad-banner` (около строки 804)
- JavaScript функции `closeAdBanner()`, `initAdBanner()` (около строки 1799)
- HTML разметку баннера с "Биржа Аудитории" (около строки 1950)

Если этого нет - версия старая, нужно обновить.


