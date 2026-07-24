# backend/src/presentation/http/dependencies/__init__.py
from src.presentation.http.dependencies.auth import get_current_admin

__all__ = ["get_current_admin"]
