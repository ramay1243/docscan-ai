import sys
import os
import sqlite3
from datetime import datetime

project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)

def get_db_path():
    try:
        from config import Config
        db_uri = Config.SQLALCHEMY_DATABASE_URI
        return db_uri.replace('sqlite:///', '')
    except Exception as e:
        db_path = os.path.join(project_path, 'docscan.db')
        print(f"⚠️ Не удалось загрузить config, используем: {db_path}")
        print(f"   Ошибка: {e}")
        return db_path

def check_table_exists(cursor, table_name):
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def migrate():
    db_path = get_db_path()
    print(f"📁 Используется база данных: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    backup_path = f"{db_path}.backup_full_news_{int(datetime.now().timestamp())}"
    print(f"💾 Создание резервной копии...")
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Резервная копия создана: {backup_path}")
    except Exception as e:
        print(f"❌ Ошибка при создании резервной копии: {e}")
        return False

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if check_table_exists(cursor, 'full_news'):
            print("✅ Таблица 'full_news' уже существует. Пропускаем создание.")
        else:
            print("⚙️ Создание таблицы 'full_news'...")
            cursor.execute("""
                CREATE TABLE full_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug VARCHAR(200) UNIQUE NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    short_description TEXT NOT NULL,
                    full_content TEXT NOT NULL,
                    category VARCHAR(50),
                    image_url VARCHAR(500),
                    author VARCHAR(100) DEFAULT 'Редакция DocScan',
                    meta_title VARCHAR(200),
                    meta_description VARCHAR(500),
                    meta_keywords VARCHAR(300),
                    published_at VARCHAR(30) NOT NULL,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30),
                    is_published BOOLEAN DEFAULT TRUE,
                    views_count INTEGER DEFAULT 0,
                    created_by VARCHAR(50)
                );
            """)
            print("✅ Таблица 'full_news' успешно создана.")
        
        # Добавляем поле full_news_id в таблицу news_items, если его нет
        try:
            cursor.execute("PRAGMA table_info(news_items)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'full_news_id' not in columns:
                print("⚙️ Добавление поля 'full_news_id' в таблицу 'news_items'...")
                cursor.execute("""
                    ALTER TABLE news_items 
                    ADD COLUMN full_news_id INTEGER;
                """)
                print("✅ Поле 'full_news_id' добавлено в таблицу 'news_items'.")
            else:
                print("✅ Поле 'full_news_id' уже существует в таблице 'news_items'.")
        except Exception as e:
            print(f"⚠️ Ошибка при добавлении поля 'full_news_id': {e}")
        
        conn.commit()
        print("🎉 Миграция завершена успешно!")
        return True

    except sqlite3.Error as e:
        print(f"❌ Ошибка SQLite при миграции: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Неизвестная ошибка при миграции: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()

