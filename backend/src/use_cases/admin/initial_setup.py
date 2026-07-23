# backend/src/use_cases/admin/initial_setup.py
from backend.src.infrastructure.db.repositories.user_repository import InMemoryUserRepository
from backend.src.core.entities.user import User
from backend.src.core.value_objects.password_hash import PasswordHash
from backend.src.core.value_objects.email import Email


async def ensure_initial_admin():
    """Создает начального администратора, если пользователей нет"""
    user_repo = InMemoryUserRepository()
    
    users = user_repo.get_all()
    if len(users) == 0:
        password_hash = PasswordHash.from_plain_password("admin123")
        email = Email("admin@papi.local")
        
        admin = User(
            username="admin",
            email=email,
            full_name="Системный администратор",
            phone=None,
            password_hash=password_hash,
            role="admin",
            is_active=True,
        )
        
        await user_repo.create(admin)
        return True
    
    return False


async def create_admin_user(username: str, email: str, password: str, full_name: str = None) -> User:
    """Создает администратора программно"""
    user_repo = InMemoryUserRepository()
    
    password_hash = PasswordHash.from_plain_password(password)
    email_obj = Email(email)
    
    admin = User(
        username=username,
        email=email_obj,
        full_name=full_name,
        phone=None,
        password_hash=password_hash,
        role="admin",
        is_active=True,
    )
    
    return await user_repo.create(admin)
