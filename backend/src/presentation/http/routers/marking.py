# backend/src/presentation/http/routers/marking.py
"""Маркировка имущества — генерация бирок для печати"""
import os
import uuid
import base64
import io
import qrcode
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user
from src.shared.utils import get_frontend_url

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


# ---------------------------------------------------------------------------
# Общие помощники для генерации бирок
# ---------------------------------------------------------------------------


def _make_qr_data_url(qr_url: str) -> str:
    """Генерирует QR-код (base64 PNG) по ссылке на актив."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"


def _render_label_html(
    *,
    name: str,
    inventory_number: str,
    responsible: str,
    purchase_date: str,
    company_name: str,
    company_short: str,
    logo_url: Optional[str],
    qr_data_url: str,
    label_width: float,
    label_height: float,
) -> str:
    """Собирает HTML одной бирки.

    Все размеры — в миллиметрах, поэтому экранное отображение и печать
    совпадают (WYSIWYG). Стили только inline, цвет текста задан явно,
    поэтому snippet можно безопасно вставлять куда угодно.
    """
    w = float(label_width)
    h = float(label_height)

    border = 0.25
    pad = round(max(0.8, min(2.0, h * 0.05)), 2)
    inner_h = h - 2 * pad - 2 * border

    # QR — квадрат, по высоте левой части, но не шире 42 % бирки
    qr_side = round(max(6.0, min(inner_h, w * 0.42)), 2)
    right_w = round(qr_side + 2 * pad, 2)

    # Масштаб шрифтов под размер бирки
    scale = max(0.5, min(h / 37.0, w / 105.0))
    f_company = round(7.2 * scale, 1)
    f_name = round(8.5 * scale, 1)
    f_small = round(5.4 * scale, 1)
    f_micro = round(4.6 * scale, 1)
    f_inv = round(6.2 * scale, 1)

    # Вспомогательные отступы
    m_logo = round(pad * 0.5, 2)
    m_company = round(pad * 0.4, 2)
    m_name = round(pad * 0.3, 2)
    m_inv_top = round(pad * 0.4, 2)
    m_inv_pad = round(pad * 0.35, 2)
    m_short = round(pad * 0.3, 2)
    logo_max_h = round(inner_h * 0.22, 2)

    # Логотип
    logo_html = ""
    if logo_url:
        logo_html = (
            f'<div style="text-align:center;overflow:hidden;margin:0 0 {m_logo}mm 0;">'
            f'<img src="{logo_url}" style="max-height:{logo_max_h}mm;max-width:96%;'
            'object-fit:contain;display:inline-block;" />'
            '</div>'
        )

    return f"""<div class="papi-label" style="width:{w}mm;height:{h}mm;box-sizing:border-box;background:#fff;color:#000;font-family:Arial,Helvetica,sans-serif;border:{border}mm solid #000;padding:{pad}mm;display:flex;flex-direction:row;overflow:hidden;page-break-inside:avoid;-webkit-print-color-adjust:exact;print-color-adjust:exact;"><div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;border-right:{border}mm solid #000;padding-right:{pad}mm;overflow:hidden;">{logo_html}<div style="text-align:center;font-weight:bold;font-size:{f_company}pt;line-height:1.15;margin:0 0 {m_company}mm 0;word-break:break-word;">{company_name}</div><div style="font-weight:bold;font-size:{f_name}pt;line-height:1.12;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin:0 0 {m_name}mm 0;">{name}</div><div style="flex:1 1 auto;min-height:0;"></div><div style="display:flex;justify-content:space-between;align-items:flex-end;gap:1mm;font-size:{f_small}pt;line-height:1.15;"><div style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">Отв: {responsible}</div><div style="text-align:right;flex:0 0 auto;">Пост.:<b>{purchase_date}</b></div></div><div style="margin-top:{m_inv_top}mm;padding-top:{m_inv_pad}mm;border-top:0.2mm solid #999;font-size:{f_micro}pt;line-height:1.15;">Инв. №<span style="font-weight:bold;font-size:{f_inv}pt;word-break:break-all;">{inventory_number}</span></div><div style="font-size:{f_micro}pt;color:#555;text-align:right;margin-top:{m_short}mm;">{company_short}</div></div><div style="flex:0 0 {right_w}mm;display:flex;align-items:center;justify-content:center;padding-left:{pad}mm;"><div style="width:{qr_side}mm;height:{qr_side}mm;flex:0 0 auto;display:flex;align-items:center;justify-content:center;"><img src="{qr_data_url}" style="width:{qr_side}mm;height:{qr_side}mm;display:block;" /></div></div></div>"""


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------


@router.get("/label-html/{asset_id}")
async def get_label_html(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить HTML-шаблон одной бирки для актива"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Актив не найден")

    company_name = _marking_settings.get("company_name", "ООО «ПАО»")
    company_short = _marking_settings.get("company_short", "ПАО")
    label_width = float(_marking_settings.get("label_width", 105))
    label_height = float(_marking_settings.get("label_height", 37))
    logo_url = _marking_settings.get("logo_url")

    responsible = format_responsible(safe_str(asset.responsible_person))
    purchase_date = safe_date(asset.purchase_date) or "—"

    frontend_url = get_frontend_url(db) or "http://localhost:5173"
    qr_url = f"{frontend_url}/inventory/asset/{asset.id}"
    qr_data_url = _make_qr_data_url(qr_url)

    label_html = _render_label_html(
        name=safe_str(asset.name),
        inventory_number=safe_str(asset.inventory_number),
        responsible=responsible,
        purchase_date=purchase_date,
        company_name=company_name,
        company_short=company_short,
        logo_url=logo_url,
        qr_data_url=qr_data_url,
        label_width=label_width,
        label_height=label_height,
    )

    return {
        "html": label_html,
        "label_width": label_width,
        "label_height": label_height,
        "inventory_number": safe_str(asset.inventory_number),
        "qr_url": qr_url,
    }


@router.get("/label-batch")
async def get_batch_labels(
    asset_ids: str = Query(..., description="CSV ID активов"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить список HTML-бирок для пакетной печати"""
    ids = [int(x.strip()) for x in asset_ids.split(",") if x.strip()]
    assets = db.query(Asset).filter(Asset.id.in_(ids)).all()

    if not assets:
        raise HTTPException(status_code=404, detail="Активы не найдены")

    company_name = _marking_settings.get("company_name", "ООО «ПАО»")
    company_short = _marking_settings.get("company_short", "ПАО")
    label_width = float(_marking_settings.get("label_width", 105))
    label_height = float(_marking_settings.get("label_height", 37))
    logo_url = _marking_settings.get("logo_url")
    per_row = int(_marking_settings.get("labels_per_row", 3))
    per_page = int(_marking_settings.get("labels_per_page", 21))

    labels_html: list[str] = []
    for asset in assets:
        responsible = format_responsible(safe_str(asset.responsible_person))
        purchase_date = safe_date(asset.purchase_date) or "—"

        frontend_url = get_frontend_url(db) or "http://localhost:5173"
        qr_url = f"{frontend_url}/inventory/asset/{asset.id}"
        qr_data_url = _make_qr_data_url(qr_url)

        label_html = _render_label_html(
            name=safe_str(asset.name),
            inventory_number=safe_str(asset.inventory_number),
            responsible=responsible,
            purchase_date=purchase_date,
            company_name=company_name,
            company_short=company_short,
            logo_url=logo_url,
            qr_data_url=qr_data_url,
            label_width=label_width,
            label_height=label_height,
        )
        labels_html.append(label_html)

    # Вычисляем реальную раскладку (чтобы превью совпадало с печатью)
    page_w, page_h = 200.0, 287.0  # A4 − поля 5 мм
    max_per_row = max(1, int(page_w // label_width))
    eff_per_row = max(1, min(per_row, max_per_row))
    rows = max(1, int(page_h // label_height))
    max_per_page = eff_per_row * rows
    eff_per_page = max(1, min(per_page, max_per_page))

    return {
        "labels": labels_html,
        "count": len(labels_html),
        "label_width": label_width,
        "label_height": label_height,
        "labels_per_row": eff_per_row,
        "labels_per_page": eff_per_page,
    }



