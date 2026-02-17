"""
Скрипт для восстановления базы данных DocScan AI из резервной копии
Использование:
    python restore_database.py                    # Интерактивный выбор бэкапа
    python restore_database.py --file backup.db.gz  # Восстановить из конкретного файла
    python restore_database.py --list              # Показать список бэкапов
"""
import os
import sys
import shutil
import gzip
from datetime import datetime
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('restore.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
DB_FILE = os.path.join(os.path.dirname(__file__), 'docscan.db')
DB_BACKUP_BEFORE_RESTORE = os.path.join(os.path.dirname(__file__), 'docscan.db.backup_before_restore')

def list_backups():
    """Выводит список всех доступных бэкапов"""
    try:
        if not os.path.exists(BACKUP_DIR):
            print("❌ Папка бэкапов не существует")
            return []
        
        backups = []
        for filename in os.listdir(BACKUP_DIR):
            file_path = os.path.join(BACKUP_DIR, filename)
            if os.path.isfile(file_path) and (filename.startswith('docscan_backup_') and filename.endswith('.db.gz')):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_size = os.path.getsize(file_path)
                size_mb = file_size / (1024 * 1024)
                backups.append({
                    'filename': filename,
                    'path': file_path,
                    'date': file_time,
                    'size': size_mb
                })
        
        # Сортируем по дате (новые первыми)
        backups.sort(key=lambda x: x['date'], reverse=True)
        
        if backups:
            print(f"\n📦 Доступные бэкапы ({len(backups)}):\n")
            print(f"{'№':<5} {'Дата создания':<20} {'Размер':<10} {'Имя файла'}")
            print("-" * 80)
            for i, backup in enumerate(backups, 1):
                date_str = backup['date'].strftime('%Y-%m-%d %H:%M:%S')
                size_str = f"{backup['size']:.2f} MB"
                print(f"{i:<5} {date_str:<20} {size_str:<10} {backup['filename']}")
        else:
            print("❌ Бэкапы не найдены")
        
        return backups
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка бэкапов: {e}")
        return []

def decompress_backup(backup_path, output_path):
    """Распаковывает сжатый бэкап"""
    try:
        logger.info(f"🗜️ Распаковка бэкапа: {os.path.basename(backup_path)}")
        with gzip.open(backup_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        logger.info(f"✅ Бэкап распакован: {output_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка распаковки бэкапа: {e}")
        return False

def restore_from_backup(backup_path):
    """Восстанавливает базу данных из бэкапа"""
    try:
        # Проверяем существование бэкапа
        if not os.path.exists(backup_path):
            logger.error(f"❌ Бэкап не найден: {backup_path}")
            return False
        
        # Создаем резервную копию текущей БД перед восстановлением
        if os.path.exists(DB_FILE):
            logger.info(f"💾 Создание резервной копии текущей БД перед восстановлением...")
            shutil.copy2(DB_FILE, DB_BACKUP_BEFORE_RESTORE)
            logger.info(f"✅ Текущая БД сохранена как: {DB_BACKUP_BEFORE_RESTORE}")
        
        # Определяем, нужно ли распаковывать
        if backup_path.endswith('.gz'):
            # Временный файл для распаковки
            temp_db = DB_FILE + '.temp'
            if not decompress_backup(backup_path, temp_db):
                return False
            # Перемещаем распакованный файл
            shutil.move(temp_db, DB_FILE)
        else:
            # Просто копируем файл
            shutil.copy2(backup_path, DB_FILE)
        
        # Проверяем размер восстановленной БД
        file_size = os.path.getsize(DB_FILE)
        size_mb = file_size / (1024 * 1024)
        
        logger.info(f"✅ База данных успешно восстановлена из бэкапа")
        logger.info(f"📊 Размер восстановленной БД: {size_mb:.2f} MB")
        logger.info(f"📂 Файл: {DB_FILE}")
        
        if os.path.exists(DB_BACKUP_BEFORE_RESTORE):
            logger.info(f"💾 Предыдущая версия БД сохранена как: {DB_BACKUP_BEFORE_RESTORE}")
            logger.info(f"   Вы можете удалить этот файл после проверки восстановления")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка восстановления БД: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Пытаемся восстановить из резервной копии, если что-то пошло не так
        if os.path.exists(DB_BACKUP_BEFORE_RESTORE):
            logger.warning(f"⚠️ Попытка восстановить предыдущую версию БД...")
            try:
                shutil.copy2(DB_BACKUP_BEFORE_RESTORE, DB_FILE)
                logger.info(f"✅ Предыдущая версия БД восстановлена")
            except Exception as restore_error:
                logger.error(f"❌ Критическая ошибка: не удалось восстановить предыдущую версию: {restore_error}")
        
        return False

def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Восстановление базы данных DocScan AI из резервной копии')
    parser.add_argument('--file', type=str, help='Путь к файлу бэкапа')
    parser.add_argument('--list', action='store_true', help='Показать список бэкапов')
    
    args = parser.parse_args()
    
    # Режим списка
    if args.list:
        list_backups()
        return
    
    # Если указан файл напрямую
    if args.file:
        backup_path = args.file
        if not os.path.isabs(backup_path):
            backup_path = os.path.join(BACKUP_DIR, backup_path)
        
        print(f"\n⚠️  ВНИМАНИЕ: Восстановление базы данных!")
        print(f"   Текущая БД будет заменена на версию из бэкапа")
        print(f"   Бэкап: {backup_path}\n")
        
        response = input("Продолжить? (yes/no): ")
        if response.lower() != 'yes':
            print("Отменено")
            return
        
        if restore_from_backup(backup_path):
            print("\n✅ Восстановление завершено успешно!")
        else:
            print("\n❌ Ошибка восстановления. Проверьте логи.")
            sys.exit(1)
        return
    
    # Интерактивный режим
    print("\n📦 Восстановление базы данных DocScan AI из резервной копии\n")
    
    backups = list_backups()
    
    if not backups:
        print("\n❌ Нет доступных бэкапов для восстановления")
        return
    
    print("\n" + "=" * 80)
    print("⚠️  ВНИМАНИЕ: Восстановление базы данных!")
    print("   Текущая БД будет заменена на версию из бэкапа")
    print("   Перед восстановлением будет создана резервная копия текущей БД")
    print("=" * 80 + "\n")
    
    try:
        choice = input(f"Выберите номер бэкапа для восстановления (1-{len(backups)}) или 'q' для отмены: ").strip()
        
        if choice.lower() == 'q':
            print("Отменено")
            return
        
        index = int(choice) - 1
        if index < 0 or index >= len(backups):
            print("❌ Неверный номер")
            return
        
        selected_backup = backups[index]
        backup_path = selected_backup['path']
        
        print(f"\n📦 Выбранный бэкап:")
        print(f"   Файл: {selected_backup['filename']}")
        print(f"   Дата: {selected_backup['date'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Размер: {selected_backup['size']:.2f} MB\n")
        
        confirm = input("Подтвердите восстановление (yes/no): ")
        if confirm.lower() != 'yes':
            print("Отменено")
            return
        
        if restore_from_backup(backup_path):
            print("\n✅ Восстановление завершено успешно!")
            print(f"💾 Предыдущая версия БД сохранена как: {DB_BACKUP_BEFORE_RESTORE}")
        else:
            print("\n❌ Ошибка восстановления. Проверьте логи.")
            sys.exit(1)
            
    except ValueError:
        print("❌ Неверный ввод")
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

