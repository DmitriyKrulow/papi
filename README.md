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


Совет: если порт по умолчанию уже используется, остановите отладчик и откройте палитру команд (Shift+cmd+P), найдите Debug: Add Configuration, выберите Python Debugger, а затем FastAPI. Это создаст пользовательский файл конфигурации в .vscode/launch.json, который вы сможете редактировать. Добавьте в "args":[] следующее, чтобы задать собственный порт: "--port=5000". Сохраните файл и перезапустите отладчик с помощью (F5).