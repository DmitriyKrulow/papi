# PAPI — Система управления активами

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

### Ubuntu

#### Вариант 1 — без токена (SSH-ключ на сервере)

```bash
wget -qO- https://api.github.com/repos/DmitriyKrulow/papi/contents/deploy/ubuntu/install.sh | python3 -c "import sys,base64,json; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" | sudo bash
```

Скрипт автоматически найдёт SSH-ключ и использует его.

#### Вариант 2 — с Personal Access Token

```bash
GITHUB_TOKEN=ghp_ваш_токен wget -qO- https://api.github.com/repos/DmitriyKrulow/papi/contents/deploy/ubuntu/install.sh | python3 -c "import sys,base64,json; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" | sudo bash
```

#### Вариант 3 — интерактивный (скрипт попросит токен)

```bash
wget -qO- https://api.github.com/repos/DmitriyKrulow/papi/contents/deploy/ubuntu/install.sh | python3 -c "import sys,base64,json; print(base64.b64decode(json.load(sys.stdin)['content']).decode())" | sudo bash
```

Скрипт установит Git и Docker, клонирует репозиторий, сгенерирует `.env`,
создаст systemd-юниты и настроит firewall.

> **Как создать токен:**
> 1. Откройте https://github.com/settings/tokens/new
> 2. Name: любой (например `server-ubuntu`)
> 3. Permissions: поставьте галочку **`repo`** (полный доступ к репозиториям)
> 4. Нажмите **Generate token** внизу
> 5. Скопируйте токен (начинается с `ghp_`)

#### После установки

1. **Проверьте статус сервисов:**
   ```bash
   systemctl status papi
   docker compose ps
   ```

2. **Откройте веб-интерфейс:**
   ```bash
   echo "http://$(hostname -I | awk '{print $1}'):$APP_PORT_VALUE"
   ```
   По умолчанию: `http://<IP-сервера>:80`

3. **Войдите под администратором:**
   - Логин: `admin`
   - Пароль: `admin123`
   - **Сразу смените пароль в настройках!**

4. **Настройте `.env` (при необходимости):**
   ```bash
   sudo nano /opt/papi/.env
   ```
   Основные параметры:
   - `CORS_ORIGINS` — домены, которым разрешён CORS
   - `FRONTEND_URL` — URL фронтенда
   - `SMTP_*` — настройки почты (если нужны)

   После изменений:
   ```bash
   sudo systemctl restart papi
   ```

5. **Проверьте логи:**
   ```bash
   docker compose logs -f backend   # логи бэкенда
   docker compose logs -f frontend  # логи фронтенда
   journalctl -u papi -f            # логи systemd
   ```

6. **Обновление:**
   ```bash
   sudo bash /opt/papi/update.sh
   ```
   Или дождитесь автообновления (каждые 15 минут).

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File deploy\windows\install.ps1
```

Аналогичный сценарий для Windows: Docker Desktop, git, `.env`,
планировщик задач для автозапуска и обновления.

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
