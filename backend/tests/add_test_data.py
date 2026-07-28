# backend/add_test_data.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.db.session import SessionLocal
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.depreciation_record import DepreciationRecord
from datetime import datetime, date
from decimal import Decimal

def add_test_data():
    db = SessionLocal()
    try:
        # Проверяем, есть ли данные
        count = db.query(Asset).count()
        if count > 0:
            print(f"В базе уже есть {count} активов")
            return
        
        print("Добавление тестовых данных...")
        
        # Создаем тестовые активы
        assets_data = [
            {
                "inventory_number": "0613202226120160000000001",
                "name": "Здание мобильное конструктивной системы 'Контур'",
                "description": "Мобильное здание для офиса",
                "model": "Контур",
                "asset_type": "building",
                "status": "active",
                "purchase_price": Decimal("131527.98"),
                "current_value": Decimal("131527.98"),
                "department_code": "УВМ УМВД",
                "responsible_person": "Иванов И.И.",
            },
            {
                "inventory_number": "0613202226120160000000002",
                "name": "Здание мобильное конструктивной системы 'Контур'",
                "description": "Мобильное здание для склада",
                "model": "Контур",
                "asset_type": "building",
                "status": "active",
                "purchase_price": Decimal("131527.98"),
                "current_value": Decimal("131527.98"),
                "department_code": "УВМ УМВД",
                "responsible_person": "Иванов И.И.",
            },
            {
                "inventory_number": "0613202226120160000000003",
                "name": "Здание мобильное конструктивной системы 'Контур'",
                "description": "Мобильное здание для персонала",
                "model": "Контур",
                "asset_type": "building",
                "status": "maintenance",
                "purchase_price": Decimal("131531.04"),
                "current_value": Decimal("131531.04"),
                "department_code": "УВМ УМВД",
                "responsible_person": "Петров П.П.",
            },
            {
                "inventory_number": "С21010572764",
                "name": "КОС Кресло 'Престиж'",
                "description": "Офисное кресло для руководителя",
                "model": "Престиж",
                "asset_type": "furniture",
                "status": "active",
                "purchase_price": Decimal("1581.00"),
                "current_value": Decimal("1581.00"),
                "department_code": "УВМ УМВД",
                "responsible_person": "Сидоров С.С.",
            },
            {
                "inventory_number": "С21010572883",
                "name": "Кресло рабочее 'Престиж'",
                "description": "Рабочее кресло для сотрудников",
                "model": "Престиж",
                "asset_type": "furniture",
                "status": "active",
                "purchase_price": Decimal("1250.00"),
                "current_value": Decimal("1250.00"),
                "department_code": "УВМ УМВД",
                "responsible_person": "Сидоров С.С.",
            },
            {
                "inventory_number": "С21010572347",
                "name": "Кресло 'Комфорт GTP' С-38",
                "description": "Офисное кресло повышенной комфортности",
                "model": "Комфорт GTP С-38",
                "asset_type": "furniture",
                "status": "active",
                "purchase_price": Decimal("2430.00"),
                "current_value": Decimal("2430.00"),
                "department_code": "УВМ УМВД",
                "responsible_person": "Сидоров С.С.",
            },
            {
                "inventory_number": "С21010572816",
                "name": "Кресло 'Престиж'",
                "description": "Офисное кресло",
                "model": "Престиж",
                "asset_type": "furniture",
                "status": "written_off",
                "purchase_price": Decimal("1500.60"),
                "current_value": Decimal("0.00"),
                "department_code": "УВМ УМВД",
                "responsible_person": "Сидоров С.С.",
            },
        ]
        
        assets = []
        for data in assets_data:
            asset = Asset(
                inventory_number=data["inventory_number"],
                name=data["name"],
                description=data["description"],
                model=data["model"],
                asset_type=data["asset_type"],
                status=data["status"],
                purchase_price=data["purchase_price"],
                current_value=data["current_value"],
                department_code=data["department_code"],
                responsible_person=data["responsible_person"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(asset)
            db.flush()  # Получаем ID
            assets.append(asset)
        
        db.commit()
        print(f"✅ Добавлено {len(assets)} активов")
        
        # Добавляем записи амортизации для активных активов
        depreciation_count = 0
        for asset in assets:
            if asset.status == "active" and asset.current_value and asset.current_value > 0:
                depreciation = DepreciationRecord(
                    asset_id=asset.id,
                    period_start=date(2024, 1, 1),
                    period_end=date(2024, 12, 31),
                    depreciation_amount=asset.current_value * Decimal("0.1"),
                    accumulated_depreciation=asset.current_value * Decimal("0.1"),
                    book_value_before=asset.current_value,
                    book_value_after=asset.current_value * Decimal("0.9"),
                    rate=Decimal("10.0"),
                    method="linear",
                    created_at=datetime.now(),
                )
                db.add(depreciation)
                depreciation_count += 1
        
        db.commit()
        print(f"✅ Добавлено {depreciation_count} записей амортизации")
        
        # Выводим статистику
        total = db.query(Asset).count()
        active = db.query(Asset).filter(Asset.status == "active").count()
        maintenance = db.query(Asset).filter(Asset.status == "maintenance").count()
        written_off = db.query(Asset).filter(Asset.status == "written_off").count()
        
        print("\n📊 Статистика:")
        print(f"  Всего активов: {total}")
        print(f"  Активных: {active}")
        print(f"  На ремонте: {maintenance}")
        print(f"  Списано: {written_off}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_data()