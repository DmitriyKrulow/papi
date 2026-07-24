from fastapi import APIRouter

from ..schemas.repairs import RepairCreate, RepairResponse, RepairUpdate

router = APIRouter(prefix="/repairs", tags=["repairs"])


@router.get("/", response_model=list[RepairResponse])
def list_repairs():
    pass


@router.get("/{repair_id}", response_model=RepairResponse)
def get_repair(repair_id: int):
    pass


@router.post("/", response_model=RepairResponse)
def create_repair(repair: RepairCreate):
    pass


@router.put("/{repair_id}", response_model=RepairResponse)
def update_repair(repair_id: int, repair: RepairUpdate):
    pass


@router.delete("/{repair_id}")
def delete_repair(repair_id: int):
    pass
