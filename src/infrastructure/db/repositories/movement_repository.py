from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import MovementRecord as MovementRecordModel
from src.core.entities.movement_record import MovementRecord
from src.core.value_objects import Coordinates


class MovementRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, record: MovementRecord) -> None:
        model = self._to_model(record)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[MovementRecord]:
        model = self.session.get(MovementRecordModel, id)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[MovementRecord]:
        statement = select(MovementRecordModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_asset(self, asset_id: int) -> List[MovementRecord]:
        statement = select(MovementRecordModel).where(MovementRecordModel.asset_id == asset_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_department(self, department_id: int) -> List[MovementRecord]:
        statement = select(MovementRecordModel).where(
            (MovementRecordModel.from_department_id == department_id) |
            (MovementRecordModel.to_department_id == department_id)
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_date_range(self, start_date, end_date) -> List[MovementRecord]:
        statement = select(MovementRecordModel).where(
            MovementRecordModel.movement_date >= start_date,
            MovementRecordModel.movement_date <= end_date
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(MovementRecordModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: MovementRecord) -> MovementRecordModel:
        return MovementRecordModel(
            id=entity.id,
            asset_id=entity.asset_id,
            movement_date=entity.movement_date,
            from_department_id=entity.from_department_id,
            from_department_name=entity.from_department_name,
            from_location=entity.from_location,
            to_department_id=entity.to_department_id,
            to_department_name=entity.to_department_name,
            to_location=entity.to_location,
            from_responsible_id=entity.from_responsible_id,
            to_responsible_id=entity.to_responsible_id,
            reason=entity.reason,
            document_number=entity.document_number,
            created_at=entity.created_at,
            created_by=entity.created_by,
        )

    def _to_entity(self, model: MovementRecordModel) -> MovementRecord:
        return MovementRecord(
            id=model.id,
            asset_id=model.asset_id,
            movement_date=model.movement_date,
            from_department_id=model.from_department_id,
            from_department_name=model.from_department_name,
            from_location=model.from_location,
            from_coordinates=None,
            to_department_id=model.to_department_id,
            to_department_name=model.to_department_name,
            to_location=model.to_location,
            to_coordinates=None,
            from_responsible_id=model.from_responsible_id,
            to_responsible_id=model.to_responsible_id,
            reason=model.reason,
            document_number=model.document_number,
            created_at=model.created_at,
            created_by=model.created_by,
        )
