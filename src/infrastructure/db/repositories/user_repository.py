from typing import List, Optional, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.infrastructure.db.models import User as UserModel
from src.core.entities.user import User
from src.core.value_objects import Email, Phone, PasswordHash

T = TypeVar('T')


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> None:
        model = self._to_model(user)
        self.session.add(model)
        self.session.flush()

    def get_by_id(self, id: int) -> Optional[User]:
        model = self.session.get(UserModel, id)
        if model:
            return self._to_entity(model)
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        statement = select(UserModel).where(UserModel.email == email)
        model = self.session.scalar(statement)
        if model:
            return self._to_entity(model)
        return None

    def get_by_username(self, username: str) -> Optional[User]:
        statement = select(UserModel).where(UserModel.username == username)
        model = self.session.scalar(statement)
        if model:
            return self._to_entity(model)
        return None

    def list_all(self) -> List[User]:
        statement = select(UserModel)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def list_by_department(self, department_id: int) -> List[User]:
        statement = select(UserModel).where(UserModel.department_id == department_id)
        models = self.session.scalars(statement).all()
        return [self._to_entity(model) for model in models]

    def count(self) -> int:
        statement = select(func.count(UserModel.id))
        return self.session.scalar(statement) or 0

    def _to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            username=entity.username,
            email=str(entity.email),
            full_name=entity.full_name,
            phone=str(entity.phone) if entity.phone else None,
            password_hash=str(entity.password_hash) if entity.password_hash else None,
            is_active=entity.is_active,
            department_id=entity.department_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            username=model.username,
            full_name=model.full_name,
            phone=Phone(model.phone) if model.phone else None,
            password_hash=PasswordHash(model.password_hash) if model.password_hash else None,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
