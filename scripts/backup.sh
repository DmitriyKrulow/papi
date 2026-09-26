#!/bin/bash
# ============================================================
# Скрипт автоматического резервного копирования PAPI
# ============================================================
# Автоматически создаёт бэкапы:
#   - База данных (бинарный дамп PostgreSQL)
#   - Загруженные файлы (uploads/)
#   - Конфигурационные файлы (.env, docker-compose.yml)
#
# Хранит последние N дней бэкапов (по умолчанию: 30)
#
# Использование:
#   ./scripts/backup.sh
#
# Настройка cron (ежедневно в 2:00 ночи):
#   0 2 * * * /path/to/scripts/backup.sh >> /var/log/papi-backup.log 2>&1
# ============================================================

set -e

# --- Переменные ---
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_NAME="papi_full_backup_$TIMESTAMP"
LOG_FILE="${LOG_FILE:-/var/log/papi-backup.log}"

# --- Функция логирования ---
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# --- Начало ---
log "=========================================="
log "🚀 Начинаю автоматическое резервное копирование"
log "=========================================="
log "Директория бэкапов: $BACKUP_DIR"
log "Хранить дней: $RETENTION_DAYS"

# --- Создание директории ---
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
mkdir -p "$BACKUP_DIR/$BACKUP_NAME/database"
mkdir -p "$BACKUP_DIR/$BACKUP_NAME/files"
mkdir -p "$BACKUP_DIR/$BACKUP_NAME/config"

# --- 1. Бэкап базы данных ---
log "📦 Бэкап базы данных..."

if command -v docker &> /dev/null && docker ps --format '{{.Names}}' | grep -q "papi-db"; then
    # Docker-версия
    if [ -n "$POSTGRES_PASSWORD" ]; then
        PGPASSWORD="$POSTGRES_PASSWORD" docker exec papi-db pg_dump -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-papidb}" -Fc -Z 9 > "$BACKUP_DIR/$BACKUP_NAME/database/papi_db.dump" 2>/dev/null && \
            log "✅ Бэкап БД создан" || log "⚠️ Ошибка бэкапа БД"
    else
        docker exec papi-db pg_dump -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-papidb}" -Fc -Z 9 > "$BACKUP_DIR/$BACKUP_NAME/database/papi_db.dump" 2>/dev/null && \
            log "✅ Бэкап БД создан" || log "⚠️ Ошибка бэкапа БД"
    fi
elif command -v pg_dump &> /dev/null; then
    # Прямой доступ к PostgreSQL
    if [ -n "$PGPASSWORD" ]; then
        PGPASSWORD="$PGPASSWORD" pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-papidb}" -Fc -Z 9 > "$BACKUP_DIR/$BACKUP_NAME/database/papi_db.dump" 2>/dev/null && \
            log "✅ Бэкап БД создан" || log "⚠️ Ошибка бэкапа БД"
    else
        log "⚠️ PGPASSWORD не установлен, пропускаю бэкап БД"
    fi
else
    log "⚠️ PostgreSQL не найден, пропускаю бэкап БД"
fi

# --- 2. Бэкап загруженных файлов ---
log "📦 Бэкап файлов (uploads)..."

if [ -d "$PROJECT_DIR/backend/uploads" ]; then
    tar -czf "$BACKUP_DIR/$BACKUP_NAME/files/uploads.tar.gz" -C "$PROJECT_DIR/backend" uploads/ 2>/dev/null && \
        log "✅ Бэкап файлов создан" || log "⚠️ Ошибка бэкапа файлов"
elif docker ps --format '{{.Names}}' | grep -q "papi-backend"; then
    # Из Docker-контейнера
    docker cp papi-backend:/app/uploads "$BACKUP_DIR/$BACKUP_NAME/files/uploads" 2>/dev/null && \
        tar -czf "$BACKUP_DIR/$BACKUP_NAME/files/uploads.tar.gz" -C "$BACKUP_DIR/$BACKUP_NAME/files" uploads && \
        rm -rf "$BACKUP_DIR/$BACKUP_NAME/files/uploads" && \
        log "✅ Бэкап файлов создан" || log "⚠️ Ошибка бэкапа файлов"
else
    log "⚠️ Директория uploads не найдена, пропускаю"
fi

# --- 3. Бэкап конфигурации ---
log "📦 Бэкап конфигурации..."

# Копируем .env (если существует и не пустой)
if [ -f "$PROJECT_DIR/.env" ] && [ -s "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$BACKUP_DIR/$BACKUP_NAME/config/.env"
    log "✅ Конфигурация скопирована"
else
    log "⚠️ .env не найден или пуст, пропускаю"
fi

# Копируем docker-compose.yml
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    cp "$PROJECT_DIR/docker-compose.yml" "$BACKUP_DIR/$BACKUP_NAME/config/docker-compose.yml"
fi

if [ -f "$PROJECT_DIR/docker-compose.yaml" ]; then
    cp "$PROJECT_DIR/docker-compose.yaml" "$BACKUP_DIR/$BACKUP_NAME/config/docker-compose.yaml"
fi

# --- 4. Создание файла с метаданными ---
cat > "$BACKUP_DIR/$BACKUP_NAME/backup_info.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "retention_days": $RETENTION_DAYS,
    "components": {
        "database": "database/papi_db.dump",
        "files": "files/uploads.tar.gz",
        "config": "config/"
    },
    "restore_instructions": [
        "1. Остановите сервисы: docker compose down",
        "2. Восстановите БД: docker compose exec -i db pg_restore -U postgres -d papidb < backups/$BACKUP_NAME/database/papi_db.dump",
        "3. Восстановите файлы: docker compose cp backups/$BACKUP_NAME/files/uploads.tar.gz papi-backend:/app/uploads",
        "4. Запустите сервисы: docker compose up -d"
    ]
}
EOF

# --- 5. Очистка старых бэкапов ---
log "🧹 Очищаю бэкапы старше $RETENTION_DAYS дней..."

if [ -d "$BACKUP_DIR" ]; then
    old_backups=$(find "$BACKUP_DIR" -maxdepth 1 -type d -name "papi_full_backup_*" -mtime +$RETENTION_DAYS 2>/dev/null || true)
    
    if [ -n "$old_backups" ]; then
        echo "$old_backups" | while read -r old_backup; do
            log "🗑️ Удаляю старый бэкап: $(basename "$old_backup")"
            rm -rf "$old_backup"
        done
    else
        log "✅ Старые бэкапы не найдены"
    fi
fi

# --- Итоговая информация ---
log ""
log "=========================================="
log "✅ Резервное копирование завершено!"
log "📦 Путь к бэкапу: $BACKUP_DIR/$BACKUP_NAME"
log "=========================================="
log "Содержимое:"
log "  - database/papi_db.dump (база данных)"
log "  - files/uploads.tar.gz (загруженные файлы)"
log "  - config/ (конфигурация)"
log "  - backup_info.json (инструкции по восстановлению)"
log "=========================================="

# --- Вывод размера ---
if command -v du &> /dev/null; then
    total_size=$(du -sh "$BACKUP_DIR/$BACKUP_NAME" 2>/dev/null | cut -f1)
    log "📊 Размер бэкапа: $total_size"
fi
