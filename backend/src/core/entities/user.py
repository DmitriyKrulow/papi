from src.core.value_objects import Email, Phone, PasswordHash


class User:
    """User entity placeholder"""
    def __init__(self, id=None, username=None, email=None, role=None, **kwargs):
        self.id = id
        self.username = username
        self.email = email
        self.role = role or "user"
        for key, value in kwargs.items():
            setattr(self, key, value)
