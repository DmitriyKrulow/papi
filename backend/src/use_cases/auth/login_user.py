# src/use_cases/auth/login_user.py
"""
Use case: авторизация пользователя с защитой от брутфорса.

Логика lockout:
- Попытки 1–5 (в рамках окна): просто отклонение при неверном пароле
- После 5 неудач: блокировка на 5 минут
- После снятия блокировки и снова 5 неудач: блокировка на 30 минут
- После снятия блокировки и снова 5 неудач: блокировка на 1 час
- Общее количество неудачных попыток >= 15: постоянная блокировка + уведомление админу
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.brute_force_log import BruteForceLog
from src.core.value_objects.password_hash import PasswordHash

logger = logging.getLogger(__name__)

# --- Константы ---
MAX_ATTEMPTS_BEFORE_LOCKOUT = 5       # Максимум попыток до первой блокировки
MAX_TOTAL_FAILURES = 15               # Общее число неудач до перманентной блокировки

# Этапы lockout (в минутах)
LOCKOUT_STAGES = [
    timedelta(minutes=5),
    timedelta(minutes=30),
    timedelta(hours=1),
]


class BruteForceException(Exception):
    """Исключение блокировки за брутфорс."""
    def __init__(self, user: User, remaining_seconds: int, total_failures: int):
        self.remaining_seconds = remaining_seconds
        self.total_failures = total_failures
        minutes = remaining_seconds // 60
        hours = minutes // 60
        remainder_minutes = minutes % 60
        if hours > 0:
            message = (
                f"Слишком много неудачных попыток. "
                f"Осталось ждать: {hours} ч. {remainder_minutes} мин. "
                f"(Всего неудачных попыток: {total_failures})"
            )
        else:
            message = (
                f"Слишком много неудачных попыток. "
                f"Осталось ждать: {remainder_minutes} мин. "
                f"(Всего неудачных попыток: {total_failures})"
            )
        super().__init__(message)


class AccountPermanentlyLockedException(Exception):
    """Постоянная блокировка аккаунта."""
    def __init__(self, user: User):
        super().__init__(
            f"Аккаунт '{user.username}' заблокирован из-за подозрительной активности. "
            "Обратитесь к администратору."
        )


def _parse_allowed_ips(user: User) -> list[str]:
    """Парсит JSON-список разрешённых IP из модели пользователя."""
    if not user.allowed_ips:
        return []
    try:
        ips = json.loads(user.allowed_ips)
        if isinstance(ips, list):
            return [str(ip).strip() for ip in ips if ip]
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Некорректный формат allowed_ips для пользователя {user.username}")
    return []


def _check_ip_allowed(user: User, ip_address: str) -> bool:
    """
    Проверяет, разрешён ли IP для данного пользователя.
    Если у пользователя есть allowed_ips (whitelist), то вход только с этих IP.
    Если allowed_ips пуст или None — вход разрешён с любого IP.
    """
    if user.role != "admin":
        return True  # Whitelist только для администраторов

    allowed = _parse_allowed_ips(user)
    if not allowed:
        return True  # Нет whitelist — вход разрешён

    return ip_address in allowed


def _get_recent_failures(db: Session, username: str, window_minutes: int = 60) -> list[BruteForceLog]:
    """
    Возвращает неудачные попытки входа для пользователя за последние window_minutes.
    """
    cutoff = datetime.now() - timedelta(minutes=window_minutes)
    return (
        db.query(BruteForceLog)
        .filter(
            BruteForceLog.username == username,
            BruteForceLog.is_success == 0,
            BruteForceLog.created_at >= cutoff,
        )
        .order_by(BruteForceLog.created_at.desc())
        .all()
    )


def _get_total_failures(db: Session, username: str) -> int:
    """
    Возвращает ОБЩЕЕ количество неудачных попыток для пользователя (за всё время).
    """
    return (
        db.query(BruteForceLog)
        .filter(BruteForceLog.username == username, BruteForceLog.is_success == 0)
        .count()
    )


def _get_current_lockout(db: Session, username: str) -> Optional[datetime]:
    """
    Проверяет, находится ли пользователь в состоянии блокировки.
    Возвращает datetime разблокировки или None.
    """
    recent_failures = _get_recent_failures(db, username, window_minutes=120)
    if not recent_failures:
        return None

    # Находим самый свежий неудачный вход в группе
    latest_failure = recent_failures[0]
    stage_index = len(recent_failures) - MAX_ATTEMPTS_BEFORE_LOCKOUT
    if stage_index < 0:
        return None  # Ещё не достигли порога блокировки

    # Если stage_index выходит за пределы массива, берём последнюю стадию
    if stage_index >= len(LOCKOUT_STAGES):
        stage_index = len(LOCKOUT_STAGES) - 1

    lockout_duration = LOCKOUT_STAGES[stage_index]
    lockout_expires = latest_failure.created_at + lockout_duration

    if datetime.now() < lockout_expires:
        return lockout_expires

    return None


def _record_failure(db: Session, username: str, ip_address: str):
    """Записывает неудачную попытку входа в лог."""
    log_entry = BruteForceLog(
        username=username,
        ip_address=ip_address,
        is_success=0,
        created_at=datetime.now(),
    )
    db.add(log_entry)
    db.flush()


def _record_success(db: Session, username: str, ip_address: str):
    """Записывает успешную попытку входа в лог."""
    log_entry = BruteForceLog(
        username=username,
        ip_address=ip_address,
        is_success=1,
        created_at=datetime.now(),
    )
    db.add(log_entry)
    db.flush()


def _notify_admins_about_attack(db: Session, username: str, ip_address: str):
    """
    Отправляет уведомление администраторам о возможной попытке взлома.
    В текущей реализации — логирование. Можно расширить email/telegram.
    """
    from src.infrastructure.db.models.user import User as UserModel

    admins = db.query(UserModel).filter(UserModel.role == "admin", UserModel.is_active == True).all()
    admin_emails = [a.email for a in admins if a.email]
    admin_usernames = [a.username for a in admins if a.username]

    subject = "⚠️ УВЕДОМЛЕНИЕ: Возможная попытка взлома аккаунта"
    body = (
        f"Обнаружена подозрительная активность!\n\n"
        f"Пользователь: {username}\n"
        f"IP адрес: {ip_address}\n"
        f"Статус: АККАУНТ ЗАБЛОКИРОВАН (достигнут лимит неудачных попыток)\n\n"
        f"Необходимо проверить безопасность аккаунта.\n"
    )

    # Логирование уведомления
    logger.warning(
        f"[SECURITY] {subject}\n"
        f"  Subject: {subject}\n"
        f"  Body: {body}\n"
        f"  Admin emails: {admin_emails}"
    )

    # TODO: Реализовать отправку email через SMTP или webhook (Telegram/Discord)
    # import smtplib
    # from email.mime.text import MIMEText
    # for email in admin_emails:
    #     send_email(email, subject, body)

    return {
        "subject": subject,
        "body": body,
        "admin_emails": admin_emails,
        "admin_usernames": admin_usernames,
    }


class LoginUser:
    """Use case: вход пользователя с защитой от брутфорса."""

    def __call__(
        self,
        username: str,
        password: str,
        db: Session,
        ip_address: str = "127.0.0.1",
    ) -> User:
        """
        Выполняет аутентификацию пользователя.

        Args:
            username: Имя пользователя
            password: Пароль в открытом виде
            db: Сессия SQLAlchemy
            ip_address: IP адрес клиента

        Returns:
            User: объект пользователя при успешной аутентификации

        Raises:
            BruteForceException: при блокировке за брутфорс
            AccountPermanentlyLockedException: при перманентной блокировке (15+ неудач)
            HTTPException: при неверном пароле или отсутствии пользователя
        """
        # --- Шаг 1: Поиск пользователя ---
        user = db.query(User).filter(User.username == username).first()
        if not user:
            _record_failure(db, username, ip_address)
            raise HTTPException(status_code=400, detail="Incorrect username or password")

        # --- Шаг 2: Проверка IP whitelist (для администраторов) ---
        if not _check_ip_allowed(user, ip_address):
            logger.warning(
                f"[SECURITY] Заблокирован вход с IP {ip_address} "
                f"для администратора {user.username} (allowed: {_parse_allowed_ips(user)})"
            )
            _record_failure(db, username, ip_address)
            raise HTTPException(
                status_code=403,
                detail="Доступ с данного IP адреса запрещён",
            )

        # --- Шаг 3: Проверка перманентной блокировки ---
        total_failures = _get_total_failures(db, username)
        if total_failures >= MAX_TOTAL_FAILURES:
            # Уведомляем администраторов
            _notify_admins_about_attack(db, username, ip_address)
            raise AccountPermanentlyLockedException(user)

        # --- Шаг 4: Проверка текущего lockout ---
        lockout_expires = _get_current_lockout(db, username)
        if lockout_expires:
            remaining = (lockout_expires - datetime.now()).total_seconds()
            _record_failure(db, username, ip_address)
            raise BruteForceException(user, int(remaining), total_failures)

        # --- Шаг 5: Проверка пароля ---
        if not user.password_hash:
            _record_failure(db, username, ip_address)
            raise HTTPException(status_code=400, detail="Password not set for user")

        try:
            password_hash = PasswordHash.from_hash_string(user.password_hash)
            if not password_hash.verify(password):
                raise HTTPException(status_code=400, detail="Incorrect username or password")
        except ValueError as e:
            _record_failure(db, username, ip_address)
            raise HTTPException(status_code=400, detail=f"Invalid password format: {str(e)}")

        # --- Шаг 6: Успешный вход ---
        _record_success(db, username, ip_address)
        logger.info(f"[Auth] Login successful for user: {username} from IP: {ip_address}")
        return user


login_user = LoginUser()
