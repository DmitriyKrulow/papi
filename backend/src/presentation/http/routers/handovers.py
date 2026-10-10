# backend/src/presentation/http/routers/handovers.py
"""Передача/возврат имущества между сотрудниками — система МОЛ"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.asset_handover import AssetHandover
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.employee import Employee
from src.presentation.http.dependencies.auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/handovers", tags=["handovers"])


# ======================================================================
# Передача актива
# ======================================================================

@router.post("/handover")
async def handover_asset(
    asset_id: int = Query(..., description="ID актива"),
    received_by_user_id: int = Query(..., description="ID получателя"),
    reason: str = Query("", description="Причина передачи"),
    return_deadline_days: int = Query(0, description="Срок возврата в днях (0 = навсегда)"),
    comment: str = Query("", description="Комментарий"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Передача актива от одного сотрудника другому.
    
    Фиксирует:
    - Кто передал (current_user)
    - Кто получил (received_by_user_id)
    - Когда (datetime.now)
    - Зачем (reason)
    - Срок возврата (return_deadline)
    
    При передаче автоматически:
    - Обновляется responsible_person на активе
    - Создаётся запись в истории передач
    """
    # Проверяем актив
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.is_active == True).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")
    
    # Проверяем получателя
    receiver = db.query(User).filter(User.id == received_by_user_id, User.is_active == True).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Получатель не найден или неактивен")
    
    # Проверяем, нет ли активной передачи этого актива
    active_handover = db.query(AssetHandover).filter(
        AssetHandover.asset_id == asset_id,
        AssetHandover.is_closed == False,
        AssetHandover.action_type == "handover"
    ).first()
    
    if active_handover:
        raise HTTPException(
            status_code=400,
            detail=f"Актив уже передан {active_handover.received_by_user.full_name} "
                   f"{active_handover.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
    
    # Создаём передачу
    handover = AssetHandover(
        asset_id=asset_id,
        handover_by=current_user.id,
        received_by=received_by_user_id,
        action_type="handover",
        reason=reason,
        return_deadline=datetime.now() + timedelta(days=return_deadline_days) if return_deadline_days > 0 else None,
        comment=comment,
        rfid_tag=asset.rfid_tag,
    )
    
    # Обновляем актив
    asset.responsible_person = receiver.full_name or receiver.username
    asset.employee_id = None  # Сбрасываем привязку к сотруднику при передаче
    
    db.add(handover)
    db.commit()
    db.refresh(handover)
    
    # Отправляем уведомление получателю
    try:
        from src.core.services.notification_service import NotificationService
        service = NotificationService()
        service.send_handover_notification(receiver, asset, current_user, reason, handover.return_deadline)
    except Exception as e:
        logger.warning(f"Failed to send handover notification: {e}")
    
    return {
        "success": True,
        "message": f"Актив '{asset.name}' передан {receiver.full_name}",
        "handover_id": handover.id,
        "asset": {
            "id": asset.id,
            "inventory_number": asset.inventory_number,
            "name": asset.name,
            "rfid_tag": asset.rfid_tag or "",
        },
        "from": current_user.full_name or current_user.username,
        "to": receiver.full_name or receiver.username,
        "reason": reason,
        "return_deadline": handover.return_deadline.isoformat() if handover.return_deadline else None,
        "created_at": handover.created_at.isoformat(),
    }


# ======================================================================
# Возврат актива
# ======================================================================

@router.post("/return")
async def return_asset(
    asset_id: int = Query(..., description="ID актива"),
    returned_by_user_id: int = Query(..., description="ID вернувшего"),
    comment: str = Query("", description="Комментарий при возврате"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возврат актива от сотрудника.
    
    Фиксирует:
    - Кто вернул (returned_by_user_id)
    - Когда (actual_return_date)
    - Статус передачи меняется на closed
    
    При возврате автоматически:
    - Актив возвращается текущему ответственному (из истории)
    - Создаётся запись о возврате
    """
    # Проверяем актив
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.is_active == True).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")
    
    # Проверяем вернувшего
    returner = db.query(User).filter(User.id == returned_by_user_id).first()
    if not returner:
        raise HTTPException(status_code=404, detail="Возвративший не найден")
    
    # Ищем активную передачу
    active_handover = db.query(AssetHandover).filter(
        AssetHandover.asset_id == asset_id,
        AssetHandover.is_closed == False,
        AssetHandover.action_type == "handover"
    ).first()
    
    if not active_handover:
        raise HTTPException(
            status_code=400,
            detail="Нет активной передачи для этого актива"
        )
    
    # Проверяем что вернувший — тот кто получил
    if active_handover.received_by != returned_by_user_id:
        raise HTTPException(
            status_code=400,
            detail="Только получатель может вернуть актив"
        )
    
    # Создаём запись о возврате
    return_record = AssetHandover(
        asset_id=asset_id,
        handover_by=returned_by_user_id,
        received_by=current_user.id,
        action_type="return",
        comment=comment,
        rfid_tag=asset.rfid_tag,
    )
    
    # Закрываем передачу
    active_handover.is_closed = True
    active_handover.actual_return_date = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Актив '{asset.name}' возвращён",
        "handover_id": active_handover.id,
        "asset": {
            "id": asset.id,
            "inventory_number": asset.inventory_number,
            "name": asset.name,
        },
        "returned_by": returner.full_name or returner.username,
        "returned_at": datetime.now().isoformat(),
        "was_on_loan_since": active_handover.created_at.isoformat(),
        "loan_duration_days": (datetime.now() - active_handover.created_at).days,
    }


# ======================================================================
# История передач актива
# ======================================================================

@router.get("/asset/{asset_id}")
async def get_asset_handover_history(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить полную историю передач актива"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")
    
    handovers = db.query(AssetHandover).options(
        joinedload(AssetHandover.handover_by_user),
        joinedload(AssetHandover.received_by_user),
    ).filter(
        AssetHandover.asset_id == asset_id
    ).order_by(AssetHandover.created_at.desc()).all()
    
    history = []
    for h in handovers:
        history.append({
            "id": h.id,
            "action_type": h.action_type,
            "from": h.handover_by_user.full_name or h.handover_by_user.username,
            "to": h.received_by_user.full_name or h.received_by_user.username,
            "reason": h.reason or "",
            "comment": h.comment or "",
            "created_at": h.created_at.isoformat() if h.created_at else None,
            "return_deadline": h.return_deadline.isoformat() if h.return_deadline else None,
            "actual_return_date": h.actual_return_date.isoformat() if h.actual_return_date else None,
            "is_closed": h.is_closed,
            "rfid_tag": h.rfid_tag or "",
        })
    
    # Активная передача
    active = next((h for h in handovers if not h.is_closed and h.action_type == "handover"), None)
    current_holder = None
    if active:
        current_holder = {
            "user_id": active.received_by,
            "full_name": active.received_by_user.full_name or active.received_by_user.username,
            "since": active.created_at.isoformat() if active.created_at else None,
            "deadline": active.return_deadline.isoformat() if active.return_deadline else None,
            "is_overdue": bool(active.return_deadline and active.return_deadline < datetime.now()),
        }
    
    return {
        "asset_id": asset.id,
        "inventory_number": asset.inventory_number,
        "name": asset.name,
        "current_holder": current_holder,
        "total_handovers": len(handovers),
        "history": history
    }


# ======================================================================
# Активные передачи текущего пользователя
# ======================================================================

@router.get("/my-active")
async def get_my_active_handovers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список активных передач, где текущий пользователь — получатель"""
    handovers = db.query(AssetHandover).options(
        joinedload(AssetHandover.handover_by_user),
        joinedload(AssetHandover.received_by_user),
    ).filter(
        AssetHandover.received_by == current_user.id,
        AssetHandover.is_closed == False,
        AssetHandover.action_type == "handover"
    ).order_by(AssetHandover.return_deadline.asc()).all()
    
    result = []
    for h in handovers:
        is_overdue = bool(h.return_deadline and h.return_deadline < datetime.now())
        result.append({
            "id": h.id,
            "asset_id": h.asset_id,
            "inventory_number": h.asset.inventory_number if h.asset else "",
            "asset_name": h.asset.name if h.asset else "",
            "rfid_tag": h.rfid_tag or "",
            "from": h.handover_by_user.full_name or h.handover_by_user.username,
            "reason": h.reason or "",
            "created_at": h.created_at.isoformat() if h.created_at else None,
            "return_deadline": h.return_deadline.isoformat() if h.return_deadline else None,
            "is_overdue": is_overdue,
            "days_overdue": max(0, (datetime.now() - h.return_deadline).days) if is_overdue else 0,
        })
    
    # Сортируем: сначала просроченные
    result.sort(key=lambda x: (not x["is_overdue"], x.get("days_overdue", 0)))
    
    overdue_count = sum(1 for r in result if r["is_overdue"])
    
    return {
        "user_id": current_user.id,
        "user_name": current_user.full_name or current_user.username,
        "total_active": len(result),
        "overdue": overdue_count,
        "handovers": result
    }


# ======================================================================
# Все активные передачи (админ)
# ======================================================================

@router.get("/all-active")
async def get_all_active_handovers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Получить все активные передачи (админ-панель)"""
    handovers = db.query(AssetHandover).options(
        joinedload(AssetHandover.handover_by_user),
        joinedload(AssetHandover.received_by_user),
    ).filter(
        AssetHandover.is_closed == False,
        AssetHandover.action_type == "handover"
    ).order_by(AssetHandover.return_deadline.asc()).all()
    
    result = []
    for h in handovers:
        is_overdue = bool(h.return_deadline and h.return_deadline < datetime.now())
        result.append({
            "id": h.id,
            "asset_id": h.asset_id,
            "inventory_number": h.asset.inventory_number if h.asset else "",
            "asset_name": h.asset.name if h.asset else "",
            "rfid_tag": h.rfid_tag or "",
            "from": h.handover_by_user.full_name or h.handover_by_user.username,
            "from_user_id": h.handover_by_user.id,
            "to": h.received_by_user.full_name or h.received_by_user.username,
            "to_user_id": h.received_by_user.id,
            "department": h.received_by_user.employees[0].department.name if h.received_by_user.employees else "",
            "reason": h.reason or "",
            "created_at": h.created_at.isoformat() if h.created_at else None,
            "return_deadline": h.return_deadline.isoformat() if h.return_deadline else None,
            "is_overdue": is_overdue,
            "days_overdue": max(0, (datetime.now() - h.return_deadline).days) if is_overdue else 0,
        })
    
    overdue_count = sum(1 for r in result if r["is_overdue"])
    
    return {
        "total_active": len(result),
        "overdue": overdue_count,
        "handovers": result
    }


# ======================================================================
# Статистика по передачам
# ======================================================================

@router.get("/stats")
async def get_handover_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Статистика по передачам имущества"""
    total_handovers = db.query(func.count(AssetHandover.id)).filter(
        AssetHandover.action_type == "handover"
    ).scalar()
    
    active_handovers = db.query(func.count(AssetHandover.id)).filter(
        AssetHandover.is_closed == False,
        AssetHandover.action_type == "handover"
    ).scalar()
    
    overdue = db.query(func.count(AssetHandover.id)).filter(
        AssetHandover.is_closed == False,
        AssetHandover.action_type == "handover",
        AssetHandover.return_deadline < datetime.now()
    ).scalar()
    
    today = datetime.now().date()
    today_handovers = db.query(func.count(AssetHandover.id)).filter(
        AssetHandover.action_type == "handover",
        func.date(AssetHandover.created_at) == today
    ).scalar()
    
    return {
        "total_handovers": total_handovers,
        "active_handovers": active_handovers,
        "overdue": overdue,
        "today_handovers": today_handovers,
        "overdue_percent": round(overdue / active_handovers * 100, 1) if active_handovers > 0 else 0
    }
