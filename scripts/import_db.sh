#!/bin/bash
# ============================================================
# Скрипт импорта данных в Docker-контейнеризированную PostgreSQL
# ============================================================
# Использование:
#   ./scripts/import_db.sh <путь_к_дампу>
#
# Типы поддерживаемых дампов:
#   - .dump (бинарный, создан pg_dump -Fc)
#   - .sql.gz (сжатый SQL)
#   - .sql (текстовый SQL)
#
# Примеры:
#   ./scripts/import_db.sh ./backups/papi_backup_20260926_140000.dump
#   ./scripts/import_db.sh ./backups/papi_backup_20260926_140000.sql.gz
#
# Переменные окружения (опционально):
#   DB_HOST      - Хост PostgreSQL (по умолчанию: localhost)
#   DB_PORT      - Порт PostgreSQL (по умолчанию: 5432)
#   DB_USER      - Пользователь (по умолчанию: papi)
#   DB_PASSWORD  - Пароль (или задайте через PGPASSWORD)
#   DB_NAME      - Имя базы (по умолчанию: papiDB)
# ============================================================

set -e

# --- Переменные ---
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-papidb}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# --- Проверка аргументов ---
if [ -z "$1" ]; then
    echo "❌ Ошибка: не указан путь к файлу дампа"
    echo ""
    echo "Использование: ./scripts/import_db.sh <путь_к_дампу>"
    echo ""
    echo "Поддерживаемые форматы:"
    echo "  - .dump   (бинарный, pg_dump -Fc)"
    echo "  - .sql.gz (сжатый SQL)"
    echo "  - .sql    (текстовый SQL)"
    exit 1
fi

DUMP_FILE="$1"

if [ ! -f "$DUMP_FILE" ]; then
    echo "❌ Ошибка: файл не найден: $DUMP_FILE"
    exit 1
fi

# --- Проверка Docker ---
if ! command -v docker &> /dev/null; then
    echo "❌ Ошибка: Docker не найден. Установите Docker."
    exit 1
fi

# --- Проверка контейнера ---
echo "🔍 Проверяю контейнер PostgreSQL..."

if ! docker ps --format '{{.Names}}' | grep -q "papi-db"; then
    echo "⚠️  Контейнер papi-db не запущен."
    echo "🚀 Запускаю Docker Compose..."
    
    if [ -f "docker-compose.yml" ]; then
        docker compose up -d db
    elif [ -f "docker-compose.yaml" ]; then
        docker compose up -d db
    else
        echo "❌ Ошибка: не найден docker-compose.yml"
        exit 1
    fi
    
    echo "⏳ Ожидание готовности PostgreSQL (до 60 секунд)..."
    retries=0
    while ! docker exec papi-db pg_isready -U "$DB_USER" -d "$DB_NAME" &> /dev/null; do
        sleep 5
        retries=$((retries + 1))
        if [ $retries -ge 12 ]; then
            echo "❌ Ошибка: PostgreSQL не запустился за 60 секунд"
            docker logs papi-db
            exit 1
        fi
    done
    echo "✅ PostgreSQL готов"
else
    echo "⏳ Проверяю готовность PostgreSQL..."
    retries=0
    while ! docker exec papi-db pg_isready -U "$DB_USER" -d "$DB_NAME" &> /dev/null; do
        sleep 5
        retries=$((retries + 1))
        if [ $retries -ge 12 ]; then
            echo "⚠️  База данных $DB_NAME может не существовать, создаю..."
            docker exec papi-db createdb -U "$DB_USER" "$DB_NAME" 2>/dev/null || true
            break
        fi
    done
    echo "✅ PostgreSQL готов"
fi

# --- Логирование ---
echo ""
echo "=========================================="
echo "🚀 Начинаю импорт данных"
echo "=========================================="
echo "Файл:    $DUMP_FILE"
echo "Хост:    $DB_HOST"
echo "Порт:    $DB_PORT"
echo "Пользователь: $DB_USER"
echo "База:    $DB_NAME"
echo "=========================================="

# --- Создание бэкапа текущей БД (если существует) ---
echo ""
echo "📦 Создаю резервную копию текущей БД перед импортом..."

BACKUP_BEFORE_IMPORT="$DB_NAME_restore_backup_$TIMESTAMP.dump"

if docker exec papi-db pg_isready -U "$DB_USER" -d "$DB_NAME" &> /dev/null; then
    PGPASSWORD="${DB_PASSWORD}" docker exec papi-db pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc -Z 9 > "$BACKUP_BEFORE_IMPORT" 2>/dev/null && \
        echo "✅ Резервная копия создана: $BACKUP_BEFORE_IMPORT" || \
        echo "⚠️  Текущая БД пуста или не существует (это нормально)"
else
    echo "⚠️  БД не доступна, пропускаю создание бэкапа"
fi

# --- Импорт ---
echo ""
echo "📦 Импортирую данные..."

FILE_EXTENSION="${DUMP_FILE##*.}"

case "$FILE_EXTENSION" in
    dump)
        echo "Использую бинарный формат (pg_restore)..."
        if [ -n "$DB_PASSWORD" ]; then
            PGPASSWORD="$DB_PASSWORD" docker exec -i papi-db pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists -c -C 2>&1 < "$DUMP_FILE"
        else
            docker exec -i papi-db pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists -c -C 2>&1 < "$DUMP_FILE"
        fi
        ;;
    
    gz)
        echo "Распаковываю и импортирую SQL..."
        if [ -n "$DB_PASSWORD" ]; then
            PGPASSWORD="$DB_PASSWORD" gunzip -c "$DUMP_FILE" | docker exec -i papi-db psql -U "$DB_USER" -d "$DB_NAME" 2>&1
        else
            gunzip -c "$DUMP_FILE" | docker exec -i papi-db psql -U "$DB_USER" -d "$DB_NAME" 2>&1
        fi
        ;;
    
    sql)
        echo "Импортирую SQL..."
        if [ -n "$DB_PASSWORD" ]; then
            PGPASSWORD="$DB_PASSWORD" docker exec -i papi-db psql -U "$DB_USER" -d "$DB_NAME" -f - 2>&1 < "$DUMP_FILE"
        else
            docker exec -i papi-db psql -U "$DB_USER" -d "$DB_NAME" -f - 2>&1 < "$DUMP_FILE"
        fi
        ;;
    
    *)
        echo "❌ Ошибка: неподдерживаемый формат файла: .$FILE_EXTENSION"
        echo "Поддерживаются: .dump, .sql.gz, .sql"
        exit 1
        ;;
esac

# --- Проверка результата ---
echo ""
echo "🔍 Проверяю результат импорта..."

TABLE_COUNT=$(docker exec papi-db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

echo "=========================================="
echo "✅ Импорт завершён!"
echo "📊 Таблиц в БД: $TABLE_COUNT"
echo "📋 Резервная копия перед импортом: $BACKUP_BEFORE_IMPORT"
echo "=========================================="
echo ""
echo "💡 Для перезапуска приложения выполните:"
echo "   docker compose up -d --build"
