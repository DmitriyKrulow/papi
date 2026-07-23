from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class EmployeeCreate(BaseModel):
    department_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    position_code: Optional[str] = Field(None, max_length=50)
    employee_number: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    department_id: Optional[int] = Field(None, gt=0)
    user_id: Optional[int] = Field(None, gt=0)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    position_code: Optional[str] = Field(None, max_length=50)
    employee_number: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    id: int
    department_id: int
    user_id: int
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    position_code: Optional[str] = None
    employee_number: Optional[str] = None
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
