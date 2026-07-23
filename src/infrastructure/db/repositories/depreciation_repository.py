from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import DepreciationRecord as DepreciationRecordModel
from src.core.entities.depreciation_record import DepreciationRecord, DepreciationMethod
from src.core.value_objects import Money


class DepreciationRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, record: DepreciationRecord) -> None:
        model = self._to_model(record)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[DepreciationRecord]:
        model = self.session.get(DepreciationRecordModel, id)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[DepreciationRecord]:
        statement = select(DepreciationRecordModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_asset(self, asset_id: int) -> List[DepreciationRecord]:
        statement = select(DepreciationRecordModel).where(DepreciationRecordModel.asset_id == asset_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_period(self, period_start: date, period_end: date) -> List[DepreciationRecord]:
        statement = select(DepreciationRecordModel).where(
            DepreciationRecordModel.period_start >= period_start,
            DepreciationRecordModel.period_end <= period_end
        )
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_method(self, method: str) -> List[DepreciationRecord]:
        statement = select(DepreciationRecordModel).where(DepreciationRecordModel.method == method)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_unposted(self) -> List[DepreciationRecord]:
        statement = select(DepreciationRecordModel).where(DepreciationRecordModel.posted_at == None)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(DepreciationRecordModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: DepreciationRecord) -> DepreciationRecordModel:
        return DepreciationRecordModel(
            id=entity.id,
            asset_id=entity.asset_id,
            period_start=entity.period_start,
            period_end=entity.period_end,
            depreciation_amount=float(entity.depreciation_amount.amount),
            accumulated_depreciation=float(entity.accumulated_depreciation.amount),
            book_value_before=float(entity.book_value_before.amount),
            book_value_after=float(entity.book_value_after.amount),
            rate=float(entity.rate),
            method=entity.method,
            created_at=entity.created_at,
            posted_at=entity.posted_at,
            posted_by=entity.posted_by,
            notes=entity.notes,
            document_number=entity.document_number,
        )

    def _to_entity(self, model: DepreciationRecordModel) -> DepreciationRecord:
        return DepreciationRecord(
            id=model.id,
            asset_id=model.asset_id,
            period_start=model.period_start,
            period_end=model.period_end,
            depreciation_amount=Money(Decimal(str(model.depreciation_amount))),
            accumulated_depreciation=Money(Decimal(str(model.accumulated_depreciation))),
            book_value_before=Money(Decimal(str(model.book_value_before))),
            book_value_after=Money(Decimal(str(model.book_value_after))),
            rate=Decimal(str(model.rate)),
            method=model.method,
            created_at=model.created_at,
            posted_at=model.posted_at,
            posted_by=model.posted_by,
            notes=model.notes,
            document_number=model.document_number,
        )
