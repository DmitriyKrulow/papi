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
from src.core.services.inventory_parser import create_inventory_parser

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
        
        # Используем универсальный парсер
        try:
            parser = create_inventory_parser(file_path)
            assets = parser.parse()
            
            logger.info(f"[Inventory Import] Parser found {len(assets)} assets")
            
            if not assets:
                return {
                    "message": "File processed but no assets found",
                    "filename": file.filename,
                    "file_path": file_path,
                    "file_size": len(content),
                    "total_rows": len(parser.df) if parser.df is not None else 0,
                    "processed_rows": 0,
                    "error_rows": 0,
                    "uploaded_at": datetime.now().isoformat(),
                }
            
            # Сохраняем активы в БД
            processed_count = 0
            error_count = 0
            duplicate_count = 0
            
            # Глобальный набор инвентарных номеров для дедупликации
            # (учитываем уже существующие в БД)
            existing_inv_numbers = set()
            for asset in db.query(Asset).filter(Asset.inventory_number.isnot(None)).all():
                existing_inv_numbers.add(asset.inventory_number)
            
            for asset_data in assets:
                try:
                    inventory_number = asset_data['inventory_number']
                    name = asset_data['name']
                    model = asset_data.get('model')
                    purchase_price = asset_data.get('purchase_price')
                    quantity = asset_data.get('quantity')
                    
                    # Пропускаем дубликаты (уже есть в БД или в этом файле)
                    if inventory_number in existing_inv_numbers:
                        # Обновляем существующий актив
                        existing_asset = db.query(Asset).filter(
                            Asset.inventory_number == inventory_number
                        ).first()
                        if existing_asset:
                            logger.info(f"[Inventory Import] Updating existing asset {inventory_number}: {name[:50]}")
                            existing_asset.name = name
                            if model:
                                existing_asset.model = model
                            existing_asset.purchase_price = purchase_price if purchase_price is not None else existing_asset.purchase_price
                            existing_asset.current_value = purchase_price if purchase_price is not None else existing_asset.current_value
                            if quantity:
                                existing_asset.quantity = quantity
                            existing_asset.updated_at = datetime.now()
                            duplicate_count += 1
                        continue
                    
                    # Создаём новый актив
                    new_asset = Asset(
                        inventory_number=inventory_number,
                        name=name,
                        model=model or None,
                        purchase_price=purchase_price,
                        current_value=purchase_price,
                        status='active',
                        is_active=True,
                    )
                    if quantity:
                        new_asset.quantity = quantity
                    db.add(new_asset)
                    existing_inv_numbers.add(inventory_number)
                    logger.info(f"[Inventory Import] Added asset {inventory_number}: {name[:50]}...")
                    
                    processed_count += 1
                    
                except Exception as row_error:
                    error_count += 1
                    logger.error(f"[Inventory Import] Error processing asset '{asset_data.get('inventory_number', '?')}': {str(row_error)}", exc_info=True)
            
            # Коммитим все изменения
            if processed_count > 0:
                db.flush()
                db.commit()
                logger.info(f"[Inventory Import] Import completed. Added: {processed_count}, Duplicates: {duplicate_count}, Errors: {error_count}")
                
                # Логирование импорта в аудит
                try:
                    from src.core.services.audit_service import AuditService
                    audit_service = AuditService(db)
                    audit_service.log_import(
                        "Asset",
                        count=processed_count,
                        user_id=current_user.id,
                        comment=f"Импорт из файла: {file.filename}",
                    )
                except Exception:
                    pass
            else:
                logger.warning("[Inventory Import] No assets were processed — nothing to commit")
            
            return {
                "message": "File uploaded and processed successfully" if processed_count > 0 else "File processed but no assets found",
                "filename": file.filename,
                "file_path": file_path,
                "file_size": len(content),
                "total_rows": len(parser.df) if parser.df is not None else 0,
                "processed_rows": processed_count,
                "duplicate_rows": duplicate_count,
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
        
        # Логирование сброса в аудит
        try:
            from src.core.services.audit_service import AuditService
            audit_service = AuditService(db)
            audit_service.log_import(
                "Asset",
                count=-deleted_count,  # отрицательное — означает удаление
                user_id=current_user.id,
                comment=f"Полный сброс активов: {deleted_count} удалено",
            )
        except Exception:
            pass
        
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
