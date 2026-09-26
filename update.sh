#!/bin/bash
# ============================================================
# Скрипт обновления и развёртывания проекта PAPI (docker compose)
# ============================================================
# Порядок: .env -> освобождение портов -> бэкап БД -> git reset --hard ->
# сборка образов -> docker compose up -d -> проверка здоровья db/backend/frontend.
#
# Запускать от root (или через sudo): нужны systemctl, docker и запись в /var/log.
#
# Приложение работает в контейнерах: backend, PostgreSQL и nginx. Хостовые venv,
# systemd-юнит papi-backend и сайт хостового nginx больше не нужны - скрипт сам
# их отключает, иначе публикация портов не проходит.
#
# .env в git не лежит (см. .gitignore), поэтому git reset его не трогает;
# недостающие ключи добавляются из .env.example, заполненные значения не меняются.
# ============================================================

set -e

# --- Переменные ---
# Каталог скрипта, а не жёсткий /opt/papi: проект можно держать в любом месте
PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
ENV_FILE="$PROJECT_DIR/.env"
ENV_EXAMPLE="$PROJECT_DIR/.env.example"
BACKUP_DIR="$PROJECT_DIR/backups"
BACKUP_KEEP=10                                # сколько pre-update дампов хранить
NGINX_ENABLED="/etc/nginx/sites-enabled"      # хостовой nginx - наследие до docker

# Лог в /var/log доступен только root; без его прав пишем в каталог проекта
LOG_FILE="/var/log/papi-update.log"
touch "$LOG_FILE" 2>/dev/null || LOG_FILE="$PROJECT_DIR/logs/update.log"
mkdir -p "$(dirname "$LOG_FILE")"

# --- Функция логирования ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Значение ключа из .env (берётся последнее объявление, кавычки отбрасываются)
env_value() {
    grep -E "^[[:space:]]*${1}=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"'
}

# --- Начало ---
log "=========================================="
log "🚀 Начинаем обновление проекта PAPI"
log "=========================================="

# --- 1. .env ---
# Файл нужен до первой команды docker: из него берутся POSTGRES_PASSWORD и порты.
if [ ! -f "$ENV_FILE" ]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    log "📝 Создан $ENV_FILE из .env.example - проверьте пароли и порты"
fi

# Файла мало: в .env от старой версии может не быть новых ключей, и тогда compose
# падает на ${POSTGRES_USER:?...}, а приложение получает пустой SECRET_KEY.
added=0
while IFS= read -r key; do
    [ -z "$key" ] && continue
    if ! grep -qE "^[[:space:]]*${key}=" "$ENV_FILE"; then
        grep -E "^[[:space:]]*${key}=" "$ENV_EXAMPLE" | head -1 >> "$ENV_FILE"
        added=$((added + 1))
    fi
done < <(grep -E '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=' "$ENV_EXAMPLE" | sed -E 's/^[[:space:]]*([A-Za-z0-9_]+)=.*/\1/' | sort -u)
if [ "$added" -gt 0 ]; then
    log "➕ В .env добавлено недостающих ключей: $added (значения из .env.example - замените своими)"
fi

# Порты из .env: нужны, чтобы проверить их занятость до запуска контейнеров
APP_PORT_VALUE=$(env_value APP_PORT);  APP_PORT_VALUE=${APP_PORT_VALUE:-80}
API_PORT_VALUE=$(env_value API_PORT);  API_PORT_VALUE=${API_PORT_VALUE:-8080}
POSTGRES_USER_VALUE=$(env_value POSTGRES_USER)
POSTGRES_DB_VALUE=$(env_value POSTGRES_DB)

# --- 1. Хостовые сервисы, которые держат наши порты ---
# Наследие до docker: backend был systemd-юнитом, сайт раздавал хостовый nginx.
# Пока они активны, публикация портов падает с "address already in use"
# (8888 юнит слушает сам, :80 занят хостовым nginx).
if systemctl list-unit-files --no-legend 2>/dev/null | grep -q '^papi-backend'; then
    log "🔧 Отключаю systemd-юнит papi-backend (backend работает в контейне)"
    systemctl stop papi-backend || true
    systemctl disable papi-backend || true
fi

# Файл хостового сайта могли установить под одним из двух имён
for site in "$NGINX_ENABLED/papi.conf" "$NGINX_ENABLED/inventory-system.conf"; do
    if [ -e "$site" ]; then
        log "🧹 Убираю хостовой сайт nginx: $site (фронтенд отдаёт контейнер)"
        rm -f "$site" || true
        nginx -t 2>/dev/null && systemctl reload nginx || true
    fi
done

if systemctl is-active --quiet nginx 2>/dev/null; then
    if [ -z "$(ls -A "$NGINX_ENABLED" 2>/dev/null)" ]; then
        log "🔧 Останавливаю хостовый nginx: :$APP_PORT_VALUE нужен контейнеру papi-frontend"
        systemctl stop nginx || true
        systemctl disable nginx || true
    else
        nginx -t && systemctl reload nginx || true
        log "ℹ️  Хостовый nginx оставлен (на нём другие сайты) - освободите :$APP_PORT_VALUE"
    fi
fi

# --- 2. Свободны ли порты, которые compose собирается опубликовать ---
for port in "$APP_PORT_VALUE" "$API_PORT_VALUE"; do
    holders=$(ss -ltnp "sport = :$port" 2>/dev/null | tail -n +2)
    [ -z "$holders" ] && continue
    # Порт может держать наш же контейнер (стек уже запущен) - это штатно:
    # compose пересоздаст привязку. Тревога только за чужие процессы.
    if echo "$holders" | grep -qE 'docker-proxy|dockerd|containerd'; then
        log "ℹ️  Порт $port занят docker-proxy (наши контейнеры) - так и должно быть"
        continue
    fi
    log "❌ Порт $port занят другим процессом:"
    echo "$holders" | tee -a "$LOG_FILE"
    log "   Освободите порт или поменяйте его в $ENV_FILE"
    exit 1
done

# --- 3. Есть ли что обновлять ---
# Скрипт запускается таймером каждые 15 минут. Без этой проверки каждая
# итерация пересобирала бы образы и перезапускала контейнеры, то есть
# приложение перезагружалось бы каждые 15 минут.
cd "$PROJECT_DIR" || { log "❌ Ошибка: не могу перейти в $PROJECT_DIR"; exit 1; }
BRANCH="${BRANCH:-main}"

if [ -d ".git" ]; then
    # git ругается на "dubious ownership", если репозиторий клонировали другим пользователем
    git config --global --add safe.directory "$PROJECT_DIR" || true
    if ! git fetch origin "$BRANCH"; then
        log "❌ git fetch не выполнился (нет сети или доступа к репозиторию) - оставляю текущую версию"
        exit 1
    fi

    local_rev=$(git rev-parse HEAD)
    remote_rev=$(git rev-parse "origin/$BRANCH")
    running=$(docker compose -f "$PROJECT_DIR/docker-compose.yml" ps --status running -q 2>/dev/null)

    if [ "$local_rev" = "$remote_rev" ] && [ -n "$running" ]; then
        log "✅ Обновлений нет ($remote_rev), контейнеры работают - ничего не делаю"
        exit 0
    fi

    if [ "$local_rev" != "$remote_rev" ]; then
        log "🔄 Есть изменения: ${local_rev:0:7} -> ${remote_rev:0:7}"
    else
        log "🔄 Изменений нет, но контейнеры не запущены - подниму стек"
    fi
else
    log "⚠️ $PROJECT_DIR не является git-репозиторием - обновление кода пропущено"
fi

# --- 4. Бэкап БД перед обновлением ---
# Если новая версия уже успела изменить схему, без дампа данные не вернуть.
mkdir -p "$BACKUP_DIR"
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^papi-db$'; then
    # Дамп сначала в файл, потом gzip: в пайпе "pg_dump | gzip" статус возвращает
    # gzip, и оборванный дамп выглядел бы успешным
    dump="$BACKUP_DIR/pre_update_$(date +%Y%m%d_%H%M%S).sql"
    if docker exec papi-db pg_dump -U "$POSTGRES_USER_VALUE" -d "$POSTGRES_DB_VALUE" > "$dump" \
        && gzip -f "$dump"; then
        log "💾 Бэкап БД перед обновлением: $dump.gz"
        # Храним только последние BACKUP_KEEP дампов: они по несколько сотен МБ
        ls -1t "$BACKUP_DIR"/pre_update_*.sql.gz 2>/dev/null | tail -n +$((BACKUP_KEEP + 1)) | xargs -r rm -f || true
    else
        rm -f "$dump" "$dump.gz"
        log "⚠️ Не удалось снять дамп БД - продолжаем без него"
    fi
else
    log "ℹ️  Контейнер papi-db не запущен - бэкап перед обновлением пропущен"
fi

# --- 5. Применение изменений кода ---
if [ -d ".git" ]; then
    # reset --hard вместо git pull: в каталоге лежат runtime-файлы (uploads, кэш),
    # из-за которых pull падает с "would be overwritten by merge".
    # .env и backups в git не входят (см. .gitignore), поэтому они остаются на месте.
    git reset --hard "origin/$BRANCH" || { log "❌ Ошибка обновления кода из git"; exit 1; }
fi

# Внутри контейнеров собираются и бэкенд (pip install из requirements.txt),
# и фронтенд (npm install + vite build, см. frontend/Dockerfile), поэтому
# отдельные venv/node_modules на хосте больше не нужны.
log "🐳 Пересобираем образы..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" build --pull 2>&1 | tee -a "$LOG_FILE"
# Статус пайпа даёт tee, поэтому на ошибку сборки смотрим через PIPESTATUS
build_rc=${PIPESTATUS[0]}
if [ "$build_rc" -ne 0 ]; then
    log "❌ Сборка образов завершилась с ошибкой (код $build_rc) - поднято предыдущее состояние контейнеров"
    exit 1
fi

log "🐳 Перезапускаем контейнеры..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d || { log "❌ Ошибка запуска контейнеров"; exit 1; }

# --- 6. Проверка работы (с ожиданием) ---
log "🔍 Проверяем работу сервисов..."

wait_for_http() {
    local url="$1" name="$2" hint="$3" i
    for i in 1 2 3 4 5; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
            log "✅ $name отвечает (HTTP 200)"
            return 0
        fi
        log "⚠️ Попытка $i: $name ещё не отвечает, ждём 3 секунды..."
        sleep 3
    done
    log "⚠️ $name не отвечает, проверьте логи: docker compose logs $hint"
    return 1
}

# Бэкенд проверяется через прямой порт контейнера, фронтенд - через nginx-контейнер
healthy=1
wait_for_http "http://127.0.0.1:$API_PORT_VALUE/docs" "бэкенд" "backend" || healthy=0
wait_for_http "http://127.0.0.1:$APP_PORT_VALUE" "фронтенд" "frontend" || healthy=0

docker compose -f "$PROJECT_DIR/docker-compose.yml" ps

# --- Завершение ---
log "=========================================="
if [ "$healthy" -eq 1 ]; then
    log "✅ Обновление успешно завершено!"
else
    log "⚠️  Код обновлён и контейнеры пересобраны, но часть сервисов не отвечает."
    log "    Это НЕ откат: посмотрите docker compose logs backend / frontend и повторите up -d."
fi
log "📋 Лог обновления: $LOG_FILE"
log "=========================================="