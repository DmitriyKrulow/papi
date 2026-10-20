import os
import secrets
from pydantic_settings import BaseSettings


def _generate_secret() -> str:
    """Генерирует случайный SECRET_KEY если не задан в env."""
    return secrets.token_urlsafe(64)


class Settings(BaseSettings):
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

    @property
    def validated_secret_key(self) -> str:
        """Возвращает SECRET_KEY, проверяя что он задан и достаточно силён."""
        key = self.secret_key or os.getenv("SECRET_KEY", "")
        if not key:
            raise RuntimeError(
                "SECRET_KEY environment variable is not set. "
                "Please add SECRET_KEY to your .env file. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
        if len(key) < 32:
            raise RuntimeError(
                f"SECRET_KEY is too short ({len(key)} chars). "
                "It must be at least 32 characters. "
                "Generate a strong one with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
        return key


settings = Settings()
