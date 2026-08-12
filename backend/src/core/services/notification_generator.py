# backend/src/core/services/notification_generator.py
"""Сервис автоматической генерации уведомлений.

Запускается периодически (например, раз в день) и проверяет:
- Истекающие гарантии
- Плановое обслуживание
- Просроченные ремонты
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.infrastructure.db.models.notification import Notification
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.repair_request import RepairRequest

logger = logging.getLogger(__name__)


class NotificationGenerator:
    """Генератор автоматических уведомлений."""

    # Предупреждать за N дней до события
    WARRANTY_WARN_DAYS = [30, 14, 7]
    MAINTENANCE_WARN_DAYS = [30, 14, 7, 1]
    REPAIR_OVERDUE_DAYS = [3, 7, 14]

    def __init__(self, db: Session):
        self.db = db

    def generate_all(self) -> Dict[str, int]:
        """Запускает все проверки и генерирует уведомления.
        
        Returns:
            Словарь {тип: количество_created}
        """
        results = {
            "warranty": 0,
            "maintenance": 0,
            "repair_overdue": 0,
            "status_change": 0,
        }

        results["warranty"] = self._check_warranty_expiry()
        results["maintenance"] = self._check_maintenance_due()
        results["repair_overdue"] = self._check_repair_overdue()

        self.db.commit()

        total = sum(results.values())
        logger.info(f"NotificationGenerator: generated {total} notifications: {results}")
        return results

    def _check_warranty_expiry(self) -> int:
        """Проверяет истекающие гарантии."""
        count = 0
        now = date.today()

        assets = self.db.query(Asset).filter(
            Asset.warranty_expiry.isnot(None),
            Asset.is_active == True,
        ).all()

        for asset in assets:
            warranty_expiry = asset.warranty_expiry  # type: ignore[union-attr]
            if warranty_expiry is None:
                continue

            days_left = (warranty_expiry - now).days  # type: ignore[operator]

            for warn_days in self.WARRANTY_WARN_DAYS:
                if days_left <= warn_days and days_left > 0:
                    if not self._notification_exists(
                        "warranty", int(asset.id), f"warn_{warn_days}"  # type: ignore[arg-type]
                    ):
                        self._create_warranty_notification(asset, days_left, f"warn_{warn_days}")
                        count += 1

            if days_left < 0:
                if not self._notification_exists("warranty", int(asset.id), "expired"):  # type: ignore[arg-type]
                    self._create_warranty_notification(asset, days_left, "expired")
                    count += 1

        return count

    def _check_maintenance_due(self) -> int:
        """Проверяет плановое обслуживание."""
        count = 0
        now = date.today()

        assets = self.db.query(Asset).filter(
            Asset.next_maintenance_date.isnot(None),
            Asset.is_active == True,
        ).all()

        for asset in assets:
            next_maint = asset.next_maintenance_date  # type: ignore[union-attr]
            if next_maint is None:
                continue

            days_left = (next_maint - now).days  # type: ignore[operator]

            for warn_days in self.MAINTENANCE_WARN_DAYS:
                if days_left <= warn_days and days_left > 0:
                    if not self._notification_exists(
                        "maintenance", int(asset.id), f"warn_{warn_days}"  # type: ignore[arg-type]
                    ):
                        self._create_maintenance_notification(asset, days_left, f"warn_{warn_days}")
                        count += 1

            if days_left < 0:
                if not self._notification_exists("maintenance", int(asset.id), "overdue"):  # type: ignore[arg-type]
                    self._create_maintenance_notification(asset, days_left, "overdue")
                    count += 1

        return count

    def _check_repair_overdue(self) -> int:
        """Проверяет просроченные ремонты."""
        count = 0

        repairs = self.db.query(RepairRequest).filter(
            RepairRequest.status.notin_(["completed", "cancelled"]),
        ).all()

        for repair in repairs:
            created_at = repair.created_at  # type: ignore[union-attr]
            if created_at is None:
                continue

            days_since = (datetime.now() - created_at).days  # type: ignore[operator]

            for overdue_days in self.REPAIR_OVERDUE_DAYS:
                if days_since >= overdue_days:
                    if not self._notification_exists(
                        "repair_overdue", int(repair.id), f"overdue_{overdue_days}"  # type: ignore[arg-type]
                    ):
                        self._create_repair_notification(repair, days_since, f"overdue_{overdue_days}")
                        count += 1

        return count

    def _create_warranty_notification(self, asset: Asset, days_left: int, ref_key: str) -> None:
        """Создаёт уведомление о гарантии."""
        if days_left < 0:
            title = f"Гарантия истекла: {asset.name}"
            message = (
                f"Гарантия на '{asset.name}' (инв. № {asset.inventory_number}) "
                f"истекла {abs(days_left)} дней назад."
            )
        elif days_left == 0:
            title = f"Гарантия истекает сегодня: {asset.name}"
            message = f"Гарантия на '{asset.name}' истекает сегодня!"
        else:
            title = f"Гарантия истекает через {days_left} дн.: {asset.name}"
            message = (
                f"Гарантия на '{asset.name}' (инв. № {asset.inventory_number}) "
                f"истекает через {days_left} дней ({asset.warranty_expiry})."
            )

        self._notify_users(
            user_ids=[],
            type="warranty",
            title=title,
            message=message,
            reference_type="asset",
            reference_id=int(asset.id),  # type: ignore[arg-type]
            ref_key=ref_key,
        )

    def _create_maintenance_notification(self, asset: Asset, days_left: int, ref_key: str) -> None:
        """Создаёт уведомление о обслуживании."""
        if days_left < 0:
            title = f"Просрочено обслуживание: {asset.name}"
            message = (
                f"Плановое обслуживание '{asset.name}' (инв. № {asset.inventory_number}) "
                f"просрочено на {abs(days_left)} дней."
            )
        elif days_left == 0:
            title = f"Обслуживание сегодня: {asset.name}"
            message = f"Сегодня необходимо провести обслуживание '{asset.name}'."
        else:
            title = f"Обслуживание через {days_left} дн.: {asset.name}"
            message = (
                f"Плановое обслуживание '{asset.name}' (инв. № {asset.inventory_number}) "
                f"назначено через {days_left} дней ({asset.next_maintenance_date})."
            )

        self._notify_users(
            user_ids=[],
            type="maintenance",
            title=title,
            message=message,
            reference_type="asset",
            reference_id=int(asset.id),  # type: ignore[arg-type]
            ref_key=ref_key,
        )

    def _create_repair_notification(self, repair: RepairRequest, days_since: int, ref_key: str) -> None:
        """Создаёт уведомление о просроченном ремонте."""
        title = f"Ремонт просрочен: {repair.title}"
        message = f"Заявка на ремонт '{repair.title}' (#{repair.id}) ожидает {days_since} дней."

        if repair.assigned_to is not None:
            self._notify_users(
                user_ids=[int(repair.assigned_to)],  # type: ignore[arg-type]
                type="repair_overdue",
                title=title,
                message=message,
                reference_type="repair_request",
                reference_id=int(repair.id),  # type: ignore[arg-type]
                ref_key=ref_key,
            )
        else:
            self._notify_users(
                user_ids=[],
                type="repair_overdue",
                title=title,
                message=message,
                reference_type="repair_request",
                reference_id=int(repair.id),  # type: ignore[arg-type]
                ref_key=ref_key,
            )

    def _notify_users(self, user_ids: list, type: str, title: str, message: str,
                      reference_type: Optional[str] = None, reference_id: Optional[int] = None,
                      ref_key: Optional[str] = None) -> None:
        """Создаёт уведомления для пользователей."""
        if user_ids:
            users = self.db.query(User).filter(User.id.in_(user_ids)).all()
        else:
            users = self.db.query(User).filter(User.is_active == True).all()

        for user in users:
            if self._notification_exists(type, reference_id or 0, ref_key or "", user_id=int(user.id)):  # type: ignore[arg-type]
                continue

            notification = Notification(
                user_id=user.id,
                type=type,
                title=title,
                message=message,
                reference_type=reference_type,
                reference_id=reference_id,
                reference_key=ref_key,
            )
            self.db.add(notification)
            # flush, чтобы последующие проверки _notification_exists в этом же
            # прогоне видели только что добавленные записи и не создавали дубли.
            self.db.flush()

    def _notification_exists(self, type: str, entity_id: int, ref_key: str = "", user_id: Optional[int] = None) -> bool:  # type: ignore[assignment]
        """Проверяет, не отправляли ли уже подобное уведомление (за 30 дней)."""
        thirty_days_ago = datetime.now() - timedelta(days=30)

        query = self.db.query(Notification).filter(
            Notification.type == type,
            Notification.created_at >= thirty_days_ago,
            Notification.reference_id == entity_id,
        )

        if ref_key:
            query = query.filter(Notification.reference_key == ref_key)

        if user_id:
            query = query.filter(Notification.user_id == user_id)  # type: ignore[arg-type]

        return query.count() > 0

    def create_for_user(self, user_id: int, type: str, title: str, message: str,
                        reference_type: Optional[str] = None, reference_id: Optional[int] = None) -> Notification:
        """Создаёт уведомление для конкретного пользователя (вызывается из роутеров)."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification
