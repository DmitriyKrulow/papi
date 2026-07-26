from typing import Optional, List, Dict, Any
from datetime import datetime, date

from src.infrastructure.db.models.repair_request import RepairRequest, RepairStatus, RepairPriority
from src.infrastructure.db.models.user import User
from src.core.entities.repair_request import RepairRequest as CoreRepairRequest, RepairStatus as CoreRepairStatus, RepairPriority as CoreRepairPriority


class RepairRequestRepository:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_by_id(self, repair_id: int) -> Optional[RepairRequest]:
        return self.db_session.query(RepairRequest).filter(RepairRequest.id == repair_id).first()

    def get_all(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        asset_id: Optional[int] = None,
        created_by: Optional[int] = None,
        assigned_to: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RepairRequest]:
        query = self.db_session.query(RepairRequest)

        if status:
            query = query.filter(RepairRequest.status == status)
        if priority:
            query = query.filter(RepairRequest.priority == priority)
        if asset_id:
            query = query.filter(RepairRequest.asset_id == asset_id)
        if created_by:
            query = query.filter(RepairRequest.created_by == created_by)
        if assigned_to:
            query = query.filter(RepairRequest.assigned_to == assigned_to)

        return query.offset(skip).limit(limit).all()

    def get_for_user(
        self,
        user_id: int,
        user_role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[RepairRequest]:
        """Получить заявки для пользователя (пользователь видит только свои, админ и ответственные - все)"""
        query = self.db_session.query(RepairRequest)

        if user_role not in ("admin", "responsible"):
            query = query.filter(RepairRequest.created_by == user_id)

        return query.offset(skip).limit(limit).all()

    def get_count_by_status(self, user_id: int, user_role: str) -> Dict[str, int]:
        """Получить количество заявок по статусам для пользователя"""
        query = self.db_session.query(RepairRequest)

        if user_role not in ("admin", "responsible"):
            query = query.filter(RepairRequest.created_by == user_id)

        results = query.all()

        counts = {}
        for status in RepairStatus:
            counts[status.value] = 0

        for repair in results:
            status_key = repair.status.value if repair.status else "draft"
            counts[status_key] = counts.get(status_key, 0) + 1

        return counts

    def create(self, repair_data: dict) -> RepairRequest:
        repair = RepairRequest(
            asset_id=repair_data.get("asset_id"),
            title=repair_data.get("title", ""),
            description=repair_data.get("description", ""),
            priority=repair_data.get("priority", RepairPriority.MEDIUM),
            status=RepairStatus.DRAFT,
            created_by=repair_data.get("created_by"),
            created_at=datetime.now(),
            desired_completion_date=repair_data.get("desired_completion_date"),
            deadline=repair_data.get("deadline"),
            estimated_cost=repair_data.get("estimated_cost"),
            updated_at=datetime.now(),
        )
        self.db_session.add(repair)
        self.db_session.commit()
        self.db_session.refresh(repair)
        return repair

    def update(self, repair_id: int, repair_data: dict) -> Optional[RepairRequest]:
        repair = self.get_by_id(repair_id)
        if not repair:
            return None

        for key, value in repair_data.items():
            if hasattr(repair, key) and key != "id":
                setattr(repair, key, value)

        repair.updated_at = datetime.now()
        if "updated_by" not in repair_data:
            repair.updated_by = repair_data.get("user_id")

        self.db_session.commit()
        self.db_session.refresh(repair)
        return repair

    def update_status(
        self,
        repair_id: int,
        status: str,
        user_id: int,
        assigned_to: Optional[int] = None,
        actual_completion_date: Optional[date] = None,
        actual_cost: Optional[float] = None,
        completion_notes: str = "",
        rejection_reason: str = ""
    ) -> Optional[RepairRequest]:
        repair = self.get_by_id(repair_id)
        if not repair:
            return None

        repair.status = status
        repair.updated_at = datetime.now()
        repair.updated_by = user_id

        if status == RepairStatus.APPROVED and assigned_to:
            repair.assigned_to = assigned_to
            repair.assigned_at = datetime.now()
        elif status == RepairStatus.COMPLETED:
            repair.actual_completion_date = actual_completion_date or date.today()
            repair.actual_cost = actual_cost
            repair.completion_notes = completion_notes
        elif status == RepairStatus.REJECTED:
            repair.rejection_reason = rejection_reason
        elif status == RepairStatus.CANCELLED:
            pass

        self.db_session.commit()
        self.db_session.refresh(repair)
        return repair

    def delete(self, repair_id: int) -> bool:
        repair = self.get_by_id(repair_id)
        if not repair:
            return False

        self.db_session.delete(repair)
        self.db_session.commit()
        return True

    def to_core_entity(self, repair: RepairRequest) -> CoreRepairRequest:
        """Преобразовать модель в core entity"""
        return CoreRepairRequest(
            id=repair.id,
            asset_id=repair.asset_id,
            title=repair.title,
            description=repair.description,
            priority=CoreRepairPriority(repair.priority.value) if repair.priority else CoreRepairPriority.MEDIUM,
            status=CoreRepairStatus(repair.status.value) if repair.status else CoreRepairStatus.DRAFT,
            created_by=repair.created_by,
            created_at=repair.created_at,
            assigned_to=repair.assigned_to,
            assigned_at=repair.assigned_at,
            desired_completion_date=repair.desired_completion_date,
            actual_completion_date=repair.actual_completion_date,
            deadline=repair.deadline,
            estimated_cost=repair.estimated_cost,
            actual_cost=repair.actual_cost,
            completion_notes=repair.completion_notes or "",
            rejection_reason=repair.rejection_reason or "",
            maintenance_record_id=repair.maintenance_record_id,
            updated_at=repair.updated_at,
            updated_by=repair.updated_by,
            asset_name=repair.asset.name if repair.asset else None,
            creator_name=repair.creator.username if repair.creator else None,
            assignee_name=repair.assignee.username if repair.assignee else None,
            inventory_number=repair.asset.inventory_number if repair.asset else None,
        )
