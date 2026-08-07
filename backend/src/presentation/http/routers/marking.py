# backend/src/presentation/http/routers/marking.py
"""Маркировка имущества — генерация бирок для печати"""
import os
import uuid
import base64
import io
import qrcode
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user

router = APIRouter(prefix="/marking", tags=["marking"])

# Directory for storing logos
LOGO_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'frontend', 'public', 'marking-logos')
os.makedirs(LOGO_DIR, exist_ok=True)

# Default settings
DEFAULT_SETTINGS = {
    "company_name": "ООО «ПАО»",
    "company_short": "ПАО",
    "label_width": 105,
    "label_height": 37,
    "labels_per_row": 3,
    "labels_per_page": 21,
    "logo_url": None,
}

# In-memory settings storage (replace with DB in production)
_marking_settings: dict = dict(DEFAULT_SETTINGS)

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
        search_pattern = f"%{search}%"
        query = query.filter(
            (Asset.name.ilike(search_pattern)) |
            (Asset.inventory_number.ilike(search_pattern)) |
            (Asset.responsible_person.ilike(search_pattern))
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
    return _marking_settings


@router.post("/settings")
async def save_marking_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Сохранить настройки маркировки"""
    global _marking_settings
    _marking_settings.update({
        "company_name": settings.get("company_name", _marking_settings["company_name"]),
        "company_short": settings.get("company_short", _marking_settings["company_short"]),
        "label_width": settings.get("label_width", _marking_settings["label_width"]),
        "label_height": settings.get("label_height", _marking_settings["label_height"]),
        "labels_per_row": settings.get("labels_per_row", _marking_settings["labels_per_row"]),
        "labels_per_page": settings.get("labels_per_page", _marking_settings["labels_per_page"]),
    })
    return {
        "message": "Настройки сохранены",
        **_marking_settings,
    }


@router.post("/logo-upload")
async def upload_logo(
    file: UploadFile = File(...),
    type: str = Form("logo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Загрузить логотип для маркировки"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Можно загружать только изображения")
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] if file.filename else '.png'
    filename = f"logo_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(LOGO_DIR, filename)
    
    # Read and save file
    contents = await file.read()
    with open(filepath, 'wb') as f:
        f.write(contents)
    
    # Update settings
    _marking_settings["logo_url"] = f"/api/marking/logos/{filename}"
    
    return {"message": "Логотип загружен", "url": f"/api/marking/logos/{filename}"}


@router.delete("/logo-upload")
async def delete_logo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удалить логотип"""
    if _marking_settings.get("logo_url"):
        # Extract filename from URL
        filename = _marking_settings["logo_url"].split('/')[-1]
        filepath = os.path.join(LOGO_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    _marking_settings["logo_url"] = None
    return {"message": "Логотип удалён"}


@router.get("/logos/{filename}")
async def serve_logo(filename: str):
    """Serve uploaded logo file"""
    filepath = os.path.join(LOGO_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(filepath, media_type='image/*')


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
    
    # Используем настройки из _marking_settings
    company_name = _marking_settings.get("company_name", "ООО «ПАО»")
    company_short = _marking_settings.get("company_short", "ПАО")
    label_width = _marking_settings.get("label_width", 105)
    label_height = _marking_settings.get("label_height", 37)
    logo_url = _marking_settings.get("logo_url")
    
    responsible = safe_str(asset.responsible_person)
    initials = get_initials(responsible)
    formatted = format_responsible(responsible)
    
    purchase_date = safe_date(asset.purchase_date) or "—"
    
    # Генерируем QR-код
    import io
    import qrcode
    from PIL import Image
    
    # URL для мобильной страницы актива (публичный)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    qr_url = f"{frontend_url}/inventory/asset/{asset.id}"
    
    # Генерируем QR-код в base64
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    qr_html = f'''<div style="text-align: center; margin-top: 1mm;">
        <img src="data:image/png;base64,{qr_base64}" style="width: 20mm; height: 20mm;" />
        <div style="font-size: 5pt; color: #666; margin-top: 0.5mm;">
            {safe_str(asset.inventory_number)}
        </div>
    </div>'''
    
    # Logo HTML if exists
    logo_html = ""
    if logo_url:
        logo_html = f'''<div style="text-align: center; margin-bottom: 2mm;">
            <img src="{logo_url}" style="max-height: 12mm; max-width: 60mm; object-fit: contain;" />
        </div>'''
    
    # Генерируем HTML-бирку
    html = f"""
    <div class="label" style="
        width: {label_width}mm;
        height: {label_height}mm;
        border: 1px solid #000;
        padding: 3mm;
        box-sizing: border-box;
        font-family: Arial, sans-serif;
        page-break-inside: avoid;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        {logo_html}
        <div style="font-size: 9pt; font-weight: bold; text-align: center; border-bottom: 1px solid #000; padding-bottom: 2mm;">
            {company_name}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
                <div style="font-size: 10pt; font-weight: bold; margin-bottom: 1mm;">
                    {safe_str(asset.name)}
                </div>
                <div style="font-size: 7pt; color: #333;">
                    Инв. №: <strong>{safe_str(asset.inventory_number)}</strong>
                </div>
                <div style="font-size: 7pt; color: #333;">
                    Отв: {formatted}
                </div>
            </div>
            <div style="text-align: right; font-size: 7pt;">
                <div>Пост. на учёт:</div>
                <div style="font-weight: bold; font-size: 9pt;">{purchase_date}</div>
            </div>
        </div>
        {qr_html}
        <div style="font-size: 6pt; color: #666; text-align: right;">
            {company_short}
        </div>
    </div>
    """
    
    return {"html": html, "inventory_number": safe_str(asset.inventory_number), "qr_url": qr_url}


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
    
    # Используем настройки
    company_name = _marking_settings.get("company_name", "ООО «ПАО»")
    company_short = _marking_settings.get("company_short", "ПАО")
    label_width = _marking_settings.get("label_width", 105)
    label_height = _marking_settings.get("label_height", 37)
    logo_url = _marking_settings.get("logo_url")
    
    # Logo HTML if exists
    logo_html = ""
    if logo_url:
        logo_html = f'''<div style="text-align: center; margin-bottom: 1mm;">
            <img src="{logo_url}" style="max-height: 10mm; max-width: 50mm; object-fit: contain;" />
        </div>'''
    
    labels_html = []
    for asset in assets:
        responsible = safe_str(asset.responsible_person)
        formatted = format_responsible(responsible)
        purchase_date = safe_date(asset.purchase_date) or "—"
        
        # Генерируем QR-код
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        qr_url = f"{frontend_url}/inventory/asset/{asset.id}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        qr_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        qr_html = f'''<div style="text-align: center; margin-top: 1mm;">
            <img src="data:image/png;base64,{qr_base64}" style="width: 18mm; height: 18mm;" />
            <div style="font-size: 4pt; color: #666; margin-top: 0.5mm;">
                {safe_str(asset.inventory_number)}
            </div>
        </div>'''
        
        label = f"""
        <div class="label" style="
            width: {label_width}mm; height: {label_height}mm; border: 1px solid #000; padding: 2mm;
            box-sizing: border-box; font-family: Arial, sans-serif;
            page-break-inside: avoid; display: inline-block;
            vertical-align: top; margin: 1mm;
            flex-direction: column; justify-content: space-between;
        ">
            {logo_html}
            <div style="font-size: 8pt; font-weight: bold; text-align: center; border-bottom: 1px solid #000; padding-bottom: 1mm;">
                {company_name}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <div style="font-size: 9pt; font-weight: bold; margin-bottom: 1mm;">
                        {safe_str(asset.name)}
                    </div>
                    <div style="font-size: 6pt; color: #333;">
                        Инв. №: <strong>{safe_str(asset.inventory_number)}</strong>
                    </div>
                    <div style="font-size: 6pt; color: #333;">
                        Отв: {formatted}
                    </div>
                </div>
                <div style="text-align: right; font-size: 6pt;">
                    <div>Пост. на учёт:</div>
                    <div style="font-weight: bold; font-size: 8pt;">{purchase_date}</div>
                </div>
            </div>
            {qr_html}
            <div style="font-size: 5pt; color: #666; text-align: right;">
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
