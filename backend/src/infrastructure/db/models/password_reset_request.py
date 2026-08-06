# src/infrastructure/db/models/password_reset_request.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from . import Base


class PasswordResetRequest(Base):
    """
    Заявка на сброс пароля.
    Пользователь создаёт заявку через публичную форму (без авторизации),
    администратор рассматривает и одобряет/отклоняет её.
    """
    __tablename__ = "password_reset_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True, comment="ID пользователя, если известен")
    username = Column(String(50), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending", comment="pending | approved | rejected")
    admin_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self) -> str:
        return f"<PasswordResetRequest(id={self.id}, username='{self.username}', status='{self.status}')>"
