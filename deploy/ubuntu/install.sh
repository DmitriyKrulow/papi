#!/bin/bash
# ============================================================
# Установка PAPI на сервер Ubuntu (22.04 / 24.04) с нуля
# ============================================================
# Что делает скрипт:
#   1. ставит Docker Engine и плагин docker compose (если их нет);
#   2. включает автозапуск docker - без него контейнеры не поднимутся после
#      перезагрузки сервера;
#   3. клонирует репозиторий в /opt/papi (или обновляет существующий);
#   4. создаёт .env из .env.example и генерирует пароли/секреты;
#   5. отключает хостовые nginx и старый systemd-юнит papi-backend - они держат
#      порт 80, который нужен контейнеру;
#   6. устанавливает systemd-юниты: papi.service (стек при загрузке) и
#      papi-update.timer (автообновление из git);
#   7. собирает образы и поднимает контейнеры;
#   8. настраивает firewall: снаружи доступны ТОЛЬКО 22 (SSH), 80 и 8080.
#
# Запуск (из-под root или через sudo):
#   sudo bash deploy/ubuntu/install.sh
#
# Параметры окружения:
#   REPO_URL   - адрес git-репозитория (по умолчанию публичный адрес проекта)
#   BRANCH     - ветка (по умолчанию main)
#   PROJECT_DIR- каталог установки (по умолчанию /opt/papi)
#   SKIP_FIREWALL=1 - не трогать ufw
# ============================================================

set -e

# По умолчанию клонируем из этого репозитория.
# Можно переопределить: REPO_URL=https://github.com/user/repo.git bash $0
REPO_URL="${REPO_URL:-https://github.com/DmitriyKrulow/papi.git}"
BRANCH="${BRANCH:-main}"
PROJECT_DIR="${PROJECT_DIR:-/opt/papi}"
SKIP_FIREWALL="${SKIP_FIREWALL:-0}"
APP_PORT_DEFAULT=80
API_PORT_DEFAULT=8080

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# ---------------------------------------------------------------------------
# Если скрипт запущен из stdin (wget -qO- ... | bash), DEPLOY_DIR будет
# указывать на текущий каталог, а не на deploy/ubuntu/. Скачаем юнит-файлы.
# ---------------------------------------------------------------------------
DEPLOY_FILES_MISSING=0
for f in papi.service papi-update.service papi-update.timer; do
    if [ ! -f "$DEPLOY_DIR/$f" ]; then
        DEPLOY_FILES_MISSING=1
        break
    fi
done

if [ "$DEPLOY_FILES_MISSING" = "1" ]; then
    log "Скрипт запущен из stdin — скачиваю systemd-юниты из репозитория"
    TMP_DEPLOY=$(mktemp -d)
    for f in papi.service papi-update.service papi-update.timer; do
        wget -q "https://raw.githubusercontent.com/DmitriyKrulow/papi/deploy/ubuntu/$f" -O "$TMP_DEPLOY/$f" 2>/dev/null || true
    done
    if [ -f "$TMP_DEPLOY/papi.service" ]; then
        DEPLOY_DIR="$TMP_DEPLOY"
        log "Юнит-файлы загружены во временную директорию"
    fi
fi

# ---------------------------------------------------------------------------
# Определяем URL для git
# ---------------------------------------------------------------------------
# Если REPO_URL уже содержит токен — используем как есть
if echo "$REPO_URL" | grep -q "x-access-token@"; then
    RESOLVED_URL="$REPO_URL"
    log "Используем REPO_URL с токеном"
# Пробуем SSH — если есть приватный ключ
elif [ -f "$HOME/.ssh/id_ed25519" ] || [ -f "$HOME/.ssh/id_rsa" ]; then
    log "Найден SSH-ключ — используем SSH"
    RESOLVED_URL=$(echo "$REPO_URL" | sed 's|https://github.com/|git@github.com:|; s|\.git$||')
# Если токен передан через переменную — подставляем
elif [ -n "${GITHUB_TOKEN:-}" ]; then
    log "Используем GITHUB_TOKEN из окружения"
    RESOLVED_URL="https://x-access-token:${GITHUB_TOKEN}@github.com$(echo "$REPO_URL" | sed 's|https://github.com/||')"
# Для публичных репозиториев — обычный HTTPS (без авторизации)
else
    log "Используем HTTPS (публичный репозиторий)"
    RESOLVED_URL="$REPO_URL"
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "Запустите с правами root: sudo bash $0"
    exit 1
fi

# ---------------------------------------------------------------------------
log "1/8. Проверка Docker и Git"
# ---------------------------------------------------------------------------
# Git нужен для клонирования репозитория
if command -v git >/dev/null 2>&1; then
    log "Git уже установлен: $(git --version)"
else
    log "Git не найден - устанавливаю"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y git
fi

if command -v docker >/dev/null 2>&1; then
    log "Docker уже установлен: $(docker --version)"
else
    log "Docker не найден - устанавливаю из репозитория Ubuntu"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    # docker.io - движок из репозитория Ubuntu, docker-compose-v2 - плагин
    # `docker compose` (без суффикса). Пакет `docker-compose` (v1, отдельный
    # бинарник) не подходит: compose-файл использует синтаксис `name:`.
    apt-get install -y docker.io docker-compose-v2 curl
fi

if ! docker compose version >/dev/null 2>&1; then
    log "Плагин `docker compose` не найден - ставлю docker-compose-v2"
    export DEBIAN_FRONTEND=noninteractive
    apt-get install -y docker-compose-v2
fi

# Ключевое для автостарта: демон должен стартовать сам при загрузке системы.
systemctl enable docker
systemctl start docker
log "Docker активен и включён в автозапуск"

# ---------------------------------------------------------------------------
log "2/8. Код проекта в $PROJECT_DIR"
# ---------------------------------------------------------------------------
if [ -d "$PROJECT_DIR/.git" ]; then
    log "Репозиторий уже клонирован - обновляю"
    git config --global --add safe.directory "$PROJECT_DIR" || true
    # Обновляем remote URL на аутентифицированный (если нужно)
    current_url=$(git -C "$PROJECT_DIR" remote get-url origin)
    if [ "$current_url" != "$RESOLVED_URL" ]; then
        log "Обновляю URL origin"
        git -C "$PROJECT_DIR" remote set-url origin "$RESOLVED_URL"
    fi
    git -C "$PROJECT_DIR" fetch origin "$BRANCH"
    # Проверяем, существует ли remote-ветка
    if git -C "$PROJECT_DIR" show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
        git -C "$PROJECT_DIR" reset --hard "origin/$BRANCH"
    else
        log "Remote-ветка origin/$BRANCH не найдена — используем FETCH_HEAD"
        git -C "$PROJECT_DIR" reset --hard FETCH_HEAD
    fi
elif [ -d "$PROJECT_DIR" ] && [ -n "$(ls -A "$PROJECT_DIR" 2>/dev/null)" ]; then
    echo "Каталог $PROJECT_DIR непустой и не является git-репозиторием."
    echo "Освободите его или укажите другой каталог: PROJECT_DIR=/opt/papi2 sudo bash $0"
    exit 1
else
    log "Клонирую $RESOLVED_URL ($BRANCH) в $PROJECT_DIR"
    # Сначала пробуем с --branch, если ветка не существует — без неё
    if ! git clone --branch "$BRANCH" "$RESOLVED_URL" "$PROJECT_DIR" 2>/dev/null; then
        log "Ветка $BRANCH не найдена — клонирую без указания ветки"
        git clone "$RESOLVED_URL" "$PROJECT_DIR"
    fi
fi

# Скрипты должны быть исполняемыми и с unix-переводами строк.
chmod +x "$PROJECT_DIR/update.sh" "$PROJECT_DIR/scripts/"*.sh 2>/dev/null || true

# ---------------------------------------------------------------------------
log "3/8. Файл настроек .env"
# ---------------------------------------------------------------------------
ENV_FILE="$PROJECT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    log ".env уже есть - существующие пароли и секреты не трогаю"
else
    cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
    chmod 600 "$ENV_FILE"

    # Значения из .env.example годятся только для разработки: пустой пароль БД
    # и константный SECRET_KEY в продакшене недопустимы.
    DB_PASS=$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)
    JWT_KEY=$(openssl rand -hex 48)
    sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${DB_PASS}|" "$ENV_FILE"
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${JWT_KEY}|" "$ENV_FILE"
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg2://postgres:${DB_PASS}@localhost:5432/papidb|" "$ENV_FILE"

    log ".env создан, сгенерированы POSTGRES_PASSWORD и SECRET_KEY"
    log "Проверьте CORS_ORIGINS и FRONTEND_URL - там указан http://localhost"
fi

APP_PORT_VALUE=$(grep -E '^APP_PORT=' "$ENV_FILE" | tail -1 | cut -d= -f2-)
API_PORT_VALUE=$(grep -E '^API_PORT=' "$ENV_FILE" | tail -1 | cut -d= -f2-)
APP_PORT_VALUE=${APP_PORT_VALUE:-$APP_PORT_DEFAULT}
API_PORT_VALUE=${API_PORT_VALUE:-$API_PORT_DEFAULT}

# ---------------------------------------------------------------------------
log "4/8. Освобождение порта $APP_PORT_VALUE от хостовых сервисов"
# ---------------------------------------------------------------------------
# Наследие до docker: приложение крутилось как systemd-юнит papi-backend, а
# фронтенд раздавал хостовой nginx. Пока они активны, контейнер не сможет
# занять порт 80 ("address already in use").
if systemctl list-unit-files --no-legend 2>/dev/null | grep -q '^papi-backend'; then
    log "Отключаю systemd-юнит papi-backend"
    systemctl stop papi-backend || true
    systemctl disable papi-backend || true
fi

if systemctl list-unit-files --no-legend 2>/dev/null | grep -q '^nginx'; then
    if [ -e /etc/nginx/sites-enabled/papi.conf ]; then
        log "Снимаю хостовой сайт papi.conf"
        rm -f /etc/nginx/sites-enabled/papi.conf
    fi
    other_sites=$(ls -A /etc/nginx/sites-enabled 2>/dev/null | wc -l)
    if [ "$other_sites" -eq 0 ]; then
        log "Останавливаю хостовой nginx - порт $APP_PORT_VALUE нужен контейнеру"
        systemctl stop nginx || true
        systemctl disable nginx || true
    else
        log "ВНИМАНИЕ: на хостовом nginx висят ещё $other_sites сайт(ов), не останавливаю."
        log "Пока он держит :$APP_PORT_VALUE, контейнер papi-frontend не запустится."
    fi
fi

# ---------------------------------------------------------------------------
log "5/8. Systemd-юниты: старт при загрузке и автообновление"
# ---------------------------------------------------------------------------
# Размаскируем и удаляем старый юнит (может быть symlink на /dev/null)
systemctl stop papi.service 2>/dev/null || true
rm -f /etc/systemd/system/papi.service
rm -f /etc/systemd/system/papi-update.service
rm -f /etc/systemd/system/papi-update.timer
cp "$DEPLOY_DIR/papi.service" /etc/systemd/system/papi.service
cp "$DEPLOY_DIR/papi-update.service" /etc/systemd/system/papi-update.service
cp "$DEPLOY_DIR/papi-update.timer" /etc/systemd/system/papi-update.timer
# Пути внутри юнитов захвачены каталогом установки, если он отличается от /opt/papi
if [ "$PROJECT_DIR" != "/opt/papi" ]; then
    sed -i "s|/opt/papi|$PROJECT_DIR|g" /etc/systemd/system/papi.service \
                                          /etc/systemd/system/papi-update.service
fi
systemctl daemon-reload
systemctl enable papi.service papi-update.timer
systemctl start papi-update.timer
log "papi.service включён (старт стека при загрузке)"
log "papi-update.timer включён (автообновление из git каждые 15 минут)"

# ---------------------------------------------------------------------------
log "6/8. Сборка и запуск контейнеров"
# ---------------------------------------------------------------------------
cd "$PROJECT_DIR"
docker compose up -d --build

# ---------------------------------------------------------------------------
log "7/8. Firewall: наружу только SSH, $APP_PORT_VALUE и $API_PORT_VALUE"
# ---------------------------------------------------------------------------
# Публикуемые docker порты обходят ufw (docker пишет свои цепочки iptables
# напрямую), поэтому список открытых портов задаётся в docker-compose.yml:
# там опубликованы ровно APP_PORT и API_PORT. Ufw закрывает всё остальное
# (в том числе 5432, если его когда-нибудь раскомментируют без привязки к 127.0.0.1).
if [ "$SKIP_FIREWALL" = "1" ]; then
    log "Пропущено (SKIP_FIREWALL=1)"
elif command -v ufw >/dev/null 2>&1 || apt-get install -y ufw >/dev/null 2>&1; then
    ufw allow OpenSSH comment 'SSH доступ'
    ufw allow "${APP_PORT_VALUE}/tcp" comment 'PAPI: веб-интерфейс' 2>/dev/null
    ufw allow "${API_PORT_VALUE}/tcp" comment 'PAPI: API' 2>/dev/null
    ufw default deny incoming
    ufw default allow outgoing
    # ufw ask может столкнуть с интерактивного ввода при первом включении
    ufw --force enable
    log "Правила ufw:"
    ufw status verbose | sed 's/^/    /'
else
    log "Не удалось установить ufw - откройте порты вручную"
fi

# Очистка временной директории (если скачивали юнит-файлы)
if [ -n "${TMP_DEPLOY:-}" ] && [ -d "${TMP_DEPLOY:-}" ]; then
    rm -rf "$TMP_DEPLOY"
fi

# ---------------------------------------------------------------------------
log "8/8. Итог"
# ---------------------------------------------------------------------------
sleep 5
docker compose ps
echo ""
echo "Веб-интерфейсы:"
echo "  приложение : http://$(hostname -I | awk '{print $1}'):$APP_PORT_VALUE"
echo "  API (docs) : http://$(hostname -I | awk '{print $1}'):$API_PORT_VALUE/docs"
echo ""
echo "Полезные команды:"
echo "  systemctl status papi                 # стек при загрузке"
echo "  systemctl list-timers papi-update     # следующее автообновление"
echo "  journalctl -u papi-update -f          # лог автообновления"
echo "  docker compose logs -f backend        # лог приложения"
echo "  sudo bash $PROJECT_DIR/update.sh      # обновиться вручную"
