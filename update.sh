#!/bin/bash
# ============================================================
# Скрипт обновления проекта PAPI
# ============================================================

set -e

# --- Переменные ---
PROJECT_DIR="/opt/papi"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
NGINX_CONF_SOURCE="$PROJECT_DIR/nginx/inventory-system.conf"
NGINX_CONF_TARGET="$NGINX_AVAILABLE/papi.conf"
BACKEND_SERVICE="papi-backend"
LOG_FILE="/var/log/papi-update.log"

# --- Функция логирования ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# --- Начало ---
log "=========================================="
log "🚀 Начинаем обновление проекта PAPI"
log "=========================================="

# --- 1. Git safe.directory ---
log "🔧 Настройка Git safe.directory..."
git config --global --add safe.directory /opt/papi || true
sudo -u papi git config --global --add safe.directory /opt/papi || true

# --- 2. Обновление кода ---
log "🔄 Обновляем код из GitHub..."
cd "$PROJECT_DIR" || { log "❌ Ошибка: не могу перейти в $PROJECT_DIR"; exit 1; }

sudo -u papi git stash push --include-untracked -m "Авто-сохранение перед обновлением $(date)" || log "⚠️ Нет изменений для stash"
sudo -u papi git pull origin main || { log "❌ Ошибка git pull"; exit 1; }
sudo -u papi git stash pop || log "⚠️ Конфликтов нет или они остались для ручного разрешения"

# --- 3. Бэкенд ---
log "📦 Обновляем бэкенд..."
cd "$PROJECT_DIR/backend" || { log "❌ Ошибка: не могу перейти в backend"; exit 1; }

if [ ! -d ".venv" ]; then
    log "⚠️ Виртуальное окружение не найдено, создаём..."
    sudo -u papi python3 -m venv .venv
fi

sudo -u papi bash -c "source .venv/bin/activate && pip install -r requirements.txt --upgrade" || log "⚠️ Ошибка pip install"

# --- 4. Фронтенд ---
log "📦 Собираем фронтенд..."
cd "$PROJECT_DIR/frontend" || { log "❌ Ошибка: не могу перейти в frontend"; exit 1; }

sudo chown -R papi:papi "$PROJECT_DIR/frontend" || true
sudo chmod -R 755 "$PROJECT_DIR/frontend" || true

sudo -u papi npm install --registry https://registry.npmmirror.com || log "⚠️ Ошибка npm install"

if sudo -u papi npm run build; then
    log "✅ Сборка фронтенда успешна"
else
    log "❌ Ошибка сборки фронтенда"
    exit 1
fi

sudo chown -R www-data:www-data "$PROJECT_DIR/frontend/dist"
sudo chmod -R 755 "$PROJECT_DIR/frontend/dist"

# --- 5. Nginx конфиг ---
log "🔄 Обновляем конфиг Nginx из $NGINX_CONF_SOURCE..."

if [ -f "$NGINX_CONF_SOURCE" ]; then
    sudo cp "$NGINX_CONF_SOURCE" "$NGINX_CONF_TARGET"
    
    if [ ! -L "$NGINX_ENABLED/papi.conf" ]; then
        log "🔗 Создаём симлинк для papi.conf"
        sudo ln -s "$NGINX_CONF_TARGET" "$NGINX_ENABLED/papi.conf"
    fi
    
    if sudo nginx -t; then
        log "✅ Конфиг Nginx корректен"
    else
        log "❌ Ошибка в конфиге Nginx"
        exit 1
    fi
else
    log "⚠️ Файл $NGINX_CONF_SOURCE не найден, пропускаем"
fi

# --- 6. Перезапуск сервисов ---
log "🔄 Перезапускаем сервисы..."

sudo systemctl restart "$BACKEND_SERVICE" || { log "❌ Ошибка перезапуска бэкенда"; exit 1; }
sudo systemctl reload nginx || { log "❌ Ошибка перезагрузки Nginx"; exit 1; }

# --- 7. Проверка работы (с ожиданием) ---
log "🔍 Проверяем работу сервисов..."

sleep 5

for i in 1 2 3; do
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8888/docs | grep -q "200"; then
        log "✅ Бэкенд отвечает (HTTP 200)"
        break
    else
        log "⚠️ Попытка $i: бэкенд ещё не отвечает, ждём 3 секунды..."
        sleep 3
    fi
done

if ! curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8888/docs | grep -q "200"; then
    log "⚠️ Бэкенд не отвечает, проверьте логи: journalctl -u $BACKEND_SERVICE -f"
fi

if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1 | grep -q "200"; then
    log "✅ Nginx отвечает (HTTP 200)"
else
    log "⚠️ Nginx не отвечает, проверьте логи: journalctl -u nginx -f"
fi

# --- Завершение ---
log "=========================================="
log "✅ Обновление успешно завершено!"
log "📋 Лог обновления: $LOG_FILE"
log "=========================================="