# Руководство по миграции PAPI: Bare-Metal → Docker

## Содержание

1. [Подготовка](#подготовка)
2. [Экспорт данных из текущей БД](#экспорт-данных-из-текущей-бд)
3. [Настройка Docker-окружения](#настройка-docker-окружения)
4. [Импорт данных в Docker-БД](#импорт-данных-в-docker-бд)
5. [Настройка автоматических обновлений](#настройка-автоматических-обновлений)
6. [Настройка автоматических бэкапов](#настройка-автоматических-бэкапов)
7. [Проверка работы](#проверка-работы)
8. [Откат при проблемах](#откат-при-проблемах)

---

## Подготовка

### Требования

- Docker ≥ 20.10
- Docker Compose ≥ 2.0
- Доступ к репозиторию Git
- Резервная копия текущих данных (на всякий случай)

### Проверка Docker

```bash
docker --version
docker compose version
```

### Клонирование репозитория (если ещё не сделано)

```bash
git clone <your-repo-url> /opt/papi
cd /opt/papi
```

---

## Экспорт данных из текущей БД

### Шаг 1: Запуск экспорта

На сервере с текущей PostgreSQL выполните:

```bash
# Установите переменные окружения с параметрами вашей БД
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_USER="postgres"
export DB_NAME="papidb"
export PGPASSWORD="!6101987Sonya"

# Запустите скрипт экспорта (параметры можно не указывать, если используете значения по умолчанию)
bash scripts/export_db.sh
```

Или с явным указанием параметров:

```bash
PGPASSWORD="!6101987Sonya" bash scripts/export_db.sh \
    --host localhost \
    --port 5432 \
    --user postgres \
    --db papidb
```

### Шаг 2: Проверка бэкапа

```bash
ls -lh backups/
# Должны появиться файлы:
# - papi_backup_YYYYMMDD_HHMMSS.dump  (бинарный дамп)
# - papi_backup_YYYYMMDD_HHMMSS.sql.gz (SQL текст)
# - backup_metadata_YYYYMMDD_HHMMSS.json (метаданные)
```

### Шаг 3: Скопируйте бэкап на новый сервер

```bash
# Если новый сервер - это другая машина
scp backups/papi_backup_*.dump user@new-server:/opt/papi/backups/
```

---

## Настройка Docker-окружения

### Шаг 1: Настройка переменных окружения

```bash
# Скопируйте шаблон
cp .env.example .env

# Отредактируйте .env
nano .env
```

**Обязательно измените:**

- `POSTGRES_PASSWORD` — надёжный пароль для БД
- `SECRET_KEY` — случайный ключ для JWT
- `POSTGRES_USER` и `POSTGRES_DB` — если используете иные имена
- Порты (`APP_PORT`, `BACKEND_PORT`) — если нужно

### Шаг 2: Запуск Docker-контейнеров

```bash
# Запуск всех сервисов
docker compose up -d --build

# Проверка статуса
docker compose ps

# Проверка логов
docker compose logs -f
```

### Шаг 3: Проверка готовности БД

```bash
# Подождите 30-60 секунд пока PostgreSQL инициализируется
docker exec papi-db pg_isready -U papi -d papiDB

# Должно ответить: "/var/run/postgresql:5432 - accepting connections"
```

---

## Импорт данных в Docker-БД

### Шаг 1: Запуск импорта

```bash
# Укажите путь к бэкапу, созданному на шаге экспорта
bash scripts/import_db.sh ./backups/papi_backup_20260926_140000.dump
```

Или для SQL-дампа:

```bash
bash scripts/import_db.sh ./backups/papi_backup_20260926_140000.sql.gz
```

### Шаг 2: Проверка импорта

```bash
# Проверьте количество таблиц
docker exec papi-db psql -U papi -d papiDB -c "\dt"

# Проверьте данные
docker exec papi-db psql -U papi -d papiDB -c "SELECT count(*) FROM assets;"
docker exec papi-db psql -U papi -d papiDB -c "SELECT count(*) FROM users;"
```

### Шаг 3: Перезапуск приложения

```bash
# Пересоберите и перезапустите все сервисы
docker compose up -d --build

# Проверьте логи
docker compose logs -f backend
```

---

## Настройка автоматических обновлений

### Вариант 1: Ручной запуск

```bash
bash update.sh
```

Скрипт сам сделает бэкап БД, подтянет код из git, досоздаёт недостающие ключи
в `.env`, пересоберёт образы, поднимет контейнеры (`db`, `backend`, `frontend`
с nginx), отключит старые systemd-сервисы и проверит здоровье всех сервисов.

### Вариант 2: Автоматический запуск через cron

```bash
# Отредактируйте cron
crontab -e
```

Добавьте строку (ежедневное обновление в 3:00 ночи):

```cron
0 3 * * * /opt/papi/update.sh >> /var/log/papi-update.log 2>&1
```

### Настройка переменных (опционально)

```bash
```bash
# В начале скрипта update.sh можно изменить:
GIT_REPO="origin"      # Имя remote репозитория
GIT_BRANCH="main"      # Ветка для обновления
```

Лог пишется в `/var/log/papi-update.log`, если запись в `/var/log` доступна
(иначе — в `logs/update.log` внутри проекта).
```

---

## Настройка автоматических бэкапов

### Настройка cron для бэкапов

```bash
crontab -e
```

Добавьте строки из `scripts/papi.cron.example`:

```cron
# Ежедневный бэкап в 2:00 ночи
0 2 * * * /opt/papi/scripts/backup.sh >> /var/log/papi-backup.log 2>&1

# Еженедельный полный бэкап (хранение 90 дней)
0 1 * * 0 RETENTION_DAYS=90 /opt/papi/scripts/backup.sh >> /var/log/papi-weekly-backup.log 2>&1
```

### Проверка бэкапов

```bash
# Посмотрите последние бэкапы
ls -lh backups/

# Проверьте размер
du -sh backups/
```

### Ручной бэкап

```bash
bash scripts/backup.sh
```

---

## Проверка работы

### 1. Проверка всех сервисов

```bash
docker compose ps
```

Должно быть:

```
NAME              STATUS
papi-db           Up (healthy)
papi-backend      Up (healthy)
papi-frontend     Up
```

### 2. Проверка API

```bash
curl http://localhost:8888/docs
# Должно вернуться HTML со страницей Swagger UI (HTTP 200)
```

### 3. Проверка фронтенда

```bash
curl http://localhost
# Должно вернуться HTML фронтенда (HTTP 200)
```

### 4. Проверка базы данных

```bash
# Подключитесь к БД
docker exec -it papi-db psql -U papi -d papiDB

# Проверьте таблицы
\dt

# Выйти
\q
```

### 5. Проверка загруженных файлов

```bash
# Проверьте volume
docker volume ls | grep papi_uploads

# Проверьте содержимое
docker exec papi-backend ls -la /app/uploads
```

---

## Откат при проблемах

### Сценарий 1: После импорта данные некорректны

```bash
# Остановите сервисы
docker compose down

# Удалите volume с БД
docker volume rm papi_pgdata

# Пересоздайте БД
docker compose up -d db

# Подождите инициализации
sleep 30

# Импортируйте бэкап заново
bash scripts/import_db.sh ./backups/papi_backup_YYYYMMDD_HHMMSS.dump
```

### Сценарий 2: Приложение не запускается

```bash
# Посмотрите логи
docker compose logs backend
docker compose logs db

# Пересоберите
docker compose up -d --build

# Проверьте .env
cat .env
```

### Сценарий 3: Полный откат на bare-metal

```bash
# Остановите Docker
docker compose down -v

# Восстановите БД из бэкапа
PGPASSWORD=your-password psql -h localhost -U papi -d papiDB < backups/papi_backup_*.sql.gz

# Верните bare-metal: update.sh при переходе на Docker отключил systemd-сервисы
sudo systemctl enable --now postgresql nginx papi-backend

# Убедитесь, что контейнеры больше не держат порт 80 и БД
docker compose down
```

---

## Решение проблем

### Проблема: PostgreSQL не запускается

```bash
# Проверьте логи
docker logs papi-db

# Проверьте права на volume
docker volume inspect papi_pgdata

# Пересоздайте volume (ДАННЫЕ БУДУТ УДАЛЕНЫ)
docker compose down -v
docker compose up -d db
```

### Проблема: Backend не подключается к БД

```bash
# Проверьте DATABASE_URL
docker exec papi-backend env | grep DATABASE_URL

# Проверьте сеть
docker network ls
docker network inspect papi_default
```

### Проблема: Ошибка при импорте БД

```bash
# Попробуйте импортировать вручную
docker compose exec -i db psql -U papi -d papiDB < backup.sql

# Проверьте кодировку
docker exec papi-db psql -U papi -d papiDB -c "SHOW server_encoding;"
```

### Проблема: Конфликты при git pull

```bash
# Посмотрите неизменённые изменения
git status

# Сохраните их
git stash

# Обновите
git pull origin main

# Восстановите изменения
git stash pop
```

---

## Полезные команды

```bash
# Все логи
docker compose logs -f

# Перезапуск одного сервиса
docker compose restart backend

# Подключение к БД
docker exec -it papi-db psql -U papi -d papiDB

# Подключение к контейнеру backend
docker exec -it papi-backend bash

# Очистка неиспользуемых образов
docker system prune -a

# Мониторинг ресурсов
docker stats
```

---

## Контакты

При возникновении проблем обратитесь к документации проекта или создайте issue в репозитории.
