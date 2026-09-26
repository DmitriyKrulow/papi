# Скрипты управления PAPI

## Обзор

Этот каталог содержит скрипты для управления базой данных, бэкапами и обновлениями системы PAPI.

## Скрипты

### 1. export_db.sh — Экспорт базы данных

Экспортирует данные из текущей PostgreSQL в бэкап-файлы.

**Параметры по умолчанию:**
- Хост: `localhost`
- Порт: `5432`
- Пользователь: `postgres`
- База: `papidb`

**Использование:**

```bash
# С значениями по умолчанию
bash scripts/export_db.sh

# С явным указанием параметров
bash scripts/export_db.sh \
    --host localhost \
    --port 5432 \
    --user postgres \
    --db papidb
```

**Результат:**
- `backups/papi_backup_YYYYMMDD_HHMMSS.dump` — бинарный дамп (для восстановления)
- `backups/papi_backup_YYYYMMDD_HHMMSS.sql.gz` — SQL текст (для просмотра)

---

### 2. import_db.sh — Импорт в Docker

Импортирует бэкап в контейнеризированную PostgreSQL.

**Использование:**

```bash
# Импортировать бинарный дамп
bash scripts/import_db.sh ./backups/papi_backup_20260926_150000.dump

# Импортировать SQL дамп
bash scripts/import_db.sh ./backups/papi_backup_20260926_150000.sql.gz
```

**Поддерживаемые форматы:**
- `.dump` — бинарный (pg_restore)
- `.sql.gz` — сжатый SQL
- `.sql` — текстовый SQL

---

### 3. backup.sh — Автоматический бэкап

Создаёт полный бэкап системы: БД + файлы + конфигурация.

**Использование:**

```bash
# Запустить бэкап
bash scripts/backup.sh

# Установить срок хранения (по умолчанию: 30 дней)
RETENTION_DAYS=60 bash scripts/backup.sh
```

**Результат:**
```
backups/papi_full_backup_YYYYMMDD_HHMMSS/
├── database/papi_db.dump
├── files/uploads.tar.gz
├── config/.env
├── config/docker-compose.yml
└── backup_info.json
```

---

### 4. update.sh — Обновление из Git (Docker-контур)

`update.sh` в корне проекта: бэкап БД, `git pull`, синхронизация `.env` с
`.env.example`, пересборка образов, `docker compose up -d`, отключение старых
systemd-сервисов (`papi-backend`, `nginx`) и проверка здоровья `db`,
`backend`, `frontend` (nginx).

`scripts/update.sh` — такая же обёртка для запуска из каталога `scripts/`
(поднимается к корню проекта), а `scripts/update_docker.sh` — совместимость со
старыми ссылками и cron-задачами. Все три варианта вызывают один и тот же код.

**Использование:**

```bash
bash update.sh
```

---

## Настройка автоматического запуска (cron)

### Ежедневный бэкап в 2:00 ночи

```bash
crontab -e
```

Добавьте строку:

```cron
0 2 * * * cd /opt/papi && bash scripts/backup.sh >> /var/log/papi-backup.log 2>&1
```

### Ежедневное обновление в 3:00 ночи

```cron
0 3 * * * cd /opt/papi && bash update.sh >> /var/log/papi-update.log 2>&1
```

### Полный пример (файл scripts/papi.cron.example)

Смотрите `scripts/papi.cron.example` для полного примера cron-конфигурации.

---

## Переменные окружения

Все скрипты поддерживают переменные окружения:

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `PGPASSWORD` | Пароль PostgreSQL | Запрашивается интерактивно |
| `DB_HOST` | Хост БД | `localhost` |
| `DB_PORT` | Порт БД | `5432` |
| `DB_USER` | Пользователь БД | `postgres` |
| `DB_NAME` | Имя базы | `papidb` |
| `POSTGRES_PASSWORD` | Пароль для Docker | Из `.env` |
| `BACKUP_DIR` | Директория бэкапов | `./backups` |
| `RETENTION_DAYS` | Срок хранения бэкапов | `30` |
| `LOG_FILE` | Файл логов | `/var/log/papi-*.log` |

---

## Решение проблем

### Ошибка: "pg_dump not found"

Установите PostgreSQL client tools:

```bash
# Ubuntu/Debian
sudo apt install postgresql-client

# CentOS/RHEL
sudo yum install postgresql

# Windows
# Добавьте PostgreSQL\bin в PATH
```

### Ошибка: "docker: command not found"

Установите Docker: https://docs.docker.com/get-docker/

### Ошибка: "Connection refused"

Проверьте, что PostgreSQL запущен:

```bash
# Для локальной БД
pg_isready -h localhost -p 5432 -U postgres

# Для Docker
docker exec papi-db pg_isready -U postgres -d papidb
```
