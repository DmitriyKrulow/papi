from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.maintenance_event import MaintenanceEvent

router = APIRouter(prefix="/maintenance-events", tags=["maintenance-events"])


def safe_decimal_to_float(value, default=0.0):
    if value is None:
        return default
    try:
        if isinstance(value, (int, float, Decimal)):
            return float(value)
        return default
    except (TypeError, ValueError):
        return default


def safe_isoformat(value):
    if value is None:
        return None
    try:
        if hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')):
            return value.isoformat()
        return str(value)
    except (AttributeError, ValueError):
        return None


@router.get("/asset/{asset_id}")
def list_maintenance_events(
    asset_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Получить историю обслуживания актива"""
    events = (
        db.query(MaintenanceEvent)
        .filter(MaintenanceEvent.asset_id == asset_id)
        .order_by(MaintenanceEvent.event_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = (
        db.query(MaintenanceEvent)
        .filter(MaintenanceEvent.asset_id == asset_id)
        .count()
    )
    return {
        "items": [
            {
                "id": e.id,
                "asset_id": e.asset_id,
                "event_type": e.event_type,
                "event_date": safe_isoformat(e.event_date),
                "description": e.description,
                "cost": safe_decimal_to_float(e.cost),
                "performed_by": e.performed_by,
                "next_event_date": safe_isoformat(e.next_event_date),
                "result": e.result,
                "document_number": e.document_number,
                "created_at": safe_isoformat(e.created_at),
            }
            for e in events
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/asset/{asset_id}")
def create_maintenance_event(
    asset_id: int,
    event_data: dict,
    db: Session = Depends(get_db),
):
    """Добавить запись об обслуживании актива"""
    from src.infrastructure.db.models.asset import Asset

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    event_date_str = event_data.get("event_date")
    next_event_date_str = event_data.get("next_event_date")
    cost_value = event_data.get("cost")

    event_date = None
    next_event_date = None
    cost = None

    if event_date_str:
        try:
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
        except ValueError:
            event_date = datetime.fromisoformat(event_date_str).date()

    if next_event_date_str:
        try:
            next_event_date = datetime.strptime(next_event_date_str, "%Y-%m-%d").date()
        except ValueError:
            next_event_date = datetime.fromisoformat(next_event_date_str).date()

    if cost_value is not None:
        try:
            cost = Decimal(str(cost_value))
        except:
            cost = Decimal("0")

    event = MaintenanceEvent(
        asset_id=asset_id,
        event_type=event_data.get("event_type", "repair"),
        event_date=event_date or date.today(),
        description=event_data.get("description"),
        cost=cost,
        performed_by=event_data.get("performed_by"),
        next_event_date=next_event_date,
        result=event_data.get("result"),
        document_number=event_data.get("document_number"),
        created_at=datetime.now(),
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "asset_id": event.asset_id,
        "event_type": event.event_type,
        "event_date": safe_isoformat(event.event_date),
        "description": event.description,
        "cost": safe_decimal_to_float(event.cost),
        "performed_by": event.performed_by,
        "next_event_date": safe_isoformat(event.next_event_date),
        "result": event.result,
        "document_number": event.document_number,
        "created_at": safe_isoformat(event.created_at),
    }
