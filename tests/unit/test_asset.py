# tests/unit/test_asset.py
from datetime import date
import pytest
from backend.src.core.entities.asset import Asset
from backend.src.core.value_objects import AssetStatus, InventoryNumber


class TestAssetEntity:
    """Тесты сущности Asset"""

    def test_create_asset_with_valid_data(self):
        """Создание актива с валидными данными"""
        inventory_number = InventoryNumber("IN-001")
        asset = Asset(
            id=1,
            inventory_number=inventory_number,
            name="Компьютер",
            status=AssetStatus.ACTIVE,
            purchase_price=100000.0,
            department_code="IT"
        )
        
        assert asset.id == 1
        assert asset.inventory_number.value == "IN-001"
        assert asset.name == "Компьютер"
        assert asset.status == AssetStatus.ACTIVE

    def test_asset_status_transitions(self):
        """Переходы статусов актива"""
        inventory_number = InventoryNumber("IN-002")
        asset = Asset(
            id=2,
            inventory_number=inventory_number,
            name="Принтер",
            status=AssetStatus.ACTIVE,
            purchase_price=50000.0,
            department_code="Finance"
        )
        
        assert asset.status == AssetStatus.ACTIVE

    def test_asset_with_optional_fields(self):
        """Актив с необязательными полями"""
        inventory_number = InventoryNumber("IN-003")
        asset = Asset(
            id=3,
            inventory_number=inventory_number,
            name="Монитор",
            status=AssetStatus.RESERVED,
            purchase_price=25000.0,
            department_code="IT",
            model="Dell P2419H",
            manufacturer_name="Dell",
            purchase_date=date(2025, 1, 15),
            commissioning_date=date(2025, 1, 20)
        )
        
        assert asset.model == "Dell P2419H"
        assert asset.manufacturer_name == "Dell"
        assert asset.purchase_date == date(2025, 1, 15)

    def test_asset_invalid_inventory_number(self):
        """Актив с невалидным инвентарным номером"""
        with pytest.raises(ValueError):
            InventoryNumber("")  # Пустой номер

    def test_asset_to_dict(self):
        """Преобразование актива в словарь"""
        inventory_number = InventoryNumber("IN-004")
        asset = Asset(
            id=4,
            inventory_number=inventory_number,
            name="Системный блок",
            status=AssetStatus.ACTIVE,
            purchase_price=75000.0,
            department_code="IT"
        )
        
        asset_dict = asset.to_dict()
        assert asset_dict['inventory_number'] == "IN-004"
        assert asset_dict['name'] == "Системный блок"

    def test_asset_str_representation(self):
        """Строковое представление актива"""
        inventory_number = InventoryNumber("IN-005")
        asset = Asset(
            id=5,
            inventory_number=inventory_number,
            name="Сканер",
            status=AssetStatus.ACTIVE,
            purchase_price=30000.0,
            department_code="Doc"
        )
        
        assert str(asset) == "Asset(IN-005, Сканер)"
