# backend/src/use_cases/auth/register_user.py
from backend.src.infrastructure.db.repositories.user_repository import InMemoryUserRepository
from backend.src.core.entities.user import User
from backend.src.core.value_objects.password_hash import PasswordHash
from backend.src.core.value_objects.email import Email

try:
    from backend.src.core.value_objects.phone import Phone
except ImportError:
    Phone = None


async def register_user(user_data: dict) -> User:
    """Регистрация нового пользователя"""
    password_hash = PasswordHash.from_plain_password(user_data["password"])
    email = Email(user_data["email"])
    
    phone = None
    if Phone and user_data.get("phone"):
        try:
            phone = Phone(user_data["phone"])
        except ValueError as e:
            raise ValueError(f"Invalid phone number: {e}")
    
    user = User(
        username=user_data["username"],
        email=email,
        full_name=user_data.get("full_name"),
        phone=phone,
        password_hash=password_hash,
        role="user",
        is_active=True,
    )
    
    user_repo = InMemoryUserRepository()
    return await user_repo.create(user)
