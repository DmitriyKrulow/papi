# src/use_cases/asset/create_asset.py
"""
Use case: создание нового актива.

Изолирует бизнес-логику создания актива от HTTP-слоя:
- Валидация данных
- Проверка уникальности inventory_number
- Создание записи в audit log
"""

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class CreateAsset:
    """Use case: создание актива."""

    def __call__(
        self,
        data: dict[str, Any],
        db: Session,
        user: User,
    ) -> Asset:
        """
        Создаёт новый актив.

        Args:
            data: Словарь с данными актива
            db: Сессия SQLAlchemy
            user: Пользователь, создающий актив

        Returns:
            Asset: созданный объект актива
        """
        # Валидация обязательных полей
        if not data.get("name"):
            raise ValueError("Поле 'name' обязательно")
        if not data.get("inventory_number"):
            raise ValueError("Поле 'inventory_number' обязательно")

        # Проверка уникальности inventory_number
        existing = (
            db.query(Asset)
            .filter(
                Asset.inventory_number == data["inventory_number"],
                Asset.is_active == True,
            )
            .first()
        )
        if existing:
            raise ValueError(
                f"Актив с инвентарным номером '{data['inventory_number']}' уже существует"
            )

        # Создание актива
        asset = Asset(
            inventory_number=data["inventory_number"],
            name=data["name"],
            description=data.get("description"),
            model=data.get("model"),
            asset_type=data.get("asset_type", "other"),
            status=data.get("status", "active"),
            purchase_price=data.get("purchase_price"),
            current_value=data.get("current_value"),
            quantity=data.get("quantity", 1),
            department_code=data.get("department_code"),
            department_name=data.get("department_name"),
            responsible_person=data.get("responsible_person"),
            employee_name=data.get("employee_name"),
            assigned_employee_id=data.get("assigned_employee_id"),
            location_address=data.get("location_address"),
            manufacturer_code=data.get("manufacturer_code"),
            manufacturer_name=data.get("manufacturer_name"),
            purchase_date=data.get("purchase_date"),
            commissioning_date=data.get("commissioning_date"),
            warranty_expiry=data.get("warranty_expiry"),
            serial_number=data.get("serial_number"),
            capacity=data.get("capacity"),
            power=data.get("power"),
            weight=data.get("weight"),
            consumable_type=data.get("consumable_type"),
            crypto_wallet_address=data.get("crypto_wallet_address"),
            crypto_token_symbol=data.get("crypto_token_symbol"),
            depreciation_years=data.get("depreciation_years"),
            next_maintenance_date=data.get("next_maintenance_date"),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            # RFID и хранение
            rfid_tag=data.get("rfid_tag"),
            storage_address_id=data.get("storage_address_id"),
            room_id=data.get("room_id"),
        )

        db.add(asset)
        db.flush()

        # Audit log
        audit_entry = AuditLog(
            entity_type="asset",
            entity_id=asset.id,
            action="create",
            user_id=user.id,
            details=f"Создан актив: {asset.name} ({asset.inventory_number})",
            created_at=datetime.now(),
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(asset)

        logger.info(
            f"[Asset] Created asset {asset.id} by user {user.username}: "
            f"{asset.name} ({asset.inventory_number})"
        )

        return asset


create_asset = CreateAsset()
