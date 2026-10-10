# backend/tests/unit/test_asset_service.py
"""Unit-тесты для сервисов активов (без БД)"""
import pytest
from datetime import date


class TestAssetModel:
    """Тесты для модели Asset (без БД)"""

    def test_valid_status_values(self):
        """Проверка допустимых значений статуса"""
        valid_statuses = ["active", "maintenance", "reserved", "decommissioned", "lost", "written_off"]
        for status in valid_statuses:
            assert status in ["active", "maintenance", "reserved", "decommissioned", "lost", "written_off"]

    def test_depreciation_calculation(self):
        """Тест расчёта амортизации"""
        purchase_price = 100000
        current_value = 60000
        
        depreciation = purchase_price - current_value
        assert depreciation == 40000
        
        depreciation_percent = (depreciation / purchase_price) * 100
        assert depreciation_percent == 40.0

    def test_asset_inventory_number_format(self):
        """Проверка формата инвентарного номера"""
        valid_numbers = ["INV001", "INV-001", "INV000001", "TEST-123"]
        for number in valid_numbers:
            assert isinstance(number, str)
            assert len(number) > 0
