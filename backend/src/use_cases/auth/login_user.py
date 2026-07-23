# backend/src/use_cases/auth/login_user.py
from backend.src.infrastructure.db.repositories.user_repository import InMemoryUserRepository
from backend.src.core.value_objects.password_hash import PasswordHash


async def login_user(username: str, password: str):
    """Аутентификация пользователя"""
    user_repo = InMemoryUserRepository()
    
    user = await user_repo.get_by_username(username)
    if not user:
        return None
    
    if not user.verify_password(password):
        return None
    
    return user
