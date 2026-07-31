my_project/
├── src/                           # Весь код приложения (корневой пакет)
│   ├── core/                      # 🔴 САМЫЙ ВНУТРЕННИЙ СЛОЙ (Сущности)
│   │   ├── entities/              # Бизнес-сущности (обычные dataclass/Pydantic)
│   │   │   ├── user.py
│   │   │   └── product.py
│   │   ├── value_objects/         # Объекты-значения (Email, Phone, Money)
│   │   └── exceptions/            # Бизнес-исключения (DomainError)
│   │
│   ├── use_cases/                 # 🟠 СЛОЙ ИНТЕРАКТОРОВ (Бизнес-логика)
│   │   ├── interfaces/            # Абстракции для внешнего мира (порты)
│   │   │   ├── repositories.py    # Абстрактные классы репозиториев
│   │   │   └── unit_of_work.py    # Абстракция транзакций
│   │   ├── auth/                  # Группировка по функционалу
│   │   │   ├── register_user.py   # Сценарий регистрации
│   │   │   └── login_user.py
│   │   └── dto/                   # Data Transfer Objects (вход/выход use_case)
│   │
│   ├── infrastructure/            # 🟡 ВНЕШНИЙ СЛОЙ (Адаптеры и драйверы)
│   │   ├── db/                    # Реализация репозиториев
│   │   │   ├── models/            # SQLAlchemy/Django ORM модели
│   │   │   ├── repositories/      # Конкретные имплементации (UserRepo)
│   │   │   └── migrations/        # Alembic миграции
│   │   ├── api/                   # Внешние сервисы (HTTP-клиенты)
│   │   │   └── payment_gateway.py
│   │   ├── message_bus/           # Очереди (RabbitMQ/Kafka)
│   │   └── ioc/                   # Внедрение зависимостей (DI-контейнер)
│   │
│   ├── presentation/              # 🟢 САМЫЙ ВНЕШНИЙ СЛОЙ (Интерфейсы ввода)
│   │   ├── http/                  # Веб-слой
│   │   │   ├── routers/           # Эндпоинты (FastAPI/Router)
│   │   │   ├── schemas/           # Pydantic-схемы для запросов/ответов
│   │   │   └── middlewares/       # Обработка ошибок, логирование
│   │   ├── cli/                   # Консольные команды (Click/Typer)
│   │   └── event_handlers/        # Обработчики входящих событий из очередей
│   │
│   └── shared/                    # 🟣 ОБЩИЙ КОД (сквозной функционал)
│       ├── config.py              # Настройки приложения (pydantic-settings)
│       ├── logging.py             # Настройка логов
│       └── utils.py               # Хелперы (без бизнес-логики!)
│
├── tests/                         # Зеркальное отражение src/
│   ├── unit/                      # Тесты сущностей и use_cases (моки)
│   ├── integration/               # Тесты с БД или внешними API
│   └── e2e/                       # Сквозные тесты (запрос -> ответ)
│
├── docker/                        # Dockerfile и docker-compose
├── scripts/                       # Скрипты для деплоя/миграций
├── pyproject.toml                 # Зависимости (poetry/pdm)
└── .env                           # Переменные окружения


## Запуск проекта

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

---

# pip install -r requirements.txt
# python.exe -m pip install --upgrade pip