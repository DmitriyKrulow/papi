#!/bin/bash
# ============================================================
# Скрипт экспорта данных из текущей PostgreSQL
# ============================================================
# Использование:
#   ./scripts/export_db.sh [опции]
#
# Опции:
#   --host HOST         Хост PostgreSQL (по умолчанию: localhost)
#   --port PORT         Порт PostgreSQL (по умолчанию: 5432)
#   --user USER         Пользователь PostgreSQL (по умолчанию: papi)
#   --db DB             Имя базы данных (по умолчанию: papiDB)
#   --password PASS     Пароль (или задайте через PGPASSWORD)
#   --output DIR        Директория для сохранения дампов (по умолчанию: ./backups)
#
# Примеры:
#   PGPASSWORD=mypassword ./scripts/export_db.sh
#   ./scripts/export_db.sh --host 192.168.1.100 --port 5433 --user admin --db mydb
# ============================================================

set -e

# --- Переменные по умолчанию ---
HOST="localhost"
PORT="5432"
USER="postgres"
DB="papidb"
OUTPUT_DIR="./backups"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="$OUTPUT_DIR/papi_backup_$TIMESTAMP.sql.gz"

# --- Парсинг аргументов ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --host) HOST="$2"; shift 2 ;;
        --port) PORT="$2"; shift 2 ;;
        --user) USER="$2"; shift 2 ;;
        --db) DB="$2"; shift 2 ;;
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        --help)
            head -20 "$0" | grep '^#' | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "Неизвестный аргумент: $1"; exit 1 ;;
    esac
done

# --- Проверка pg_dump ---
if ! command -v pg_dump &> /dev/null; then
    echo "❌ Ошибка: pg_dump не найден. Установите PostgreSQL client tools."
    echo "   Ubuntu/Debian: sudo apt install postgresql-client"
    echo "   CentOS/RHEL:   sudo yum install postgresql-contrib"
    echo "   Windows: Добавьте PostgreSQL\\bin в PATH"
    exit 1
fi

# --- Создание директории ---
mkdir -p "$OUTPUT_DIR"

# --- Логирование ---
echo "=========================================="
echo "🚀 Начинаем экспорт базы данных"
echo "=========================================="
echo "Хост:    $HOST"
echo "Порт:    $PORT"
echo "Пользователь: $USER"
echo "База:    $DB"
echo "Файл:    $BACKUP_FILE"
echo "=========================================="

# --- Экспорт ---
echo "📦 Создаю дамп..."

if [ -n "$PGPASSWORD" ]; then
    PGPASSWORD="$PGPASSWORD" pg_dump -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -Fc -Z 9 > "$OUTPUT_DIR/papi_backup_$TIMESTAMP.dump" 2>&1
    echo "✅ Бинарный дамп сохранён: $OUTPUT_DIR/papi_backup_$TIMESTAMP.dump"
else
    echo "⚠️  PGPASSWORD не установлен. Будет запрошен пароль интерактивно."
    pg_dump -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -Fc -Z 9 > "$OUTPUT_DIR/papi_backup_$TIMESTAMP.dump" 2>&1
    echo "✅ Бинарный дамп сохранён: $OUTPUT_DIR/papi_backup_$TIMESTAMP.dump"
fi

# --- Создание текстового дампа (опционально) ---
echo "📦 Создаю SQL дамп (текстовый)..."

if [ -n "$PGPASSWORD" ]; then
    PGPASSWORD="$PGPASSWORD" pg_dump -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" --no-owner --no-privileges -Z 9 | gzip > "$BACKUP_FILE"
else
    pg_dump -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" --no-owner --no-privileges -Z 9 | gzip > "$BACKUP_FILE"
fi

echo "✅ SQL дамп сохранён: $BACKUP_FILE"

# --- Информация о размере ---
echo ""
echo "📊 Размер бэкапов:"
ls -lh "$OUTPUT_DIR/papi_backup_$TIMESTAMP.dump" 2>/dev/null || true
ls -lh "$BACKUP_FILE" 2>/dev/null || true

# --- Создание файла с метаданными ---
cat > "$OUTPUT_DIR/backup_metadata_$TIMESTAMP.json" << EOF
{
    "timestamp": "$TIMESTAMP",
    "source": {
        "host": "$HOST",
        "port": $PORT,
        "user": "$USER",
        "database": "$DB"
    },
    "files": {
        "binary": "papi_backup_$TIMESTAMP.dump",
        "sql": "papi_backup_$TIMESTAMP.sql.gz"
    }
}
EOF

echo ""
echo "✅ Экспорт успешно завершён!"
echo "📋 Файлы бэкапа:"
echo "   - $OUTPUT_DIR/papi_backup_$TIMESTAMP.dump (бинарный, для восстановления)"
echo "   - $BACKUP_FILE (SQL текст, для просмотра/редактирования)"
echo "   - $OUTPUT_DIR/backup_metadata_$TIMESTAMP.json (метаданные)"
echo "=========================================="
