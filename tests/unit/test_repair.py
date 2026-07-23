# tests/unit/test_repair.py
import pytest
from datetime import datetime
from backend.src.core.entities.repair_request import RepairRequest, RepairPriority, RepairStatus


class TestRepairRequestEntity:
    """Тесты сущности RepairRequest"""

    def test_create_repair_request_with_valid_data(self):
        """Создание заявки на ремонт с валидными данными"""
        repair = RepairRequest(
            id=1,
            asset_id=100,
            title="Не работает принтер",
            description="Принтер не печатает, ошибка 0x001",
            priority=RepairPriority.HIGH,
            status=RepairStatus.SUBMITTED,
            created_by=1
        )
        
        assert repair.id == 1
        assert repair.asset_id == 100
        assert repair.title == "Не работает принтер"
        assert repair.priority == RepairPriority.HIGH
        assert repair.status == RepairStatus.SUBMITTED

    def test_repair_request_with_assigned_user(self):
        """Заявка с назначенным исполнителем"""
        repair = RepairRequest(
            id=2,
            asset_id=101,
            title="Замена масла в принтере",
            description="Требуется замена масла",
            priority=RepairPriority.MEDIUM,
            status=RepairStatus.APPROVED,
            created_by=1,
            assigned_to=2,
            estimated_cost=5000.0,
            actual_cost=4500.0
        )
        
        assert repair.assigned_to == 2
        assert repair.estimated_cost == 5000.0
        assert repair.actual_cost == 4500.0

    def test_repair_request_priority_transitions(self):
        """Переходы приоритетов"""
        repair = RepairRequest(
            id=3,
            asset_id=102,
            title="Поменять картридж",
            description="Картридж заправлен",
            priority=RepairPriority.LOW,
            status=RepairStatus.DRAFT,
            created_by=1
        )
        
        assert repair.priority == RepairPriority.LOW
        assert repair.status == RepairStatus.DRAFT

    def test_repair_request_str_representation(self):
        """Строковое представление заявки"""
        repair = RepairRequest(
            id=4,
            asset_id=103,
            title="Ремонт монитора",
            description="Мерцает экран",
            priority=RepairPriority.MEDIUM,
            status=RepairStatus.IN_PROGRESS,
            created_by=1
        )
        
        assert "Ремонт монитора" in str(repair)
        assert "IN_PROGRESS" in str(repair)
