from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from src.infrastructure.db.models import RepairRequest as RepairRequestModel
from src.core.entities.repair_request import RepairRequest, RepairPriority, RepairStatus
from src.core.value_objects import Money


class RepairRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, repair: RepairRequest) -> None:
        model = self._to_model(repair)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[RepairRequest]:
        model = self.session.get(RepairRequestModel, id)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[RepairRequest]:
        statement = select(RepairRequestModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_asset(self, asset_id: int) -> List[RepairRequest]:
        statement = select(RepairRequestModel).where(RepairRequestModel.asset_id == asset_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_status(self, status: RepairStatus) -> List[RepairRequest]:
        statement = select(RepairRequestModel).where(RepairRequestModel.status == str(status.value))
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_priority(self, priority: RepairPriority) -> List[RepairRequest]:
        statement = select(RepairRequestModel).where(RepairRequestModel.priority == str(priority.value))
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_user(self, user_id: int) -> List[RepairRequest]:
        statement = select(RepairRequestModel).where(
            or_(
                RepairRequestModel.created_by == user_id,
                RepairRequestModel.assigned_to == user_id
            )
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_active(self) -> List[RepairRequest]:
        statement = select(RepairRequestModel).where(
            RepairRequestModel.status.not_in(['completed', 'rejected', 'cancelled'])
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_overdue(self) -> List[RepairRequest]:
        today = date.today()
        statement = select(RepairRequestModel).where(
            RepairRequestModel.deadline < today,
            RepairRequestModel.status.not_in(['completed', 'rejected', 'cancelled'])
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(RepairRequestModel.id))
        return self.session.scalar(statement) or 0

    def count_by_status(self, status: RepairStatus) -> int:
        statement = select(func.count(RepairRequestModel.id)).where(
            RepairRequestModel.status == str(status.value)
        )
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: RepairRequest) -> RepairRequestModel:
        return RepairRequestModel(
            id=entity.id,
            asset_id=entity.asset_id,
            title=entity.title,
            description=entity.description,
            created_by=entity.created_by,
            priority=str(entity.priority.value) if entity.priority else None,
            status=str(entity.status.value) if entity.status else None,
            created_at=entity.created_at,
            assigned_to=entity.assigned_to,
            assigned_at=entity.assigned_at,
            desired_completion_date=entity.desired_completion_date,
            actual_completion_date=entity.actual_completion_date,
            deadline=entity.deadline,
            estimated_cost=float(entity.estimated_cost.amount) if entity.estimated_cost else None,
            actual_cost=float(entity.actual_cost.amount) if entity.actual_cost else None,
            completion_notes=entity.completion_notes,
            rejection_reason=entity.rejection_reason,
            maintenance_record_id=entity.maintenance_record_id,
            updated_at=entity.updated_at,
            updated_by=entity.updated_by,
        )

    def _to_entity(self, model: RepairRequestModel) -> RepairRequest:
        return RepairRequest(
            id=model.id,
            asset_id=model.asset_id,
            title=model.title,
            description=model.description,
            created_by=model.created_by,
            priority=RepairPriority(model.priority) if model.priority else RepairPriority.MEDIUM,
            status=RepairStatus(model.status) if model.status else RepairStatus.DRAFT,
            created_at=model.created_at,
            assigned_to=model.assigned_to,
            assigned_at=model.assigned_at,
            desired_completion_date=model.desired_completion_date,
            actual_completion_date=model.actual_completion_date,
            deadline=model.deadline,
            estimated_cost=Money(Decimal(str(model.estimated_cost))) if model.estimated_cost else None,
            actual_cost=Money(Decimal(str(model.actual_cost))) if model.actual_cost else None,
            completion_notes=model.completion_notes,
            rejection_reason=model.rejection_reason,
            maintenance_record_id=model.maintenance_record_id,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
        )
