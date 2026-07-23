# src/presentation/http/routers/assets.py
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from decimal import Decimal

from backend.src.presentation.http.schemas.assets import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
)

router = APIRouter()

assets_db: dict = {}
asset_id_counter = 1


@router.get("/", response_model=List[AssetResponse], status_code=status.HTTP_200_OK)
async def get_all_assets():
    return [asset for asset in assets_db.values() if asset.is_active]


@router.get("/{asset_id}", response_model=AssetResponse, status_code=status.HTTP_200_OK)
async def get_asset(asset_id: int):
    if asset_id not in assets_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return assets_db[asset_id]


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(asset: AssetCreate):
    global asset_id_counter
    
    try:
        asset_data = asset.model_dump()
        new_asset = AssetResponse(
            id=asset_id_counter,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **asset_data
        )
        assets_db[asset_id_counter] = new_asset
        asset_id_counter += 1
        return new_asset
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{asset_id}", response_model=AssetResponse, status_code=status.HTTP_200_OK)
async def update_asset(asset_id: int, asset: AssetUpdate):
    if asset_id not in assets_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    
    try:
        existing_asset = assets_db[asset_id]
        update_data = asset.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(existing_asset, field, value)
        
        existing_asset.updated_at = datetime.now()
        return existing_asset
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{asset_id}/hide", response_model=AssetResponse, status_code=status.HTTP_200_OK)
async def hide_asset(asset_id: int):
    if asset_id not in assets_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    
    assets_db[asset_id].is_active = False
    assets_db[asset_id].updated_at = datetime.now()
    return assets_db[asset_id]
