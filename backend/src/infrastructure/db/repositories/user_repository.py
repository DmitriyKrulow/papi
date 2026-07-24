from datetime import datetime
from typing import Optional

from src.infrastructure.db.models.user import User


class InMemoryUserRepository:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db_session.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db_session.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db_session.query(User).filter(User.id == user_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        return (
            self.db_session.query(User)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, user_data: dict) -> User:
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            phone=user_data.get("phone"),
            password_hash=user_data["password_hash"],
            role=user_data.get("role", "user"),
            is_active=user_data.get("is_active", True),
            department_id=user_data.get("department_id"),
            created_at=user_data.get("created_at", datetime.now()),
            updated_at=user_data.get("updated_at", datetime.now()),
        )
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def update(self, user_id: int, user_data: dict) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        for key, value in user_data.items():
            if hasattr(user, key) and key != "id":
                setattr(user, key, value)
        user.updated_at = datetime.now()
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.db_session.delete(user)
        self.db_session.commit()
        return True

    def exists_by_username(self, username: str) -> bool:
        return (
            self.db_session.query(User)
            .filter(User.username == username)
            .count()
            > 0
        )

    def exists_by_email(self, email: str) -> bool:
        return (
            self.db_session.query(User).filter(User.email == email).count() > 0
        )
