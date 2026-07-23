from datetime import datetime
from typing import List, Tuple, Optional
import json
import os
from pathlib import Path

from backend.src.core.entities.user import User
from backend.src.use_cases.interfaces.repositories import IUserRepository
from backend.src.core.value_objects import Email, Phone, PasswordHash


class InMemoryUserRepository(IUserRepository):
    """Ин-мемори репозиторий для работы с пользователями (для начальной настройки)"""
    
    _instance: Optional['InMemoryUserRepository'] = None
    _storage_file: Path = Path("backend/data/users.json")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._users: dict = {}
            cls._instance._counter = 0
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        if self._storage_file.exists():
            try:
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._users = data.get('users', {})
                    self._counter = data.get('counter', 0)
            except Exception:
                self._users = {}
                self._counter = 0
    
    def _save(self):
        self._storage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._storage_file, 'w', encoding='utf-8') as f:
            json.dump({'users': self._users, 'counter': self._counter}, f, indent=2, default=str)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        if str(user_id) not in self._users:
            return None
        return self._to_entity(self._users[str(user_id)])
    
    async def get_by_username(self, username: str) -> Optional[User]:
        for user_id, user_data in self._users.items():
            if user_data['username'] == username:
                return self._to_entity(user_data)
        return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        for user_id, user_data in self._users.items():
            if user_data['email'] == email:
                return self._to_entity(user_data)
        return None
    
    async def create(self, user: User) -> User:
        self._counter += 1
        user.id = self._counter
        user_data = self._to_dict(user)
        self._users[str(self._counter)] = user_data
        self._save()
        return user
    
    async def update(self, user: User) -> User:
        if str(user.id) not in self._users:
            raise ValueError("User not found")
        self._users[str(user.id)] = self._to_dict(user)
        self._save()
        return user
    
    async def delete(self, user_id: int) -> None:
        if str(user_id) in self._users:
            del self._users[str(user_id)]
            self._save()
    
    def _to_entity(self, data: dict) -> User:
        password_hash = None
        if data.get('password_hash'):
            password_hash = PasswordHash(data['password_hash'])
        
        return User(
            id=data['id'],
            email=Email(data['email']),
            username=data['username'],
            full_name=data.get('full_name'),
            phone=Phone(data['phone']) if data.get('phone') else None,
            password_hash=password_hash,
            role=data.get('role', 'user'),
            is_active=data.get('is_active', True),
        )
    
    def _to_dict(self, user: User) -> dict:
        return {
            'id': user.id,
            'email': str(user.email),
            'username': user.username,
            'full_name': user.full_name,
            'phone': str(user.phone) if user.phone else None,
            'password_hash': str(user.password_hash) if user.password_hash else None,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
        }
    
    def get_all(self) -> List[User]:
        return [self._to_entity(data) for data in self._users.values()]
    
    def get_by_role(self, role: str) -> List[User]:
        return [self._to_entity(data) for data in self._users.values() if data.get('role') == role]


async def get_user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()
