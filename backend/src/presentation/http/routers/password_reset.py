# backend/src/presentation/http/routers/password_reset.py
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.password_reset_request import PasswordResetRequest
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_admin

# Публичный роутер: /api/password-reset/...
public_router = APIRouter(prefix="/password-reset", tags=["password-reset"])

# Админский роутер: /api/admin/password-reset/...
admin_router = APIRouter(prefix="/admin/password-reset", tags=["password-reset"])


def _safe_isoformat(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    try:
        if hasattr(value, "isoformat") and callable(getattr(value, "isoformat")):
            return value.isoformat()
        return str(value)
    except (AttributeError, ValueError):
        return None


def _request_to_dict(req: PasswordResetRequest) -> dict:
    return {
        "id": req.id,
        "user_id": req.user_id,
        "username": req.username or "",
        "email": req.email or "",
        "full_name": req.full_name or "",
        "reason": req.reason or "",
        "status": req.status or "pending",
        "admin_comment": req.admin_comment,
        "created_at": _safe_isoformat(req.created_at),
        "updated_at": _safe_isoformat(req.updated_at),
    }


# ==================== Public endpoints ====================


@public_router.post("/request")
async def create_password_reset_request(
    data: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Создать заявку на сброс пароля (публичный, без авторизации)."""
    username = data.get("username")
    reason = data.get("reason")

    if not username or not reason:
        raise HTTPException(status_code=400, detail="username and reason are required")

    # Пытаемся привязать заявку к существующему пользователю
    user_id = None
    email = data.get("email")
    user = db.query(User).filter(User.username == username).first()
    if user:
        user_id = user.id
        if not email:
            email = user.email

    req = PasswordResetRequest(
        user_id=user_id,
        username=username,
        email=email,
        full_name=data.get("full_name"),
        reason=reason,
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(req)
    db.commit()
    db.refresh(req)

    return {"message": "Заявка отправлена", "id": req.id}


# ==================== Admin endpoints ====================


@admin_router.get("/requests")
async def list_password_reset_requests(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """Получить список заявок на сброс пароля (только для админов)."""
    query = db.query(PasswordResetRequest)

    if status:
        query = query.filter(PasswordResetRequest.status == status)

    requests = query.order_by(PasswordResetRequest.created_at.desc()).all()

    return [_request_to_dict(r) for r in requests]


@admin_router.post("/requests/{request_id}/approve")
async def approve_password_reset_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """Одобрить заявку на сброс пароля (только для админов)."""
    req = db.query(PasswordResetRequest).filter(PasswordResetRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Заявка уже обработана (статус: {req.status})")

    req.status = "approved"
    req.updated_at = datetime.now()
    db.commit()
    db.refresh(req)

    return {"message": "Заявка одобрена", "request": _request_to_dict(req)}


@admin_router.post("/requests/{request_id}/reject")
async def reject_password_reset_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """Отклонить заявку на сброс пароля (только для админов)."""
    req = db.query(PasswordResetRequest).filter(PasswordResetRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Заявка уже обработана (статус: {req.status})")

    req.status = "rejected"
    req.updated_at = datetime.now()
    db.commit()
    db.refresh(req)

    return {"message": "Заявка отклонена", "request": _request_to_dict(req)}
