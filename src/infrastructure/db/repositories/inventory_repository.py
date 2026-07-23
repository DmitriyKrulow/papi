from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import InventoryCheck as InventoryCheckModel
from src.core.entities.inventory_check import InventoryCheck


class InventoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, check: InventoryCheck) -> None:
        model = self._to_model(check)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[InventoryCheck]:
        model = self.session.get(InventoryCheckModel, id)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[InventoryCheck]:
        statement = select(InventoryCheckModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_department(self, department_id: int) -> List[InventoryCheck]:
        statement = select(InventoryCheckModel).where(InventoryCheckModel.department_id == department_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_date_range(self, start_date: date, end_date: date) -> List[InventoryCheck]:
        statement = select(InventoryCheckModel).where(
            InventoryCheckModel.check_date >= start_date,
            InventoryCheckModel.check_date <= end_date
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_status(self, status: str) -> List[InventoryCheck]:
        statement = select(InventoryCheckModel).where(InventoryCheckModel.status == status)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_active(self) -> List[InventoryCheck]:
        statement = select(InventoryCheckModel).where(
            InventoryCheckModel.status.not_in(['completed', 'cancelled'])
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(InventoryCheckModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: InventoryCheck) -> InventoryCheckModel:
        return InventoryCheckModel(
            id=entity.id,
            name=entity.name,
            check_date=entity.check_date,
            department_id=entity.department_id,
            total_checked=entity.total_checked,
            found=entity.found,
            missing=entity.missing,
            surplus=entity.surplus,
            status=entity.status,
            responsible_id=entity.responsible_id,
            commission_members=",".join(str(x) for x in entity.commission_members) if entity.commission_members else None,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
        )

    def _to_entity(self, model: InventoryCheckModel) -> InventoryCheck:
        commission_members = []
        if model.commission_members:
            try:
                commission_members = [int(x) for x in model.commission_members.split(",")]
            except ValueError:
                commission_members = []
        
        return InventoryCheck(
            id=model.id,
            name=model.name,
            check_date=model.check_date,
            department_id=model.department_id,
            total_checked=model.total_checked,
            found=model.found,
            missing=model.missing,
            surplus=model.surplus,
            status=model.status,
            responsible_id=model.responsible_id,
            commission_members=commission_members,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )
