from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import Employee as EmployeeModel
from src.core.entities.employee import Employee
from src.core.value_objects import Phone, Email


class EmployeeRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, employee: Employee) -> None:
        model = self._to_model(employee)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[Employee]:
        model = self.session.get(EmployeeModel, id)
        if model:
            return self._to_entity(model)
        return None

    def get_by_user_id(self, user_id: int) -> Optional[Employee]:
        statement = select(EmployeeModel).where(EmployeeModel.user_id == user_id)
        model = self.session.scalar(statement)
        if model:
            return self._to_entity(model)
        return None

    def get_by_department(self, department_id: int) -> List[Employee]:
        statement = select(EmployeeModel).where(EmployeeModel.department_id == department_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_all(self) -> List[Employee]:
        statement = select(EmployeeModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_active(self) -> List[Employee]:
        statement = select(EmployeeModel).where(EmployeeModel.is_active == True)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(EmployeeModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: Employee) -> EmployeeModel:
        return EmployeeModel(
            id=entity.id,
            department_id=entity.department_id,
            user_id=entity.user_id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            middle_name=entity.middle_name,
            phone=str(entity.phone) if entity.phone else None,
            email=str(entity.email) if entity.email else None,
            position=entity.position,
            position_code=entity.position_code,
            employee_number=entity.employee_number,
            hire_date=entity.hire_date,
            termination_date=entity.termination_date,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, model: EmployeeModel) -> Employee:
        return Employee(
            id=model.id,
            department_id=model.department_id,
            first_name=model.first_name,
            last_name=model.last_name,
            middle_name=model.middle_name,
            phone=Phone(model.phone) if model.phone else None,
            email=Email(model.email) if model.email else None,
            position=model.position,
            position_code=model.position_code,
            employee_number=model.employee_number,
            hire_date=model.hire_date,
            termination_date=model.termination_date,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
