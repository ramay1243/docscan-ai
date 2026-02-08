# Инструкция по отправке изменений на GitHub

## Вариант 1: Через BAT файл (Windows)

1. Дважды кликните на файл `push_to_github.bat`
2. Скрипт автоматически выполнит все команды

## Вариант 2: Через Git Bash

1. Откройте Git Bash
2. Перейдите в папку проекта:
   ```bash
   cd "c:\Users\Radmil\Desktop\docscan lk"
   ```
3. Выполните скрипт:
   ```bash
   bash push_to_github.sh
   ```

## Вариант 3: Вручную через командную строку

Откройте командную строку (CMD) или PowerShell и выполните:

```bash
cd "c:\Users\Radmil\Desktop\docscan lk"
git add static/templates/proverka-dogovorov.html
git add static/templates/articles.html
git add static/templates/*.html
git commit -m "Fix: checkAuth function - get DOM elements once before if/else block"
git push origin main
```

## Вариант 4: Через VS Code

1. Откройте папку проекта в VS Code
2. Нажмите Ctrl+Shift+G (панель Source Control)
3. Нажмите "+" рядом с измененными файлами
4. Введите сообщение коммита: "Fix: checkAuth function - get DOM elements once before if/else block"
5. Нажмите кнопку галочки (Commit)
6. Нажмите "..." (три точки) → "Push"

## Что делает скрипт:

1. Добавляет все измененные HTML файлы из templates
2. Создает коммит с описанием исправлений
3. Отправляет изменения на GitHub в ветку main


