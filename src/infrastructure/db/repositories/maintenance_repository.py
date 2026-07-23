from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import MaintenanceRecord as MaintenanceRecordModel
from src.core.entities.maintenance_record import MaintenanceRecord
from src.core.value_objects import Money


class MaintenanceRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, record: MaintenanceRecord) -> None:
        model = self._to_model(record)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[MaintenanceRecord]:
        model = self.session.get(MaintenanceRecordModel, id)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[MaintenanceRecord]:
        statement = select(MaintenanceRecordModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_asset(self, asset_id: int) -> List[MaintenanceRecord]:
        statement = select(MaintenanceRecordModel).where(MaintenanceRecordModel.asset_id == asset_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_type(self, maintenance_type: str) -> List[MaintenanceRecord]:
        statement = select(MaintenanceRecordModel).where(
            MaintenanceRecordModel.maintenance_type == maintenance_type
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_date_range(self, start_date, end_date) -> List[MaintenanceRecord]:
        statement = select(MaintenanceRecordModel).where(
            MaintenanceRecordModel.maintenance_date >= start_date,
            MaintenanceRecordModel.maintenance_date <= end_date
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def get_completed(self, asset_id: int) -> List[MaintenanceRecord]:
        statement = select(MaintenanceRecordModel).where(
            MaintenanceRecordModel.asset_id == asset_id,
            MaintenanceRecordModel.result == "Выполнено"
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(MaintenanceRecordModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: MaintenanceRecord) -> MaintenanceRecordModel:
        return MaintenanceRecordModel(
            id=entity.id,
            asset_id=entity.asset_id,
            maintenance_date=entity.maintenance_date,
            maintenance_type=entity.maintenance_type,
            description=entity.description,
            cost=float(entity.cost.amount) if entity.cost else None,
            performed_by=entity.performed_by,
            contractor=entity.contractor,
            result=entity.result,
            next_maintenance_date=entity.next_maintenance_date,
            document_number=entity.document_number,
            document_date=entity.document_date,
            created_at=entity.created_at,
            created_by=entity.created_by,
        )

    def _to_entity(self, model: MaintenanceRecordModel) -> MaintenanceRecord:
        return MaintenanceRecord(
            id=model.id,
            asset_id=model.asset_id,
            maintenance_date=model.maintenance_date,
            maintenance_type=model.maintenance_type,
            description=model.description,
            cost=Money(Decimal(str(model.cost))) if model.cost else None,
            performed_by=model.performed_by,
            contractor=model.contractor,
            result=model.result,
            next_maintenance_date=model.next_maintenance_date,
            document_number=model.document_number,
            document_date=model.document_date,
            created_at=model.created_at,
            created_by=model.created_by,
        )
