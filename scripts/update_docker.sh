#!/bin/bash
# ============================================================
# Скрипт обновления проекта PAPI (Docker-версия)
# ============================================================
# Аналог update.sh, но для Docker-развёртывания.
#
# Использование:
#   ./scripts/update_docker.sh
#
# Автоматически:
#   1. Делает бэкап базы данных
#   2. Обновляет код из Git
#   3. Пересобирает и перезапускает контейнеры
#   4. Проверяет здоровье сервисов
#
# Для автоматического запуска через cron:
#   0 2 * * * /path/to/scripts/update_docker.sh >> /var/log/papi-docker-update.log 2>&1
# ============================================================

set -e

# --- Переменные ---
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GIT_REPO="${GIT_REPO:-origin}"
GIT_BRANCH="${GIT_BRANCH:-main}"
LOG_FILE="/var/log/papi-docker-update.log"
BACKUP_DIR="$PROJECT_DIR/backups"

# --- Функция логирования ---
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# --- Начало ---
log "=========================================="
log "🚀 Начинаем обновление PAPI (Docker)"
log "=========================================="

# --- 1. Бэкап базы данных ---
log "📦 Создаю бэкап базы данных..."

cd "$PROJECT_DIR" || { log "❌ Ошибка: не могу перейти в $PROJECT_DIR"; exit 1; }

if [ -f "scripts/export_db.sh" ]; then
    PGPASSWORD="${POSTGRES_PASSWORD}" bash scripts/export_db.sh \
        --host localhost \
        --port "${POSTGRES_PORT:-5432}" \
        --user "${POSTGRES_USER:-postgres}" \
        --db "${POSTGRES_DB:-papidb}" \
        --output "$BACKUP_DIR" || log "⚠️ Ошибка создания бэкапа (продолжаю)"
else
    log "⚠️ Скрипт export_db.sh не найден, пропускаю бэкап"
fi

# --- 2. Обновление кода из Git ---
log "🔄 Обновляем код из Git ($GIT_REPO/$GIT_BRANCH)..."

git config --global --add safe.directory "$PROJECT_DIR" || true

# Сохраняем локальные изменения
git stash push --include-untracked -m "Авто-сохранение перед обновлением $(date)" 2>/dev/null || log "⚠️ Нет изменений для stash"

# Обновление
if git pull "$GIT_REPO" "$GIT_BRANCH"; then
    log "✅ Код обновлён"
else
    log "❌ Ошибка git pull"
    git stash pop 2>/dev/null || true
    exit 1
fi

# Восстанавливаем изменения
git stash pop 2>/dev/null || log "⚠️ Конфликтов нет или они остались для ручного разрешения"

# --- 3. Пересборка и перезапуск контейнеров ---
log "📦 Пересобираю и перезапускаю контейнеры..."

if ! docker compose up -d --build; then
    log "❌ Ошибка пересборки контейнеров"
    exit 1
fi

log "✅ Контейнеры перезапущены"

# --- 4. Ожидание готовности ---
log "⏳ Ожидание готовности сервисов..."

sleep 10

# --- 5. Проверка PostgreSQL ---
log "🔍 Проверяю PostgreSQL..."

retries=0
while ! docker exec papi-db pg_isready -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-papidb}" &> /dev/null; do
    sleep 5
    retries=$((retries + 1))
    if [ $retries -ge 12 ]; then
        log "⚠️ PostgreSQL не ответил за 60 секунд"
        break
    fi
    log "⏳ Ожидание PostgreSQL... (попытка $retries)"
done

if docker exec papi-db pg_isready -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-papidb}" &> /dev/null; then
    log "✅ PostgreSQL отвечает"
else
    log "⚠️ PostgreSQL не отвечает, проверьте логи: docker logs papi-db"
fi

# --- 6. Проверка Backend ---
log "🔍 Проверяю Backend..."

BACKEND_PORT="${BACKEND_PORT:-8888}"
retries=0

for i in 1 2 3 4 5; do
    if docker exec papi-backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" 2>/dev/null; then
        log "✅ Backend отвечает (HTTP 200)"
        break
    else
        log "⏳ Попытка $i: Backend ещё не отвечает, ждём 5 секунд..."
        sleep 5
    fi
done

if ! docker exec papi-backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" 2>/dev/null; then
    log "⚠️ Backend не отвечает, проверьте логи: docker logs papi-backend"
fi

# --- 7. Проверка Frontend ---
log "🔍 Проверяю Frontend..."

APP_PORT="${APP_PORT:-80}"

if docker exec papi-frontend nginx -t &> /dev/null; then
    log "✅ Nginx конфиг корректен"
else
    log "⚠️ Nginx конфиг содержит ошибки"
fi

# --- Завершение ---
log "=========================================="
log "✅ Обновление успешно завершено!"
log "📋 Лог обновления: $LOG_FILE"
log "📦 Бэкапы в: $BACKUP_DIR"
log "=========================================="
