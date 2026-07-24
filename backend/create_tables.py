# backend/create_tables.py
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.db.session import engine
from src.infrastructure.db.models import Base

def create_tables():
    print("Создание таблиц...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы успешно созданы!")
        
        # Проверяем, какие таблицы создались
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Созданные таблицы: {', '.join(tables)}")
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()