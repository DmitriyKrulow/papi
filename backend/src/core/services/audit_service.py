# src/core/services/audit_service.py
"""Сервис аудита — логирование значимых действий в системе."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class AuditAction(str, Enum):
    """Тип действия для аудита."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    STATUS_CHANGE = "status_change"
    IMPORT = "import"
    EXPORT = "export"
    INVENTORY_START = "inventory_start"
    INVENTORY_COMPLETE = "inventory_complete"
    REPAIR_CREATE = "repair_create"
    REPAIR_UPDATE = "repair_update"


@dataclass
class AuditEntry:
    """Запись для аудита."""
    entity_type: str
    entity_id: int
    action: AuditAction
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    user_agent: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None

    @property
    def diff_summary(self) -> Optional[str]:
        """Краткое описание изменений из old/new values."""
        if not self.old_values or not self.new_values:
            return None

        changed_fields = []
        all_keys = set(self.old_values.keys()) | set(self.new_values.keys())
        for key in sorted(all_keys):
            old_val = self.old_values.get(key)
            new_val = self.new_values.get(key)
            if old_val != new_val:
                changed_fields.append(f"{key}: {old_val} → {new_val}")

        if not changed_fields:
            return None

        summary = ", ".join(changed_fields[:3])  # максимум 3 поля
        if len(changed_fields) > 3:
            summary += f" (+{len(changed_fields) - 3} more)"
        return summary[:500]

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для сохранения в БД."""
        d = {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action.value if isinstance(self.action, AuditAction) else self.action,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "method": self.method,
            "path": self.path,
            "user_agent": self.user_agent,
            "old_values": json.dumps(self.old_values, ensure_ascii=False) if self.old_values else None,
            "new_values": json.dumps(self.new_values, ensure_ascii=False) if self.new_values else None,
            "comment": self.comment,
        }
        if self.diff_summary:
            d["diff_summary"] = self.diff_summary
        return d


class AuditService:
    """Сервис для логирования действий."""

    def __init__(self, db_session, request_meta: Optional[Dict[str, Any]] = None):
        """
        Args:
            db_session: сессия SQLAlchemy
            request_meta: метаданные запроса {ip_address, method, path, user_agent}
        """
        self.db = db_session
        self.request_meta = request_meta or {}

    def _get_user_id(self) -> Optional[int]:
        """Получить ID текущего пользователя из сессии."""
        try:
            # Пробуем получить из текущего пользователя в сессии
            from sqlalchemy import text
            # Это заглушка — реальный user_id будет передаваться явно
            return None
        except Exception:
            return None

    def log(self, entry: AuditEntry) -> None:
        """Записать запись в журнал аудита."""
        from src.infrastructure.db.models.audit_log import AuditLog

        data = entry.to_dict()
        data["created_at"] = datetime.now()

        self.db.add(AuditLog(**data))
        self.db.commit()

    def log_asset_create(self, asset_id: int, asset_data: Dict[str, Any], user_id: Optional[int] = None) -> None:
        """Логирование создания актива."""
        self.log(AuditEntry(
            entity_type="Asset",
            entity_id=asset_id,
            action=AuditAction.CREATE,
            user_id=user_id,
            new_values=asset_data,
            comment="Создан новый актив",
        ))

    def log_asset_update(self, asset_id: int, old_data: Dict[str, Any], new_data: Dict[str, Any], user_id: Optional[int] = None) -> None:
        """Логирование изменения актива."""
        self.log(AuditEntry(
            entity_type="Asset",
            entity_id=asset_id,
            action=AuditAction.UPDATE,
            user_id=user_id,
            old_values=old_data,
            new_values=new_data,
        ))

    def log_asset_delete(self, asset_id: int, old_data: Dict[str, Any], user_id: Optional[int] = None) -> None:
        """Логирование удаления актива."""
        self.log(AuditEntry(
            entity_type="Asset",
            entity_id=asset_id,
            action=AuditAction.DELETE,
            user_id=user_id,
            old_values=old_data,
            comment="Актив удалён",
        ))

    def log_login(self, user_id: int, ip_address: Optional[str] = None) -> None:
        """Логирование входа в систему."""
        self.log(AuditEntry(
            entity_type="User",
            entity_id=user_id,
            action=AuditAction.LOGIN,
            user_id=user_id,
            ip_address=ip_address,
            comment="Вход в систему",
        ))

    def log_logout(self, user_id: int) -> None:
        """Логирование выхода из системы."""
        self.log(AuditEntry(
            entity_type="User",
            entity_id=user_id,
            action=AuditAction.LOGOUT,
            user_id=user_id,
            comment="Выход из системы",
        ))

    def log_status_change(self, entity_type: str, entity_id: int, old_status: str, new_status: str, comment: str = "", user_id: Optional[int] = None) -> None:
        """Логирование изменения статуса."""
        self.log(AuditEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.STATUS_CHANGE,
            user_id=user_id,
            old_values={"status": old_status},
            new_values={"status": new_status},
            comment=comment or f"Статус изменён: {old_status} → {new_status}",
        ))

    def log_inventory_start(self, check_id: int, check_name: str, user_id: Optional[int] = None) -> None:
        """Логирование начала инвентаризации."""
        self.log(AuditEntry(
            entity_type="InventoryCheck",
            entity_id=check_id,
            action=AuditAction.INVENTORY_START,
            user_id=user_id,
            new_values={"name": check_name, "status": "in_progress"},
            comment=f"Инвентаризация начата: {check_name}",
        ))

    def log_inventory_complete(self, check_id: int, check_name: str, user_id: Optional[int] = None) -> None:
        """Логирование завершения инвентаризации."""
        self.log(AuditEntry(
            entity_type="InventoryCheck",
            entity_id=check_id,
            action=AuditAction.INVENTORY_COMPLETE,
            user_id=user_id,
            new_values={"name": check_name, "status": "completed"},
            comment=f"Инвентаризация завершена: {check_name}",
        ))

    def log_import(self, entity_type: str, count: int, user_id: Optional[int] = None, comment: str = "") -> None:
        """Логирование импорта данных."""
        self.log(AuditEntry(
            entity_type=entity_type,
            entity_id=0,  # Импорт — нет конкретного entity_id
            action=AuditAction.IMPORT,
            user_id=user_id,
            new_values={"imported_count": count},
            comment=comment or f"Импортировано {count} записей",
        ))

    def get_history(self, entity_type: str, entity_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Получить историю изменений сущности."""
        from src.infrastructure.db.models.audit_log import AuditLog
        from sqlalchemy import text

        results = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "user_id": r.user_id,
                "user_name": r.user.username if r.user else None,
                "action": r.action,
                "old_values": json.loads(r.old_values) if r.old_values else None,
                "new_values": json.loads(r.new_values) if r.new_values else None,
                "diff_summary": r.diff_summary,
                "comment": r.comment,
            }
            for r in results
        ]

    def get_all(self, limit: int = 50, offset: int = 0,
                entity_type: Optional[str] = None,
                action: Optional[str] = None,
                user_id: Optional[int] = None,
                start_date: Optional[str] = None,
                end_date: Optional[str] = None) -> Dict[str, Any]:
        """Получить все записи аудита с фильтрацией."""
        from src.infrastructure.db.models.audit_log import AuditLog

        query = self.db.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if start_date:
            query = query.filter(AuditLog.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(AuditLog.created_at <= datetime.fromisoformat(end_date))

        total = query.count()
        results = (
            query.order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [
                {
                    "id": r.id,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "user_id": r.user_id,
                    "user_name": r.user.username if r.user else None,
                    "ip_address": r.ip_address,
                    "method": r.method,
                    "entity_type": r.entity_type,
                    "entity_id": r.entity_id,
                    "action": r.action,
                    "diff_summary": r.diff_summary,
                    "comment": r.comment,
                }
                for r in results
            ],
        }
