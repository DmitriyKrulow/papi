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
            
            # Структура файла (после строки заголовков):
            # - Колонка 0: "Код строки" (порядковый номер 1, 2, 3...)
            # - Колонка 3: "Наименование имущества" (название)
            # - Колонка 21: "Номер (код) объекта учета (инвентарный или иной)" (инвентарный номер)
            # - Колонка 31: "Фактическое местоположение"
            # - Колонка 77: "Балансовая стоимость"
            # - и т.д.
            
            # Индексы колонок
            row_num_col = df.columns[0] if len(df.columns) > 0 else None
            name_col = df.columns[3] if len(df.columns) > 3 else None
            inventory_col = df.columns[21] if len(df.columns) > 21 else None
            location_col = df.columns[31] if len(df.columns) > 31 else None
            cost_col = df.columns[77] if len(df.columns) > 77 else None
            
            logger.info(f"[Inventory Import] Using column indices: row_num={row_num_col}, name={name_col}, inventory={inventory_col}, location={location_col}, cost={cost_col}")
            if cost_col:
                sample_costs = []
                for i in range(min(5, len(df))):
                    val = df.iloc[i].get(cost_col) if pd.notna(df.iloc[i].get(cost_col)) else 'N/A'
                    sample_costs.append(str(val)[:50])
                logger.info(f"[Inventory Import] Sample values from cost column: {sample_costs}")
            
            # Ищем начало данных (строки с числовыми значениями в первом столбце)
            data_start_row = None
            for idx, row in df.iterrows():
                val = row.get(inventory_col) if inventory_col else None
                if pd.notna(val):
                    try:
                        num = float(str(val).strip())
                        if num >= 1 and num <= 100:
                            data_start_row = idx
                            logger.info(f"[Inventory Import] Data starts at row {data_start_row}")
                            break
                    except (ValueError, TypeError):
                        continue
            
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
                    
                    # Логируем первую строку для отладки
                    if processed_count == 0 and error_count == 0:
                        logger.info(f"[Inventory Import] Sample data: row_num={row_num}, name={name[:50]}, inventory={inventory_number[:30] if len(inventory_number) > 0 else ''}, location={location[:50] if location else ''}, cost={cost}")
                    
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
                        )
                        db.add(new_asset)
                        processed_count += 1
                        logger.info(f"[Inventory Import] Added asset {inventory_number} (row {row_num}): {name[:50]}...")
                    
                except Exception as row_error:
                    error_count += 1
                    logger.error(f"[Inventory Import] Error processing row {idx}: {str(row_error)}", exc_info=True)
            
            db.commit()
            logger.info(f"[Inventory Import] Import completed. Added: {processed_count}, Errors: {error_count}")
            
            return {
                "message": "File uploaded and processed successfully",
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
