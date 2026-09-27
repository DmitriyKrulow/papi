# backend/src/presentation/http/routers/system_settings.py
"""Глобальные настройки системы (включая HTTPS)"""
import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.infrastructure.db.init_db import get_db
from src.infrastructure.db.models.user import User
from src.infrastructure.db.models.system_settings import SystemSettings
from src.presentation.http.dependencies.auth import get_current_admin, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system-settings", tags=["system-settings"])


@router.get("/config")
async def get_system_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить глобальные настройки системы"""
    settings = db.query(SystemSettings).first()
    
    if not settings:
        # Создаём настройки по умолчанию
        settings = SystemSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return {
        "system_name": settings.system_name or os.getenv("SYSTEM_NAME") or "PAPI Система",
        "frontend_url": settings.frontend_url or os.getenv("FRONTEND_URL") or "http://localhost",
        "https_enabled": bool(settings.https_enabled),
        "https_domain": settings.https_domain or os.getenv("LETSENCRYPT_DOMAIN") or "",
        "https_email": settings.https_email or os.getenv("LETSENCRYPT_EMAIL") or "",
        "https_port": settings.https_port or int(os.getenv("HTTPS_PORT") or "443"),
        "http_warning_enabled": bool(settings.http_warning_enabled),
    }


@router.post("/config")
async def save_system_config(
    config: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Сохранить глобальные настройки системы"""
    settings = db.query(SystemSettings).first()
    
    if not settings:
        settings = SystemSettings()
        db.add(settings)
    
    # Основные настройки
    settings.system_name = config.get("system_name", "PAPI Система")
    settings.frontend_url = config.get("frontend_url")
    
    # HTTPS настройки
    settings.https_enabled = 1 if config.get("https_enabled", True) else 0
    settings.https_domain = config.get("https_domain")
    settings.https_email = config.get("https_email")
    settings.https_port = config.get("https_port", 443)
    
    # Предупреждение о HTTP
    settings.http_warning_enabled = 1 if config.get("http_warning_enabled", True) else 0
    
    db.commit()
    db.refresh(settings)
    
    # Обновляем .env файл если HTTPS настройки изменены
    if config.get("https_domain") or config.get("https_enabled") is not None:
        _update_env_https(config)
    
    return {"message": "Настройки сохранены", "id": settings.id}


def _update_env_https(config: dict):
    """Обновить HTTPS настройки в .env файле"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), ".env")
    
    if not os.path.exists(env_path):
        logger.warning(f".env file not found at {env_path}")
        return
    
    lines = []
    https_domain_set = False
    https_email_set = False
    https_enabled_set = False
    https_port_set = False
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read .env: {e}")
        return
    
    new_lines = []
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("LETSENCRYPT_DOMAIN="):
            new_lines.append(f"LETSENCRYPT_DOMAIN={config.get('https_domain', '')}\n")
            https_domain_set = True
        elif stripped.startswith("LETSENCRYPT_EMAIL="):
            new_lines.append(f"LETSENCRYPT_EMAIL={config.get('https_email', '')}\n")
            https_email_set = True
        elif stripped.startswith("LETSENCRYPT_ENABLE="):
            val = "true" if config.get("https_enabled", True) else "false"
            new_lines.append(f"LETSENCRYPT_ENABLE={val}\n")
            https_enabled_set = True
        elif stripped.startswith("HTTPS_PORT="):
            new_lines.append(f"HTTPS_PORT={config.get('https_port', 443)}\n")
            https_port_set = True
        else:
            new_lines.append(line)
    
    # Если ключи не найдены — добавляем в конец
    if not https_domain_set and config.get("https_domain"):
        new_lines.append(f"LETSENCRYPT_DOMAIN={config['https_domain']}\n")
    if not https_email_set and config.get("https_email"):
        new_lines.append(f"LETSENCRYPT_EMAIL={config['https_email']}\n")
    if not https_enabled_set:
        val = "true" if config.get("https_enabled", True) else "false"
        new_lines.append(f"LETSENCRYPT_ENABLE={val}\n")
    if not https_port_set:
        new_lines.append(f"HTTPS_PORT={config.get('https_port', 443)}\n")
    
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        logger.info("HTTPS settings updated in .env")
    except Exception as e:
        logger.error(f"Failed to write .env: {e}")


@router.post("/restart-https")
async def restart_https(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Перезапустить frontend контейнер для применения HTTPS настроек.
    
    Внимание: это вызовет кратковременный простой (10-30 секунд).
    """
    import subprocess
    
    try:
        # Команда для перезапуска frontend контейнера
        result = subprocess.run(
            ["docker", "compose", "restart", "frontend"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            return {
                "message": "Frontend контейнер перезапущен. HTTPS настройки применяются.",
                "status": "restarting",
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка перезапуска: {result.stderr}",
            )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Docker не найден. Перезапустите вручную: docker compose restart frontend",
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Превышено время ожидания перезапуска",
        )
    except Exception as e:
        logger.error(f"Failed to restart frontend: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка перезапуска: {str(e)}",
        )


@router.get("/https-status")
async def get_https_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить статус HTTPS (проверка сертификатов)"""
    import subprocess
    import urllib.request
    import ssl
    
    settings = db.query(SystemSettings).first()
    domain = settings.https_domain if settings else None
    
    if not domain:
        return {
            "enabled": False,
            "domain": "",
            "certificate_valid": False,
            "days_remaining": 0,
            "error": "Домен не настроен",
        }
    
    # 1. Проверяем через Docker (если доступен)
    docker_works = False
    try:
        result = subprocess.run(
            ["docker", "exec", "papi-frontend", "certbot", "certificates", "--quiet"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0 and "Certificate Name" in result.stdout:
            output = result.stdout
            days_remaining = 0
            cert_valid = False
            
            for line in output.split("\n"):
                if "Expiry Date" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        date_str = parts[-1].strip()
                        from datetime import datetime
                        try:
                            expiry = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                            now = datetime.now()
                            days_remaining = (expiry - now).days
                            cert_valid = days_remaining > 0
                        except ValueError:
                            pass
            
            return {
                "mode": "https",
                "enabled": True,
                "domain": domain,
                "certificate_valid": cert_valid,
                "days_remaining": days_remaining,
                "error": None,
            }
        docker_works = True
    except Exception as e:
        logger.debug(f"Docker check failed: {e}")
    
    # 2. Проверяем HTTPS (порт 443)
    https_works = False
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(f"https://frontend/", timeout=5, context=ctx) as response:
            cert = response.getpeercert()
            https_works = True
            
            if cert:
                not_after = cert.get('notAfter', '')
                if not_after:
                    from datetime import datetime
                    try:
                        expiry = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        now = datetime.now()
                        days_remaining = (expiry - now).days
                        return {
                            "mode": "https",
                            "enabled": True,
                            "domain": domain,
                            "certificate_valid": days_remaining > 0,
                            "days_remaining": days_remaining,
                            "error": None,
                        }
                    except ValueError:
                        pass
                return {
                    "mode": "https",
                    "enabled": True,
                    "domain": domain,
                    "certificate_valid": True,
                    "days_remaining": -1,
                    "error": None,
                }
    except Exception as e:
        logger.debug(f"HTTPS check failed: {e}")
    
    # 3. Проверяем HTTP (порт 80)
    http_works = False
    try:
        with urllib.request.urlopen(f"http://frontend/", timeout=5) as response:
            if response.status == 200:
                http_works = True
    except Exception as e:
        logger.debug(f"HTTP check failed: {e}")
    
    # Определяем режим работы
    if https_works:
        return {
            "mode": "https",
            "enabled": True,
            "domain": domain,
            "certificate_valid": True,
            "days_remaining": -1,
            "error": None,
        }
    elif http_works:
        return {
            "mode": "http",
            "enabled": True,
            "domain": domain,
            "certificate_valid": False,
            "days_remaining": 0,
            "error": "HTTPS не активен — система работает в HTTP режиме. Для активации HTTPS перезапустите: docker compose restart frontend",
        }
    else:
        return {
            "mode": "unknown",
            "enabled": True,
            "domain": domain,
            "certificate_valid": False,
            "days_remaining": 0,
            "error": "Не удалось проверить статус — frontend не отвечает",
        }
