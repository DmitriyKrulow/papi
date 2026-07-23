from decimal import Decimal
from typing import List, Optional, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import Asset as AssetModel
from src.core.entities.asset import Asset
from src.core.value_objects import (
    InventoryNumber,
    BatchId,
    SerialNumber,
    YearPeriod,
    AssetType,
    AssetCategory,
    Status,
    AssetStatus,
    Money,
    Coordinates,
    Phone,
)

T = TypeVar('T')


class AssetRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, asset: Asset) -> None:
        model = self._to_model(asset)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[Asset]:
        model = self.session.get(AssetModel, id)
        if model:
            return self._to_entity(model)
        return None

    def get_by_inventory_number(self, inventory_number: str) -> Optional[Asset]:
        statement = select(AssetModel).where(AssetModel.inventory_number == inventory_number)
        model = self.session.scalar(statement)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[Asset]:
        statement = select(AssetModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_status(self, status: str) -> List[Asset]:
        statement = select(AssetModel).where(AssetModel.status == status)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_department(self, department_code: str) -> List[Asset]:
        statement = select(AssetModel).where(AssetModel.department_code == department_code)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_category(self, category_id: int) -> List[Asset]:
        statement = select(AssetModel).where(AssetModel.category_id == category_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(AssetModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: Asset) -> AssetModel:
        return AssetModel(
            id=entity.id,
            inventory_number=str(entity.inventory_number),
            batch_id=str(entity.batch_id) if entity.batch_id else None,
            serial_number=str(entity.serial_number) if entity.serial_number else None,
            year_period=str(entity.year_period) if entity.year_period else None,
            asset_type=str(entity.asset_type) if entity.asset_type else None,
            name=entity.name,
            description=entity.description,
            model=entity.model,
            manufacturer_code=entity.manufacturer_code,
            manufacturer_name=entity.manufacturer_name,
            country_of_origin=entity.country_of_origin,
            accounting_code=entity.accounting_code,
            department_code=entity.department_code,
            responsible_person=entity.responsible_person,
            purchase_price=float(entity.purchase_price.amount) if entity.purchase_price else None,
            current_value=float(entity.current_value.amount) if entity.current_value else None,
            residual_value=float(entity.residual_value.amount) if entity.residual_value else None,
            depreciation_rate=float(entity.depreciation_rate) if entity.depreciation_rate else None,
            status=str(entity.status),
            location=str(entity.location) if entity.location else None,
            location_address=entity.location_address,
            responsible_phone=str(entity.responsible_phone) if entity.responsible_phone else None,
            purchase_date=entity.purchase_date,
            commissioning_date=entity.commissioning_date,
            warranty_expiry=entity.warranty_expiry,
            last_maintenance_date=entity.last_maintenance_date,
            next_maintenance_date=entity.next_maintenance_date,
            decommissioning_date=entity.decommissioning_date,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            tags=",".join(entity.tags) if entity.tags else None,
            notes=entity.notes,
            is_active=entity.is_active,
        )

    def _to_entity(self, model: AssetModel) -> Asset:
        return Asset(
            id=model.id,
            inventory_number=InventoryNumber(model.inventory_number),
            batch_id=BatchId(model.batch_id) if model.batch_id else None,
            serial_number=SerialNumber.from_string(model.serial_number) if model.serial_number else None,
            year_period=YearPeriod.from_inventory_number(model.year_period) if model.year_period else None,
            asset_type=AssetType.from_inventory_prefix(model.asset_type) if model.asset_type else None,
            name=model.name or "",
            description=model.description,
            model=model.model,
            manufacturer_code=model.manufacturer_code,
            manufacturer_name=model.manufacturer_name,
            country_of_origin=model.country_of_origin,
            accounting_code=model.accounting_code,
            department_code=model.department_code,
            responsible_person=model.responsible_person,
            purchase_price=Money(Decimal(str(model.purchase_price))) if model.purchase_price else None,
            current_value=Money(Decimal(str(model.current_value))) if model.current_value else None,
            residual_value=Money(Decimal(str(model.residual_value))) if model.residual_value else None,
            depreciation_rate=Decimal(str(model.depreciation_rate)) if model.depreciation_rate else None,
            status=Status(AssetStatus(model.status) if model.status else AssetStatus.ACTIVE),
            location=Coordinates.from_string(model.location) if model.location else None,
            location_address=model.location_address,
            responsible_phone=Phone(model.responsible_phone) if model.responsible_phone else None,
            purchase_date=model.purchase_date,
            commissioning_date=model.commissioning_date,
            warranty_expiry=model.warranty_expiry,
            last_maintenance_date=model.last_maintenance_date,
            next_maintenance_date=model.next_maintenance_date,
            decommissioning_date=model.decommissioning_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            tags=model.tags.split(",") if model.tags else [],
            notes=model.notes,
            is_active=model.is_active,
        )
