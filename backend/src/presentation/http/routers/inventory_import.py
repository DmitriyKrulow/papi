import os
from datetime import datetime
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.asset import Asset
from src.infrastructure.db.models.user import User
from src.presentation.http.dependencies.auth import get_current_user

router = APIRouter(prefix="/inventory-import", tags=["inventory-import"])

UPLOAD_DIR = "uploads/inventory"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_inventory_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Загружает и обрабатывает файл инвентаризационной описи для импорта активов.
    """
    logger.info(f"[Inventory Import] Upload started for user: {current_user.username}")
    logger.info(f"[Inventory Import] Filename: {file.filename}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Only Excel files are supported")
    
    try:
        content = await file.read()
        logger.info(f"[Inventory Import] File size: {len(content)} bytes")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"inventory_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"[Inventory Import] File saved to: {file_path}")
        
        # Обработка Excel файла
        try:
            df = pd.read_excel(file_path)
            logger.info(f"[Inventory Import] Excel file loaded. Rows: {len(df)}, Columns: {len(df.columns)}")
            logger.info(f"[Inventory Import] Column names: {list(df.columns)}")
            logger.info(f"[Inventory Import] First 3 rows, first 5 columns:")
            for i in range(min(3, len(df))):
                row_data = df.iloc[i].dropna()
                logger.info(f"[Inventory Import] Row {i}: {row_data.tolist()[:5]}")
            
            # Удаляем пустые строки
            df = df.dropna(how='all')
            logger.info(f"[Inventory Import] After removing empty rows: {len(df)} rows")
            
            # Сбрасываем индекс для удобства
            df = df.reset_index(drop=True)
            
            processed_count = 0
            error_count = 0
            processed_inventory_numbers = set()
            
            # Структура файла — Excel со слиянными ячейками (pandas читает иначе):
            # Данные начинаются со строки 40 (индекс pandas, строка 41 в Excel)
            # Колонка 0: № п/п
            # Колонка 3: Наименование объекта нефинансового актива
            # Колонка 10: Номер (код) объекта учета (инвентарный номер)
            # Колонка 18: Единица измерения
            # Колонка 26: Количество
            # Колонка 50: Балансовая стоимость, руб.
            
            # Индексы колонок (после слиянных ячеек)
            row_num_col = df.columns[0] if len(df.columns) > 0 else None
            name_col = df.columns[3] if len(df.columns) > 3 else None
            inventory_col = df.columns[10] if len(df.columns) > 10 else None
            location_col = df.columns[18] if len(df.columns) > 18 else None  # Единица измерения
            cost_col = df.columns[50] if len(df.columns) > 50 else None      # Балансовая стоимость
            
            logger.info(f"[Inventory Import] Using column indices: row_num={row_num_col}, name={name_col}, inventory={inventory_col}, location={location_col}, cost={cost_col}")
            
            # Показываем примеры значений из ключевых колонок
            for col_idx, col_name in [(0, row_num_col), (3, name_col), (10, inventory_col), (50, cost_col)]:
                if col_name:
                    samples = []
                    for i in range(40, min(44, len(df))):
                        val = df.iloc[i].get(col_name)
                        if pd.notna(val):
                            samples.append(str(val).strip()[:50])
                    logger.info(f"[Inventory Import] Column '{col_name}' (idx {col_idx}) samples: {samples}")
            
            # Данные начинаются со строки 40 (пропускаем шапку и заголовок таблицы)
            data_start_row = 40
            logger.info(f"[Inventory Import] Data starts at row {data_start_row}")
            
            if data_start_row is None:
                logger.warning("[Inventory Import] Could not find data start row")
                return {
                    "message": "File processed but no data found",
                    "filename": file.filename,
                    "file_path": file_path,
                    "file_size": len(content),
                    "total_rows": len(df),
                    "processed_rows": 0,
                    "error_rows": 0,
                    "uploaded_at": datetime.now().isoformat(),
                }
            
            for idx in range(data_start_row, len(df)):
                try:
                    row = df.iloc[idx]
                    row_num = str(row.get(row_num_col, '')).strip() if row_num_col and pd.notna(row.get(row_num_col, '')) else ''
                    name = str(row.get(name_col, '')).strip() if name_col and pd.notna(row.get(name_col, '')) else ''
                    inventory_number = str(row.get(inventory_col, '')).strip() if inventory_col and pd.notna(row.get(inventory_col, '')) else ''
                    location = str(row.get(location_col, '')).strip() if location_col and pd.notna(row.get(location_col, '')) else ''
                    cost = str(row.get(cost_col, '')).strip() if cost_col and pd.notna(row.get(cost_col, '')) else ''
                    
                    # Обрезаем кириллическую "Р" в начале инвентарного номера
                    if inventory_number and inventory_number.startswith('Р'):
                        inventory_number = inventory_number[1:].strip()
                    
                    # Для модели используем сочетание названия и местоположения
                    model = None
                    if location and location.lower() != 'nan':
                        model = location
                    
                    # Пропускаем строки без номера инвентаря или с пустым названием
                    if not inventory_number or not name or inventory_number.lower() in ['код строки', 'всего']:
                        if inventory_number and inventory_number.lower() == 'всего':
                            logger.info(f"[Inventory Import] Skipping summary row: {inventory_number}")
                        continue
                    
                    # Пропускаем строки-заголовки (где name = "N/п", "Наименование" и т.д.)
                    skip_keywords = ['n/п', 'n п', '№', 'наименование', 'код', 'единица', 'количество', 'балансовая', 'остаточная', 'инвентарный']
                    if any(kw in name.lower() for kw in skip_keywords):
                        logger.debug(f"[Inventory Import] Skipping header-like row: name='{name}'")
                        continue
                    
                    # Пропускаем строки, где name — это просто число (признак смещения колонок)
                    try:
                        float(name)
                        logger.debug(f"[Inventory Import] Skipping row with numeric name: '{name}' — likely column offset issue")
                        continue
                    except ValueError:
                        pass
                    
                    # Логируем первую строку для отладки
                    if processed_count == 0 and error_count == 0:
                        logger.info(f"[Inventory Import] Sample data: row_num={row_num}, name={name[:50]}, inventory={inventory_number[:30] if len(inventory_number) > 0 else ''}, location={location[:50] if location else ''}, cost={cost}")
                    
                    # Если после всех проверок name и inventory — это просто числа, вероятно колонки смещены
                    # Пытаемся найти реальные данные — проверяем, есть ли осмысленные значения
                    name_is_numeric = False
                    try:
                        float(name)
                        name_is_numeric = True
                    except ValueError:
                        pass
                    
                    inv_is_short_number = False
                    if inventory_number and inventory_number.isdigit() and len(inventory_number) <= 4:
                        inv_is_short_number = True
                    
                    if name_is_numeric and inv_is_short_number:
                        logger.debug(f"[Inventory Import] Skipping row — likely column offset: name='{name}', inventory='{inventory_number}'")
                        continue
                    
                    # Парсим стоимость (формат: 256,18 -> 256.18)
                    purchase_price = None
                    if cost and cost.lower() != 'nan' and cost.strip():
                        try:
                            cost_clean = cost.replace(' ', '').replace(',', '.')
                            if cost_clean.replace('.', '').replace('-', '').strip():
                                purchase_price = float(cost_clean)
                                logger.info(f"[Inventory Import] Parsed cost '{cost}' -> {purchase_price}")
                            else:
                                logger.debug(f"[Inventory Import] Cost is empty after cleaning for row {row_num}, inventory: {inventory_number}")
                        except ValueError:
                            logger.warning(f"[Inventory Import] Could not parse cost: '{cost}' from row {row_num}, inventory: {inventory_number}")
                    else:
                        logger.debug(f"[Inventory Import] Cost is empty or nan for row {row_num}, inventory: {inventory_number}, cost value: '{cost}'")
                    
                    # Проверяем, что порядковый номер - это число (1, 2, 3...)
                    try:
                        int(row_num)
                    except ValueError:
                        logger.debug(f"[Inventory Import] Skipping non-numeric row number: {row_num}")
                        continue
                    
                    # Проверяем дубликаты в текущей сессии
                    if inventory_number in processed_inventory_numbers:
                        logger.debug(f"[Inventory Import] Skipping duplicate inventory number: {inventory_number}")
                        continue
                    
                    processed_inventory_numbers.add(inventory_number)
                    
                    existing_asset = db.query(Asset).filter(Asset.inventory_number == inventory_number).first()
                    
                    if existing_asset:
                        logger.info(f"[Inventory Import] Asset {inventory_number} already exists, updating")
                        existing_asset.name = name
                        existing_asset.model = model or existing_asset.model
                        existing_asset.purchase_price = purchase_price if purchase_price is not None else existing_asset.purchase_price
                        existing_asset.current_value = purchase_price if purchase_price is not None else existing_asset.current_value
                        existing_asset.updated_at = datetime.now()
                        processed_count += 1
                    else:
                        new_asset = Asset(
                            inventory_number=inventory_number,
                            name=name,
                            model=model or None,
                            purchase_price=purchase_price,
                            current_value=purchase_price,
                            status='active',
                            is_active=True,
                        )
                        db.add(new_asset)
                        processed_count += 1
                        logger.info(f"[Inventory Import] Added asset {inventory_number} (row {row_num}): {name[:50]}...")
                    
                except Exception as row_error:
                    error_count += 1
                    logger.error(f"[Inventory Import] Error processing row {idx}: {str(row_error)}", exc_info=True)
            
            # Коммитим все изменения
            if processed_count > 0:
                db.flush()  # Проверка на SQL-ошибки (уникальность, not null и т.д.)
                db.commit()
                logger.info(f"[Inventory Import] Import completed. Added: {processed_count}, Errors: {error_count}")
            else:
                logger.warning("[Inventory Import] No assets were processed — nothing to commit")
            
            return {
                "message": "File uploaded and processed successfully" if processed_count > 0 else "File processed but no assets found",
                "filename": file.filename,
                "file_path": file_path,
                "file_size": len(content),
                "total_rows": len(df),
                "processed_rows": processed_count,
                "error_rows": error_count,
                "uploaded_at": datetime.now().isoformat(),
            }
            
        except Exception as parse_error:
            logger.error(f"[Inventory Import] Error parsing Excel file: {str(parse_error)}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Error parsing Excel file: {str(parse_error)}")
            
    except Exception as e:
        logger.error(f"[Inventory Import] Error saving file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@router.post("/reset")
async def reset_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Удаляет все активы из базы данных.
    """
    logger.info(f"[Inventory Import] Reset started by user: {current_user.username}")
    
    try:
        deleted_count = db.query(Asset).count()
        db.query(Asset).delete()
        db.commit()
        
        logger.info(f"[Inventory Import] Reset completed. Deleted {deleted_count} assets")
        
        return {
            "message": "All assets have been deleted",
            "deleted_count": deleted_count,
            "reset_at": datetime.now().isoformat(),
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"[Inventory Import] Error resetting assets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error resetting assets: {str(e)}")
