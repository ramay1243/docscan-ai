"""
Скрипт для резервного копирования базы данных DocScan AI
Использование:
    python backup_database.py              # Создать бэкап с автоматическим именем
    python backup_database.py --manual     # Интерактивный режим
    python backup_database.py --clean     # Удалить старые бэкапы (старше 30 дней)
"""
import os
import sys
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
DB_FILE = os.path.join(os.path.dirname(__file__), 'docscan.db')
MAX_BACKUP_AGE_DAYS = 30  # Удалять бэкапы старше 30 дней
MAX_BACKUPS_COUNT = 50  # Максимальное количество бэкапов (удалять самые старые)

def ensure_backup_dir():
    """Создает папку для бэкапов, если её нет"""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Папка для бэкапов: {BACKUP_DIR}")

def create_backup(compress=True):
    """Создает резервную копию базы данных"""
    try:
        # Проверяем существование БД
        if not os.path.exists(DB_FILE):
            logger.error(f"❌ База данных не найдена: {DB_FILE}")
            return False
        
        # Создаем папку для бэкапов
        ensure_backup_dir()
        
        # Генерируем имя файла с датой и временем
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'docscan_backup_{timestamp}.db'
        if compress:
            backup_filename += '.gz'
        
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Копируем файл БД
        logger.info(f"📦 Создание бэкапа: {backup_filename}")
        shutil.copy2(DB_FILE, backup_path.replace('.gz', ''))
        
        # Сжимаем, если нужно
        if compress:
            logger.info("🗜️ Сжатие бэкапа...")
            with open(backup_path.replace('.gz', ''), 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(backup_path.replace('.gz', ''))
        
        # Получаем размер файла
        file_size = os.path.getsize(backup_path)
        size_mb = file_size / (1024 * 1024)
        
        logger.info(f"✅ Бэкап успешно создан: {backup_filename} ({size_mb:.2f} MB)")
        logger.info(f"📂 Путь: {backup_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания бэкапа: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def clean_old_backups():
    """Удаляет старые бэкапы (старше MAX_BACKUP_AGE_DAYS дней)"""
    try:
        if not os.path.exists(BACKUP_DIR):
            logger.info("📁 Папка бэкапов не существует, нечего удалять")
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=MAX_BACKUP_AGE_DAYS)
        deleted_count = 0
        
        logger.info(f"🧹 Удаление бэкапов старше {MAX_BACKUP_AGE_DAYS} дней...")
        
        for filename in os.listdir(BACKUP_DIR):
            file_path = os.path.join(BACKUP_DIR, filename)
            
            # Пропускаем не файлы
            if not os.path.isfile(file_path):
                continue
            
            # Получаем время модификации файла
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_time < cutoff_date:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"🗑️ Удален старый бэкап: {filename} (создан: {file_time.strftime('%Y-%m-%d %H:%M')})")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить {filename}: {e}")
        
        if deleted_count > 0:
            logger.info(f"✅ Удалено {deleted_count} старых бэкапов")
        else:
            logger.info("✅ Старых бэкапов не найдено")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления старых бэкапов: {e}")
        return 0

def limit_backups_count():
    """Ограничивает количество бэкапов до MAX_BACKUPS_COUNT, удаляя самые старые"""
    try:
        if not os.path.exists(BACKUP_DIR):
            return 0
        
        # Получаем все бэкапы с временем создания
        backups = []
        for filename in os.listdir(BACKUP_DIR):
            file_path = os.path.join(BACKUP_DIR, filename)
            if os.path.isfile(file_path) and (filename.startswith('docscan_backup_') and filename.endswith('.db.gz')):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                backups.append((file_time, file_path, filename))
        
        # Сортируем по времени (старые первыми)
        backups.sort(key=lambda x: x[0])
        
        # Удаляем лишние
        deleted_count = 0
        if len(backups) > MAX_BACKUPS_COUNT:
            to_delete = backups[:len(backups) - MAX_BACKUPS_COUNT]
            for _, file_path, filename in to_delete:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"🗑️ Удален бэкап (превышен лимит): {filename}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить {filename}: {e}")
        
        if deleted_count > 0:
            logger.info(f"✅ Удалено {deleted_count} бэкапов (превышен лимит {MAX_BACKUPS_COUNT})")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Ошибка ограничения количества бэкапов: {e}")
        return 0

def list_backups():
    """Выводит список всех бэкапов"""
    try:
        if not os.path.exists(BACKUP_DIR):
            print("📁 Папка бэкапов не существует")
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
            print(f"\n📦 Найдено бэкапов: {len(backups)}\n")
            print(f"{'№':<5} {'Дата создания':<20} {'Размер':<10} {'Имя файла'}")
            print("-" * 80)
            for i, backup in enumerate(backups, 1):
                date_str = backup['date'].strftime('%Y-%m-%d %H:%M:%S')
                size_str = f"{backup['size']:.2f} MB"
                print(f"{i:<5} {date_str:<20} {size_str:<10} {backup['filename']}")
        else:
            print("📦 Бэкапы не найдены")
        
        return backups
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка бэкапов: {e}")
        return []

def get_backup_info():
    """Получает информацию о бэкапах"""
    try:
        if not os.path.exists(BACKUP_DIR):
            return {
                'total': 0,
                'total_size_mb': 0,
                'oldest': None,
                'newest': None
            }
        
        backups = []
        total_size = 0
        
        for filename in os.listdir(BACKUP_DIR):
            file_path = os.path.join(BACKUP_DIR, filename)
            if os.path.isfile(file_path) and (filename.startswith('docscan_backup_') and filename.endswith('.db.gz')):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_size = os.path.getsize(file_path)
                total_size += file_size
                backups.append((file_time, file_size))
        
        if backups:
            backups.sort(key=lambda x: x[0])
            return {
                'total': len(backups),
                'total_size_mb': total_size / (1024 * 1024),
                'oldest': backups[0][0],
                'newest': backups[-1][0]
            }
        else:
            return {
                'total': 0,
                'total_size_mb': 0,
                'oldest': None,
                'newest': None
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о бэкапах: {e}")
        return None

def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Резервное копирование базы данных DocScan AI')
    parser.add_argument('--manual', action='store_true', help='Интерактивный режим')
    parser.add_argument('--clean', action='store_true', help='Удалить старые бэкапы')
    parser.add_argument('--list', action='store_true', help='Показать список бэкапов')
    parser.add_argument('--info', action='store_true', help='Показать информацию о бэкапах')
    parser.add_argument('--no-compress', action='store_true', help='Не сжимать бэкап')
    
    args = parser.parse_args()
    
    # Режим списка
    if args.list:
        list_backups()
        return
    
    # Режим информации
    if args.info:
        info = get_backup_info()
        if info:
            print(f"\n📊 Информация о бэкапах:")
            print(f"   Всего бэкапов: {info['total']}")
            print(f"   Общий размер: {info['total_size_mb']:.2f} MB")
            if info['oldest']:
                print(f"   Самый старый: {info['oldest'].strftime('%Y-%m-%d %H:%M:%S')}")
            if info['newest']:
                print(f"   Самый новый: {info['newest'].strftime('%Y-%m-%d %H:%M:%S')}")
        return
    
    # Режим очистки
    if args.clean:
        clean_old_backups()
        limit_backups_count()
        return
    
    # Режим создания бэкапа
    if args.manual:
        print("\n📦 Создание резервной копии базы данных DocScan AI\n")
        print(f"База данных: {DB_FILE}")
        print(f"Папка бэкапов: {BACKUP_DIR}\n")
        
        response = input("Создать бэкап? (y/n): ")
        if response.lower() != 'y':
            print("Отменено")
            return
    
    # Создаем бэкап
    success = create_backup(compress=not args.no_compress)
    
    if success:
        # Очищаем старые бэкапы
        clean_old_backups()
        # Ограничиваем количество
        limit_backups_count()
        print("\n✅ Резервное копирование завершено успешно!")
    else:
        print("\n❌ Ошибка создания бэкапа. Проверьте логи.")
        sys.exit(1)

if __name__ == '__main__':
    main()

