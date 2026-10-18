# src/use_cases/asset/update_asset.py
"""
Use case: обновление актива.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class UpdateAsset:
    """Use case: обновление актива."""

    def __call__(
        self,
        asset_id: int,
        data: dict[str, Any],
        db: Session,
        user: User,
    ) -> Asset:
        """
        Обновляет актив.

        Args:
            asset_id: ID актива
            data: Словарь с полями для обновления
            db: Сессия SQLAlchemy
            user: Пользователь, обновляющий актив

        Returns:
            Asset: обновлённый объект актива
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Актив с ID {asset_id} не найден")

        # Обновляем поля
        updatable_fields = {
            "name", "description", "model", "asset_type", "status",
            "purchase_price", "current_value", "quantity",
            "department_code", "department_name", "responsible_person",
            "employee_name", "assigned_employee_id", "location_address",
            "manufacturer_code", "manufacturer_name", "purchase_date",
            "commissioning_date", "warranty_expiry", "serial_number",
            "capacity", "power", "weight", "consumable_type",
            "crypto_wallet_address", "crypto_token_symbol",
            "depreciation_years", "next_maintenance_date",
            "rfid_tag", "storage_address_id", "room_id",
        }

        old_values = {}
        for field in updatable_fields:
            if field in data:
                old_values[field] = getattr(asset, field, None)
                setattr(asset, field, data[field])

        asset.updated_at = datetime.now()
        db.flush()

        # Audit log
        audit_entry = AuditLog(
            entity_type="asset",
            entity_id=asset.id,
            action="update",
            user_id=user.id,
            details=f"Обновлён актив: {asset.name}",
            old_values=old_values,
            new_values={k: v for k, v in data.items() if k in updatable_fields},
            created_at=datetime.now(),
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(asset)

        logger.info(
            f"[Asset] Updated asset {asset.id} by user {user.username}: "
            f"{asset.name}"
        )

        return asset


update_asset = UpdateAsset()
