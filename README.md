# PAPI — Система управления активами

PAPI — полнофункциональная система управления активами с веб-интерфейсом, REST API и автоматическим SSL.

**Возможности:**
- Веб-интерфейс на React + Vite
- REST API на FastAPI (Python)
- PostgreSQL 16 для хранения данных
- Автоматическое получение SSL-сертификатов Let's Encrypt
- Автообновление из git каждые 15 минут
- Docker-контейнеризация всего стека

**Доступ:**
- Веб-приложение: `http://<IP>` или `https://<домен>` (после SSL)
- API Swagger: `http://<IP>:8080/docs`
- Администратор: `admin` / `admin123` (сразу смените пароль!)

## Запуск проекта через Docker Compose (рекомендуется)

Все пароли и секретные настройки хранятся в файле `.env` в корне проекта
(он игнорируется git). Шаблон со всеми переменными и пояснениями — `.env.example`.

### Развёртывание

1. Скопируйте шаблон и заполните своими значениями (как минимум
   `POSTGRES_PASSWORD` и `SECRET_KEY`):
   ```bash
   copy .env.example .env        # Windows
   cp .env.example .env          # Linux/macOS
   ```

   Сгенерируйте надёжный JWT-ключ:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

2. Соберите и запустите стек (PostgreSQL + FastAPI + nginx с фронтендом):
   ```bash
   docker compose up -d --build
   ```

3. Откройте `http://localhost` (порт настраивается переменной `APP_PORT` в `.env`).
   Первый запуск создаёт администратора: `admin` / `admin123` (смените пароль!).

### Полезные команды

| Команда | Действие |
|---|---|
| `docker compose logs -f backend` | логи бэкенда |
| `docker compose ps` | статус сервисов |
| `docker compose restart backend` | перезапуск бэкенда |
| `docker compose down` | остановка (данные сохраняются) |
| `docker compose down -v` | остановка + удаление томов с данными |

### Архитектура стека

- **db** — PostgreSQL 16, данные в named-томе `pgdata`; порт БД на хост не публикуется,
  backend подключается по внутреннему имени сервиса `db:5432`;
- **backend** — FastAPI (uvicorn, порт 8000 внутри сети), загружаемые файлы в томе `uploads_data`;
  публикуется на`${API_PORT:-8080}` (настраивается через `.env`);
- **frontend** — собранная Vite-сборка за nginx; `/api/`, `/ws/`, `/docs`, `/openapi.json`
  проксируются на backend. Наружу публикуется порт `APP_PORT` (по умолчанию 80).

---

## Обновление проекта

### На продакшен-сервере

```bash
sudo bash update.sh
```

Скрипт (запускать от root — нужны docker, systemctl и запись в `/var/log`):

1. создаёт `.env` из `.env.example`, если файла нет, и дописывает недостающие
   ключи (существующие значения не трогаются);
2. отключает хостовые сервисы, которые держат наши порты: systemd-юнит
   `papi-backend` и хостовой nginx с его сайтом;
3. проверяет, что порты `APP_PORT` и `API_PORT` свободны;
4. снимает дамп БД в `backups/pre_update_<дата>.sql.gz` (хранится 10 последних);
5. обновляет код `git fetch` + `git reset --hard origin/main`;
6. пересобирает образы и поднимает контейнеры;
7. проверяет доступность бэкенда (`/docs`) и фронтенда, печатает `docker compose ps`.

Лог — `/var/log/papi-update.log` (если прав не хватает — `logs/update.log` в проекте).

### Автоматическое обновление (systemd timer)

При развёртывании через `deploy/ubuntu/install.sh` устанавливается таймер
`papi-update.timer`, который проверяет git каждые 15 минут.

### Скрипты для бэкапов и импорта

В директории `scripts/` находятся вспомогательные утилиты:

| Скрипт | Описание |
|---|---|
| `backup.sh` | Полный бэкап: БД + загрузки + конфиги |
| `export_db.sh` | Экспорт дампа PostgreSQL |
| `import_db.sh` | Импорт дампа в Docker PostgreSQL |
| `update.sh` | Обёртка для основного скрипта обновления |
| `papi.cron.example` | Пример cron-конфигурации |

Подробнее — `scripts/README.md`.

---

## Развёртывание на новом сервере

### Ubuntu / Debian

```bash
wget -qO- https://api.github.com/repos/DmitriyKrulow/papi/contents/deploy/ubuntu/install.sh | python3 -c "import sys,base64,json; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" | sudo bash
```

Скрипт делает всё автоматически:

1. Устанавливает **Git, Python3, Docker Engine** с mirror-ами (для серверов в РФ)
2. Клонирует репозиторий в `/opt/papi`
3. Создаёт `.env` с сгенерированными паролями (если файла нет)
4. Отключает конфликтующие сервисы (хостовой nginx, старый papi-backend)
5. Устанавливает systemd-юниты: `papi.service` (стек при загрузке) и `papi-update.timer` (автообновление)
6. Собирает Docker-образы и поднимает контейнеры
7. Настраивает firewall: наружу доступны только 22 (SSH), 80 (HTTP), 8080 (API)

**Как работает HTTPS:**
- Сайт сразу открывается по **HTTP** — без ожидания
- В фоне (через 5 сек) начинается получение SSL-сертификата Let's Encrypt
- После успешного получения — автоматический переход на **HTTPS** с редиректом
- Сертификат автоматически обновляется за 30 дней до истечения
- До 5 повторных попыток при ошибке (rate limit)

> **Примечание:** Для корректной работы HTTPS домен должен указывать на IP сервера (A-запись), а порт 80 — быть открытым в фаерволе.

#### Параметры

```bash
# Кастомный репозиторий
REPO_URL=https://github.com/user/repo.git bash -

# Кастомная ветка
BRANCH=develop bash -

# Другая директория
PROJECT_DIR=/opt/myapp bash -

# Пропустить настройку firewall
SKIP_FIREWALL=1 bash -

# Приватный репозиторий (с токеном)
GITHUB_TOKEN=ghp_xxxx bash -
```

### Windows Server

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
powershell -File deploy\windows\install.ps1
```

Скрипт делает:
1. Проверяет Docker Desktop (установите если нет)
2. Клонирует репозиторий в `C:\papi`
3. Создаёт `.env` с паролями
4. Освобождает порт 80 (останавливает IIS если нужен)
5. Регистрирует задачи планировщика: `PAPI-Start` (автостарт) и `PAPI-Update` (автообновление)
6. Открывает порты 80 и 8080 в брандмауэре
7. Собирает образы и поднимает контейнеры

> **Примечание:** Docker Desktop должен быть установлен и работать. Для серверов без GUI — используйте Ubuntu.

---

## После установки

### 1. Проверка

```bash
# Статус контейнеров
docker compose ps

# Логи
docker compose logs -f frontend   # веб-интерфейс
docker compose logs -f backend    # API
```

### 2. Вход в систему

- **URL:** `http://<IP-сервера>` (HTTP работает сразу)
- **Логин:** `admin`
- **Пароль:** `admin123`
- ⚠️ **Сразу смените пароль в настройках!**

### 3. HTTPS

Сайт автоматически переключится на HTTPS после получения сертификата Let's Encrypt (~1-2 минуты).

**Условия для HTTPS:**
- Домен настроен (A-запись на IP сервера)
- Порт 80 открыт в фаерволе
- Email для сертификата указан в `.env`: `LETSENCRYPT_EMAIL=your@email.com`

### 4. Настройка `.env`

```bash
sudo nano /opt/papi/.env
```

Основные параметры:
| Параметр | Описание |
|---|---|
| `APP_PORT` | Порт веб-интерфейса (по умолч. 80) |
| `API_PORT` | Порт API (по умолч. 8080) |
| `CORS_ORIGINS` | Домены для CORS (через запятую) |
| `FRONTEND_URL` | URL фронтенда |
| `LETSENCRYPT_EMAIL` | Email для SSL-сертификатов |
| `SMTP_*` | Настройки отправки почты |

После изменений: `sudo systemctl restart papi`

### 5. Обновление

```bash
# Ручное обновление
sudo bash /opt/papi/update.sh

# Автообновление каждые 15 минут (по умолчанию)
systemctl list-timers papi-update
```

### 6. Полезные команды

```bash
# Стек
systemctl status papi                    # статус сервиса
sudo systemctl restart papi              # перезапуск
sudo systemctl stop papi                 # остановка

# Контейнеры
docker compose ps                        # статус
docker compose logs -f backend           # логи API
docker compose logs -f frontend          # логи веб
docker compose down                      # остановить
docker compose down -v                   # остановить + удалить данные

# Автообновление
systemctl list-timers papi-update        # расписание
journalctl -u papi-update -f             # лог обновлений
```

---

## Запуск проекта локально (без Docker)

### Требования

- Python 3.12+
- Node.js 18+
- PostgreSQL (локально или Docker)

### Бэкенд

1. Перейдите в директорию `backend/`:
   ```bash
   cd backend
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Настройте переменные окружения (создайте `.env` на основе `.env.example`):

4. Запустите сервер:
   ```bash
   python -m src.infrastructure.main
   ```
   или
   ```bash
   python main.py
   ```

   Сервер запустится на `http://127.0.0.1:8888`.

    > **Примечание:** При использовании `python main.py` включён `reload=True` для автоматической перезагрузки при изменении файлов.

### Фронтенд

1. Перейдите в директорию `frontend/`:
   ```bash
   cd frontend
   ```

2. Установите зависимости:
   ```bash
   npm install
   ```

3. Запустите dev-сервер:
   ```bash
   npm run dev
   ```

   Фронтенд запустится на `http://localhost:5173`.

---

## Известные предупреждения

- **FastAPI `on_event`** — в `main.py` используется устаревший декоратор `@app.on_event()`. Рекомендуется перейти на lifespan-хендлеры: [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
- **npm audit (react-router)** — уязвимость `GHSA-qwww-vcr4-c8h2` затронуто версии `>=7.12.0, <8.3.0`. Текущая версия `7.11.0` **не уязвима**. Когда появится версия `8.3.0`, обновитесь через `npm install react-router-dom@latest`.
