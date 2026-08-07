# backend/src/core/services/notification_service.py
import smtplib
import os
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис отправки уведомлений через email и MAX chat"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_user)
        self.max_api_url = os.getenv("MAX_API_URL", "http://localhost:8080/api/notify")
        self.max_api_token = os.getenv("MAX_API_TOKEN", "")
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Отправка email уведомления"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
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
