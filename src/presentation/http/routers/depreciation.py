from typing import List

from fastapi import APIRouter, HTTPException, Depends
from src.presentation.schemas.depreciation import DepreciationCreate, DepreciationResponse
from src.infrastructure.db.unit_of_work import UnitOfWork

router = APIRouter(prefix="/depreciation", tags=["Depreciation"])


@router.get("/", response_model=List[DepreciationResponse])
def list_depreciation(uow: UnitOfWork = Depends()):
    depreciation = uow.depreciation_repository.list_all()
    return depreciation


@router.get("/{depreciation_id}", response_model=DepreciationResponse)
def get_depreciation(depreciation_id: int, uow: UnitOfWork = Depends()):
    depreciation = uow.depreciation_repository.get_by_id(depreciation_id)
    if not depreciation:
        raise HTTPException(status_code=404, detail="Depreciation not found")
    return depreciation


@router.get("/asset/{asset_id}", response_model=List[DepreciationResponse])
def get_depreciation_by_asset(asset_id: int, uow: UnitOfWork = Depends()):
    depreciation = uow.depreciation_repository.list_by_asset(asset_id)
    return depreciation


@router.post("/", response_model=DepreciationResponse, status_code=201)
def create_depreciation(depreciation: DepreciationCreate, uow: UnitOfWork = Depends()):
    try:
        uow.depreciation_repository.save(depreciation)
        uow.commit()
        return uow.depreciation_repository.get_by_id(depreciation.id)
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{depreciation_id}", status_code=204)
def delete_depreciation(depreciation_id: int, uow: UnitOfWork = Depends()):
    existing_depreciation = uow.depreciation_repository.get_by_id(depreciation_id)
    if not existing_depreciation:
        raise HTTPException(status_code=404, detail="Depreciation not found")
    try:
        uow.depreciation_repository.delete(depreciation_id)
        uow.commit()
    except Exception as e:
        uow.rollback()
        raise HTTPException(status_code=400, detail=str(e))
