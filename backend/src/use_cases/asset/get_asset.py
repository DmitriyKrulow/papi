# src/use_cases/asset/get_asset.py
"""
Use case: получение одного актива по ID.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.infrastructure.db.models.asset import Asset

logger = logging.getLogger(__name__)


class GetAsset:
    """Use case: получение актива по ID."""

    def __call__(
        self,
        asset_id: int,
        db: Session,
        include_hidden: bool = False,
    ) -> Optional[Asset]:
        """
        Получает актив по ID.

        Args:
            asset_id: ID актива
            db: Сессия SQLAlchemy
            include_hidden: Включать скрытые активы

        Returns:
            Asset или None
        """
        query = db.query(Asset).filter(Asset.id == asset_id)

        if not include_hidden:
            query = query.filter(Asset.is_active == True)

        return query.first()


get_asset = GetAsset()
