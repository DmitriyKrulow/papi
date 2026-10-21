# backend/src/presentation/http/routers/transfer_acts.py
"""Акты передачи имущества в пользование сотрудникам"""
import os
import re
import uuid
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.employee import Employee
from src.infrastructure.db.models.transfer_act import TransferAct
from src.infrastructure.db.models.asset_transfer_history import AssetTransferHistory
from src.presentation.http.dependencies.auth import get_current_admin

router = APIRouter(prefix="/admin/transfer-acts", tags=["transfer-acts"])

# Папки для файлов
REPORTS_DIR = "uploads/reports"
PRINT_DIR = "uploads/prints"
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(PRINT_DIR, exist_ok=True)

MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024  # 20 MB

_ALLOWED_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff")


def safe_isoformat(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    try:
        return value.isoformat() if hasattr(value, "isoformat") else str(value)
    except (AttributeError, ValueError):
        return None


def employee_display_name(emp) -> str:
    """ФИО сотрудника в формате 'Фамилия Имя Отчество'"""
    if not emp:
        return ""
    parts = [emp.last_name or "", emp.first_name or "", emp.middle_name or ""]
    return " ".join(p for p in parts if p).strip()


def _safe_file_path(directory: str, filename: str) -> str:
    """Защита от path traversal"""
    base = os.path.abspath(directory)
    path = os.path.abspath(os.path.join(base, filename))
    if not path.startswith(base + os.sep) and path != base:
        raise HTTPException(status_code=400, detail="Недопустимое имя файла")
    return path


def transfer_act_to_dict(act: TransferAct, db: Session) -> dict:
    # Загружаем активы, входящие в акт
    assets = []
    if act.asset_ids:
        asset_rows = db.query(Asset).filter(Asset.id.in_(act.asset_ids), Asset.is_active == True).all()
        by_id = {a.id: a for a in asset_rows}
        for asset_id in act.asset_ids:
            a = by_id.get(asset_id)
            if a:
                assets.append({
                    "id": a.id,
                    "name": a.name or "",
                    "inventory_number": a.inventory_number or "",
                    "quantity": a.quantity or 1,
                    "model": a.model or "",
                    "serial_number": a.serial_number or "",
                })

    return {
        "id": act.id,
        "act_number": act.act_number,
        "act_date": safe_isoformat(act.act_date),
        "employee_id": act.employee_id,
        "employee_name": act.employee_name,
        "employee_position": act.employee_position,
        "department_id": act.department_id,
        "department_name": act.department_name,
        "room_id": act.room_id,
        "room_name": act.room_name,
        "asset_ids": act.asset_ids or [],
        "assets": assets,
        "asset_count": len(act.asset_ids or []),
        "file_path": act.file_path,
        "attachments": act.attachments or [],
        "signed": act.signed,
        "signed_at": safe_isoformat(act.signed_at),
        "signed_by": act.signed_by_user.full_name if act.signed_by_user else None,
        "is_archived": act.is_archived,
        "archived_at": safe_isoformat(act.archived_at),
        "created_by": act.created_by_user.full_name if act.created_by_user else None,
        "created_at": safe_isoformat(act.created_at),
    }


def _next_act_number(db: Session) -> str:
    from sqlalchemy import func as sa_func

    year = datetime.now().year
    max_id = db.query(sa_func.max(TransferAct.id)).scalar() or 0
    seq = max_id + 1
    return f"АП-{year}-{seq:04d}"


@router.get("/history")
async def list_transfer_history(
    asset_id: Optional[int] = Query(None, description="Фильтр по активу"),
    employee_id: Optional[int] = Query(None, description="Фильтр по сотруднику-получателю"),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """История передачи активов сотрудникам (описи + акты передачи)"""
    from src.infrastructure.db.models.asset import Asset

    query = db.query(AssetTransferHistory).options(
        joinedload(AssetTransferHistory.asset),
        joinedload(AssetTransferHistory.new_employee),
    )
    if asset_id is not None:
        query = query.filter(AssetTransferHistory.asset_id == asset_id)
    if employee_id is not None:
        query = query.filter(AssetTransferHistory.new_employee_id == employee_id)

    rows = query.order_by(AssetTransferHistory.transfer_date.desc()).limit(limit).all()

    result = []
    for h in rows:
        asset = h.asset
        result.append({
            "id": h.id,
            "asset_id": h.asset_id,
            "asset_name": asset.name if asset else "",
            "inventory_number": asset.inventory_number if asset else "",
            "prev_employee_id": h.prev_employee_id,
            "prev_employee_name": h.prev_employee_name,
            "new_employee_id": h.new_employee_id,
            "new_employee_name": h.new_employee_name,
            "source": h.source,
            "source_id": h.source_id,
            "source_ref": h.source_ref,
            "transfer_date": safe_isoformat(h.transfer_date),
            "created_by": h.created_by_user.full_name if h.created_by_user else None,
            "created_at": safe_isoformat(h.created_at),
        })
    return JSONResponse(content=result)


@router.get("/")
async def list_transfer_acts(
    signed: Optional[bool] = Query(None),
    archived: Optional[bool] = Query(None, description="По умолчанию — только неархивированные"),
    employee_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """Список актов передачи"""
    query = db.query(TransferAct)
    if archived is None:
        query = query.filter(TransferAct.is_archived == False)
    else:
        query = query.filter(TransferAct.is_archived == archived)
    if signed is not None:
        query = query.filter(TransferAct.signed == signed)
    if employee_id:
        query = query.filter(TransferAct.employee_id == employee_id)

    acts = query.order_by(TransferAct.created_at.desc()).all()
    return JSONResponse(content=[transfer_act_to_dict(a, db) for a in acts])


@router.post("/")
async def create_transfer_act(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """Создать акт передачи: {asset_ids: [..], employee_id: int, room_id?: int}"""
    from src.infrastructure.reports.transfer_act_report import TransferActReportGenerator

    asset_ids = data.get("asset_ids") or []
    employee_id = data.get("employee_id")
    room_id = data.get("room_id")

    if not asset_ids:
        raise HTTPException(status_code=400, detail="Не выбрано ни одного актива")
    if not employee_id:
        raise HTTPException(status_code=400, detail="Не выбран сотрудник-получатель")

    employee = db.query(Employee).filter(
        Employee.id == employee_id, Employee.is_active == True
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    # Опциональный кабинет
    room = None
    department_name = ""
    room_name = ""
    if room_id:
        from src.infrastructure.db.models.department import Room, Department

        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            room_name = room.name or ""
            dept = db.query(Department).filter(Department.id == room.department_id).first()
            department_name = dept.name if dept else ""

    full_name = employee_display_name(employee)
    position = employee.position or ""

    assets = db.query(Asset).filter(
        Asset.id.in_(asset_ids), Asset.is_active == True
    ).all()
    if not assets:
        raise HTTPException(status_code=400, detail="Активы не найдены или неактивны")

    act_number = _next_act_number(db)
    act_date = data.get("act_date")
    try:
        act_date_dt = datetime.fromisoformat(act_date) if act_date else datetime.now()
    except (ValueError, TypeError):
        act_date_dt = datetime.now()

    # Генерируем Excel-акт
    from src.infrastructure.reports.transfer_act_report import TransferActReportGenerator as Gen

    generator = Gen()
    assets_data = [
        {
            "name": a.name or "",
            "inventory_number": a.inventory_number or "",
            "quantity": a.quantity or 1,
            "model": a.model or "",
            "serial_number": a.serial_number or "",
        }
        for a in assets
    ]
    act_filename = f"акт_передачи_{act_number.replace('/', '_').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    act_filepath = os.path.join(REPORTS_DIR, act_filename)
    excel_bytes = generator.generate(
        act_number=act_number,
        act_date=act_date_dt,
        employee_name=full_name,
        employee_position=position,
        department_name=department_name,
        room_name=room_name,
        assets=assets_data,
    )
    with open(act_filepath, "wb") as f:
        f.write(excel_bytes)

    act = TransferAct(
        act_number=act_number,
        act_date=act_date_dt,
        employee_id=employee.id,
        employee_name=full_name,
        employee_position=position,
        department_id=room.department_id if room else None,
        department_name=department_name,
        room_id=room.id if room else None,
        room_name=room_name,
        asset_ids=asset_ids,
        file_path=act_filepath,
        attachments=[],
        signed=False,
        created_by_user_id=current_user.id,
        created_at=datetime.now(),
    )
    db.add(act)
    db.commit()
    db.refresh(act)

    return JSONResponse(content={
        "message": "Акт передачи сформирован",
        "act": transfer_act_to_dict(act, db),
    })


@router.get("/{act_id}")
async def get_transfer_act(
    act_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    act = db.query(TransferAct).filter(TransferAct.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")
    return JSONResponse(content=transfer_act_to_dict(act, db))


@router.get("/{act_id}/download")
async def download_transfer_act(
    act_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    act = db.query(TransferAct).filter(TransferAct.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")
    if not act.file_path or not os.path.exists(act.file_path):
        raise HTTPException(status_code=404, detail="Файл акта не найден")
    return FileResponse(
        path=act.file_path,
        filename=os.path.basename(act.file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/{act_id}/confirm")
async def confirm_transfer_act(
    act_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """Подписать акт: проставить сотрудника активам и записать историю передач"""
    from src.infrastructure.db.models.asset_transfer_history import AssetTransferHistory

    act = db.query(TransferAct).filter(TransferAct.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")
    if act.signed:
        raise HTTPException(status_code=400, detail="Акт уже подписан")
    if act.is_archived:
        raise HTTPException(status_code=400, detail="Нельзя подписать архивированный акт")

    employee = None
    if act.employee_id:
        employee = db.query(Employee).filter(Employee.id == act.employee_id).first()
    if not employee:
        raise HTTPException(status_code=400, detail="Сотрудник-получатель не найден")

    assets = db.query(Asset).filter(Asset.id.in_(act.asset_ids or [])).all()
    updated = 0
    for asset in assets:
        prev_emp_id = asset.employee_id
        prev_emp_name = None
        if prev_emp_id:
            prev = db.query(Employee).filter(Employee.id == prev_emp_id).first()
            prev_emp_name = employee_display_name(prev) if prev else None

        asset.employee_id = employee.id
        asset.responsible_person = employee_display_name(employee)
        updated += 1

        history = AssetTransferHistory(
            asset_id=asset.id,
            prev_employee_id=prev_emp_id,
            prev_employee_name=prev_emp_name,
            new_employee_id=employee.id,
            new_employee_name=employee_display_name(employee),
            source="transfer_act",
            source_id=act.id,
            source_ref=f"Акт передачи {act.act_number}",
            transfer_date=datetime.now(),
            created_by_user_id=current_user.id,
            created_at=datetime.now(),
        )
        db.add(history)

    act.signed = True
    act.signed_at = datetime.now()
    act.signed_by_user_id = current_user.id
    db.commit()

    return JSONResponse(content={
        "message": "Акт подписан, сотрудник проставлен активам",
        "act_id": act.id,
        "assets_updated": updated,
    })


@router.post("/{act_id}/archive")
async def archive_transfer_act(
    act_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    act = db.query(TransferAct).filter(TransferAct.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")
    if act.signed:
        raise HTTPException(status_code=400, detail="Нельзя архивировать подписанный акт")
    if act.is_archived:
        raise HTTPException(status_code=400, detail="Акт уже архивирован")

    act.is_archived = True
    act.archived_at = datetime.now()
    db.commit()

    return JSONResponse(content={
        "message": "Акт архивирован",
        "act_id": act.id,
    })


@router.post("/{act_id}/attachments")
async def upload_transfer_act_attachment(
    act_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    """Загрузка скан-копий расписок / приложений к акту"""
    act = db.query(TransferAct).filter(TransferAct.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    filename = file.filename or "scan.jpg"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Недопустимый тип файла")

    contents = await file.read()
    if len(contents) > MAX_ATTACHMENT_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 20 МБ)")

    att_id = uuid.uuid4().hex
    safe_stored_name = f"{att_id}{ext}"
    file_path = os.path.join(PRINT_DIR, safe_stored_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    attachments = list(act.attachments or [])
    attachments.append({
        "id": att_id,
        "filename": filename,
        "file_path": file_path,
        "uploaded_at": datetime.now().isoformat(),
        "uploaded_by": current_user.full_name or str(current_user.id),
    })
    act.attachments = attachments
    db.commit()
    db.refresh(act)

    return JSONResponse(content={
        "message": "Скан-копия прикреплена",
        "attachments": act.attachments,
    })


@router.get("/{act_id}/attachments/{att_id}")
async def download_transfer_act_attachment(
    act_id: int,
    att_id: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_admin),
):
    act = db.query(TransferAct).filter(TransferAct.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Акт не найден")

    attachments = act.attachments or []
    att = next((a for a in attachments if a.get("id") == att_id), None)
    if not att or not att.get("file_path") or not os.path.exists(att["file_path"]):
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(
        path=att["file_path"],
        filename=att.get("filename", f"attachment{os.path.splitext(att['file_path'])[1]}"),
    )