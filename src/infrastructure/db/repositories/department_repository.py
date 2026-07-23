from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import Department as DepartmentModel
from src.core.entities.department import Department
from src.core.value_objects import Phone, Email


class DepartmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, department: Department) -> None:
        model = self._to_model(department)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[Department]:
        model = self.session.get(DepartmentModel, id)
        if model:
            return self._to_entity(model)
        return None

    def get_by_code(self, code: str) -> Optional[Department]:
        statement = select(DepartmentModel).where(DepartmentModel.code == code)
        model = self.session.scalar(statement)
        if model:
            return self._to_entity(model)
        return None

    def get_by_organization(self, organization_id: int) -> List[Department]:
        statement = select(DepartmentModel).where(DepartmentModel.organization_id == organization_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def get_subdepartments(self, parent_id: int) -> List[Department]:
        statement = select(DepartmentModel).where(DepartmentModel.parent_id == parent_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_all(self) -> List[Department]:
        statement = select(DepartmentModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_active(self) -> List[Department]:
        statement = select(DepartmentModel).where(DepartmentModel.is_active == True)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(DepartmentModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: Department) -> DepartmentModel:
        return DepartmentModel(
            id=entity.id,
            organization_id=entity.organization_id,
            name=entity.name,
            code=entity.code,
            parent_id=entity.parent_id,
            head=entity.head,
            phone=str(entity.phone) if entity.phone else None,
            email=str(entity.email) if entity.email else None,
            location=entity.location,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, model: DepartmentModel) -> Department:
        return Department(
            id=model.id,
            organization_id=model.organization_id,
            name=model.name,
            code=model.code,
            parent_id=model.parent_id,
            head=model.head,
            phone=Phone(model.phone) if model.phone else None,
            email=Email(model.email) if model.email else None,
            location=model.location,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
