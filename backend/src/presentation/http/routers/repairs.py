# backend/src/presentation/http/routers/repairs.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal
import logging

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.repair_request import RepairRequest, RepairStatus, RepairPriority
from src.infrastructure.db.models.repair_template import RepairTemplate
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user
from src.presentation.http.schemas.repairs import (
    RepairRequestCreate,
    RepairRequestUpdate,
    RepairRequestResponse,
    RepairRequestListResponse,
    RepairTemplateCreate,
    RepairTemplateUpdate,
    RepairTemplateResponse,
    RepairTemplateListResponse,
    RepairTemplateApply,
    RepairStatusUpdate,
    RepairPriorityUpdate,
)

from pydantic import ValidationError
from src.infrastructure.reports.repair_report import RepairReportGenerator

router = APIRouter(prefix="/repairs", tags=["repairs"])


def safe_str(value: Optional[Any], default: str = "") -> str:
    if value is None:
        return default
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_decimal_to_float(value: Optional[Any], default: float = 0.0) -> float:
    print(f"[safe_decimal_to_float] value: {value}, type: {type(value)}")
    if value is None:
        print(f"[safe_decimal_to_float] returning default: {default}")
        return default
    try:
        if isinstance(value, (int, float, Decimal)):
            result = float(value)
            print(f"[safe_decimal_to_float] returning: {result}")
            return result
        print(f"[safe_decimal_to_float] returning default: {default}")
        return default
    except (TypeError, ValueError):
        print(f"[safe_decimal_to_float] returning default: {default}")
        return default


def safe_isoformat(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    try:
        if hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')):
            return value.isoformat()
        return str(value)
    except (AttributeError, ValueError):
        return None


def get_priority_value(priority: str) -> RepairPriority:
    valid_priorities = ["low", "medium", "high", "urgent"]
    if not priority:
        print(f"[get_priority_value] priority is empty, returning MEDIUM")
        return RepairPriority.MEDIUM
    priority_lower = priority.lower()
    print(f"[get_priority_value] priority: {priority}, priority_lower: {priority_lower}")
    if priority_lower in valid_priorities:
        result = RepairPriority(priority_lower)
        print(f"[get_priority_value] result: {result}")
        return result
    print(f"[get_priority_value] priority_lower not in valid_priorities, returning MEDIUM")
    return RepairPriority.MEDIUM


def get_status_value(status: str) -> RepairStatus:
    valid_statuses = ["draft", "submitted", "approved", "in_progress", "completed", "rejected", "cancelled"]
    if not status:
        print(f"[get_status_value] status is empty, returning DRAFT")
        return RepairStatus.DRAFT
    status_lower = status.lower()
    print(f"[get_status_value] status: {status}, status_lower: {status_lower}")
    if status_lower in valid_statuses:
        result = RepairStatus(status_lower)
        print(f"[get_status_value] result: {result}")
        return result
    print(f"[get_status_value] status_lower not in valid_statuses, returning DRAFT")
    return RepairStatus.DRAFT


def repair_to_response(repair: RepairRequest) -> dict:
    print(f"[repair_to_response] repair.id: {repair.id}")
    print(f"[repair_to_response] repair.estimated_cost: {repair.estimated_cost}")
    response = {
        "id": repair.id,
        "asset_id": repair.asset_id,
        "title": safe_str(repair.title),
        "description": safe_str(repair.description),
        "priority": repair.priority.value if repair.priority else "medium",
        "status": repair.status.value if repair.status else "draft",
        "created_by": repair.created_by,
        "creator_name": safe_str(repair.creator.username) if repair.creator else None,
        "created_at": safe_isoformat(repair.created_at),
        "assigned_to": repair.assigned_to,
        "assigned_at": safe_isoformat(repair.assigned_at),
        "actual_completion_date": safe_isoformat(repair.actual_completion_date),
        "actual_cost": safe_decimal_to_float(repair.actual_cost) if repair.actual_cost else None,
        "completion_notes": safe_str(repair.completion_notes),
        "rejection_reason": safe_str(repair.rejection_reason),
        "updated_at": safe_isoformat(repair.updated_at),
        "asset_name": safe_str(repair.asset.name) if repair.asset else None,
        "inventory_number": safe_str(repair.asset.inventory_number) if repair.asset else None,
        "assigned_to_name": safe_str(repair.assignee.username) if repair.assignee else None,
        "desired_completion_date": safe_isoformat(repair.desired_completion_date),
        "deadline": safe_isoformat(repair.deadline),
        "estimated_cost": safe_decimal_to_float(repair.estimated_cost) if repair.estimated_cost else None,
    }
    
    print(f"[repair_to_response] response: {response}")
    return response


def template_to_response(template: RepairTemplate) -> dict:
    return {
        "id": template.id,
        "name": safe_str(template.name),
        "description": safe_str(template.description),
        "template_data": template.template_data or {},
        "is_active": template.is_active,
        "is_default": template.is_default,
        "created_by": template.created_by,
        "created_at": safe_isoformat(template.created_at),
        "updated_at": safe_isoformat(template.updated_at),
    }


@router.get("/", response_model=RepairRequestListResponse)
def list_repairs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    asset_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger = logging.getLogger(__name__)
    logger.info(f"[repairs] list_repairs called, path: {request.url.path}")
    query = db.query(RepairRequest).options(
        joinedload(RepairRequest.asset),
        joinedload(RepairRequest.creator),
        joinedload(RepairRequest.assignee)
    )
    
    # Если не админ, скрываем заявки от скрытых (списанных) активов
    if current_user.role != "admin":
        query = query.join(RepairRequest.asset).filter(Asset.is_active == True)
    
    if status:
        status_value = get_status_value(status)
        query = query.filter(RepairRequest.status == status_value)
    
    if priority:
        priority_value = get_priority_value(priority)
        query = query.filter(RepairRequest.priority == priority_value)
    
    if asset_id:
        query = query.filter(RepairRequest.asset_id == asset_id)
    
    if status is None and current_user.role not in ("admin", "responsible"):
        query = query.filter(RepairRequest.created_by == current_user.id)
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return {
        "items": [repair_to_response(repair) for repair in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{repair_id}/", response_model=RepairRequestResponse)
def get_repair(repair_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repair = db.query(RepairRequest).options(
        joinedload(RepairRequest.asset),
        joinedload(RepairRequest.creator),
        joinedload(RepairRequest.assignee)
    ).filter(RepairRequest.id == repair_id).first()
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    
    if current_user.role not in ("admin", "responsible") and repair.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return repair_to_response(repair)


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_repair(
    repair: RepairRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print(f"[create_repair] repair: {repair.model_dump()}")
    asset = db.query(Asset).filter(Asset.id == repair.asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset not found")
    
    db_repair = RepairRequest(
        asset_id=repair.asset_id,
        title=repair.title,
        description=repair.description,
        priority=get_priority_value(repair.priority) if repair.priority else RepairPriority.MEDIUM,
        status=RepairStatus.DRAFT,
        created_by=current_user.id,
        desired_completion_date=repair.desired_completion_date,
        deadline=repair.deadline,
        estimated_cost=repair.estimated_cost,
    )
    
    # Меняем статус актива на "maintenance" при создании заявки
    asset.status = "maintenance"
    
    db.add(db_repair)
    db.commit()
    db.refresh(db_repair)
    
    print(f"[create_repair] db_repair.id: {db_repair.id}")
    print(f"[create_repair] Asset status changed to: {asset.status}")
    print(f"[create_repair] returning from create_repair")
    
    return repair_to_response(db_repair)


@router.put("/{repair_id}/", response_model=dict)
def update_repair(
    repair_id: int,
    repair: RepairRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print(f"[update_repair] repair_id: {repair_id}")
    print(f"[update_repair] repair: {repair.model_dump()}")
    try:
        db_repair = db.query(RepairRequest).filter(RepairRequest.id == repair_id).first()
        if not db_repair:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
        
        if current_user.role not in ("admin", "responsible") and db_repair.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        update_data = repair.model_dump(exclude_unset=True)
        print(f"[update_repair] update_data: {update_data}")
    except Exception as e:
        print(f"[update_repair] error: {e}")
        raise
    for field, value in update_data.items():
        if value is not None and hasattr(db_repair, field):
            setattr(db_repair, field, value)
    
    db.commit()
    db.refresh(db_repair)
    
    print(f"[update_repair] returning from update_repair")
    
    return repair_to_response(db_repair)


@router.patch("/{repair_id}/status/", response_model=dict)
def update_repair_status(
    repair_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from pydantic import ValidationError
    
    try:
        status_update = RepairStatusUpdate(**payload)
    except ValidationError:
        if "status_update" in payload and isinstance(payload["status_update"], dict):
            status_update = RepairStatusUpdate(**payload["status_update"])
        else:
            raise
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[update_repair_status] repair_id: {repair_id}")
    logger.info(f"[update_repair_status] status_update: {status_update.model_dump()}")
    logger.info(f"[update_repair_status] status_update.status: {status_update.status}")
    logger.info(f"[update_repair_status] current_user: {current_user.username}, role: {current_user.role}")
    
    try:
        db_repair = db.query(RepairRequest).filter(RepairRequest.id == repair_id).first()
        if not db_repair:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
        
        if current_user.role not in ("admin", "responsible") and db_repair.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        status_value = get_status_value(status_update.status)
        print(f"[update_repair_status] status_value: {status_value}")
    except Exception as e:
        print(f"[update_repair_status] error: {e}")
        raise
    db_repair.status = status_value
    
    # Обновляем статус актива в зависимости от статуса заявки
    if db_repair.asset:
        if status_value == "approved":
            # При одобрении заявки статус актива остается maintenance (был изменен при создании заявки)
            pass
        elif status_value == "in_progress":
            db_repair.asset.status = "maintenance"
        elif status_value == "completed":
            db_repair.asset.status = "active"
        elif status_value == "rejected" or status_value == "cancelled":
            # Если заявка отклонена или отменена, возвращаем статус актива на active
            db_repair.asset.status = "active"
    
    if status_value == "approved" and status_update.assigned_to is not None:
        db_repair.assigned_to = status_update.assigned_to
        db_repair.assigned_at = datetime.now()
    elif status_value == "completed":
        db_repair.actual_completion_date = status_update.actual_completion_date or date.today()
        db_repair.actual_cost = status_update.actual_cost
        db_repair.completion_notes = status_update.completion_notes
    elif status_value == "rejected":
        db_repair.rejection_reason = status_update.rejection_reason
    
    db_repair.updated_at = datetime.now()
    db.commit()
    db.refresh(db_repair)
    db.refresh(db_repair.asset)
    
    print(f"[update_repair_status] db_repair.status: {db_repair.status}")
    print(f"[update_repair_status] returning from update_repair_status")
    
    return repair_to_response(db_repair)


@router.patch("/{repair_id}/priority/", response_model=dict)
def update_repair_priority(
    repair_id: int,
    priority_update: RepairPriorityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[update_repair_priority] repair_id: {repair_id}")
    logger.info(f"[update_repair_priority] priority_update: {priority_update.model_dump()}")
    logger.info(f"[update_repair_priority] priority_update.priority: {priority_update.priority}")
    try:
        db_repair = db.query(RepairRequest).filter(RepairRequest.id == repair_id).first()
        if not db_repair:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
        
        if current_user.role not in ("admin", "responsible") and db_repair.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    except Exception as e:
        logger.error(f"[update_repair_priority] error: {e}")
        raise
    db_repair.priority = get_priority_value(priority_update.priority)
    db_repair.updated_at = datetime.now()
    db.commit()
    db.refresh(db_repair)
    
    logger.info(f"[update_repair_priority] db_repair.priority: {db_repair.priority}")
    logger.info(f"[update_repair_priority] returning from update_repair_priority")
    
    return repair_to_response(db_repair)


@router.delete("/{repair_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_repair(repair_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_repair = db.query(RepairRequest).filter(RepairRequest.id == repair_id).first()
    if not db_repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    
    if current_user.role not in ("admin", "responsible") and db_repair.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Запрещаем удаление одобренных или взятых в работу заявок
    if db_repair.status in ("approved", "in_progress", "completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить одобренную, выполняемую или завершённую заявку. Сначала отмените её."
        )
    
    db.delete(db_repair)
    db.commit()
    return None


@router.get("/templates/", response_model=RepairTemplateListResponse)
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(RepairTemplate)
    if active_only:
        query = query.filter(RepairTemplate.is_active == True)
    
    items = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "items": [template_to_response(template) for template in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/templates/{template_id}/", response_model=RepairTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    template = db.query(RepairTemplate).filter(RepairTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    return template_to_response(template)


@router.post("/templates/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_template(
    template: RepairTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_template = RepairTemplate(
        name=template.name,
        description=template.description,
        template_data=template.template_data or {},
        is_active=template.is_active,
        is_default=template.is_default,
        created_by=current_user.id,
        created_at=datetime.now(),
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return template_to_response(db_template)


@router.put("/templates/{template_id}/", response_model=dict)
def update_template(
    template_id: int,
    template: RepairTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_template = db.query(RepairTemplate).filter(RepairTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    update_data = template.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None and hasattr(db_template, field):
            setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    
    return template_to_response(db_template)


@router.delete("/templates/{template_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_template = db.query(RepairTemplate).filter(RepairTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    db.delete(db_template)
    db.commit()
    return None


@router.post("/templates/{template_id}/apply/", response_model=dict)
def apply_template(
    template_id: int,
    apply_data: RepairTemplateApply,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = db.query(RepairTemplate).filter(RepairTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    
    asset = db.query(Asset).filter(Asset.id == apply_data.asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset not found")
    
    db_repair = RepairRequest(
        asset_id=apply_data.asset_id,
        title=template.name,
        description=template.description or "",
        priority="medium",
        status="draft",
        created_by=current_user.id,
        template_data=template.template_data,
    )
    
    db.add(db_repair)
    db.commit()
    db.refresh(db_repair)
    
    return repair_to_response(db_repair)


@router.get("/{repair_id}/print/")
def simple_print_repair(repair_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repair = db.query(RepairRequest).filter(RepairRequest.id == repair_id).first()
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    
    return repair_to_response(repair)


@router.get("/stats/")
def get_repair_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(RepairRequest)
    
    if current_user.role not in ("admin", "responsible"):
        query = query.filter(RepairRequest.created_by == current_user.id)
    
    total = query.count()
    
    results = query.all()
    
    counts = {}
    for status in RepairStatus:
        counts[status.value] = 0
    
    for repair in results:
        status_key = repair.status.value if repair.status else "draft"
        counts[status_key] = counts.get(status_key, 0) + 1
    
    templates_count = db.query(RepairTemplate).count()
    
    return {
        "total_repairs": total,
        "pending": counts.get("draft", 0) + counts.get("submitted", 0) + counts.get("approved", 0),
        "in_progress": counts.get("in_progress", 0),
        "completed": counts.get("completed", 0),
        "rejected": counts.get("rejected", 0),
        "cancelled": counts.get("cancelled", 0),
        "total_templates": templates_count,
    }


@router.post("/{repair_id}/print/pdf/")
def full_pdf_print(repair_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repair = db.query(RepairRequest).filter(RepairRequest.id == repair_id).first()
    if not repair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    
    repair_data = repair_to_response(repair)
    
    generator = RepairReportGenerator()
    pdf_bytes = generator.generate_single_repair(repair_data)
    
    return {
        "success": True,
        "repair_id": repair_id,
        "message": "PDF generated successfully",
    }
