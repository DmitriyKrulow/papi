# src/use_cases/asset/delete_asset.py
"""
Use case: удаление (списание) актива.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class DeleteAsset:
    """Use case: списание актива (soft delete)."""

    def __call__(
        self,
        asset_id: int,
        db: Session,
        user: User,
        reason: str = "",
    ) -> Asset:
        """
        Списывает актив (soft delete).

        Args:
            asset_id: ID актива
            db: Сессия SQLAlchemy
            user: Пользователь, списывающий актив
            reason: Причина списания

        Returns:
            Asset: списанный объект актива
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Актив с ID {asset_id} не найден")

        asset.is_active = False
        asset.updated_at = datetime.now()
        db.flush()

        # Audit log
        audit_entry = AuditLog(
            entity_type="asset",
            entity_id=asset.id,
            action="delete",
            user_id=user.id,
            details=f"Списан актив: {asset.name} ({asset.inventory_number}). Причина: {reason or 'Не указана'}",
            created_at=datetime.now(),
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(asset)

        logger.info(
            f"[Asset] Deleted asset {asset.id} by user {user.username}: "
            f"{asset.name} ({asset.inventory_number})"
        )

        return asset


class RestoreAsset:
    """Use case: восстановление актива."""

    def __call__(
        self,
        asset_id: int,
        db: Session,
        user: User,
    ) -> Asset:
        """
        Восстанавливает актив.

        Args:
            asset_id: ID актива
            db: Сессия SQLAlchemy
            user: Пользователь, восстанавливающий актив

        Returns:
            Asset: восстановленный объект актива
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Актив с ID {asset_id} не найден")

        asset.is_active = True
        asset.updated_at = datetime.now()
        db.flush()

        # Audit log
        audit_entry = AuditLog(
            entity_type="asset",
            entity_id=asset.id,
            action="restore",
            user_id=user.id,
            details=f"Восстановлен актив: {asset.name} ({asset.inventory_number})",
            created_at=datetime.now(),
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(asset)

        logger.info(
            f"[Asset] Restored asset {asset.id} by user {user.username}: "
            f"{asset.name}"
        )

        return asset


delete_asset = DeleteAsset()
restore_asset = RestoreAsset()
