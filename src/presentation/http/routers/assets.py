from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.presentation.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetListResponse,
)
from src.infrastructure.db.unit_of_work import UnitOfWork
from src.infrastructure.auth.dependencies import get_current_user, get_current_admin_user
from src.core.domain.roles import UserRole

router = APIRouter(prefix="/api/assets", tags=["Assets"])


@router.get("/", response_model=AssetListResponse)
def list_assets(
    current_user: UserResponse = Depends(get_current_user),
    uow: UnitOfWork = Depends(),
):
    if current_user.role == UserRole.ADMIN:
        assets = uow.asset_repository.list_all()
    else:
        from src.infrastructure.db.models import AssetStatus
        assets = uow.asset_repository.list_by_status(AssetStatus.ACTIVE)
    return {"total": len(assets), "items": assets}


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    current_user: UserResponse = Depends(get_current_user),
    uow: UnitOfWork = Depends(),
):
    asset = uow.asset_repository.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if current_user.role != UserRole.ADMIN and asset.status == "written_off":
        raise HTTPException(status_code=403, detail="Asset not accessible")
    return asset


@router.post("/", response_model=AssetResponse, status_code=201)
def create_asset(asset: AssetCreate, uow: UnitOfWork = Depends()):
    try:
        uow.asset_repository.save(asset)
        uow.commit()
        return uow.asset_repository.get_by_inventory_number(asset.inventory_number)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: int, asset: AssetUpdate, uow: UnitOfWork = Depends()):
    existing_asset = uow.asset_repository.get_by_id(asset_id)
    if not existing_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        uow.asset_repository.save(asset)
        uow.commit()
        return uow.asset_repository.get_by_id(asset_id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{asset_id}", status_code=204)
def delete_asset(asset_id: int, uow: UnitOfWork = Depends()):
    existing_asset = uow.asset_repository.get_by_id(asset_id)
    if not existing_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        uow.asset_repository.delete(asset_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))
