# backend/src/core/services/notification_service.py
import smtplib
import os
import json
import logging
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SMTPConnectionPool:
    """Кэш SMTP-соединений для избежания частых логин-аут."""
    
    def __init__(self, max_age: int = 300):
        self.smtp_host = None
        self.smtp_port = None
        self.smtp_user = None
        self.smtp_password = None
        self.use_tls = True
        self.use_ssl = False
        self.connection = None
        self.last_used = 0
        self.max_age = max_age  # секунд жизни соединения
        self._lock = threading.Lock()
    
    def get_connection(self, host, port, user, password, use_tls=True, use_ssl=False):
        """Получить кэшированное или создать новое соединение."""
        with self._lock:
            # Проверяем, что параметры те же
            same_params = (
                self.smtp_host == host and
                self.smtp_port == port and
                self.smtp_user == user and
                self.smtp_password == password and
                self.use_tls == use_tls and
                self.use_ssl == use_ssl
            )
            
            # Проверяем срок жизни
            expired = (time.time() - self.last_used) > self.max_age
            
            if same_params and self.connection and not expired:
                logger.debug("Reusing cached SMTP connection")
                try:
                    self.connection.noop()  # Проверяем живость
                    return self.connection
                except Exception:
                    # Соединение мёртвое — создаём новое
                    self.connection = None
            
            # Закрываем старое соединение
            if self.connection:
                try:
                    self.connection.quit()
                except Exception:
                    pass
                self.connection = None
            
            # Создаём новое соединение
            logger.info("Creating new SMTP connection")
            conn = self._create_connection(host, port, user, password, use_tls, use_ssl)
            self.smtp_host = host
            self.smtp_port = port
            self.smtp_user = user
            self.smtp_password = password
            self.use_tls = use_tls
            self.use_ssl = use_ssl
            self.connection = conn
            self.last_used = time.time()
            return conn
    
    def _create_connection(self, host, port, user, password, use_tls, use_ssl):
        """Создаёт SMTP-соединение и выполняет логин."""
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if use_tls:
                server.starttls()
        server.login(user, password)
        return server
    
    def close(self):
        """Закрывает кэшированное соединение."""
        with self._lock:
            if self.connection:
                try:
                    self.connection.quit()
                except Exception:
                    pass
                self.connection = None


class NotificationService:
    """Сервис отправки уведомлений через email и MAX chat"""
    
    # Лимиты для избежания блокировок SMTP
    MIN_INTERVAL_BETWEEN_EMAILS = 2.0  # секунд между отправками
    MAX_EMAILS_PER_MINUTE = 10  # Yandex лимит ~100/час, ставим 10/мин для запаса
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        sender_email: Optional[str] = None,
        system_name: Optional[str] = None,
        use_tls: Optional[bool] = None,
        use_ssl: Optional[bool] = None,
    ):
        # Приоритет: переданные параметры > env vars > дефолты
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST") or os.getenv("MAIL_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT") or os.getenv("MAIL_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER") or os.getenv("MAIL_USERNAME", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD", "")
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL") or os.getenv("MAIL_DEFAULT_SENDER", self.smtp_user)
        self.system_name = system_name or os.getenv("SYSTEM_NAME") or "PAPI Система"
        
        # TLS/SSL настройки
        env_use_tls = os.getenv("MAIL_USE_TLS", "true")
        env_use_ssl = os.getenv("MAIL_USE_SSL", "false")
        
        if use_tls is not None:
            self.use_tls = use_tls
        elif "MAIL_USE_TLS" in os.environ:
            self.use_tls = env_use_tls.lower() in ("true", "1", "yes")
        else:
            self.use_tls = self.smtp_port == 587
        
        if use_ssl is not None:
            self.use_ssl = use_ssl
        elif "MAIL_USE_SSL" in os.environ:
            self.use_ssl = env_use_ssl.lower() in ("true", "1", "yes")
        else:
            self.use_ssl = self.smtp_port == 465
        
        self.max_api_url = os.getenv("MAX_API_URL", "http://localhost:8080/api/notify")
        self.max_api_token = os.getenv("MAX_API_TOKEN", "")
        
        # Пул SMTP-соединений
        self._pool = SMTPConnectionPool(max_age=300)
        
        # Rate limiting
        self._last_send_time = 0
        self._emails_sent_in_window = []
        self._lock = threading.Lock()
    
    def _enforce_rate_limit(self):
        """Применяет rate limiting для избежания блокировок."""
        now = time.time()
        
        with self._lock:
            # Удаляем старые записи (старше 1 минуты)
            self._emails_sent_in_window = [
                t for t in self._emails_sent_in_window
                if now - t < 60
            ]
            
            # Если превысили лимит — ждём
            if len(self._emails_sent_in_window) >= self.MAX_EMAILS_PER_MINUTE:
                wait_time = 60 - (now - self._emails_sent_in_window[0])
                if wait_time > 0:
                    logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    self._emails_sent_in_window = []
            
            # Минимальная задержка между письмами
            elapsed = now - self._last_send_time
            if elapsed < self.MIN_INTERVAL_BETWEEN_EMAILS:
                sleep_time = self.MIN_INTERVAL_BETWEEN_EMAILS - elapsed
                time.sleep(sleep_time)
            
            self._emails_sent_in_window.append(time.time())
            self._last_send_time = time.time()
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        use_tls: Optional[bool] = None,
        use_ssl: Optional[bool] = None,
        max_retries: int = 2,
    ) -> bool:
        """Отправка email уведомления с retry и connection pooling."""
        local_use_tls = use_tls if use_tls is not None else self.use_tls
        local_use_ssl = use_ssl if use_ssl is not None else self.use_ssl
        
        for attempt in range(1, max_retries + 1):
            try:
                # Применяем rate limiting
                self._enforce_rate_limit()
                
                # Получаем соединение из пула
                server = self._pool.get_connection(
                    host=self.smtp_host,
                    port=self.smtp_port,
                    user=self.smtp_user,
                    password=self.smtp_password,
                    use_tls=local_use_tls,
                    use_ssl=local_use_ssl,
                )
                
                # Формируем письмо
                msg = MIMEMultipart()
                # Yandex требует ТОЛЬКО email в From, display name в заголовке
                msg['From'] = self.sender_email
                msg['Reply-To'] = self.sender_email
                msg['To'] = to_email
                msg['Subject'] = subject
                # Добавляем название системы как display name
                if self.system_name and self.system_name != "PAPI Система":
                    msg.add_header('X-System-Name', self.system_name)
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # Отправляем
                server.send_message(msg)
                
                logger.info(f"Email sent to {to_email}: {subject}")
                return True
                
            except smtplib.SMTPServerDisconnected:
                logger.warning(f"SMTP connection lost (attempt {attempt}/{max_retries}), retrying...")
                # Закрываем пул, чтобы создать новое соединение
                self._pool.close()
                if attempt < max_retries:
                    time.sleep(3 ** attempt)  # экспоненциальная задержка 3s, 9s, 27s...
                    continue
                return False
                
            except smtplib.SMTPException as e:
                error_str = str(e)
                
                # Временная ошибка (блокировка SMTP) — пробуем снова с большой задержкой
                if "454" in error_str or "421" in error_str:
                    logger.warning(f"Temporary SMTP error (attempt {attempt}/{max_retries}): {e}")
                    self._pool.close()
                    if attempt < max_retries:
                        wait_time = 30 * attempt  # 30s, 60s, 90s...
                        logger.warning(f"Yandex rate limit detected, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    # Все попытки исчерпаны — возвращаем понятную ошибку
                    logger.error(f"SMTP rate limit exceeded after {max_retries} retries. Yandex may have temporarily blocked SMTP access.")
                    return False
                
                # Постоянная ошибка — не retry
                logger.error(f"SMTP error (no retry): {e}")
                return False
                
            except Exception as e:
                logger.error(f"Failed to send email to {to_email}: {str(e)}")
                return False
        
        return False
    
    def send_max_notification(self, user_id: int, title: str, message: str) -> bool:
        """Отправка уведомления через MAX chat"""
        try:
            if not self.max_api_url or not self.max_api_token:
                logger.warning("MAX API not configured")
                return False
            
            payload = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            import requests
            response = requests.post(
                self.max_api_url,
                json=payload,
                headers={"Authorization": f"Bearer {self.max_api_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"MAX notification sent to user {user_id}: {title}")
                return True
            else:
                logger.error(f"MAX notification failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send MAX notification to user {user_id}: {str(e)}")
            return False
    
    def send_inventory_notification(self, user, inventory_check, asset=None):
        """Отправка уведомления об инвентаризации"""
        title = f"📋 Инвентаризация: {inventory_check.name}"
        
        if inventory_check.status == "in_progress":
            message = f"Начата инвентаризация '{inventory_check.name}'. "
            if asset:
                message += f"Пожалуйста, проверьте наличие актива: {asset.name} (инв. № {asset.inventory_number})."
            else:
                message += "Пожалуйста, проверьте наличие всего имущества."
        elif inventory_check.status == "completed":
            message = f"Инвентаризация '{inventory_check.name}' завершена. Найдено: {inventory_check.found}, Отсутствует: {inventory_check.missing}."
        else:
            message = f"Статус инвентаризации '{inventory_check.name}' обновлен: {inventory_check.status}."
        
        # Сохраняем уведомление в БД
        from src.infrastructure.db.models.notification import Notification
        from src.infrastructure.db.init_db import SessionLocal
        
        db = SessionLocal()
        try:
            notification = Notification(
                user_id=user.id,
                type="inventory",
                title=title,
                message=message,
                reference_type="inventory_check",
                reference_id=inventory_check.id
            )
            db.add(notification)
            db.commit()
            
            # Отправляем email
            if user.email:
                email_sent = self.send_email(user.email, title, message)
                if email_sent:
                    notification.email_sent = True
                    notification.email_sent_at = datetime.now()
                    db.commit()
            
            # Отправляем через MAX
            max_sent = self.send_max_notification(user.id, title, message)
            if max_sent:
                notification.max_sent = True
                notification.max_sent_at = datetime.now()
                db.commit()
                
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to send notification to user {user.id}: {str(e)}")
        finally:
            db.close()
