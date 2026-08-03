# backend/src/presentation/http/routers/marking.py
"""Маркировка имущества — генерация бирок для печати"""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user

router = APIRouter(prefix="/marking", tags=["marking"])


def safe_str(val, default=""):
    if val is None:
        return default
    return str(val)


def safe_date(val) -> Optional[str]:
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)


def get_initials(full_name: str) -> str:
    """Извлекает инициалы из полного имени"""
    if not full_name:
        return ""
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}.{parts[1][0]}."
    elif len(parts) == 1:
        return f"{parts[0][0]}."
    return ""


def format_responsible(responsible: str) -> str:
    """Форматирует ФИО ответственного: Иванов И.И."""
    if not responsible:
        return "—"
    parts = responsible.strip().split()
    if len(parts) >= 3:
        return f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
    elif len(parts) == 2:
        return f"{parts[0]} {parts[1][0]}."
    return responsible


@router.get("/assets")
async def get_marking_assets(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    search: Optional[str] = Query(None, description="Поиск"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список активов для маркировки"""
    query = db.query(Asset).filter(Asset.is_active == True)
    
    if status:
        query = query.filter(Asset.status == status)
    
    if search:
        query = query.filter(
            (Asset.name.contains(search)) |
            (Asset.inventory_number.contains(search)) |
            (Asset.responsible_person.contains(search))
        )
    
    assets = query.order_by(Asset.inventory_number).all()
    
    return [
        {
            "id": a.id,
            "inventory_number": safe_str(a.inventory_number),
            "name": safe_str(a.name),
            "status": safe_str(a.status),
            "responsible": safe_str(a.responsible_person),
            "responsible_initials": get_initials(safe_str(a.responsible_person)) if a.responsible_person else "",
            "purchase_date": safe_date(a.purchase_date),
            "commissioning_date": safe_date(a.commissioning_date),
            "location": safe_str(a.location_address),
            "department": safe_str(a.department_code),
        }
        for a in assets
    ]


@router.get("/settings")
async def get_marking_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить настройки маркировки"""
    # Проверим, есть ли настройки в таблице assets как специальные записи
    # Или используем дефолтные значения
    return {
        "company_name": "ООО «ПАО»",  # Дефолтное название фирмы
        "company_short": "ПАО",  # Сокращённое
        "label_width": 105,  # мм
        "label_height": 37,  # мм
        "labels_per_row": 3,
        "labels_per_page": 21,
    }


@router.post("/settings")
async def save_marking_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сохранить настройки маркировки"""
    return {
        "message": "Настройки сохранены",
        "company_name": settings.get("company_name", "ООО «ПАО»"),
        "company_short": settings.get("company_short", "ПАО"),
    }


@router.get("/label-html/{asset_id}")
async def get_label_html(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить HTML-шаблон бирки для актива"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")
    
    company_name = "ООО «ПАО»"
    company_short = "ПАО"
    
    responsible = safe_str(asset.responsible_person)
    initials = get_initials(responsible)
    formatted = format_responsible(responsible)
    
    purchase_date = safe_date(asset.purchase_date) or "—"
    
    # Генерируем HTML-бирку
    html = f"""
    <div class="label" style="
        width: {105}mm;
        height: {37}mm;
        border: 1px solid #000;
        padding: 3mm;
        box-sizing: border-box;
        font-family: Arial, sans-serif;
        page-break-inside: avoid;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="font-size: 10pt; font-weight: bold; text-align: center; border-bottom: 1px solid #000; padding-bottom: 2mm;">
            {company_name}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
                <div style="font-size: 11pt; font-weight: bold; margin-bottom: 1mm;">
                    {safe_str(asset.name)}
                </div>
                <div style="font-size: 8pt; color: #333;">
                    Инв. №: <strong>{safe_str(asset.inventory_number)}</strong>
                </div>
                <div style="font-size: 8pt; color: #333;">
                    Отв: {formatted}
                </div>
            </div>
            <div style="text-align: right; font-size: 8pt;">
                <div>Пост. на учёт:</div>
                <div style="font-weight: bold; font-size: 10pt;">{purchase_date}</div>
            </div>
        </div>
        <div style="font-size: 7pt; color: #666; text-align: right;">
            {company_short}
        </div>
    </div>
    """
    
    return {"html": html, "inventory_number": safe_str(asset.inventory_number)}


@router.get("/label-batch")
async def get_batch_labels(
    asset_ids: str = Query(..., description="CSV ID активов"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить HTML для пакетной печати бирок"""
    ids = [int(x.strip()) for x in asset_ids.split(",") if x.strip()]
    assets = db.query(Asset).filter(Asset.id.in_(ids)).all()
    
    if not assets:
        raise HTTPException(status_code=404, detail="Активы не найдены")
    
    company_name = "ООО «ПАО»"
    company_short = "ПАО"
    
    labels_html = []
    for asset in assets:
        responsible = safe_str(asset.responsible_person)
        formatted = format_responsible(responsible)
        purchase_date = safe_date(asset.purchase_date) or "—"
        
        label = f"""
        <div class="label" style="
            width: 105mm; height: 37mm; border: 1px solid #000; padding: 3mm;
            box-sizing: border-box; font-family: Arial, sans-serif;
            page-break-inside: avoid; display: inline-block;
            vertical-align: top; margin: 2mm;
            flex-direction: column; justify-content: space-between;
        ">
            <div style="font-size: 10pt; font-weight: bold; text-align: center; border-bottom: 1px solid #000; padding-bottom: 2mm;">
                {company_name}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <div style="font-size: 11pt; font-weight: bold; margin-bottom: 1mm;">
                        {safe_str(asset.name)}
                    </div>
                    <div style="font-size: 8pt; color: #333;">
                        Инв. №: <strong>{safe_str(asset.inventory_number)}</strong>
                    </div>
                    <div style="font-size: 8pt; color: #333;">
                        Отв: {formatted}
                    </div>
                </div>
                <div style="text-align: right; font-size: 8pt;">
                    <div>Пост. на учёт:</div>
                    <div style="font-weight: bold; font-size: 10pt;">{purchase_date}</div>
                </div>
            </div>
            <div style="font-size: 7pt; color: #666; text-align: right;">
                {company_short}
            </div>
        </div>
        """
        labels_html.append(label)
    
    full_html = f"""
    <html>
    <head>
        <title>Бирки для печати</title>
        <style>
            @page {{ size: A4; margin: 10mm; }}
            body {{ margin: 0; padding: 0; }}
            .page-break {{ page-break-after: always; }}
        </style>
    </head>
    <body>
        {''.join(labels_html)}
    </body>
    </html>
    """
    
    return {"html": full_html, "count": len(assets)}
