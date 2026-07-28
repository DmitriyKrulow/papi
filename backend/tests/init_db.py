# backend/init_db.py
from src.infrastructure.db.session import engine
from src.infrastructure.db.models import Base
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.depreciation_record import DepreciationRecord
from src.infrastructure.db.session import SessionLocal
from datetime import datetime, date
from decimal import Decimal

def init_database():
    print("Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы!")
    
    # Добавляем тестовые данные
    db = SessionLocal()
    try:
        # Проверяем, есть ли данные
        if db.query(Asset).count() == 0:
            print("Добавление тестовых данных...")
            
            # Создаем тестовые активы
            assets = [
                Asset(
                    inventory_number="0613202226120160000000001",
                    name="Здание мобильное конструктивной системы 'Контур'",
                    description="Мобильное здание",
                    model="Контур",
                    asset_type="building",
                    status="active",
                    purchase_price=Decimal("131527.98"),
                    current_value=Decimal("131527.98"),
                    department_code="УВМ УМВД",
                    responsible_person="Иванов И.И.",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                Asset(
                    inventory_number="0613202226120160000000002",
                    name="Здание мобильное конструктивной системы 'Контур'",
                    description="Мобильное здание",
                    model="Контур",
                    asset_type="building",
                    status="active",
                    purchase_price=Decimal("131527.98"),
                    current_value=Decimal("131527.98"),
                    department_code="УВМ УМВД",
                    responsible_person="Иванов И.И.",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                Asset(
                    inventory_number="0613202226120160000000003",
                    name="Здание мобильное конструктивной системы 'Контур'",
                    description="Мобильное здание",
                    model="Контур",
                    asset_type="building",
                    status="maintenance",
                    purchase_price=Decimal("131531.04"),
                    current_value=Decimal("131531.04"),
                    department_code="УВМ УМВД",
                    responsible_person="Петров П.П.",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                Asset(
                    inventory_number="С21010572764",
                    name="КОС Кресло 'Престиж'",
                    description="Офисное кресло",
                    model="Престиж",
                    asset_type="furniture",
                    status="active",
                    purchase_price=Decimal("1581.00"),
                    current_value=Decimal("1581.00"),
                    department_code="УВМ УМВД",
                    responsible_person="Сидоров С.С.",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                Asset(
                    inventory_number="С21010572883",
                    name="Кресло рабочее 'Престиж'",
                    description="Рабочее кресло",
                    model="Престиж",
                    asset_type="furniture",
                    status="active",
                    purchase_price=Decimal("1250.00"),
                    current_value=Decimal("1250.00"),
                    department_code="УВМ УМВД",
                    responsible_person="Сидоров С.С.",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
            ]
            
            for asset in assets:
                db.add(asset)
            
            db.commit()
            print(f"Добавлено {len(assets)} тестовых активов")
            
            # Добавляем тестовые записи амортизации
            for asset in assets:
                # Проверяем, что current_value существует
                if asset.current_value is not None:
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
            
            db.commit()
            print("Добавлены тестовые записи амортизации")
            
        else:
            print(f"В базе уже есть {db.query(Asset).count()} активов")
            
    except Exception as e:
        print(f"Ошибка при добавлении тестовых данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()