# backend/src/presentation/http/routers/marking.py
"""Маркировка имущества — генерация бирок для печати"""
import os
import uuid
import base64
import io
import qrcode
from PIL import Image
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


def _restore_settings_from_disk():
    """Восстанавливает настройки из файлов на диске при перезапуске"""
    global _marking_settings
    
    # Ищем существующий логотип в JSON метафайле
    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'data')
    logo_meta_file = os.path.join(data_dir, 'marking_logo_meta.json')
    if os.path.exists(logo_meta_file):
        try:
            import json
            with open(logo_meta_file, 'r', encoding='utf-8') as f:
                logo_meta = json.load(f)
            logo_filename = logo_meta.get("logo_filename")
            if logo_filename:
                logo_path = os.path.join(LOGO_DIR, logo_filename)
                if os.path.exists(logo_path):
                    _marking_settings["logo_url"] = f"/api/marking/logos/{logo_filename}"
        except Exception:
            pass
    else:
        # Если метафайла нет, ищем любой существующий логотип
        try:
            logo_files = [f for f in os.listdir(LOGO_DIR) if f.startswith('logo_')]
            if logo_files:
                logo_file = sorted(logo_files)[-1]
                _marking_settings["logo_url"] = f"/api/marking/logos/{logo_file}"
        except Exception:
            pass
    
    # Восстанавливаем остальные настройки из JSON файла
    settings_file = os.path.join(data_dir, 'marking_settings.json')
    if os.path.exists(settings_file):
        try:
            import json
            with open(settings_file, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
            _marking_settings.update({
                "company_name": saved_settings.get("company_name", DEFAULT_SETTINGS["company_name"]),
                "company_short": saved_settings.get("company_short", DEFAULT_SETTINGS["company_short"]),
                "label_width": saved_settings.get("label_width", DEFAULT_SETTINGS["label_width"]),
                "label_height": saved_settings.get("label_height", DEFAULT_SETTINGS["label_height"]),
                "labels_per_row": saved_settings.get("labels_per_row", DEFAULT_SETTINGS["labels_per_row"]),
                "labels_per_page": saved_settings.get("labels_per_page", DEFAULT_SETTINGS["labels_per_page"]),
            })
        except Exception:
            pass


def _save_settings_to_disk():
    """Сохраняет настройки в JSON файл"""
    import json
    settings_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'data')
    os.makedirs(settings_dir, exist_ok=True)
    settings_file = os.path.join(settings_dir, 'marking_settings.json')
    
    # Не сохраняем logo_url в JSON (он на диске)
    settings_to_save = {k: v for k, v in _marking_settings.items() if k != "logo_url"}
    
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings_to_save, f, ensure_ascii=False, indent=2)


def _save_logo_url_to_disk(filename: str):
    """Сохраняет URL логотипа в отдельный JSON файл"""
    import json
    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    logo_meta_file = os.path.join(data_dir, 'marking_logo_meta.json')
    
    with open(logo_meta_file, 'w', encoding='utf-8') as f:
        json.dump({"logo_filename": filename}, f, ensure_ascii=False, indent=2)


# Восстанавливаем настройки при импорте модуля
_restore_settings_from_disk()

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
    # Сохраняем на диск
    _save_settings_to_disk()
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
    
    # Сохраняем URL логотипа на диск
    _save_logo_url_to_disk(filename)
    
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
    
    # Удаляем файл с URL логотипа
    logo_meta_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'data', 'marking_logo_meta.json')
    if os.path.exists(logo_meta_file):
        os.remove(logo_meta_file)
    
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
    
    # URL для мобильной страницы актива (публичный)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    qr_url = f"{frontend_url}/inventory/asset/{asset.id}"
    
    # Генерируем QR-код в base64 — компактный размер для бирки
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    # Увеличиваем разрешение для качественной печати
    img = img.resize((300, 300), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    px_per_mm = 3  # коэффициент для экранного отображения
    label_w = int(label_width * px_per_mm)
    label_h = int(label_height * px_per_mm)
    pad = int(2 * px_per_mm)
    qr_size = int(14 * px_per_mm)  # 14mm в px
    font_company = int(7 * px_per_mm)
    font_name = int(9 * px_per_mm)
    font_small = int(6 * px_per_mm)
    font_qr_text = int(5 * px_per_mm)
    font_footer = int(5 * px_per_mm)
    
    # QR-код баз64
    # QR-код — 65% от высоты бирки (динамический размер)
    qr_size_mm = int(label_height * 0.65)
    qr_img_html = f'<img src="data:image/png;base64,{qr_base64}" width="{int(qr_size_mm*px_per_mm)}" height="{int(qr_size_mm*px_per_mm)}" style="display:block" />'
    
    # Logo
    logo_img_html = ""
    if logo_url:
        logo_img_html = f'<div style="text-align: center; margin: 0 0 1px 0;"><img src="{logo_url}" style="max-height: {int(5*px_per_mm)}px; max-width: 90%; display: inline-block;" /></div>'
    
    # Генерируем HTML-бирку — ЛЕВАЯ ПОЛОВИНА: лого+фирма+информация, ПРАВАЯ: QR
    html = f"""<div class="label-wrapper" style="
        display: inline-block;
        position: relative;
        max-width: 100%;
    ">
    <style>
        .label-wrapper .label {{
            image-rendering: pixelated;
            image-rendering: high-quality;
        }}
        @media screen {{
            .label-wrapper {{
                transform: scale({px_per_mm * 0.6});
                transform-origin: 0 0;
            }}
        }}
        @media print {{
            @page {{ size: auto; margin: 2mm; }}
            .label-wrapper {{
                max-width: 100% !important;
                zoom: 1 !important;
            }}
            .label {{
                width: {label_width}mm !important;
                height: {label_height}mm !important;
                padding: {int(1.5*px_per_mm)}mm !important;
            }}
        }}
    </style>
    <div class="label" style="
        width: {label_w}px;
        height: {label_h}px;
        border: 1px solid #000;
        padding: 0;
        box-sizing: border-box;
        font-family: Arial, sans-serif;
        background: #fff;
        display: flex;
        flex-direction: row;
        overflow: hidden;
    ">
        <!-- ЛЕВАЯ ПОЛОВИНКА: логотип, название фирмы, информация -->
        <div style="width: 50%; height: 100%; padding: {pad}px; display: flex; flex-direction: column; border-right: 2px solid #000; overflow: hidden;">
            <!-- Логотип сверху -->
            {logo_img_html}
            <!-- Название фирмы -->
            <div style="text-align: center; margin: 0 0 {pad}px 0;">
                <div style="font-size: {font_company}px; font-weight: bold; line-height: 1.2;">
                    {company_name}
                </div>
            </div>
            <!-- Остальные элементы -->
            <div style="flex: 1; display: flex; flex-direction: column; justify-content: flex-start; min-height: 0; overflow: hidden;">
                <div style="font-size: {font_name}px; font-weight: bold; line-height: 1.15; margin: 0 0 {pad}px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {safe_str(asset.name)}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: flex-end; font-size: {font_small}px; margin: 0;">
                    <div style="color: #333; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Отв: {formatted}</div>
                    <div style="text-align: right; white-space: nowrap;">
                        <div>Пост.:</div>
                        <div style="font-weight: bold;">{purchase_date}</div>
                    </div>
                </div>
            </div>
            <!-- Инв. номер внизу левой части -->
            <div style="font-size: {font_qr_text}px; margin-top: auto; padding-top: {pad}px; border-top: 1px solid #ccc;">
                <div>Инв. №:</div>
                <div style="font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{safe_str(asset.inventory_number)}</div>
            </div>
            <!-- Сокращение компании -->
            <div style="font-size: {font_footer}px; color: #666; text-align: right; margin: 1px 0 0 0;">
                {company_short}
            </div>
        </div>
        <!-- ПРАВАЯ ПОЛОВИНКА: QR-код -->
        <div style="width: 50%; height: 100%; padding: {pad}px; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden;">
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; width: 100%;">
                <div style="display: flex; align-items: center; justify-content: center; width: 100%;">
                    <div style="flex-shrink: 0; width: {int(qr_size_mm*px_per_mm)}px; height: {int(qr_size_mm*px_per_mm)}px;">
                        {qr_img_html}
                    </div>
                </div>
            </div>
        </div>
    </div>
    </div>"""
    
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
        
        # Генерируем QR-код — компактный размер для бирки
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        qr_url = f"{frontend_url}/inventory/asset/{asset.id}"
        
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        # Увеличиваем разрешение для качественной печати
        img = img.resize((250, 250), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        qr_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        qr_html = f'''<div style="flex-shrink: 0; width: {int(label_height * 0.65)}mm; height: {int(label_height * 0.65)}mm; display: flex; align-items: center; justify-content: center;">
            <img src="data:image/png;base64,{qr_base64}" style="width: {int(label_height * 0.65)}mm; height: {int(label_height * 0.65)}mm; object-fit: contain;" />
        </div>'''
        
        label = f"""
        <div class="label" style="
            width: {label_width}mm; height: {label_height}mm; border: 1px solid #000; padding: 0;
            box-sizing: border-box; font-family: Arial, sans-serif;
            page-break-inside: avoid; display: inline-block;
            vertical-align: top; margin: 0;
            display: flex;
            flex-direction: row;
        ">
            <!-- ЛЕВАЯ ПОЛОВИНКА: лого+фирма+информация -->
            <div style="width: 50%; height: 100%; padding: 1.5mm; display: flex; flex-direction: column; border-right: 1px solid #000;">
                <!-- Логотип сверху -->
                {logo_html}
                <!-- Название фирмы -->
                <div style="text-align: center; margin: 0 0 0.5mm 0;">
                    <div style="font-size: 7.5pt; font-weight: bold; line-height: 1.2;">
                        {company_name}
                    </div>
                </div>
                <!-- Остальные элементы -->
                <div style="flex: 1; display: flex; flex-direction: column; justify-content: flex-start; min-height: 0; overflow: hidden;">
                    <div style="font-size: 9pt; font-weight: bold; margin: 0 0 0.5mm 0; line-height: 1.15; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {safe_str(asset.name)}
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-end; font-size: 5.5pt; margin: 0;">
                        <div style="color: #333; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Отв: {formatted}</div>
                        <div style="text-align: right; white-space: nowrap;">
                            <div>Пост.:</div>
                            <div style="font-weight: bold; font-size: 7pt;">{purchase_date}</div>
                        </div>
                    </div>
                </div>
                <!-- Инв. номер внизу -->
                <div style="font-size: 4.5pt; margin-top: auto; padding-top: 0.5mm; border-top: 0.5px solid #ccc;">
                    <div>Инв. №:</div>
                    <div style="font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{safe_str(asset.inventory_number)}</div>
                </div>
                <div style="font-size: 4.5pt; color: #666; text-align: right; margin: 0.3mm 0 0 0;">
                    {company_short}
                </div>
            </div>
            <!-- ПРАВАЯ ПОЛОВИНКА: QR-код -->
            <div style="width: 50%; height: 100%; padding: 1.5mm; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; width: 100%;">
                    {qr_html}
                </div>
            </div>
        </div>
        """
        labels_html.append(label)
    
    full_html = f"""
    <html>
    <head>
        <title>Бирки для печати</title>
        <style>
            @page {{ size: A4; margin: 5mm; }}
            body {{ margin: 0; padding: 0; }}
            .page-break {{ page-break-after: always; }}
            @media print {{
                body {{ margin: 0; padding: 0; }}
                .label {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        {''.join(labels_html)}
    </body>
    </html>
    """
    
    return {"html": full_html, "count": len(assets)}
