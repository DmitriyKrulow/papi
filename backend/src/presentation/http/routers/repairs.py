# src/presentation/http/routers/repairs.py
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from decimal import Decimal

from backend.src.presentation.http.schemas.repairs import (
    RepairCreate,
    RepairResponse,
    RepairUpdate,
)

router = APIRouter()

repairs_db: dict = {}
repair_id_counter = 1


@router.get("/", response_model=List[RepairResponse], status_code=status.HTTP_200_OK)
async def get_all_repairs():
    return list(repairs_db.values())


@router.get("/{repair_id}", response_model=RepairResponse, status_code=status.HTTP_200_OK)
async def get_repair(repair_id: int):
    if repair_id not in repairs_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    return repairs_db[repair_id]


@router.post("/", response_model=RepairResponse, status_code=status.HTTP_201_CREATED)
async def create_repair(repair: RepairCreate):
    global repair_id_counter
    
    try:
        repair_data = repair.model_dump()
        new_repair = RepairResponse(
            id=repair_id_counter,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            **repair_data
        )
        repairs_db[repair_id_counter] = new_repair
        repair_id_counter += 1
        return new_repair
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{repair_id}", response_model=RepairResponse, status_code=status.HTTP_200_OK)
async def update_repair(repair_id: int, repair: RepairUpdate):
    if repair_id not in repairs_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    
    try:
        existing_repair = repairs_db[repair_id]
        update_data = repair.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(existing_repair, field, value)
        
        existing_repair.updated_at = datetime.now()
        return existing_repair
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{repair_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repair(repair_id: int):
    if repair_id not in repairs_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair not found")
    
    del repairs_db[repair_id]
    return None
