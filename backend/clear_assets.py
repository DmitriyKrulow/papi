# backend/clear_assets.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.db.session import SessionLocal
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.depreciation_record import DepreciationRecord

def clear_assets():
    db = SessionLocal()
    try:
        print(f"Удаление записей амортизации...")
        depreciation_count = db.query(DepreciationRecord).delete()
        print(f"Удалено записей амортизации: {depreciation_count}")
        
        print(f"Удаление активов...")
        asset_count = db.query(Asset).delete()
        print(f"Удалено активов: {asset_count}")
        
        db.commit()
        print("\n[OK] Все данные из таблиц активов и амортизации удалены")
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    clear_assets()
